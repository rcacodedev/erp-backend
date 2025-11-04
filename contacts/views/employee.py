# contacts/views/employee.py
from rest_framework import viewsets, filters as drf_filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from contacts.models import Contact
from contacts.serializers.contact import ContactListSerializer, ContactDetailSerializer
from contacts.filters import ContactFilter
from .mixins import OrgScopedViewSet

class EmployeeViewSet(OrgScopedViewSet, viewsets.ModelViewSet):
    """
    CRUD de contactos tipo 'employee'. Acepta creación anidada de 'empleado'
    vía ContactDetailSerializer (ya lo tienes).
    """
    permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend, drf_filters.OrderingFilter, drf_filters.SearchFilter)
    filterset_class = ContactFilter
    ordering_fields = ("id", "nombre", "razon_social", "updated_at", "created_at")
    search_fields = ("nombre", "apellidos", "razon_social", "email", "telefono", "documento_id")
    http_method_names = ["get", "post", "put", "patch", "delete", "head", "options"]
    queryset = (
        Contact.objects.filter(tipo='employee')
        .select_related('org')
        .order_by('id')
    )

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(tipo='employee')

    def get_serializer_class(self):
        return ContactDetailSerializer if self.action in ("retrieve","create","update","partial_update") else ContactListSerializer

    def perform_create(self, serializer):
        # Inyecta org/tipo y auditoría al crear
        serializer.save(
            org=self.get_org(),
            tipo="employee",
            created_by=self.request.user,
            updated_by=self.request.user,
        )

    def perform_update(self, serializer):
        # Evita cambio de 'tipo' en PATCH/PUT
        serializer.save(tipo="employee", updated_by=self.request.user)
