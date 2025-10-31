# gps/utils.py

from math import radians, sin, cos, sqrt, atan2
from django.utils import timezone
from rutas.models import Desvio, Ruta
from decimal import Decimal


def calcular_distancia(lat1, lon1, lat2, lon2):
    """Devuelve la distancia en metros entre dos coordenadas."""
    R = 6371000  # radio de la Tierra en metros
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


def detectar_desvio(ruta: Ruta, lat_actual: float, lon_actual: float):
    """Detecta automáticamente si el bus se desvió del trazado de la ruta."""
    coordenadas = [
        (float(p.parada.latitud), float(p.parada.longitud))
        for p in ruta.rutas_paradas.all()
        if p.parada.latitud and p.parada.longitud
    ]

    if not coordenadas:
        return None

    dist_min = min(
        calcular_distancia(lat_actual, lon_actual, lat_p, lon_p)
        for lat_p, lon_p in coordenadas
    )

    UMBRAL_METROS = 100
    desvio_activo = ruta.desvios.filter(activo=True).first()

    if dist_min > UMBRAL_METROS:
        if not desvio_activo:
            Desvio.objects.create(
                ruta=ruta,
                distancia_desviacion=Decimal(dist_min),
                descripcion=f"Desvío detectado automáticamente ({int(dist_min)} m fuera del trazado)."
            )
    else:
        if desvio_activo:
            desvio_activo.fin = timezone.now()
            desvio_activo.activo = False
            desvio_activo.save()
