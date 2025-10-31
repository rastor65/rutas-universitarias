# paradas/serializers.py

from rest_framework import serializers
from .models import Parada, ZonaParada
from rutas.models import RutaParada


# === ZONAS DE PARADA ===
class ZonaParadaSerializer(serializers.ModelSerializer):
    """Serializador para zonas o sectores de paradas."""
    
    class Meta:
        model = ZonaParada
        fields = ["id", "nombre", "descripcion"]


# === PARADAS ===
class ParadaSerializer(serializers.ModelSerializer):
    """Serializador detallado de paradas, con validación de coordenadas y zona."""
    
    zona = ZonaParadaSerializer(read_only=True)
    zona_id = serializers.PrimaryKeyRelatedField(
        queryset=ZonaParada.objects.all(),
        source="zona",
        write_only=True,
        required=False,
        allow_null=True
    )

    rutas_asociadas = serializers.SerializerMethodField()

    class Meta:
        model = Parada
        fields = [
            "id",
            "nombre",
            "direccion",
            "latitud",
            "longitud",
            "zona",
            "zona_id",
            "activa",
            "rutas_asociadas",
            "creada_en",
            "actualizada_en",
        ]
        read_only_fields = ["creada_en", "actualizada_en"]

    def get_rutas_asociadas(self, obj):
        """Devuelve una lista simplificada de rutas que pasan por esta parada."""
        return [
            {
                "id": rp.ruta.id,
                "nombre": rp.ruta.nombre,
                "orden": rp.orden
            }
            for rp in obj.paradas_rutas.select_related("ruta").all().order_by("orden")
        ]

    def validate(self, attrs):
        lat = attrs.get("latitud")
        lon = attrs.get("longitud")

        if not (-90 <= float(lat) <= 90) or not (-180 <= float(lon) <= 180):
            raise serializers.ValidationError("Las coordenadas GPS no son válidas.")

        return attrs


# === ASOCIACIÓN RUTA-PARADA ===
class RutaParadaSerializer(serializers.ModelSerializer):
    """Serializador para la relación entre rutas y paradas (ordenadas)."""

    ruta_nombre = serializers.CharField(source="ruta.nombre", read_only=True)
    parada_nombre = serializers.CharField(source="parada.nombre", read_only=True)
    zona = serializers.CharField(source="parada.zona.nombre", read_only=True, allow_null=True)

    class Meta:
        model = RutaParada
        fields = [
            "id",
            "ruta",
            "ruta_nombre",
            "parada",
            "parada_nombre",
            "zona",
            "orden",
            "tiempo_estimado",
        ]
