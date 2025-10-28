# contacts/views/supplier_certifications.py
from datetime import date
from django.db import models
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from contacts.models import SupplierCertification, Contact
from contacts.serializers.supplier_certification import SupplierCertificationSerializer
from .mixins import OrgScopedViewSet

class SupplierCertificationViewSet(OrgScopedViewSet, viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = SupplierCertificationSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ("tipo",)   # 👈 quita 'vigente'

    def get_queryset(self):
        qs = (SupplierCertification.objects
              .select_related('supplier')
              .filter(supplier_id=self.kwargs['supplier_pk'],
                      supplier__org=self.get_org())
              .order_by('-id'))

        vigente = self.request.query_params.get('vigente')
        if vigente is not None:
            hoy = date.today()
            if vigente.lower() in ("1","true","yes","y","t"):
                qs = qs.filter(models.Q(fecha_caducidad__isnull=True) |
                               models.Q(fecha_caducidad__gte=hoy))
            else:
                qs = qs.filter(fecha_caducidad__lt=hoy)
        return qs

    def perform_create(self, serializer):
        supplier = Contact.objects.get(pk=self.kwargs['supplier_pk'], org=self.get_org(), tipo='supplier')
        serializer.save(supplier=supplier, created_by=self.request.user, updated_by=self.request.user)
