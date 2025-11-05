# common/mixins.py  (o donde prefieras)
from rest_framework import viewsets
from rest_framework.exceptions import ValidationError
from django.utils.functional import cached_property
from core.models import Organization  # ajusta import si procede

class OrgScopedModelViewSet(viewsets.ModelViewSet):
    """
    - Filtra queryset por organización.
    - Inyecta self.org y la pasa automáticamente en perform_create(..., org=self.org).
    - Añade 'org' al serializer_context.
    """
    org_lookup = "org"
    queryset = None  # obligatorio en subclases

    @cached_property
    def org(self):
        # 1) middleware (si lo tienes)
        o = getattr(self.request, "org", None)
        if o:
            return o
        # 2) fallback por slug en la URL
        slug = self.kwargs.get("org_slug")
        if slug:
            return Organization.objects.get(slug=slug)
        raise ValidationError("Organización no resuelta (falta org_slug o request.org)")

    def get_queryset(self):
        assert self.queryset is not None, f"{self.__class__.__name__} debe definir 'queryset'"
        return self.queryset.filter(**{self.org_lookup: self.org})

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx["org"] = self.org
        return ctx

    def perform_create(self, serializer):
        # Si el modelo tiene campo 'org', lo seteamos aquí
        serializer.save(org=self.org)

    # Si quieres, protege updates de cambiar org
    def perform_update(self, serializer):
        serializer.save(org=self.org)
