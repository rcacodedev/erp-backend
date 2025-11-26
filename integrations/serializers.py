# integrations/serializers.py
from rest_framework import serializers
from .models import WebhookEndpoint, WebhookDelivery


class WebhookEndpointSerializer(serializers.ModelSerializer):
    secret = serializers.CharField(
        allow_blank=True,
        required=False,
        write_only=True,
        help_text="Se usará para firmar la cabecera X-Preator-Signature",
    )

    class Meta:
        model = WebhookEndpoint
        fields = [
            "id",
            "name",
            "target_url",
            "event",
            "secret",
            "is_active",
            "last_status",
            "last_status_code",
            "last_error",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["last_status", "last_status_code", "last_error", "created_at", "updated_at"]


class WebhookDeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = WebhookDelivery
        fields = [
            "id",
            "event_name",
            "status",
            "attempt_count",
            "last_status_code",
            "last_error",
            "response_body",
            "payload",
            "created_at",
            "last_attempt_at",
        ]
        read_only_fields = fields
