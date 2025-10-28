# contacts/views/supplier_prices.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from contacts.models import SupplierPrice, Contact
from contacts.serializers.supplier_price import SupplierPriceSerializer
from .mixins import OrgScopedViewSet

class SupplierPriceViewSet(OrgScopedViewSet, viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = SupplierPriceSerializer
    filter_backends = (DjangoFilterBackend,)
    # ✅ usa campos reales del modelo
    filterset_fields = ("sku_proveedor", "producto_sku_interno", "moneda", "min_qty", "lead_time_dias")

    def get_queryset(self):
        return (
            SupplierPrice.objects
            .select_related('supplier')
            .filter(supplier_id=self.kwargs['supplier_pk'], supplier__org=self.get_org())
            .order_by('-id')
        )

    def perform_create(self, serializer):
        # ✅ mete también org, obligatorio en el modelo
        supplier = Contact.objects.get(pk=self.kwargs['supplier_pk'], org=self.get_org(), tipo='supplier')
        serializer.save(
            org=self.get_org(),
            supplier=supplier,
            created_by=self.request.user,
            updated_by=self.request.user,
        )

    def perform_update(self, serializer):
        # mantener org/supplier coherentes en updates
        supplier = Contact.objects.get(pk=self.kwargs['supplier_pk'], org=self.get_org(), tipo='supplier')
        serializer.save(
            org=self.get_org(),
            supplier=supplier,
            updated_by=self.request.user,
        )

    @action(detail=False, methods=['post'])
    def import_csv(self, request, *args, **kwargs):
        """
        CSV esperado (cabeceras):
        sku_proveedor,producto_sku_interno,precio,moneda,min_qty,lead_time_dias,valido_desde,valido_hasta
        """
        f = request.FILES.get('file')
        if not f:
            return Response({"detail": "Falta archivo CSV en 'file'."}, status=400)

        import csv, io
        from datetime import date
        supplier = Contact.objects.get(pk=self.kwargs['supplier_pk'], org=self.get_org(), tipo='supplier')
        reader = csv.DictReader(io.TextIOWrapper(f.file, encoding='utf-8'))

        created = updated = 0
        errors = []

        def parse_date(s):
            if not s:
                return None
            return date.fromisoformat(s)  # YYYY-MM-DD

        for i, row in enumerate(reader, start=1):
            try:
                obj, was_created = SupplierPrice.objects.update_or_create(
                    org=self.get_org(),
                    supplier=supplier,
                    sku_proveedor=row['sku_proveedor'].strip(),
                    valido_desde=parse_date(row.get('valido_desde') or ""),
                    defaults={
                        'producto_sku_interno': (row.get('producto_sku_interno') or "").strip(),
                        'precio': row['precio'],
                        'moneda': (row.get('moneda') or 'EUR').strip(),
                        'min_qty': int(row.get('min_qty') or 1),
                        'lead_time_dias': int(row.get('lead_time_dias') or 0),
                        'valido_hasta': parse_date(row.get('valido_hasta') or ""),
                        'updated_by': request.user,
                    }
                )
                if was_created:
                    obj.created_by = request.user
                    obj.save(update_fields=['created_by'])
                    created += 1
                else:
                    updated += 1
            except Exception as e:
                errors.append({"row": i, "error": str(e)})

        return Response({"created": created, "updated": updated, "errors": errors})
