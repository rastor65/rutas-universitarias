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
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cupos"
    )
    ruta = models.ForeignKey(
        "rutas.Ruta",
        on_delete=models.CASCADE,
        related_name="cupos"
    )
    estado = models.CharField(max_length=20, choices=EstadoCupo.choices, default=EstadoCupo.RESERVADO)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    confirmado_en = models.DateTimeField(blank=True, null=True)
    cancelado_en = models.DateTimeField(blank=True, null=True)
    activo = models.BooleanField(default=True)

    class Meta:
        unique_together = ("usuario", "ruta")
        ordering = ["-creado_en"]
        verbose_name = "Cupo"
        verbose_name_plural = "Cupos"

    def __str__(self):
        return f"Cupo de {self.usuario} en {self.ruta.nombre} ({self.estado})"

    def marcar_confirmado(self):
        """Confirma la asistencia del usuario antes de la salida."""
        self.estado = EstadoCupo.CONFIRMADO
        self.confirmado_en = timezone.now()
        self.save(update_fields=["estado", "confirmado_en", "actualizado_en"])

    def marcar_expirado(self):
        """Marca como expirado si el usuario no está dentro del área antes de salir."""
        self.estado = EstadoCupo.EXPIRADO
        self.activo = False
        self.save(update_fields=["estado", "activo", "actualizado_en"])

    def marcar_cancelado(self):
        """Permite cancelación manual de la reserva."""
        self.estado = EstadoCupo.CANCELADO
        self.activo = False
        self.cancelado_en = timezone.now()
        self.save(update_fields=["estado", "activo", "cancelado_en", "actualizado_en"])

    def marcar_ocupado(self):
        """Usado automáticamente en rutas de regreso."""
        self.estado = EstadoCupo.OCUPADO
        self.activo = False
        self.save(update_fields=["estado", "activo", "actualizado_en"])


class ListaEspera(models.Model):
    """
    Representa la lista de espera para una ruta (solo aplica a rutas de salida).
    Si un cupo reservado expira, se asigna automáticamente al siguiente de esta lista.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="listas_espera"
    )
    ruta = models.ForeignKey(
        "rutas.Ruta",
        on_delete=models.CASCADE,
        related_name="listas_espera"
    )
    posicion = models.PositiveIntegerField(help_text="Posición en la lista de espera.")
    creado_en = models.DateTimeField(auto_now_add=True)
    asignado = models.BooleanField(default=False, help_text="Si el usuario fue promovido a cupo.")

    class Meta:
        ordering = ["posicion"]
        unique_together = ("usuario", "ruta")
        verbose_name = "Lista de espera"
        verbose_name_plural = "Listas de espera"

    def __str__(self):
        return f"#{self.posicion} en espera ({self.usuario}) - {self.ruta.nombre}"


class LlenadoRuta(models.Model):
    """
    Registra los llenados (manual o automático) de una ruta.
    Solo aplica a rutas de regreso (REGRESO).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ruta = models.ForeignKey("rutas.Ruta", on_delete=models.CASCADE, related_name="llenados")
    conductor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="llenados_reportados"
    )
    tipo = models.CharField(
        max_length=20,
        choices=[("MANUAL", "Manual"), ("AUTOMATICO", "Automático")],
        default="AUTOMATICO"
    )
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
