# contacts/filters.py
import django_filters
from django.db.models import Q
from contacts.models import Contact

class ContactFilter(django_filters.FilterSet):
    # Nota: si usas DRF SearchFilter, puedes ignorar 'q'. Si prefieres tener 'q' custom, habilítalo.
    q = django_filters.CharFilter(method='search', label='search')
    tipo = django_filters.CharFilter(field_name='tipo')
    activo = django_filters.BooleanFilter(field_name='activo')
    bloqueado = django_filters.BooleanFilter(field_name='bloqueado')
    etiquetas = django_filters.CharFilter(method='by_tag')

    class Meta:
        model = Contact
        fields = ("tipo", "activo", "bloqueado")

    def search(self, qs, name, value):
        v = (value or "").strip()
        if not v:
            return qs
        return qs.filter(
            Q(nombre__icontains=v) |
            Q(apellidos__icontains=v) |
            Q(razon_social__icontains=v) |
            Q(email__icontains=v) |
            Q(telefono__icontains=v) |
            Q(documento_id__icontains=v)
        )

    def by_tag(self, qs, name, value):
        v = (value or "").strip()
        if not v:
            return qs
        # JSONField (lista de strings) → contains exige lista para "contenga 'v'"
        return qs.filter(etiquetas__contains=[v])
