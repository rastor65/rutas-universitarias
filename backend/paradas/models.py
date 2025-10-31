#paradas/models.py
import uuid
from django.db import models


class ZonaParada(models.Model):
    """
    Permite agrupar paradas por zonas o sectores de la ciudad.
    Ejemplo: 'Centro', 'Ranchería', 'Aeropuerto', 'Villa Sharin'.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        verbose_name = "Zona de parada"
        verbose_name_plural = "Zonas de paradas"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Parada(models.Model):
    """
    Representa un punto de parada dentro del recorrido de una ruta universitaria.
    Puede pertenecer a varias rutas (relación M:N a través de 'rutas.RutaParada').
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombre = models.CharField(max_length=150)
    direccion = models.CharField(max_length=200, blank=True, help_text="Referencia o dirección aproximada.")
    latitud = models.DecimalField(max_digits=9, decimal_places=6)
    longitud = models.DecimalField(max_digits=9, decimal_places=6)
    zona = models.ForeignKey(
        "paradas.ZonaParada",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="paradas"
    )
    activa = models.BooleanField(default=True)
    creada_en = models.DateTimeField(auto_now_add=True)
    actualizada_en = models.DateTimeField(auto_now=True)

    # Relación M:N con rutas (definida a través de 'rutas.RutaParada')
    rutas = models.ManyToManyField(
        "rutas.Ruta",
        through="rutas.RutaParada",
        related_name="paradas"
    )

    class Meta:
        verbose_name = "Parada"
        verbose_name_plural = "Paradas"
        ordering = ["nombre"]
        unique_together = ("latitud", "longitud")

    def __str__(self):
        return f"{self.nombre} ({'Activa' if self.activa else 'Inactiva'})"

    def ubicacion_str(self):
        """Devuelve la ubicación en formato legible."""
        return f"{self.latitud}, {self.longitud}"

    def activar(self):
        self.activa = True
        self.save(update_fields=["activa"])

    def desactivar(self):
        self.activa = False
        self.save(update_fields=["activa"])
