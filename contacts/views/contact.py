from rest_framework import viewsets, filters as drf_filters
from django_filters.rest_framework import DjangoFilterBackend
from contacts.models import Contact
from contacts.serializers.contact import ContactListSerializer, ContactDetailSerializer
from contacts.filters import ContactFilter
from contacts.permissions import IsOrgMember, CanManageContacts
from .mixins import OrgScopedViewSet
from rest_framework.permissions import IsAuthenticated

class ContactViewSet(OrgScopedViewSet, viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend, drf_filters.OrderingFilter, drf_filters.SearchFilter)
    filterset_class = ContactFilter
    ordering_fields = ("nombre", "apellidos", "razon_social", "updated_at")
    search_fields = ("nombre", "apellidos", "razon_social", "email", "telefono")

    def get_permissions(self):
        base = super().get_permissions()
        if self.request.method in ("POST", "PUT", "PATCH", "DELETE"):
            base.append(CanManageContacts())
        return base

    def get_serializer_class(self):
        if self.action == "list":
            return ContactListSerializer
        return ContactDetailSerializer