# rutas/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rutas.views import (
    RutaViewSet,
    BusViewSet,
    HorarioRutaViewSet,
    BusRutaViewSet,
    RutaParadaViewSet,
    DesvioViewSet,
    HistorialRutaViewSet,
)

router = DefaultRouter()
router.register(r"rutas", RutaViewSet, basename="rutas")
router.register(r"buses", BusViewSet, basename="buses")
router.register(r"horarios", HorarioRutaViewSet, basename="horarios")
router.register(r"bus-rutas", BusRutaViewSet, basename="busrutas")
router.register(r"ruta-paradas", RutaParadaViewSet, basename="rutaparadas")
router.register(r"desvios", DesvioViewSet, basename="desvios")
router.register(r"historial", HistorialRutaViewSet, basename="historialrutas")

urlpatterns = [
    path("", include(router.urls)),
]
