from rest_framework import serializers


class AuditSerializer(serializers.ModelSerializer):
    class Meta:
        fields = ("id", "created_at", "updated_at", "created_by", "updated_by")
        read_only_fields = fields