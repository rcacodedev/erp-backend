# contacts/views/consent.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from contacts.models import Consent
from contacts.serializers.consent import ConsentSerializer  # asumiendo que ya lo tienes
# OJO: NO usamos el get_queryset() del mixin porque ese asume campo 'org' directo en el modelo

class ConsentViewSet(viewsets.ModelViewSet):
    """
    Lista/crea consentimientos para un contacto.
    Filtra por organización vía contact__org y por contact_pk del path.
    """
    permission_classes = (IsAuthenticated,)
    serializer_class = ConsentSerializer
    http_method_names = ["get", "post", "head", "options"]  # si quieres permitir retrieve, añade "retrieve"
    queryset = (
        Consent.objects
        .select_related("contact", "contact__org", "created_by", "updated_by")
        .order_by("-timestamp", "-id")
    )

    def get_queryset(self):
        qs = self.queryset
        # org desde middleware (lo tienes en request.org si usas tu TenantMiddleware)
        org = getattr(self.request, "org", None)
        if org is not None:
            qs = qs.filter(contact__org=org)
        # anidado por contacto: /contacts/<int:contact_pk>/consents/
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
