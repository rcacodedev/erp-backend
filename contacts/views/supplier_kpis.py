# contacts/views/supplier_kpis.py
from datetime import date
from calendar import monthrange
from django.db.models import Avg, Q
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from contacts.models import Contact, SupplierPrice, SupplierCertification

class SupplierKPIsView(APIView):
    permission_classes = (IsAuthenticated,)

    def _month_range(self, y, m):
        start = date(y, m, 1)
        end = date(y, m, monthrange(y, m)[1])
        return start, end

    def get(self, request, org_slug=None, supplier_pk=None):
        # month=YYYY-MM (sin barra final)
        month = request.query_params.get("month")
        if not month:
            return Response({"detail": "Parámetro 'month=YYYY-MM' requerido"}, status=400)
        try:
            y, m = map(int, month.split("-"))
            start, end = self._month_range(y, m)
        except Exception:
            return Response({"detail": "Formato inválido en 'month'. Usa YYYY-MM"}, status=400)

        # Validar supplier en el tenant
        try:
            supplier = Contact.objects.get(pk=supplier_pk, org__slug=org_slug, tipo="supplier")
        except Contact.DoesNotExist:
            return Response({"detail": "Supplier no encontrado en la organización"}, status=404)

        # 1) Lead time medio de precios vigentes en el mes
        # Vigente = (valido_desde <= end) y (valido_hasta is null o valido_hasta >= start)
        lead_time = (SupplierPrice.objects
                     .filter(
                         supplier=supplier,
                         valido_desde__lte=end
                     )
                     .filter(Q(valido_hasta__isnull=True) | Q(valido_hasta__gte=start))
                     .aggregate(avg=Avg("lead_time_dias"))["avg"])

        # 2) Certificaciones activas en el mes (sin caducidad o caduca después de start)
        active_certs = (SupplierCertification.objects
                        .filter(
                            supplier=supplier
                        )
                        .filter(Q(fecha_caducidad__isnull=True) | Q(fecha_caducidad__gte=start))
                        .count())

        # 3) KPIs que requieren más modelo (placeholders)
        on_time_rate = None           # requiere órdenes de compra + recepciones con fechas
        quality_incidents = 0         # requiere modelo de incidencias de calidad

        return Response({
            "supplier_id": supplier.id,
            "period": month,
            "on_time_rate": on_time_rate,
            "avg_lead_time_days": float(lead_time) if lead_time is not None else None,
            "quality_incidents": quality_incidents,
            "active_certs": active_certs,
        })
