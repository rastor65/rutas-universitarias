from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import HasRoleResourcePermission
from paradas.models import Parada, ZonaParada
from paradas.serializers import ParadaSerializer, ZonaParadaSerializer
from accounts.audit import AuditMixin


class ZonaParadaViewSet(AuditMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestionar zonas de paradas.
    """
    queryset = ZonaParada.objects.all().order_by("nombre")
    serializer_class = ZonaParadaSerializer
    permission_classes = [IsAuthenticated, HasRoleResourcePermission]


class ParadaViewSet(AuditMixin, viewsets.ModelViewSet):
    """
    ViewSet para gestionar las paradas de las rutas.
    """
    queryset = Parada.objects.select_related("zona").prefetch_related("rutas").all()
    serializer_class = ParadaSerializer
    permission_classes = [IsAuthenticated, HasRoleResourcePermission]
