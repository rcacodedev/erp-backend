# contacts/views/mixins.py
from rest_framework import viewsets

class OrgScopedViewSet(viewsets.GenericViewSet):
    """
    Aplica un filtro por organización al queryset.
    Por defecto usa 'org'; para modelos sin org directo, sobreescribe org_lookup.
    """
    org_lookup = "org"
    queryset = None

    def get_org(self):
        return getattr(self.request, "org", None)

    def get_queryset(self):
        assert self.queryset is not None, (
            f"{self.__class__.__name__} debe definir 'queryset'"
        )
        qs = self.queryset
        org = self.get_org()
        if org is not None:
            qs = qs.filter(**{self.org_lookup: org})
        return qs
