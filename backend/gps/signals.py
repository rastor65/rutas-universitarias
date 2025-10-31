# gps/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Posicion, Trayecto, AlertaGPS
from rutas.models import Desvio
from cupos.models import Cupo
from gps.utils import calcular_distancia  # lo implementaremos luego


@receiver(post_save, sender=Posicion)
def procesar_posicion_gps(sender, instance, created, **kwargs):
    """
    Analiza cada nueva posición GPS para detectar eventos automáticos.
    """
    if not created:
        return

    # Si el origen es un vehículo, analizar trayecto y desvíos
    if instance.origen_tipo == "VEHICULO" and instance.ruta:
        verificar_desvio(instance)

    # Si el origen es un usuario → confirmar cupo si está dentro del rango
    elif instance.origen_tipo == "USUARIO":
        confirmar_asistencia_usuario(instance)


def verificar_desvio(posicion):
    """Detecta si la posición del vehículo se desvía de su ruta."""
    ruta = posicion.ruta
    if not ruta or not ruta.paradas.exists():
        return

    # Comparar con las paradas más cercanas
    min_dist = float("inf")
    for parada in ruta.paradas.all():
        distancia = calcular_distancia(
            float(posicion.latitud),
            float(posicion.longitud),
            float(parada.latitud),
            float(parada.longitud),
        )
        if distancia < min_dist:
            min_dist = distancia

    # Si la desviación supera 300 metros → registrar desvío
    if min_dist > 300:
        Desvio.objects.create(
            ruta=ruta,
            distancia_desviacion=min_dist,
            descripcion=f"Desvío detectado ({int(min_dist)} m fuera de ruta).",
            detectado_automaticamente=True,
        )
        AlertaGPS.objects.create(
            ruta=ruta,
            tipo="DESVIO",
            descripcion=f"El bus se alejó {int(min_dist)} m de la ruta.",
            posicion=posicion,
        )


def confirmar_asistencia_usuario(posicion):
    """Confirma cupo si el usuario está cerca de una parada activa."""
    from paradas.models import Parada

    paradas = Parada.objects.filter(activa=True)
    for parada in paradas:
        distancia = calcular_distancia(
            float(posicion.latitud),
            float(posicion.longitud),
            float(parada.latitud),
            float(parada.longitud),
        )
        if distancia < 100:  # dentro del rango de 100m
            # Confirmar cupo activo de ese usuario si existe
            cupo = Cupo.objects.filter(
                usuario__id=posicion.origen_id,
                activo=True,
                estado="RESERVADO",
            ).first()
            if cupo:
                cupo.marcar_confirmado()
                print(f"[GPS] Cupo confirmado automáticamente para {cupo.usuario}")
            break
