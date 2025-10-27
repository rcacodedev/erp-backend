from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Sum
from contacts.models import EmployeeHours
from contacts.serializers.employee_hours import EmployeeHoursSerializer
from .mixins import OrgScopedViewSet

class EmployeeHoursViewSet(OrgScopedViewSet, viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = EmployeeHoursSerializer
    queryset = EmployeeHours.objects.all()

    def get_queryset(self):
        return super().get_queryset().filter(contact_id=self.kwargs['contact_pk'])

    @action(detail=False, methods=['get'])
    def summary(self, request, contact_pk=None):
        month = request.query_params.get('month')  # YYYY-MM
        qs = self.get_queryset()
        if month:
            from calendar import monthrange
            from datetime import date
            y,m = map(int, month.split('-'))
            start = date(y,m,1); end = date(y,m,monthrange(y,m)[1])
            qs = qs.filter(fecha__range=(start,end))
        total = qs.aggregate(total=Sum('horas_totales'))['total'] or 0
        return Response({"contact_id": int(contact_pk), "total_horas": float(total)})
