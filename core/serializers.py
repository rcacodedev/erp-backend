# --- FILE: core/serializers.py
from rest_framework import serializers

class KpisPrefsSerializer(serializers.Serializer):
    rangePreset = serializers.ChoiceField(choices=["current_year", "last_year", "all", "custom"])
    groupBy = serializers.ChoiceField(choices=["category", "product", "customer", "seller"])
    bucket = serializers.ChoiceField(choices=["day", "week", "month"])
    topBy = serializers.ChoiceField(choices=["revenue", "margin"])
    fromDate = serializers.DateField(required=False, allow_null=True)
    toDate = serializers.DateField(required=False, allow_null=True)
