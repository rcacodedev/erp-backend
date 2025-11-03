# contacts/filters.py
import django_filters
from contacts.models import Contact

class ContactFilter(django_filters.FilterSet):
    tipo = django_filters.CharFilter(field_name='tipo')
    activo = django_filters.BooleanFilter(field_name='activo')
    bloqueado = django_filters.BooleanFilter(field_name='bloqueado')
    etiquetas = django_filters.CharFilter(method='by_tag')  # JSON list contains

    class Meta:
        model = Contact
        fields = ("tipo", "activo", "bloqueado", "etiquetas")

    def by_tag(self, queryset, name, value: str):
        """
        Filtra contactos cuya lista JSON 'etiquetas' contenga exactamente el valor dado.
        Ej.: ?etiquetas=vip  -> etiquetas = ["vip", "gold"]  ✅
        """
        v = (value or "").strip()
        if not v:
            return queryset
        # Para Postgres JSONField list: contiene 'v'
        return queryset.filter(etiquetas__contains=[v])
