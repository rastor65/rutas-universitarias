# cupos/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from cupos.views import CupoViewSet, LlenadoRutaViewSet

router = DefaultRouter()
router.register(r"cupos", CupoViewSet, basename="cupos")
router.register(r"llenados", LlenadoRutaViewSet, basename="llenados")

urlpatterns = [
    path("", include(router.urls)),
]
