from rest_framework import serializers
from contacts.models import LocationLite

class LocationLiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationLite
        fields = ('id', 'nombre')
