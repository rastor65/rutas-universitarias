#rutas/models.py

import uuid
from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.conf import settings


# === ENUMS ===

class EstadoRuta(models.TextChoices):
    PROGRAMADA = "PROGRAMADA", "Programada"
    EN_CURSO = "EN_CURSO", "En curso"
    FINALIZADA = "FINALIZADA", "Finalizada"
    CANCELADA = "CANCELADA", "Cancelada"


class TipoRuta(models.TextChoices):
    NORMAL = "ciudad", "Desde la universidad hacia la ciudad"
    MUNICIPAL = "fuera_de_la_ciudad", "Desde la universidad hacia municipios cercanos"


# === MODELOS ===

class Bus(models.Model):
    """Vehículo de transporte universitario."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    placa = models.CharField(max_length=20, unique=True, help_text="Placa o identificación del vehículo.")
    modelo = models.CharField(max_length=50, blank=True)
    capacidad = models.PositiveIntegerField(default=40, help_text="Capacidad total de pasajeros.")
    activo = models.BooleanField(default=True)
    creada_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["placa"]
        verbose_name = "Bus"
        verbose_name_plural = "Buses"

    def __str__(self):
        return f"{self.placa} ({'Activo' if self.activo else 'Inactivo'})"


class Ruta(models.Model):
    """Representa un recorrido fijo (independiente de los horarios diarios)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=120)
    tipo = models.CharField(max_length=30, choices=TipoRuta.choices, default=TipoRuta.NORMAL)
    estado = models.CharField(max_length=20, choices=EstadoRuta.choices, default=EstadoRuta.PROGRAMADA)
    conductor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="rutas_asignadas",
        limit_choices_to={"is_staff": True},
        help_text="Conductor responsable principal de la ruta."
    )
    buses = models.ManyToManyField("rutas.Bus", through="rutas.BusRuta", related_name="rutas")

    capacidad_total = models.PositiveIntegerField(default=40)
    capacidad_espera = models.PositiveIntegerField(default=10)
    creada_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Ruta universitaria"
        verbose_name_plural = "Rutas universitarias"

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"


class HorarioRuta(models.Model):
    """Define los diferentes horarios de salida y llegada para una misma ruta."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ruta = models.ForeignKey("rutas.Ruta", on_delete=models.CASCADE, related_name="horarios")
    hora_salida = models.TimeField()
    hora_llegada_estimada = models.TimeField(blank=True, null=True)
    activo = models.BooleanField(default=True, help_text="Indica si el horario está actualmente vigente.")
    observaciones = models.CharField(max_length=255, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["hora_salida"]
        verbose_name = "Horario de ruta"
        verbose_name_plural = "Horarios de ruta"

    def __str__(self):
        return f"{self.ruta.nombre} - {self.hora_salida.strftime('%H:%M')}"


class BusRuta(models.Model):
    """Asociación entre buses y rutas (no horarios)."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bus = models.ForeignKey("rutas.Bus", on_delete=models.CASCADE, related_name="bus_rutas")
    ruta = models.ForeignKey("rutas.Ruta", on_delete=models.CASCADE, related_name="bus_rutas")
    fecha_asignacion = models.DateField(default=timezone.now)
    activo = models.BooleanField(default=True)

    class Meta:
        unique_together = ("bus", "ruta")
        verbose_name = "Asignación de bus a ruta"
        verbose_name_plural = "Asignaciones bus-ruta"

    def __str__(self):
        return f"{self.bus.placa} → {self.ruta.nombre} ({'Activa' if self.activo else 'Inactiva'})"


class RutaParada(models.Model):
    """Asociación entre rutas y paradas, con orden y tiempo estimado."""
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
    """Registra automáticamente los desvíos detectados por el sistema GPS."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ruta = models.ForeignKey("rutas.Ruta", on_delete=models.CASCADE, related_name="desvios")
    horario = models.ForeignKey("rutas.HorarioRuta", on_delete=models.SET_NULL, null=True, blank=True, related_name="desvios")
    inicio = models.DateTimeField(default=timezone.now)
    fin = models.DateTimeField(blank=True, null=True)
    distancia_desviacion = models.DecimalField(max_digits=6, decimal_places=3, help_text="Distancia máxima fuera de ruta (en metros).")
    descripcion = models.TextField(blank=True, help_text="Detalle del desvío detectado automáticamente.")
    activo = models.BooleanField(default=True)
    detectado_automaticamente = models.BooleanField(default=True)
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="desvios_registrados",
        help_text="Solo si se registra manualmente."
    )

    class Meta:
        ordering = ["-inicio"]
        verbose_name = "Desvío detectado"
        verbose_name_plural = "Desvíos detectados"

    def __str__(self):
        estado = "Activo" if self.activo else "Cerrado"
        return f"{self.ruta.nombre} ({estado}) - {self.distancia_desviacion} m"


class HistorialRuta(models.Model):
    """Eventos asociados a la ruta (inicio, paradas, cierre, incidencias)."""
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
