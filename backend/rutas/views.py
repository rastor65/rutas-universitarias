# rutas/views.py

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import HasRoleResourcePermission
from accounts.audit import AuditMixin

from .models import (
    Bus,
    Ruta,
    HorarioRuta,
    BusRuta,
    RutaParada,
    Desvio,
    HistorialRuta,
)
from .serializers import (
    BusSerializer,
    RutaSerializer,
    HorarioRutaSerializer,
    BusRutaSerializer,
    RutaParadaSerializer,
    DesvioSerializer,
    HistorialRutaSerializer,
)


# === BUS ===
class BusViewSet(AuditMixin, viewsets.ModelViewSet):
    queryset = Bus.objects.all()
    serializer_class = BusSerializer
    permission_classes = [IsAuthenticated, ]
    filter_backends = [filters.SearchFilter]
    search_fields = ["placa", "modelo"]

    @action(detail=False, methods=["get"])
    def activos(self, request):
        """Lista de buses activos."""
        activos = self.get_queryset().filter(activo=True)
        serializer = self.get_serializer(activos, many=True)
        return Response(serializer.data)


# === RUTA ===
class RutaViewSet(AuditMixin, viewsets.ModelViewSet):
    queryset = Ruta.objects.prefetch_related("buses", "horarios", "paradas")
    serializer_class = RutaSerializer
    permission_classes = [IsAuthenticated, HasRoleResourcePermission]
    filter_backends = [filters.SearchFilter]
    search_fields = ["nombre", "tipo", "estado"]

    @action(detail=True, methods=["get"])
    def resumen(self, request, pk=None):
        """
        Devuelve un resumen general de la ruta:
        capacidad, ocupación y estado.
        """
        ruta = self.get_object()
        data = {
            "nombre": ruta.nombre,
            "tipo": ruta.get_tipo_display(),
            "estado": ruta.get_estado_display(),
            "capacidad_total": ruta.capacidad_total,
            "capacidad_espera": ruta.capacidad_espera,
            "buses_asignados": ruta.buses.count(),
            "horarios_disponibles": ruta.horarios.filter(activo=True).count(),
            "paradas": ruta.paradas.count(),
        }
        return Response(data)

    @action(detail=True, methods=["post"])
    def cambiar_estado(self, request, pk=None):
        """
        Cambia el estado de una ruta (Programada, En curso, Finalizada, Cancelada).
        """
        ruta = self.get_object()
        nuevo_estado = request.data.get("estado")

        if nuevo_estado not in dict(ruta._meta.get_field("estado").choices):
            return Response({"error": "Estado inválido."}, status=400)

        ruta.estado = nuevo_estado
        ruta.save(update_fields=["estado"])

        # Registrar en historial
        HistorialRuta.objects.create(
            ruta=ruta,
            evento=f"Cambio de estado: {nuevo_estado}",
            usuario=request.user,
        )

        return Response({"message": f"Ruta actualizada a {nuevo_estado}."})


# === HORARIO RUTA ===
class HorarioRutaViewSet(viewsets.ModelViewSet):
    queryset = HorarioRuta.objects.select_related("ruta")
    serializer_class = HorarioRutaSerializer
    permission_classes = [IsAuthenticated, HasRoleResourcePermission]
    filter_backends = [filters.SearchFilter]
    search_fields = ["ruta__nombre"]

    @action(detail=False, methods=["get"])
    def proximos(self, request):
        """Lista los horarios próximos a ejecutarse."""
        ahora = timezone.localtime().time()
        proximos = self.get_queryset().filter(hora_salida__gt=ahora, activo=True)[:10]
        serializer = self.get_serializer(proximos, many=True)
        return Response(serializer.data)


# === BUS-RUTA ===
class BusRutaViewSet(viewsets.ModelViewSet):
    queryset = BusRuta.objects.select_related("bus", "ruta")
    serializer_class = BusRutaSerializer
    permission_classes = [IsAuthenticated, HasRoleResourcePermission]


# === RUTA-PARADA ===
class RutaParadaViewSet(viewsets.ModelViewSet):
    queryset = RutaParada.objects.select_related("ruta", "parada")
    serializer_class = RutaParadaSerializer
    permission_classes = [IsAuthenticated, HasRoleResourcePermission]
    filter_backends = [filters.SearchFilter]
    search_fields = ["ruta__nombre", "parada__nombre"]

    @action(detail=False, methods=["get"])
    def por_ruta(self, request):
        """Filtra las paradas por ID de ruta."""
        ruta_id = request.query_params.get("ruta_id")
        if not ruta_id:
            return Response({"error": "Debe indicar 'ruta_id'."}, status=400)
        paradas = self.get_queryset().filter(ruta_id=ruta_id)
        serializer = self.get_serializer(paradas, many=True)
        return Response(serializer.data)


# === DESVÍOS ===
class DesvioViewSet(AuditMixin, viewsets.ModelViewSet):
    queryset = Desvio.objects.select_related("ruta", "horario", "creado_por")
    serializer_class = DesvioSerializer
    permission_classes = [IsAuthenticated, HasRoleResourcePermission]
    filter_backends = [filters.SearchFilter]
    search_fields = ["ruta__nombre"]

    @action(detail=False, methods=["get"])
    def activos(self, request):
        """Lista los desvíos activos."""
        activos = self.get_queryset().filter(activo=True)
        serializer = self.get_serializer(activos, many=True)
        return Response(serializer.data)


# === HISTORIAL DE RUTA ===
class HistorialRutaViewSet(AuditMixin, viewsets.ReadOnlyModelViewSet):
    queryset = HistorialRuta.objects.select_related("ruta", "usuario")
    serializer_class = HistorialRutaSerializer
    permission_classes = [IsAuthenticated, HasRoleResourcePermission]
    filter_backends = [filters.SearchFilter]
    search_fields = ["ruta__nombre", "evento", "usuario__username"]

    @action(detail=False, methods=["get"])
    def por_ruta(self, request):
        """Filtra eventos por ruta."""
        ruta_id = request.query_params.get("ruta_id")
        if not ruta_id:
            return Response({"error": "Debe indicar 'ruta_id'."}, status=400)
        eventos = self.get_queryset().filter(ruta_id=ruta_id)
        serializer = self.get_serializer(eventos, many=True)
        return Response(serializer.data)
