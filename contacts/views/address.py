from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from contacts.models import Address
from contacts.serializers.address import AddressSerializer
from .mixins import OrgScopedViewSet

class AddressViewSet(OrgScopedViewSet, viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = AddressSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    org_lookup = "contact__org"
    queryset = (
        Address.objects
        .select_related("contact", "contact__org", "created_by", "updated_by")
        .order_by("id")
    )

    def get_queryset(self):
        qs = super().get_queryset()
        contact_pk = self.kwargs.get("contact_pk")
        if contact_pk:
            qs = qs.filter(contact_id=contact_pk)
        return qs

    def perform_create(self, serializer):
        serializer.save(
            contact_id=self.kwargs.get("contact_pk"),
            created_by=self.request.user,
            updated_by=self.request.user,
        )

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
