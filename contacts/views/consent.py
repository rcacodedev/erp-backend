from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from contacts.models import Consent
from contacts.serializers.consent import ConsentSerializer
from .mixins import OrgScopedViewSet

class ConsentViewSet(OrgScopedViewSet, viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = ConsentSerializer
    http_method_names = ["get", "post", "head", "options"]  # añade "retrieve" si quieres
    org_lookup = "contact__org"
    queryset = (
        Consent.objects
        .select_related("contact", "contact__org", "created_by", "updated_by")
        .order_by("-timestamp", "-id")
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
