from rest_framework import serializers
from .models import Event, Note

class OrgContactValidatorMixin:
    def validate(self, attrs):
        org = self.context["request"].org  # viene del OrgScoped mixin
        contact = attrs.get("contact")
        if contact and contact.org_id != org.id:
            raise serializers.ValidationError("El contacto no pertenece a tu organización.")
        return attrs

class EventSerializer(OrgContactValidatorMixin, serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = "__all__"
        read_only_fields = ("org","created_at","updated_at")

class NoteSerializer(OrgContactValidatorMixin, serializers.ModelSerializer):
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())  # ← lo rellena automáticamente

    class Meta:
        model = Note
        fields = "__all__"
        read_only_fields = ("org","created_at","updated_at")

    def create(self, validated_data):
        validated_data["org"] = self.context["request"].org
        validated_data["owner"] = self.context["request"].user
        return super().create(validated_data)

