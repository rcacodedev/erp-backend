# --- FILE: core/serializers.py
from rest_framework import serializers
from core.models import OrganizationEmailSettings

class KpisPrefsSerializer(serializers.Serializer):
    rangePreset = serializers.ChoiceField(choices=["current_year", "last_year", "all", "custom"])
    groupBy = serializers.ChoiceField(choices=["category", "product", "customer", "seller"])
    bucket = serializers.ChoiceField(choices=["day", "week", "month"])
    topBy = serializers.ChoiceField(choices=["revenue", "margin"])
    fromDate = serializers.DateField(required=False, allow_null=True)
    toDate = serializers.DateField(required=False, allow_null=True)

class OrganizationEmailSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationEmailSettings
        fields = [
            "from_name",
            "from_email",
            "reply_to_email",
            "bcc_on_outgoing",
            "send_system_emails",
        ]