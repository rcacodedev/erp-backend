from rest_framework import viewsets
from contacts.models import Address, Contact
from contacts.serializers.address import AddressSerializer
from .mixins import OrgScopedViewSet

class AddressViewSet(OrgScopedViewSet, viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    queryset = Address.objects.select_related('contact')

    def get_queryset(self):
        qs = super().get_queryset()
        contact_id = self.kwargs.get('contact_pk')
        if contact_id:
            qs = qs.filter(contact_id=contact_id)
        return qs