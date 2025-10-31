#cupos/models.py

import uuid
from django.db import models
from django.utils import timezone
from django.conf import settings


class EstadoCupo(models.TextChoices):
    RESERVADO = "RESERVADO", "Reservado"
    CONFIRMADO = "CONFIRMADO", "Confirmado (en zona)"
    CANCELADO = "CANCELADO", "Cancelado"
    EXPIRADO = "EXPIRADO", "Expirado (no llegó a tiempo)"
    OCUPADO = "OCUPADO", "Ocupado (ruta de regreso)"


class Cupo(models.Model):
    """
    Representa la reserva o uso de un cupo en una ruta.
    Solo se permiten reservas en rutas de tipo IDA.
    En rutas de REGRESO los cupos se marcan automáticamente por GPS.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cupos")
    ruta = models.ForeignKey("rutas.Ruta", on_delete=models.CASCADE, related_name="cupos")
    horario = models.ForeignKey("rutas.HorarioRuta", on_delete=models.SET_NULL, null=True, blank=True, related_name="cupos")
    estado = models.CharField(max_length=20, choices=EstadoCupo.choices, default=EstadoCupo.RESERVADO)
    activo = models.BooleanField(default=True)
    es_lista_espera = models.BooleanField(default=False, help_text="Indica si este cupo fue tomado como lista de espera automática.")
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    confirmado_en = models.DateTimeField(blank=True, null=True)
    cancelado_en = models.DateTimeField(blank=True, null=True)
    expirado_en = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ("usuario", "ruta", "horario")
        ordering = ["-creado_en"]
        verbose_name = "Cupo"
        verbose_name_plural = "Cupos"

    def __str__(self):
        return f"{self.usuario} - {self.ruta.nombre} ({'Espera' if self.es_lista_espera else 'Cupo'})"

    # === MÉTODOS DE ESTADO ===

    def marcar_confirmado(self):
        self.estado = EstadoCupo.CONFIRMADO
        self.confirmado_en = timezone.now()
        self.save(update_fields=["estado", "confirmado_en", "actualizado_en"])

    def marcar_expirado(self):
        self.estado = EstadoCupo.EXPIRADO
        self.activo = False
        self.expirado_en = timezone.now()
        self.save(update_fields=["estado", "activo", "expirado_en", "actualizado_en"])
        Cupo.promover_siguiente(self.ruta)

    def marcar_cancelado(self):
        self.estado = EstadoCupo.CANCELADO
        self.activo = False
        self.cancelado_en = timezone.now()
        self.save(update_fields=["estado", "activo", "cancelado_en", "actualizado_en"])
        Cupo.promover_siguiente(self.ruta)

    def marcar_ocupado(self):
        self.estado = EstadoCupo.OCUPADO
        self.activo = False
        self.save(update_fields=["estado", "activo", "actualizado_en"])

    # === LÓGICA AUTOMÁTICA ===

    @staticmethod
    def crear_automaticamente(usuario, ruta):
        """
        Intenta crear un cupo automáticamente para el siguiente horario disponible.
        Si los cupos están llenos, agrega al usuario a lista de espera automática.
        """
        from rutas.models import HorarioRuta

        ahora = timezone.localtime().time()
        horario_disponible = (
            ruta.horarios.filter(hora_salida__gt=ahora, activo=True)
            .order_by("hora_salida")
            .first()
        )
        if not horario_disponible:
            raise ValueError("No hay horarios disponibles para reservar.")

        cupos_activos = Cupo.objects.filter(ruta=ruta, horario=horario_disponible, activo=True, es_lista_espera=False).count()
        cupos_espera = Cupo.objects.filter(ruta=ruta, horario=horario_disponible, activo=True, es_lista_espera=True).count()

        capacidad_normal = ruta.capacidad_total
        capacidad_espera = ruta.capacidad_espera

        # Caso 1: aún hay cupos disponibles
        if cupos_activos < capacidad_normal:
            return Cupo.objects.create(usuario=usuario, ruta=ruta, horario=horario_disponible)

        # Caso 2: cupos llenos, pero aún hay espacio en lista de espera
        elif cupos_espera < capacidad_espera:
            cupo_espera = Cupo.objects.create(
                usuario=usuario,
                ruta=ruta,
                horario=horario_disponible,
                es_lista_espera=True
            )
            # Aquí puedes disparar notificación (correo/push)
            return cupo_espera

        # Caso 3: todo lleno
        else:
            raise ValueError("Ruta y lista de espera llenas para este horario.")

    @staticmethod
    def promover_siguiente(ruta):
        """
        Promueve automáticamente al siguiente usuario de la lista de espera
        si se libera un cupo antes de la salida.
        """
        cupo_espera = (
            Cupo.objects.filter(ruta=ruta, activo=True, es_lista_espera=True)
            .order_by("creado_en")
            .first()
        )
        if cupo_espera:
            cupo_espera.es_lista_espera = False
            cupo_espera.estado = EstadoCupo.RESERVADO
            cupo_espera.save(update_fields=["es_lista_espera", "estado"])
            # Aquí puedes enviar notificación push o correo:
            # Notificar que fue promovido a cupo activo
            return cupo_espera
        return None


class LlenadoRuta(models.Model):
    """
    Registra los llenados (manual o automático) de una ruta.
    Solo aplica a rutas de regreso (REGRESO).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ruta = models.ForeignKey("rutas.Ruta", on_delete=models.CASCADE, related_name="llenados")
    conductor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="llenados_reportados")
    tipo = models.CharField(max_length=20, choices=[("MANUAL", "Manual"), ("AUTOMATICO", "Automático")], default="AUTOMATICO")
    cupos_ocupados = models.PositiveIntegerField(default=0)
    total_cupos = models.PositiveIntegerField(default=0)
    fecha = models.DateTimeField(default=timezone.now)
    observaciones = models.TextField(blank=True)

    class Meta:
        ordering = ["-fecha"]
        verbose_name = "Llenado de ruta"
        verbose_name_plural = "Llenados de rutas"

    def __str__(self):
        return f"Llenado {self.get_tipo_display()} - {self.ruta.nombre} ({self.cupos_ocupados}/{self.total_cupos})"

    @staticmethod
    def registrar_llenado_automatico(ruta, total_cupos, cupos_ocupados):
        """Registra llenado automático basado en datos GPS (para rutas de regreso)."""
        return LlenadoRuta.objects.create(
            ruta=ruta,
            tipo="AUTOMATICO",
            cupos_ocupados=cupos_ocupados,
            total_cupos=total_cupos,
            observaciones="Llenado registrado automáticamente por sistema GPS."
        )
