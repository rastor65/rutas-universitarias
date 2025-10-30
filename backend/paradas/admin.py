from django.contrib import admin
from .models import Parada, ZonaParada

@admin.register(ZonaParada)
class ZonaParadaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "descripcion")
    search_fields = ("nombre",)

@admin.register(Parada)
class ParadaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "zona", "latitud", "longitud", "activa", "creada_en")
    list_filter = ("zona", "activa")
    search_fields = ("nombre", "direccion", "zona__nombre")
    readonly_fields = ("creada_en", "actualizada_en")
    ordering = ["nombre"]

    def ver_en_mapa(self, obj):
        """Enlace rápido a Google Maps."""
        if obj.latitud and obj.longitud:
            return f"https://www.google.com/maps?q={obj.latitud},{obj.longitud}"
        return "-"
    ver_en_mapa.short_description = "Ver en mapa (Google Maps)"
