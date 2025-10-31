# cupos/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Cupo, EstadoCupo


@receiver(post_save, sender=Cupo)
def gestionar_estado_cupo(sender, instance, created, **kwargs):
    """
    Maneja eventos automáticos cuando se actualiza un cupo.
    """
    # Si el cupo acaba de expirar o cancelarse → promover siguiente
    if not created and instance.estado in [EstadoCupo.CANCELADO, EstadoCupo.EXPIRADO]:
        Cupo.promover_siguiente(instance.ruta)

    # Si se acaba de confirmar → opcionalmente log o notificación
    if not created and instance.estado == EstadoCupo.CONFIRMADO:
        # Aquí podrías disparar una notificación push o correo
        print(f"[INFO] Cupo confirmado para {instance.usuario}")
