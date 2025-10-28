# contacts/views/location_lite.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from contacts.models import LocationLite
from contacts.serializers.location_lite import LocationLiteSerializer
from .mixins import OrgScopedViewSet

class LocationLiteViewSet(viewsets.ModelViewSet, OrgScopedViewSet):
    queryset = LocationLite.objects.all()
    serializer_class = LocationLiteSerializer
    permission_classes = (IsAuthenticated,)
    http_method_names = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']

    def get_queryset(self):
        # Aseguramos el scoping por org explícitamente
        return LocationLite.objects.filter(org=self.get_org()).order_by('id')

    def perform_create(self, serializer):
        # Inyecta siempre org/created_by/updated_by
        serializer.save(
            org=self.get_org(),
            created_by=self.request.user,
            updated_by=self.request.user,
        )

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
