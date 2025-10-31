# paradas/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from paradas.views import ParadaViewSet, ZonaParadaViewSet

router = DefaultRouter()
router.register(r"paradas", ParadaViewSet, basename="paradas")
router.register(r"zonas", ZonaParadaViewSet, basename="zonasparada")

urlpatterns = [
    path("", include(router.urls)),
]
