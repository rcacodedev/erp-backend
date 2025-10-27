# contacts/views/mixins.py
from rest_framework import viewsets
from core.models import Organization

class OrgScopedViewSet(viewsets.GenericViewSet):
    """
    Lee org desde la URL /api/v1/t/<org_slug>/...,
    la guarda en request.org y filtra queryset por org.
    """
    def get_org(self):
        if not hasattr(self, "_org"):
            self._org = Organization.objects.get(slug=self.kwargs["org_slug"])
            # Hacemos disponible la org para permisos que miran request.org
            self.request.org = self._org
        return self._org

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(org=self.get_org())

    def perform_create(self, serializer):
        serializer.save(org=self.get_org(), created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
