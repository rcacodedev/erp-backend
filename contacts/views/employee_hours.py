from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Sum
from datetime import date
from calendar import monthrange

from contacts.models import EmployeeHours
from contacts.serializers.employee_hours import EmployeeHoursSerializer
from .mixins import OrgScopedViewSet

class EmployeeHoursViewSet(OrgScopedViewSet, viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = EmployeeHoursSerializer

    def get_queryset(self):
        return (
            EmployeeHours.objects
            .select_related('contact')
            .filter(
                contact_id=self.kwargs['contact_pk'],
                contact__org=self.get_org(),
            )
            .order_by('-fecha', '-id')
        )

    def perform_create(self, serializer):
        serializer.save(
            contact_id=self.kwargs['contact_pk'],
            created_by=self.request.user,
            updated_by=self.request.user,
        )

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=['get'])
    def summary(self, request, *args, **kwargs):
        # Aceptamos org_slug y demás kwargs del path
        contact_pk = int(kwargs['contact_pk'])

        month = request.query_params.get('month')  # formato: YYYY-MM
        qs = self.get_queryset()

        if month:
            try:
                y, m = map(int, month.split('-'))
                start = date(y, m, 1)
                end = date(y, m, monthrange(y, m)[1])
                qs = qs.filter(fecha__range=(start, end))
            except Exception:
                return Response(
                    {"detail": "Parámetro 'month' inválido. Usa YYYY-MM, p.ej. 2025-10"},
                    status=400
                )
        else:
            # (Opcional) si no pasan month, sumariza mes actual
            today = date.today()
            start = date(today.year, today.month, 1)
            end = date(today.year, today.month, monthrange(today.year, today.month)[1])
            qs = qs.filter(fecha__range=(start, end))

        total = qs.aggregate(total=Sum('horas_totales'))['total'] or 0
        return Response({"contact_id": contact_pk, "total_horas": float(total)})
