from django.contrib import admin
from .models import Ruta, RutaParada, Desvio, HistorialRuta

class RutaParadaInline(admin.TabularInline):
    model = RutaParada
    extra = 0
    autocomplete_fields = ["parada"]
    ordering = ["orden"]
    readonly_fields = ["tiempo_estimado"]

@admin.register(Ruta)
class RutaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tipo", "estado", "vehiculo", "conductor", "hora_salida", "capacidad_total")
    list_filter = ("tipo", "estado", "conductor")
    search_fields = ("nombre", "vehiculo", "conductor__username", "conductor__first_name")
    inlines = [RutaParadaInline]
    readonly_fields = ("creada_en", "actualizada_en")
    ordering = ["hora_salida"]

@admin.register(RutaParada)
class RutaParadaAdmin(admin.ModelAdmin):
    list_display = ("ruta", "parada", "orden", "tiempo_estimado")
    list_filter = ("ruta",)
    search_fields = ("ruta__nombre", "parada__nombre")
    ordering = ["ruta", "orden"]

@admin.register(Desvio)
class DesvioAdmin(admin.ModelAdmin):
    list_display = ("ruta", "descripcion", "inicio", "fin", "activo")
    list_filter = ("activo", "ruta")
    search_fields = ("ruta__nombre", "descripcion")
    readonly_fields = ("inicio",)

@admin.register(HistorialRuta)
class HistorialRutaAdmin(admin.ModelAdmin):
    list_display = ("ruta", "evento", "timestamp", "usuario")
    list_filter = ("ruta", "evento")
    search_fields = ("ruta__nombre", "evento", "usuario__username")
    readonly_fields = ("timestamp",)
    ordering = ["-timestamp"]
