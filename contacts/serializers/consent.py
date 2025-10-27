from rest_framework import serializers
from contacts.models import Consent


class ConsentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consent
        fields = ("id", "tipo", "estado", "metodo", "ip", "user_agent", "version_texto", "timestamp")
        read_only_fields = ("timestamp",)