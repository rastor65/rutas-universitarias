import uuid
from django.db import models
from django.utils import timezone
from django.conf import settings

# Importaciones cruzadas referenciadas
# (usar string para evitar dependencias circulares)
# Ejemplo: "paradas.Parada" o "gps.Posicion"

class EstadoRuta(models.TextChoices):
    PROGRAMADA = "PROGRAMADA", "Programada"
    EN_CURSO = "EN_CURSO", "En curso"
    FINALIZADA = "FINALIZADA", "Finalizada"
    CANCELADA = "CANCELADA", "Cancelada"


class TipoRuta(models.TextChoices):
    IDA = "IDA", "Ida (desde la universidad)"
    REGRESO = "REGRESO", "Regreso (hacia la universidad)"


class Ruta(models.Model):
    """
    Representa una ruta universitaria (ida o regreso).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True)
    tipo = models.CharField(max_length=20, choices=TipoRuta.choices, default=TipoRuta.IDA)
    estado = models.CharField(max_length=20, choices=EstadoRuta.choices, default=EstadoRuta.PROGRAMADA)
    conductor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="rutas_asignadas",
        limit_choices_to={"is_staff": True},
        help_text="Usuario asignado como conductor principal."
    )
    vehiculo = models.CharField(max_length=50, help_text="Identificación o placa del vehículo asignado.")
    capacidad_total = models.PositiveIntegerField(default=40)
    capacidad_espera = models.PositiveIntegerField(default=10)
    hora_salida = models.DateTimeField()
    hora_llegada_estimada = models.DateTimeField(blank=True, null=True)
    creada_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["hora_salida"]
        verbose_name = "Ruta universitaria"
        verbose_name_plural = "Rutas universitarias"

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"


class RutaParada(models.Model):
    """
    Asociación entre rutas y paradas, con orden y tiempo estimado de llegada.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ruta = models.ForeignKey("rutas.Ruta", on_delete=models.CASCADE, related_name="rutas_paradas")
    parada = models.ForeignKey("paradas.Parada", on_delete=models.CASCADE, related_name="paradas_rutas")
    orden = models.PositiveIntegerField(help_text="Orden de paso en la ruta.")
    tiempo_estimado = models.DurationField(blank=True, null=True, help_text="Tiempo estimado desde el inicio.")

    class Meta:
        ordering = ["orden"]
        unique_together = ("ruta", "parada")
        verbose_name = "Parada en ruta"
        verbose_name_plural = "Paradas por ruta"

    def __str__(self):
        return f"{self.ruta.nombre} → {self.parada.nombre} (#{self.orden})"


class Desvio(models.Model):
    """
    Registra un desvío temporal en una ruta.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ruta = models.ForeignKey("rutas.Ruta", on_delete=models.CASCADE, related_name="desvios")
    descripcion = models.TextField(help_text="Motivo o detalle del desvío.")
    inicio = models.DateTimeField(default=timezone.now)
    fin = models.DateTimeField(blank=True, null=True)
    activo = models.BooleanField(default=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="desvios_registrados"
    )

    class Meta:
        ordering = ["-inicio"]
        verbose_name = "Desvío"
        verbose_name_plural = "Desvíos"

    def __str__(self):
        return f"Desvío en {self.ruta.nombre} ({'Activo' if self.activo else 'Cerrado'})"


class HistorialRuta(models.Model):
    """
    Historial de eventos asociados a la ruta (inicio, paradas, cierre).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ruta = models.ForeignKey("rutas.Ruta", on_delete=models.CASCADE, related_name="historial")
    evento = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="eventos_ruta"
    )

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "Evento de ruta"
        verbose_name_plural = "Historial de rutas"

    def __str__(self):
        return f"{self.ruta.nombre}: {self.evento}"
