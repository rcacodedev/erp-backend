from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from contacts.models import ClientNote
from contacts.serializers.client_note import ClientNoteSerializer
from .mixins import OrgScopedViewSet

class ClientNoteViewSet(OrgScopedViewSet, viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = ClientNoteSerializer
    queryset = ClientNote.objects.all()
    def get_queryset(self):
        return super().get_queryset().filter(cliente_id=self.kwargs['client_pk'])
