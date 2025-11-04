from rest_framework import viewsets, filters as drf_filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from contacts.models import Contact
from contacts.serializers.contact import ContactListSerializer, ContactDetailSerializer
from contacts.filters import ContactFilter
from .mixins import OrgScopedViewSet

class ClientViewSet(OrgScopedViewSet, viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)

    # 🔧 BASE queryset requerido por DRF
    queryset = (
        Contact.objects.filter(tipo='client')
        .select_related('org')
        # .prefetch_related('direcciones')  # activa si lo necesitas en list
        .order_by('id')
    )

    filter_backends = (
        DjangoFilterBackend,
        drf_filters.OrderingFilter,
        drf_filters.SearchFilter,
    )
    filterset_class = ContactFilter
    ordering_fields = ("nombre", "razon_social", "updated_at")
    search_fields = ("nombre", "razon_social", "email", "telefono")

    # Opcional: si quieres reforzar el filtro por tipo aquí también
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(tipo='client')

    def get_serializer_class(self):
        return (
            ContactDetailSerializer
            if self.action in ("retrieve", "create", "update", "partial_update")
            else ContactListSerializer
        )

    def perform_create(self, serializer):
        serializer.save(
            org=self.get_org(),
            tipo="client",
            created_by=self.request.user,
            updated_by=self.request.user,
        )

    def perform_update(self, serializer):
        serializer.save(tipo="client", updated_by=self.request.user)
