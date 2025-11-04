from rest_framework import serializers
from contacts.models import Address

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            "id","contact","tipo","linea1","linea2","cp","ciudad","provincia","pais","es_principal",
            "created_at","updated_at","created_by","updated_by",
        ]
        read_only_fields = ["id","contact","created_at","updated_at","created_by","updated_by"]
