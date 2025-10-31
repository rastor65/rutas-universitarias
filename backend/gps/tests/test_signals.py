# gps/tests/test_signals.py

from django.test import TestCase
from django.utils import timezone
from decimal import Decimal
from gps.models import Posicion
from rutas.models import Ruta, Bus, RutaParada, Desvio
from paradas.models import Parada, ZonaParada


class TestDeteccionDesvios(TestCase):
    def setUp(self):
        """Crea datos base para la simulación."""
        self.zona = ZonaParada.objects.create(nombre="Centro", descripcion="Zona principal")
        self.parada1 = Parada.objects.create(nombre="Parada A", latitud=11.5446, longitud=-72.9060, zona=self.zona)
        self.parada2 = Parada.objects.create(nombre="Parada B", latitud=11.5460, longitud=-72.9050, zona=self.zona)

        self.bus = Bus.objects.create(placa="ABC123", modelo="Hyundai", capacidad=40)
        self.ruta = Ruta.objects.create(nombre="Ruta Test", tipo="ciudad", capacidad_total=40)
        RutaParada.objects.create(ruta=self.ruta, parada=self.parada1, orden=1)
        RutaParada.objects.create(ruta=self.ruta, parada=self.parada2, orden=2)

    def test_detecta_desvio_automatico(self):
        """Simula una posición GPS desviada y verifica creación de Desvio."""
        # Latitud y longitud fuera del rango de 100m
        posicion = Posicion.objects.create(
            origen_tipo="VEHICULO",
            origen_id=self.bus.id,
            latitud=11.5500,  # ≈ 600 m lejos
            longitud=-72.9100,
            ruta=self.ruta,
        )

        # Espera que la señal haya creado un desvío
        self.assertTrue(Desvio.objects.filter(ruta=self.ruta, activo=True).exists(), "No se detectó el desvío automáticamente.")

        desvio = Desvio.objects.filter(ruta=self.ruta).first()
        print(f"✅ Desvío detectado: {desvio.descripcion} (distancia={desvio.distancia_desviacion} m)")
        self.assertGreater(desvio.distancia_desviacion, Decimal(100))


    def test_no_detecta_si_en_rango(self):
        """Simula posición dentro del rango permitido (100m)."""
        Posicion.objects.create(
            origen_tipo="VEHICULO",
            origen_id=self.bus.id,
            latitud=11.5447,  # Muy cerca de Parada A
            longitud=-72.9061,
            ruta=self.ruta,
        )

        self.assertFalse(Desvio.objects.filter(ruta=self.ruta, activo=True).exists(), "Detectó desvío aunque estaba dentro del rango permitido.")
