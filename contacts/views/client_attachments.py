from rest_framework import viewsets, parsers
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from contacts.models import ClientAttachment, Contact
from contacts.serializers.client_attachment import ClientAttachmentSerializer
from .mixins import OrgScopedViewSet

class ClientAttachmentViewSet(OrgScopedViewSet, viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = ClientAttachmentSerializer
    parser_classes = (parsers.MultiPartParser, parsers.FormParser, parsers.JSONParser)
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ("categoria",)

    def get_queryset(self):
        # ⚠️ No llamamos a super(): ClientAttachment no tiene 'org'
        return (
            ClientAttachment.objects
            .select_related('cliente')
            .filter(
                cliente_id=self.kwargs['client_pk'],
                cliente__org=self.get_org(),   # scope por tenant vía cliente
            )
            .order_by('-id')
        )

    def perform_create(self, serializer):
        # Añade también el scope por org al obtener el cliente
        cliente = Contact.objects.get(pk=self.kwargs['client_pk'], org=self.get_org())
        serializer.save(
            cliente=cliente,
            created_by=self.request.user,
            updated_by=self.request.user
        )
