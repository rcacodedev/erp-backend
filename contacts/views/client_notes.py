from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from contacts.models import ClientNote, Contact
from contacts.serializers.client_note import ClientNoteSerializer
from .mixins import OrgScopedViewSet

class ClientNoteViewSet(OrgScopedViewSet, viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = ClientNoteSerializer

    def get_queryset(self):
        # ⚠️ No usar super(): ClientNote no tiene 'org'
        return (
            ClientNote.objects
            .select_related('cliente')
            .filter(
                cliente_id=self.kwargs['client_pk'],
                cliente__org=self.get_org(),   # scope por tenant vía cliente
            )
            .order_by('-id')
        )

    def perform_create(self, serializer):
        # ⚠️ No pasar 'org'; ligamos la nota al cliente del path, scoped por org
        cliente = Contact.objects.get(pk=self.kwargs['client_pk'], org=self.get_org())
        serializer.save(
            cliente=cliente,
            created_by=self.request.user,
            updated_by=self.request.user,
        )

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
