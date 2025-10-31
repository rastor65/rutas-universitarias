from django.contrib import admin
from cupos.admin import LlenadoRutaInline, LlenadoRutaInline
from cupos.models import Cupo
from .models import (
    Ruta,
    Bus,
    BusRuta,
    HorarioRuta,
    RutaParada,
    Desvio,
    HistorialRuta,
)

# === INLINES ===
class CupoInline(admin.TabularInline):
    model = Cupo
    extra = 0
    fields = ("usuario", "estado", "es_lista_espera", "horario", "creado_en")
    readonly_fields = ("usuario", "estado", "es_lista_espera", "horario", "creado_en")
    can_delete = False
    ordering = ("-creado_en",)
    verbose_name_plural = "Cupos asociados"

class HorarioRutaInline(admin.TabularInline):
    model = HorarioRuta
    extra = 1
    fields = ("hora_salida", "hora_llegada_estimada", "activo", "observaciones")
    ordering = ("hora_salida",)
    show_change_link = True


class BusRutaInline(admin.TabularInline):
    model = BusRuta
    extra = 0
    autocomplete_fields = ["bus"]
    readonly_fields = ["fecha_asignacion"]
    ordering = ("-fecha_asignacion",)


class RutaParadaInline(admin.TabularInline):
    model = RutaParada
    extra = 0
    autocomplete_fields = ["parada"]
    ordering = ("orden",)


class DesvioInline(admin.TabularInline):
    model = Desvio
    extra = 0
    readonly_fields = ("inicio", "fin", "distancia_desviacion", "descripcion", "detectado_automaticamente")
    can_delete = False


# === ADMIN PRINCIPALES ===

@admin.register(Ruta)
class RutaAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tipo", "estado", "conductor", "capacidad_total", "capacidad_espera", "creada_en")
    list_filter = ("tipo", "estado")
    search_fields = ("nombre", "conductor__username")
    ordering = ("nombre",)
    inlines = [HorarioRutaInline, BusRutaInline, RutaParadaInline, DesvioInline, CupoInline, LlenadoRutaInline]


@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = ("placa", "modelo", "capacidad", "activo")
    search_fields = ("placa", "modelo")
    list_filter = ("activo",)
    ordering = ("placa",)


@admin.register(HorarioRuta)
class HorarioRutaAdmin(admin.ModelAdmin):
    list_display = ("ruta", "hora_salida", "hora_llegada_estimada", "activo")
    list_filter = ("activo", "ruta")
    ordering = ("ruta", "hora_salida")
    search_fields = ("ruta__nombre",)


@admin.register(BusRuta)
class BusRutaAdmin(admin.ModelAdmin):
    list_display = ("bus", "ruta", "fecha_asignacion", "activo")
    list_filter = ("activo", "ruta")
    readonly_fields = ("fecha_asignacion",)
    search_fields = ("bus__placa", "ruta__nombre")


@admin.register(Desvio)
class DesvioAdmin(admin.ModelAdmin):
    list_display = ("ruta", "inicio", "fin", "distancia_desviacion", "activo", "detectado_automaticamente")
    list_filter = ("activo", "detectado_automaticamente")
    readonly_fields = ("inicio", "fin", "descripcion", "detectado_automaticamente")
    ordering = ("-inicio",)
    search_fields = ("ruta__nombre", "descripcion")


@admin.register(HistorialRuta)
class HistorialRutaAdmin(admin.ModelAdmin):
    list_display = ("ruta", "evento", "timestamp", "usuario")
    list_filter = ("evento", "timestamp")
    search_fields = ("ruta__nombre", "evento", "usuario__username")
    ordering = ("-timestamp",)
