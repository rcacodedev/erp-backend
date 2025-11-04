from rest_framework import viewsets, filters as drf_filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from contacts.models import Contact
from contacts.serializers.supplier import SupplierListSerializer, SupplierDetailSerializer
from contacts.filters import ContactFilter
from .mixins import OrgScopedViewSet

class SupplierViewSet(OrgScopedViewSet, viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend, drf_filters.OrderingFilter, drf_filters.SearchFilter)
    filterset_class = ContactFilter
    ordering_fields = ("razon_social","nombre","updated_at")
    search_fields = ("razon_social","nombre","apellidos","email","telefono")
    queryset = (
        Contact.objects.filter(tipo='supplier')
        .select_related('org')
        .order_by('id')
    )

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(tipo='supplier')

    def get_serializer_class(self):
        return SupplierDetailSerializer if self.action in ("retrieve","create","update","partial_update") else SupplierListSerializer

    def perform_create(self, serializer):
        # Inyecta org y tipo; auditoría
        serializer.save(
            org=self.get_org(),
            tipo="supplier",
            created_by=self.request.user,
            updated_by=self.request.user,
        )

    def perform_update(self, serializer):
        # Evita que cambien 'tipo' en PATCH/PUT
        serializer.save(tipo="supplier", updated_by=self.request.user)
