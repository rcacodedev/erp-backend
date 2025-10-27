from rest_framework import viewsets, parsers
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from contacts.models import ClientAttachment, Contact
from contacts.serializers.client_attachment import ClientAttachmentSerializer
from .mixins import OrgScopedViewSet

class ClientAttachmentViewSet(OrgScopedViewSet, viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = ClientAttachmentSerializer
    queryset = ClientAttachment.objects.select_related('cliente')
    parser_classes = (parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ("categoria",)

    def get_queryset(self):
        return super().get_queryset().filter(cliente_id=self.kwargs['client_pk'])

    def perform_create(self, serializer):
        cliente = Contact.objects.get(pk=self.kwargs['client_pk'])
        serializer.save(cliente=cliente, created_by=self.request.user, updated_by=self.request.user)
