from rest_framework import serializers
from contacts.models import Consent

class ConsentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consent
        fields = [
            "id", "contact", "tipo", "estado", "metodo",
            "ip", "user_agent", "version_texto", "timestamp",
            "created_at", "updated_at", "created_by", "updated_by",
        ]
        read_only_fields = ["id", "timestamp", "created_at", "updated_at", "created_by", "updated_by", "contact"]
