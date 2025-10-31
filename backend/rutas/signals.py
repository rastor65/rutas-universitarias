# rutas/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Ruta, HistorialRuta, Desvio
from gps.models import Trayecto


@receiver(post_save, sender=Ruta)
def registrar_historial_estado(sender, instance, created, **kwargs):
    """
    Guarda un registro histórico cuando cambia el estado de una ruta.
    """
    if not created:
        HistorialRuta.objects.create(
            ruta=instance,
            evento=f"Cambio de estado a {instance.get_estado_display()}",
            descripcion=f"La ruta {instance.nombre} cambió de estado automáticamente.",
        )


@receiver(post_save, sender=Trayecto)
def cerrar_desvios_al_finalizar(sender, instance, created, **kwargs):
    """
    Cierra todos los desvíos activos cuando se finaliza un trayecto.
    """
    if not created and instance.finalizado:
        Desvio.objects.filter(ruta=instance.ruta, activo=True).update(
            activo=False, fin=timezone.now()
        )
        HistorialRuta.objects.create(
            ruta=instance.ruta,
            evento="Cierre de trayecto y desvíos",
            descripcion="El trayecto finalizó y los desvíos activos se cerraron.",
        )
