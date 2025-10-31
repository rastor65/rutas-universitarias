# rutas/serializers.py

from rest_framework import serializers
from django.utils import timezone
from .models import (
    Bus,
    Ruta,
    HorarioRuta,
    BusRuta,
    RutaParada,
    Desvio,
    HistorialRuta
)
from paradas.serializers import ParadaSerializer
from accounts.serializers import UserSerializer


# === BUS ===
class BusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bus
        fields = [
            "id",
            "placa",
            "modelo",
            "capacidad",
            "activo",
            "creada_en",
            "actualizada_en",
        ]
        read_only_fields = ["creada_en", "actualizada_en"]


# === HORARIO DE RUTA ===
class HorarioRutaSerializer(serializers.ModelSerializer):
    ruta_nombre = serializers.CharField(source="ruta.nombre", read_only=True)

    class Meta:
        model = HorarioRuta
        fields = [
            "id",
            "ruta",
            "ruta_nombre",
            "hora_salida",
            "hora_llegada_estimada",
            "activo",
            "observaciones",
            "creado_en",
        ]
        read_only_fields = ["creado_en"]

    def validate(self, attrs):
        """Valida que la hora de llegada sea posterior a la hora de salida."""
        salida = attrs.get("hora_salida")
        llegada = attrs.get("hora_llegada_estimada")
        if llegada and llegada <= salida:
            raise serializers.ValidationError("La hora de llegada debe ser posterior a la de salida.")
        return attrs


# === RUTA ===
class RutaSerializer(serializers.ModelSerializer):
    conductor = UserSerializer(read_only=True)
    conductor_id = serializers.PrimaryKeyRelatedField(
        source="conductor",
        queryset=Ruta._meta.get_field("conductor").remote_field.model.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )

    buses = BusSerializer(many=True, read_only=True)
    horarios = HorarioRutaSerializer(many=True, read_only=True)
    paradas = ParadaSerializer(many=True, read_only=True)

    class Meta:
        model = Ruta
        fields = [
            "id",
            "nombre",
            "tipo",
            "estado",
            "conductor",
            "conductor_id",
            "buses",
            "capacidad_total",
            "capacidad_espera",
            "creada_en",
            "actualizada_en",
            "horarios",
            "paradas",
        ]
        read_only_fields = ["creada_en", "actualizada_en"]

    def validate(self, attrs):
        if attrs.get("capacidad_espera", 0) > attrs.get("capacidad_total", 0) * 0.5:
            raise serializers.ValidationError("La lista de espera no puede superar el 50% de la capacidad total.")
        return attrs


# === BUS-RUTA ===
class BusRutaSerializer(serializers.ModelSerializer):
    bus_placa = serializers.CharField(source="bus.placa", read_only=True)
    ruta_nombre = serializers.CharField(source="ruta.nombre", read_only=True)

    class Meta:
        model = BusRuta
        fields = ["id", "bus", "bus_placa", "ruta", "ruta_nombre", "fecha_asignacion", "activo"]


# === RUTA-PARADA ===
class RutaParadaSerializer(serializers.ModelSerializer):
    ruta_nombre = serializers.CharField(source="ruta.nombre", read_only=True)
    parada_nombre = serializers.CharField(source="parada.nombre", read_only=True)

    class Meta:
        model = RutaParada
        fields = ["id", "ruta", "ruta_nombre", "parada", "parada_nombre", "orden", "tiempo_estimado"]


# === DESVÍO ===
class DesvioSerializer(serializers.ModelSerializer):
    ruta_nombre = serializers.CharField(source="ruta.nombre", read_only=True)
    horario_hora = serializers.TimeField(source="horario.hora_salida", read_only=True, allow_null=True)
    creado_por_nombre = serializers.CharField(source="creado_por.username", read_only=True, allow_null=True)

    class Meta:
        model = Desvio
        fields = [
            "id",
            "ruta",
            "ruta_nombre",
            "horario",
            "horario_hora",
            "inicio",
            "fin",
            "distancia_desviacion",
            "descripcion",
            "activo",
            "detectado_automaticamente",
            "creado_por",
            "creado_por_nombre",
        ]
        read_only_fields = ["inicio"]

    def update(self, instance, validated_data):
        """
        Si el desvío se marca como inactivo, registra el cierre con hora actual.
        """
        activo = validated_data.get("activo", instance.activo)
        if not activo and instance.activo:
            instance.fin = timezone.now()
            instance.activo = False
            instance.save(update_fields=["fin", "activo"])
        return instance


# === HISTORIAL DE RUTA ===
class HistorialRutaSerializer(serializers.ModelSerializer):
    ruta_nombre = serializers.CharField(source="ruta.nombre", read_only=True)
    usuario_nombre = serializers.CharField(source="usuario.username", read_only=True)

    class Meta:
        model = HistorialRuta
        fields = [
            "id",
            "ruta",
            "ruta_nombre",
            "evento",
            "descripcion",
            "timestamp",
            "usuario",
            "usuario_nombre",
        ]
        read_only_fields = ["timestamp"]
