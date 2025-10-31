# cupos/serializers.py

from rest_framework import serializers
from django.utils import timezone
from .models import Cupo, LlenadoRuta, EstadoCupo
from rutas.models import Ruta, HorarioRuta
from accounts.serializers import UserSerializer


class CupoSerializer(serializers.ModelSerializer):
    """
    Serializador principal de Cupo.
    Permite listar, crear y actualizar el estado de los cupos.
    """

    usuario = UserSerializer(read_only=True)
    usuario_id = serializers.PrimaryKeyRelatedField(
        source="usuario", queryset=Cupo._meta.get_field("usuario").remote_field.model.objects.all(), write_only=True
    )

    ruta_nombre = serializers.CharField(source="ruta.nombre", read_only=True)
    horario_hora = serializers.TimeField(source="horario.hora_salida", read_only=True)

    class Meta:
        model = Cupo
        fields = [
            "id",
            "usuario",
            "usuario_id",
            "ruta",
            "ruta_nombre",
            "horario",
            "horario_hora",
            "estado",
            "activo",
            "es_lista_espera",
            "creado_en",
            "actualizado_en",
            "confirmado_en",
            "cancelado_en",
            "expirado_en",
        ]
        read_only_fields = [
            "estado",
            "activo",
            "creado_en",
            "actualizado_en",
            "confirmado_en",
            "cancelado_en",
            "expirado_en",
        ]

    def create(self, validated_data):
        """
        Crea el cupo automáticamente según disponibilidad de la ruta.
        Si está llena, lo agrega a lista de espera.
        """
        usuario = validated_data["usuario"]
        ruta = validated_data["ruta"]

        try:
            cupo = Cupo.crear_automaticamente(usuario=usuario, ruta=ruta)
            return cupo
        except ValueError as e:
            raise serializers.ValidationError({"detalle": str(e)})


class EstadoCupoSerializer(serializers.Serializer):
    """
    Serializador para actualizar el estado del cupo.
    Se usa en endpoints tipo PATCH.
    """
    estado = serializers.ChoiceField(choices=EstadoCupo.choices)

    def update(self, instance, validated_data):
        estado = validated_data.get("estado")

        if estado == EstadoCupo.CONFIRMADO:
            instance.marcar_confirmado()
        elif estado == EstadoCupo.CANCELADO:
            instance.marcar_cancelado()
        elif estado == EstadoCupo.EXPIRADO:
            instance.marcar_expirado()
        elif estado == EstadoCupo.OCUPADO:
            instance.marcar_ocupado()

        return instance


class LlenadoRutaSerializer(serializers.ModelSerializer):
    """
    Serializador para reportes de llenado de rutas (manual o automático).
    """
    ruta_nombre = serializers.CharField(source="ruta.nombre", read_only=True)
    conductor_nombre = serializers.CharField(source="conductor.username", read_only=True)

    class Meta:
        model = LlenadoRuta
        fields = [
            "id",
            "ruta",
            "ruta_nombre",
            "conductor",
            "conductor_nombre",
            "tipo",
            "cupos_ocupados",
            "total_cupos",
            "fecha",
            "observaciones",
        ]
        read_only_fields = ["fecha"]
