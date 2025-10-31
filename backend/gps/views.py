# gps/views.py

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import HasRoleResourcePermission
from django.utils import timezone
from django.db.models import Count
from accounts.audit import AuditMixin

from .models import Posicion, Trayecto, AlertaGPS
from .serializers import PosicionSerializer, TrayectoSerializer, AlertaGPSSerializer
from .utils import detectar_desvio
from rutas.models import Ruta


# === POSICIONES ===
class PosicionViewSet(viewsets.ModelViewSet):
    """
    Registra posiciones GPS (usuarios o vehículos).
    Si es un vehículo asociado a una ruta, se verifica automáticamente si hay desvío.
    """
    queryset = Posicion.objects.select_related("ruta")
    serializer_class = PosicionSerializer
    permission_classes = [IsAuthenticated, HasRoleResourcePermission]
    filter_backends = [filters.SearchFilter]
    search_fields = ["origen_tipo", "estado", "ruta__nombre"]

    def perform_create(self, serializer):
        posicion = serializer.save()

        # Detectar desvío automáticamente (solo si la posición tiene ruta)
        if posicion.ruta:
            detectar_desvio(
                ruta=posicion.ruta,
                lat_actual=float(posicion.latitud),
                lon_actual=float(posicion.longitud)
            )

    @action(detail=False, methods=["get"])
    def recientes(self, request):
        """
        Lista las últimas posiciones registradas.
        """
        recientes = self.get_queryset()[:30]
        serializer = self.get_serializer(recientes, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def por_ruta(self, request):
        """Filtra posiciones por ruta."""
        ruta_id = request.query_params.get("ruta_id")
        if not ruta_id:
            return Response({"error": "Debe indicar 'ruta_id'."}, status=400)
        posiciones = self.get_queryset().filter(ruta_id=ruta_id)
        serializer = self.get_serializer(posiciones, many=True)
        return Response(serializer.data)


# === TRAYECTOS ===
class TrayectoViewSet(viewsets.ModelViewSet):
    """
    Gestiona los recorridos GPS completos (inicio-fin) de un bus o conductor.
    """
    queryset = Trayecto.objects.select_related("ruta", "conductor")
    serializer_class = TrayectoSerializer
    permission_classes = [IsAuthenticated, HasRoleResourcePermission]
    filter_backends = [filters.SearchFilter]
    search_fields = ["ruta__nombre", "conductor__username"]

    @action(detail=True, methods=["post"])
    def finalizar(self, request, pk=None):
        """
        Marca un trayecto como finalizado.
        Calcula automáticamente duración y distancia (si se pasa como parámetro).
        """
        trayecto = self.get_object()
        distancia_km = request.data.get("distancia_km")
        trayecto.finalizar(distancia_km)
        serializer = self.get_serializer(trayecto)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def iniciar(self, request):
        """
        Inicia un nuevo trayecto para una ruta.
        Si el conductor ya tiene uno activo, lo devuelve.
        """
        ruta_id = request.data.get("ruta_id")
        if not ruta_id:
            return Response({"error": "Debe indicar 'ruta_id'."}, status=400)

        try:
            ruta = Ruta.objects.get(id=ruta_id)
        except Ruta.DoesNotExist:
            return Response({"error": "Ruta no encontrada."}, status=404)

        trayecto_activo = Trayecto.objects.filter(ruta=ruta, finalizado=False).first()
        if trayecto_activo:
            serializer = self.get_serializer(trayecto_activo)
            return Response(serializer.data)

        trayecto = Trayecto.objects.create(
            ruta=ruta,
            conductor=request.user,
            fecha_inicio=timezone.now(),
        )
        serializer = self.get_serializer(trayecto)
        return Response(serializer.data, status=201)

    @action(detail=False, methods=["get"])
    def activos(self, request):
        """Muestra trayectos en curso."""
        activos = self.get_queryset().filter(finalizado=False)
        serializer = self.get_serializer(activos, many=True)
        return Response(serializer.data)


# === ALERTAS GPS ===
class AlertaGPSViewSet(viewsets.ModelViewSet):
    """
    Registra y gestiona alertas automáticas (desvíos, fuera de zona, sin señal, etc.).
    """
    queryset = AlertaGPS.objects.select_related("ruta", "posicion", "resuelta_por")
    serializer_class = AlertaGPSSerializer
    permission_classes = [IsAuthenticated, HasRoleResourcePermission]
    filter_backends = [filters.SearchFilter]
    search_fields = ["ruta__nombre", "tipo", "resuelta"]

    @action(detail=False, methods=["get"])
    def activas(self, request):
        """Lista las alertas GPS no resueltas."""
        activas = self.get_queryset().filter(resuelta=False)
        serializer = self.get_serializer(activas, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def resolver(self, request, pk=None):
        """Marca una alerta como resuelta."""
        alerta = self.get_object()
        alerta.marcar_resuelta(request.user)
        return Response({"message": "Alerta marcada como resuelta."})

    @action(detail=False, methods=["post"])
    def registrar(self, request):
        """
        Registra una alerta GPS manual o generada por sistema.
        """
        ruta_id = request.data.get("ruta_id")
        tipo = request.data.get("tipo")
        descripcion = request.data.get("descripcion", "")
        posicion_id = request.data.get("posicion_id")

        if not (ruta_id and tipo):
            return Response({"error": "Debe indicar ruta_id y tipo de alerta."}, status=400)

        alerta = AlertaGPS.objects.create(
            ruta_id=ruta_id,
            tipo=tipo,
            descripcion=descripcion,
            posicion_id=posicion_id,
            detectada_en=timezone.now(),
        )
        serializer = self.get_serializer(alerta)
        return Response(serializer.data, status=201)
