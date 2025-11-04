# contacts/views/address.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from contacts.models import Address
from contacts.serializers.address import AddressSerializer

class AddressViewSet(viewsets.ModelViewSet):
    """
    Direcciones anidadas bajo un contacto:
      GET/POST     /contacts/<contact_pk>/addresses/
      GET/PATCH/DELETE /contacts/<contact_pk>/addresses/<id>/
    Filtra por organización vía contact__org (no hay campo org directo en Address).
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = AddressSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    queryset = (
        Address.objects
        .select_related("contact", "contact__org", "created_by", "updated_by")
        .order_by("id")
    )

    def get_queryset(self):
        qs = self.queryset
        org = getattr(self.request, "org", None)  # viene del TenantMiddleware
        if org is not None:
            qs = qs.filter(contact__org=org)
        contact_pk = self.kwargs.get("contact_pk")
        if contact_pk:
            qs = qs.filter(contact_id=contact_pk)
        return qs

    def perform_create(self, serializer):
        contact_pk = self.kwargs.get("contact_pk")
        serializer.save(
            contact_id=contact_pk,
            created_by=self.request.user,
            updated_by=self.request.user,
        )

    def perform_update(self, serializer):
        # Garantiza trazabilidad
        serializer.save(updated_by=self.request.user)
