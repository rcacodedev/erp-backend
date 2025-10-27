from rest_framework import serializers
from contacts.models import ClientEvent
class ClientEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientEvent
        fields = ('id','tipo','titulo','descripcion','inicio','fin','empleado_asignado','estado','ubicacion')
