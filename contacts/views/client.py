from rest_framework import viewsets, filters as drf_filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from contacts.models import Contact
from contacts.serializers.contact import ContactListSerializer, ContactDetailSerializer
from contacts.filters import ContactFilter
from .mixins import OrgScopedViewSet

class ClientViewSet(OrgScopedViewSet, viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    queryset = Contact.objects.filter(tipo='client')
    filter_backends = (DjangoFilterBackend, drf_filters.OrderingFilter, drf_filters.SearchFilter)
    filterset_class = ContactFilter
    ordering_fields = ("nombre", "razon_social", "updated_at")
    search_fields = ("nombre", "razon_social", "email", "telefono", "documento_id")  # ← añadido

    def get_queryset(self):
        return super().get_queryset().filter(tipo='client')

    def get_serializer_class(self):
        return ContactDetailSerializer if self.action in ("retrieve","create","update","partial_update") else ContactListSerializer
