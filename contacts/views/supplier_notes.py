from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from contacts.models import SupplierNote, Contact
from contacts.serializers.supplier_note import SupplierNoteSerializer
from .mixins import OrgScopedViewSet

class SupplierNoteViewSet(OrgScopedViewSet, viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = SupplierNoteSerializer

    def get_queryset(self):
        return (SupplierNote.objects
                .select_related('supplier')
                .filter(supplier_id=self.kwargs['supplier_pk'],
                        supplier__org=self.get_org())
                .order_by('-id'))

    def perform_create(self, serializer):
        supplier = Contact.objects.get(pk=self.kwargs['supplier_pk'], org=self.get_org(), tipo='supplier')
        serializer.save(supplier=supplier, created_by=self.request.user, updated_by=self.request.user)
