import django_filters
from contacts.models import Contact

class ContactFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method='search', label='search')
    tipo = django_filters.CharFilter(field_name='tipo')
    activo = django_filters.BooleanFilter(field_name='activo')
    bloqueado = django_filters.BooleanFilter(field_name='bloqueado')
    etiquetas = django_filters.CharFilter(method='by_tag')

    class Meta:
        model = Contact
        fields = ("tipo", "activo", "bloqueado")

def search(self, qs, name, value):
    return qs.filter(
        models.Q(nombre__icontains=value) |
        models.Q(apellidos__icontains=value) |
        models.Q(razon_social__icontains=value) |
        models.Q(email__icontains=value) |
        models.Q(telefono__icontains=value)
    )

def by_tag(self, qs, name, value):
    return qs.filter(etiquetas__contains=[value])