from django.contrib import admin
from .models import Cupo, ListaEspera, LlenadoRuta

@admin.register(Cupo)
class CupoAdmin(admin.ModelAdmin):
    list_display = ("usuario", "ruta", "estado", "creado_en", "confirmado_en", "activo")
    list_filter = ("estado", "ruta__tipo", "ruta__nombre")
    search_fields = ("usuario__username", "ruta__nombre")
    readonly_fields = ("creado_en", "actualizado_en", "confirmado_en", "cancelado_en")
    actions = ["marcar_como_confirmados", "marcar_como_expirados"]

    @admin.action(description="Marcar cupos seleccionados como confirmados")
    def marcar_como_confirmados(self, request, queryset):
        for cupo in queryset:
            cupo.marcar_confirmado()

    @admin.action(description="Marcar cupos seleccionados como expirados")
    def marcar_como_expirados(self, request, queryset):
        for cupo in queryset:
            cupo.marcar_expirado()

@admin.register(ListaEspera)
class ListaEsperaAdmin(admin.ModelAdmin):
    list_display = ("usuario", "ruta", "posicion", "asignado", "creado_en")
    list_filter = ("ruta__nombre", "asignado")
    search_fields = ("usuario__username", "ruta__nombre")
    ordering = ["ruta", "posicion"]

@admin.register(LlenadoRuta)
class LlenadoRutaAdmin(admin.ModelAdmin):
    list_display = ("ruta", "conductor", "tipo", "cupos_ocupados", "total_cupos", "fecha")
    list_filter = ("tipo", "ruta__tipo")
    search_fields = ("ruta__nombre", "conductor__username")
    readonly_fields = ("fecha",)
    ordering = ["-fecha"]
