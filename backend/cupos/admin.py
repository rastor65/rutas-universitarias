from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Cupo, LlenadoRuta, EstadoCupo


# === INLINES ===

class LlenadoRutaInline(admin.TabularInline):
    model = LlenadoRuta
    extra = 0
    readonly_fields = ("fecha", "tipo", "cupos_ocupados", "total_cupos", "observaciones")
    can_delete = False
    ordering = ("-fecha",)
    verbose_name = "Registro de llenado"
    verbose_name_plural = "Historial de llenados"


# === ADMIN PRINCIPAL: CUPOS ===

@admin.register(Cupo)
class CupoAdmin(admin.ModelAdmin):
    list_display = (
        "usuario",
        "ruta",
        "get_horario",
        "get_estado_coloreado",
        "es_lista_espera",
        "activo",
        "creado_en",
        "confirmado_en",
    )
    list_filter = (
        "estado",
        "es_lista_espera",
        "ruta__nombre",
        "horario__hora_salida",
        "activo",
    )
    search_fields = ("usuario__username", "usuario__email", "ruta__nombre")
    ordering = ("-creado_en",)
    list_per_page = 30
    readonly_fields = (
        "creado_en",
        "actualizado_en",
        "confirmado_en",
        "cancelado_en",
        "expirado_en",
    )

    fieldsets = (
        ("Información general", {
            "fields": (
                "usuario",
                "ruta",
                "horario",
                "estado",
                "activo",
                "es_lista_espera",
            )
        }),
        ("Tiempos", {
            "fields": (
                "creado_en",
                "actualizado_en",
                "confirmado_en",
                "cancelado_en",
                "expirado_en",
            )
        }),
    )

    # === MÉTODOS PERSONALIZADOS ===

    def get_horario(self, obj):
        if obj.horario:
            return obj.horario.hora_salida.strftime("%H:%M")
        return "—"
    get_horario.short_description = "Horario"

    def get_estado_coloreado(self, obj):
        colores = {
            EstadoCupo.RESERVADO: "orange",
            EstadoCupo.CONFIRMADO: "green",
            EstadoCupo.CANCELADO: "gray",
            EstadoCupo.EXPIRADO: "red",
            EstadoCupo.OCUPADO: "blue",
        }
        color = colores.get(obj.estado, "black")

        # Si es lista de espera, resaltarlo en violeta
        if obj.es_lista_espera:
            color = "purple"

        return format_html(f'<b style="color:{color};">{obj.estado}</b>')
    get_estado_coloreado.short_description = "Estado"

    # === ACCIONES MASIVAS ===

    actions = [
        "accion_confirmar",
        "accion_cancelar",
        "accion_expirar",
        "accion_promover_siguiente",
    ]

    @admin.action(description="Confirmar cupos seleccionados")
    def accion_confirmar(self, request, queryset):
        count = queryset.update(
            estado=EstadoCupo.CONFIRMADO, confirmado_en=timezone.now()
        )
        self.message_user(request, f"{count} cupos confirmados correctamente.")

    @admin.action(description="Cancelar cupos seleccionados")
    def accion_cancelar(self, request, queryset):
        count = queryset.update(
            estado=EstadoCupo.CANCELADO,
            cancelado_en=timezone.now(),
            activo=False,
        )
        self.message_user(request, f"{count} cupos cancelados correctamente.")

    @admin.action(description="Marcar cupos como expirados")
    def accion_expirar(self, request, queryset):
        count = queryset.update(
            estado=EstadoCupo.EXPIRADO,
            expirado_en=timezone.now(),
            activo=False,
        )
        self.message_user(request, f"{count} cupos marcados como expirados.")

    @admin.action(description="Promover siguiente en lista de espera")
    def accion_promover_siguiente(self, request, queryset):
        """
        Promueve manualmente al siguiente usuario en lista de espera
        de la ruta seleccionada.
        """
        rutas_promovidas = set()
        for cupo in queryset:
            from cupos.models import Cupo as CupoModel
            promovido = CupoModel.promover_siguiente(cupo.ruta)
            if promovido:
                rutas_promovidas.add(cupo.ruta.nombre)
        if rutas_promovidas:
            self.message_user(request, f"Promovidos cupos en rutas: {', '.join(rutas_promovidas)}.")
        else:
            self.message_user(request, "No había usuarios en lista de espera.")


# === ADMIN DE LLENADOS ===

@admin.register(LlenadoRuta)
class LlenadoRutaAdmin(admin.ModelAdmin):
    list_display = (
        "ruta",
        "get_conductor",
        "get_tipo_coloreado",
        "cupos_ocupados",
        "total_cupos",
        "fecha",
    )
    list_filter = ("tipo", "ruta__nombre", "fecha")
    search_fields = ("ruta__nombre", "conductor__username")
    readonly_fields = ("fecha", "tipo", "cupos_ocupados", "total_cupos", "observaciones")
    ordering = ("-fecha",)
    list_per_page = 25

    def get_conductor(self, obj):
        return obj.conductor or "—"
    get_conductor.short_description = "Conductor"

    def get_tipo_coloreado(self, obj):
        color = "green" if obj.tipo == "AUTOMATICO" else "blue"
        return format_html(f'<b style="color:{color};">{obj.get_tipo_display()}</b>')
    get_tipo_coloreado.short_description = "Tipo"
