# contacts/views/supplier_attachments.py
from rest_framework import viewsets, parsers
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from contacts.models import SupplierAttachment, Contact
from contacts.serializers.supplier_attachment import SupplierAttachmentSerializer
from .mixins import OrgScopedViewSet

class SupplierAttachmentViewSet(OrgScopedViewSet, viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = SupplierAttachmentSerializer
    parser_classes = (parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ("categoria",)

    def get_queryset(self):
        # ⚠️ NO usar super(): SupplierAttachment no tiene campo org
        return (
            SupplierAttachment.objects
            .select_related("supplier")
            .filter(
                supplier_id=self.kwargs["supplier_pk"],
                supplier__org=self.get_org(),   # scope por tenant vía supplier
            )
            .order_by("-id")
        )

    def perform_create(self, serializer):
        # Asegura que el supplier es del tenant
        supplier = Contact.objects.get(
            pk=self.kwargs["supplier_pk"], org=self.get_org(), tipo="supplier"
        )
        serializer.save(
            supplier=supplier,
            created_by=self.request.user,
            updated_by=self.request.user,
        )
