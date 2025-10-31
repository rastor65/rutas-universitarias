# gps/serializers.py

from rest_framework import serializers
from django.utils import timezone
from .models import Posicion, Trayecto, AlertaGPS
from rutas.models import Ruta
from accounts.serializers import UserSerializer


# === POSICIÓN GPS ===
class PosicionSerializer(serializers.ModelSerializer):
    ruta_nombre = serializers.CharField(source="ruta.nombre", read_only=True)
    tiempo_transcurrido_segundos = serializers.SerializerMethodField()

    class Meta:
        model = Posicion
        fields = [
            "id",
            "origen_tipo",
            "origen_id",
            "latitud",
            "longitud",
            "precision",
            "estado",
            "timestamp",
            "ruta",
            "ruta_nombre",
            "tiempo_transcurrido_segundos",
        ]

    def get_tiempo_transcurrido_segundos(self, obj):
        """Retorna el tiempo transcurrido desde la última posición (en segundos)."""
        return int((timezone.now() - obj.timestamp).total_seconds())

    def validate(self, attrs):
        """
        Evita posiciones duplicadas en un mismo instante
        y valida rangos GPS razonables.
        """
        lat, lon = attrs.get("latitud"), attrs.get("longitud")

        if not (-90 <= float(lat) <= 90) or not (-180 <= float(lon) <= 180):
            raise serializers.ValidationError("Coordenadas fuera de rango válido.")

        return attrs


# === TRAYECTO ===
class TrayectoSerializer(serializers.ModelSerializer):
    ruta_nombre = serializers.CharField(source="ruta.nombre", read_only=True)
    conductor = UserSerializer(read_only=True)
    duracion_minutos = serializers.SerializerMethodField()

    class Meta:
        model = Trayecto
        fields = [
            "id",
            "ruta",
            "ruta_nombre",
            "conductor",
            "fecha_inicio",
            "fecha_fin",
            "distancia_recorrida_km",
            "duracion_total",
            "duracion_minutos",
            "finalizado",
        ]

    def get_duracion_minutos(self, obj):
        if obj.duracion_total:
            return round(obj.duracion_total.total_seconds() / 60, 2)
        return None

    def update(self, instance, validated_data):
        """
        Si el cliente envía un campo 'finalizado=True', cierra automáticamente el trayecto.
        """
        if validated_data.get("finalizado") and not instance.finalizado:
            instance.finalizar(distancia_km=validated_data.get("distancia_recorrida_km"))
        return instance


# === ALERTAS GPS ===
class AlertaGPSSerializer(serializers.ModelSerializer):
    ruta_nombre = serializers.CharField(source="ruta.nombre", read_only=True)
    posicion_id = serializers.PrimaryKeyRelatedField(
        source="posicion", read_only=True
    )
    resuelta_por_nombre = serializers.CharField(
        source="resuelta_por.username", read_only=True
    )

    class Meta:
        model = AlertaGPS
        fields = [
            "id",
            "ruta",
            "ruta_nombre",
            "tipo",
            "descripcion",
            "detectada_en",
            "posicion_id",
            "resuelta",
            "resuelta_en",
            "resuelta_por",
            "resuelta_por_nombre",
        ]
        read_only_fields = ["detectada_en", "resuelta_en", "resuelta_por"]

    def update(self, instance, validated_data):
        """
        Permite resolver la alerta desde un endpoint PATCH.
        """
        if validated_data.get("resuelta") and not instance.resuelta:
            usuario = self.context["request"].user if "request" in self.context else None
            instance.marcar_resuelta(usuario=usuario)
        return instance
