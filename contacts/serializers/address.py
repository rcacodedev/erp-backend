from rest_framework import serializers
from contacts.models import Address


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ("id", "tipo", "linea1", "linea2", "cp", "ciudad", "provincia", "pais", "es_principal")