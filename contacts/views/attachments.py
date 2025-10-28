from rest_framework import viewsets, parsers
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from contacts.models import Attachment
from contacts.serializers.attachments import AttachmentSerializer
from .mixins import OrgScopedViewSet

class AttachmentViewSet(OrgScopedViewSet, viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = AttachmentSerializer
    queryset = Attachment.objects.select_related('contact')
    parser_classes = (parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ("categoria","periodo_nomina")

    def get_queryset(self):
        return (
            Attachment.objects
            .select_related('contact')
            .filter(
                contact_id=self.kwargs["contact_pk"],
                contact__org=self.get_org(),   # <- scoping por org vía contact
            )
            .order_by('-id')
        )


    def perform_create(self, serializer):
        obj = serializer.save(
            contact_id=self.kwargs["contact_pk"],
            created_by=self.request.user, updated_by=self.request.user
        )
        if obj.categoria == "nomina" and not obj.confidencial:
            obj.confidencial = True
            obj.save(update_fields=["confidencial"])
