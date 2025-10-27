from rest_framework import viewsets
from contacts.models import Consent, Contact
from contacts.serializers.consent import ConsentSerializer
from .mixins import OrgScopedViewSet

class ConsentViewSet(OrgScopedViewSet, viewsets.ModelViewSet):
    serializer_class = ConsentSerializer
    queryset = Consent.objects.select_related('contact')

    def get_queryset(self):
        qs = super().get_queryset()
        contact_id = self.kwargs.get('contact_pk')
        if contact_id:
            qs = qs.filter(contact_id=contact_id)
        return qs