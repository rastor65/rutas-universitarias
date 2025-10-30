import uuid
from django.db import models
from django.utils import timezone
from django.conf import settings


class TipoOrigen(models.TextChoices):
    USUARIO = "USUARIO", "Usuario"
    VEHICULO = "VEHICULO", "Vehículo"


class EstadoPosicion(models.TextChoices):
    ACTIVA = "ACTIVA", "Activa"
    FUERA_DE_RANGO = "FUERA_DE_RANGO", "Fuera de rango"
    SIN_SENAL = "SIN_SEÑAL", "Sin señal"
    FINALIZADA = "FINALIZADA", "Finalizada"


class Posicion(models.Model):
    """
    Representa una lectura de ubicación GPS (usuario o vehículo).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    origen_tipo = models.CharField(max_length=20, choices=TipoOrigen.choices)
    origen_id = models.UUIDField(help_text="UUID del usuario o vehículo asociado.")
    latitud = models.DecimalField(max_digits=9, decimal_places=6)
    longitud = models.DecimalField(max_digits=9, decimal_places=6)
    precision = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Precisión del GPS en metros.")
    estado = models.CharField(max_length=20, choices=EstadoPosicion.choices, default=EstadoPosicion.ACTIVA)
    timestamp = models.DateTimeField(default=timezone.now)
    ruta = models.ForeignKey(
        "rutas.Ruta",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posiciones"
    )

    class Meta:
        ordering = ["-timestamp"]
        verbose_name = "Posición GPS"
        verbose_name_plural = "Posiciones GPS"

    def __str__(self):
        return f"{self.origen_tipo} @ {self.latitud}, {self.longitud} ({self.estado})"

    def coordenadas_str(self):
        return f"{self.latitud}, {self.longitud}"

    def es_activa(self):
        """Indica si la posición aún está dentro de un rango válido (menos de 5 minutos)."""
        return (timezone.now() - self.timestamp).total_seconds() < 300


class Trayecto(models.Model):
    """
    Agrupa una secuencia de posiciones GPS para un recorrido completo (una ejecución de la ruta).
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ruta = models.ForeignKey("rutas.Ruta", on_delete=models.CASCADE, related_name="trayectos")
    conductor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="trayectos_realizados"
    )
    fecha_inicio = models.DateTimeField(default=timezone.now)
    fecha_fin = models.DateTimeField(blank=True, null=True)
    distancia_recorrida_km = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    duracion_total = models.DurationField(blank=True, null=True)
    finalizado = models.BooleanField(default=False)

    class Meta:
        ordering = ["-fecha_inicio"]
        verbose_name = "Trayecto GPS"
        verbose_name_plural = "Trayectos GPS"

    def __str__(self):
        return f"Trayecto de {self.ruta.nombre} ({self.fecha_inicio.strftime('%Y-%m-%d %H:%M')})"

    def finalizar(self, distancia_km=None):
        """Marca el trayecto como finalizado y calcula duración."""
        self.fecha_fin = timezone.now()
        self.finalizado = True
        if distancia_km:
            self.distancia_recorrida_km = distancia_km
        if self.fecha_inicio:
            self.duracion_total = self.fecha_fin - self.fecha_inicio
        self.save(update_fields=["fecha_fin", "finalizado", "distancia_recorrida_km", "duracion_total"])


class AlertaGPS(models.Model):
    """
    Registra eventos o alertas asociadas al sistema de geolocalización.
    Ejemplo: pérdida de señal, salida del perímetro, exceso de distancia.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ruta = models.ForeignKey("rutas.Ruta", on_delete=models.CASCADE, related_name="alertas_gps")
    tipo = models.CharField(max_length=100, help_text="Tipo de alerta (sin señal, desvío, fuera de zona, etc.)")
    descripcion = models.TextField(blank=True)
    detectada_en = models.DateTimeField(default=timezone.now)
    posicion = models.ForeignKey("gps.Posicion", on_delete=models.SET_NULL, null=True, blank=True, related_name="alertas")
    resuelta = models.BooleanField(default=False)
    resuelta_en = models.DateTimeField(blank=True, null=True)
    resuelta_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="alertas_resueltas"
    )

    class Meta:
        ordering = ["-detectada_en"]
        verbose_name = "Alerta GPS"
        verbose_name_plural = "Alertas GPS"

    def __str__(self):
        return f"Alerta: {self.tipo} ({'Resuelta' if self.resuelta else 'Activa'})"

    def marcar_resuelta(self, usuario=None):
        """Marca la alerta como resuelta."""
        self.resuelta = True
        self.resuelta_en = timezone.now()
        if usuario:
            self.resuelta_por = usuario
        self.save(update_fields=["resuelta", "resuelta_en", "resuelta_por"])
