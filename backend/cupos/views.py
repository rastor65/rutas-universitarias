# cupos/views.py

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import HasRoleResourcePermission
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count
from accounts.audit import AuditMixin

from .models import Cupo, LlenadoRuta
from .serializers import CupoSerializer, LlenadoRutaSerializer
from rutas.models import Ruta


# === CUPOS ===
class CupoViewSet(AuditMixin, viewsets.ModelViewSet):
    """
    Gestiona las reservas de cupos para rutas universitarias.
    Permite creación automática, confirmación, cancelación y promoción.
    """
    queryset = Cupo.objects.select_related("usuario", "ruta", "horario")
    serializer_class = CupoSerializer
    permission_classes = [IsAuthenticated, HasRoleResourcePermission]
    filter_backends = [filters.SearchFilter]
    search_fields = ["usuario__username", "ruta__nombre", "estado"]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return self.queryset
        # Los usuarios normales solo ven sus propias reservas
        return self.queryset.filter(usuario=user)

    @action(detail=False, methods=["post"])
    def reservar(self, request):
        """
        Reserva un cupo automáticamente para el próximo horario disponible.
        """
        user = request.user
        ruta_id = request.data.get("ruta_id")

        if not ruta_id:
            return Response({"error": "Debe indicar el ID de la ruta."}, status=400)

        try:
            ruta = Ruta.objects.get(id=ruta_id)
            cupo = Cupo.crear_automaticamente(user, ruta)
        except Ruta.DoesNotExist:
            return Response({"error": "Ruta no encontrada."}, status=404)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)

        serializer = self.get_serializer(cupo)
        return Response(serializer.data, status=201)

    @action(detail=True, methods=["post"])
    def confirmar(self, request, pk=None):
        """
        Confirma la asistencia antes de la salida.
        """
        cupo = self.get_object()
        cupo.marcar_confirmado()
        return Response({"message": "Cupo confirmado correctamente."})

    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        """
        Permite cancelar la reserva antes de la salida.
        """
        cupo = self.get_object()
        cupo.marcar_cancelado()
        return Response({"message": "Cupo cancelado y liberado."})

    @action(detail=False, methods=["get"])
    def activos(self, request):
        """Lista los cupos activos del usuario."""
        activos = self.get_queryset().filter(activo=True, es_lista_espera=False)
        serializer = self.get_serializer(activos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def lista_espera(self, request):
        """Lista los cupos que están en lista de espera."""
        espera = self.get_queryset().filter(es_lista_espera=True, activo=True)
        serializer = self.get_serializer(espera, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def resumen(self, request):
        """
        Devuelve un resumen general del estado de cupos del usuario.
        """
        user = request.user
        data = {
            "activos": user.cupos.filter(activo=True, es_lista_espera=False).count(),
            "espera": user.cupos.filter(es_lista_espera=True, activo=True).count(),
            "ocupados": user.cupos.filter(estado="OCUPADO").count(),
            "cancelados": user.cupos.filter(estado="CANCELADO").count(),
        }
        return Response(data)
        

# === LLENADOS ===
class LlenadoRutaViewSet(viewsets.ModelViewSet):
    """
    Controla los registros de llenado de rutas (manuales o automáticos).
    En rutas de regreso, los llenados pueden ser detectados por GPS.
    """
    queryset = LlenadoRuta.objects.select_related("ruta", "conductor")
    serializer_class = LlenadoRutaSerializer
    permission_classes = [IsAuthenticated, HasRoleResourcePermission]
    filter_backends = [filters.SearchFilter]
    search_fields = ["ruta__nombre", "conductor__username"]

    @action(detail=False, methods=["post"])
    def registrar_manual(self, request):
        """
        Permite al conductor registrar manualmente el llenado de su ruta.
        """
        ruta_id = request.data.get("ruta_id")
        cupos_ocupados = request.data.get("cupos_ocupados")

        if not ruta_id or not cupos_ocupados:
            return Response({"error": "Debe indicar ruta_id y cupos_ocupados."}, status=400)

        try:
            ruta = Ruta.objects.get(id=ruta_id)
        except Ruta.DoesNotExist:
            return Response({"error": "Ruta no encontrada."}, status=404)

        llenado = LlenadoRuta.objects.create(
            ruta=ruta,
            conductor=request.user,
            tipo="MANUAL",
            cupos_ocupados=int(cupos_ocupados),
            total_cupos=ruta.capacidad_total,
            observaciones="Registro manual por conductor."
        )
        serializer = self.get_serializer(llenado)
        return Response(serializer.data, status=201)

    @action(detail=False, methods=["get"])
    def ultimos(self, request):
        """Muestra los últimos registros de llenado."""
        llenados = self.get_queryset()[:20]
        serializer = self.get_serializer(llenados, many=True)
        return Response(serializer.data)
