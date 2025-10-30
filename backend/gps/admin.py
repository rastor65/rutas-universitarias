from django.contrib import admin
from .models import Posicion, Trayecto, AlertaGPS

@admin.register(Posicion)
class PosicionAdmin(admin.ModelAdmin):
    list_display = ("origen_tipo", "origen_id", "latitud", "longitud", "estado", "timestamp", "ruta")
    list_filter = ("origen_tipo", "estado", "ruta__nombre")
    search_fields = ("origen_id", "ruta__nombre")
    readonly_fields = ("timestamp",)
    ordering = ["-timestamp"]

    def ver_en_mapa(self, obj):
        """Enlace directo a Google Maps."""
        if obj.latitud and obj.longitud:
            return f"https://www.google.com/maps?q={obj.latitud},{obj.longitud}"
        return "-"
    ver_en_mapa.short_description = "Ver en mapa"

@admin.register(Trayecto)
class TrayectoAdmin(admin.ModelAdmin):
    list_display = ("ruta", "conductor", "fecha_inicio", "fecha_fin", "distancia_recorrida_km", "finalizado")
    list_filter = ("finalizado", "ruta__nombre", "conductor")
    search_fields = ("ruta__nombre", "conductor__username")
    readonly_fields = ("fecha_inicio", "fecha_fin")
    actions = ["marcar_finalizados"]

    @admin.action(description="Marcar trayectos seleccionados como finalizados")
    def marcar_finalizados(self, request, queryset):
        for trayecto in queryset.filter(finalizado=False):
            trayecto.finalizar()

@admin.register(AlertaGPS)
class AlertaGPSAdmin(admin.ModelAdmin):
    list_display = ("tipo", "ruta", "detectada_en", "resuelta", "resuelta_en", "resuelta_por")
    list_filter = ("resuelta", "ruta__nombre")
    search_fields = ("tipo", "descripcion", "ruta__nombre")
    readonly_fields = ("detectada_en",)
    ordering = ["-detectada_en"]
    actions = ["marcar_resueltas"]

    @admin.action(description="Marcar alertas seleccionadas como resueltas")
    def marcar_resueltas(self, request, queryset):
        for alerta in queryset.filter(resuelta=False):
            alerta.marcar_resuelta(usuario=request.user)
