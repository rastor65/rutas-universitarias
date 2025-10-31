# gps/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from gps.views import PosicionViewSet, TrayectoViewSet, AlertaGPSViewSet

router = DefaultRouter()
router.register(r"posiciones", PosicionViewSet, basename="gpsposiciones")
router.register(r"trayectos", TrayectoViewSet, basename="gpstrayectos")
router.register(r"alertas", AlertaGPSViewSet, basename="gpsalertas")

urlpatterns = [
    path("", include(router.urls)),
]
