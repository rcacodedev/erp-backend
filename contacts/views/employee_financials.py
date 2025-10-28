# contacts/views/employee_financials.py
from datetime import date
from calendar import monthrange
from decimal import Decimal

from django.db import models
from django.db.models import Sum, Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from contacts.models import Contact, EmployeeCompensation, EmployeeHours, LocationRevenue


class EmployeeFinancialsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get_month_range(self, y: int, m: int):
        start = date(y, m, 1)
        end = date(y, m, monthrange(y, m)[1])
        return start, end

    def parse_month(self, raw: str):
        """Acepta 'YYYY-MM' y tolera barras/espacios al final."""
        if not raw:
            return None
        raw = raw.strip().rstrip("/")
        parts = raw.split("-", 1)
        if len(parts) != 2:
            return None
        try:
            y, m = int(parts[0]), int(parts[1])
            if not (1 <= m <= 12):
                return None
            return y, m
        except Exception:
            return None

    def get(self, request, org_slug=None, contact_pk=None):
        # 1) month requerido con normalización
        month_raw = request.query_params.get("month", "")
        parsed = self.parse_month(month_raw)
        if not parsed:
            return Response({"detail": "Parámetro 'month' inválido. Usa YYYY-MM (p.ej. 2025-10)."},
                            status=status.HTTP_400_BAD_REQUEST)
        y, m = parsed
        start, end = self.get_month_range(y, m)

        # 2) Empleado (scoping por org y tipo)
        try:
            emp = (Contact.objects
                   .select_related('empleado__ubicacion', 'org')
                   .get(pk=contact_pk, org__slug=org_slug, tipo='employee'))
        except Contact.DoesNotExist:
            return Response({"detail": "Empleado no encontrado en esta organización."},
                            status=status.HTTP_404_NOT_FOUND)
        emp_prof = getattr(emp, 'empleado', None)

        # 3) Compensación vigente en el mes
        comp = (EmployeeCompensation.objects
                .filter(contact=emp, inicio__lte=end)
                .filter(Q(fin__isnull=True) | Q(fin__gte=start))
                .order_by('-inicio')
                .first())

        sueldo_mensual = Decimal('0.00')
        coste_mes = Decimal('0.00')
        if comp:
            # usa Decimal para evitar sorpresas
            salario = Decimal(comp.salario_bruto_anual)
            coste_pct = Decimal(comp.coste_empresa_pct) / Decimal('100')
            plus = Decimal(comp.plus_mensual)
            sueldo_mensual = (salario / Decimal('12'))
            coste_mes = (sueldo_mensual * (Decimal('1') + coste_pct)) + plus

        # 4) Horas del mes del empleado
        horas_emp = (EmployeeHours.objects
                     .filter(contact=emp, fecha__range=(start, end))
                     .aggregate(total=Sum('horas_totales'))['total']) or 0
        horas_emp = float(horas_emp)

        # 5) Ingresos del mes (puente V1 por ubicación)
        ingresos_mes = Decimal('0.00')
        if emp_prof and getattr(emp_prof, 'ubicacion_id', None):
            lr = (LocationRevenue.objects
                  .filter(location_id=emp_prof.ubicacion_id, periodo=start)
                  .first())
            if lr:
                same_loc_contacts = list(Contact.objects
                                         .filter(org=emp.org, tipo='employee', empleado__ubicacion_id=emp_prof.ubicacion_id)
                                         .values_list('id', flat=True))
                horas_loc_total = (EmployeeHours.objects
                                   .filter(contact_id__in=same_loc_contacts, fecha__range=(start, end))
                                   .aggregate(total=Sum('horas_totales'))['total']) or 0
                horas_loc_total = float(horas_loc_total)
                if horas_loc_total > 0 and horas_emp > 0:
                    ingresos_mes = Decimal(lr.ingresos) * Decimal(horas_emp / horas_loc_total)
                else:
                    count_emp = len(set(same_loc_contacts)) or 1
                    ingresos_mes = Decimal(lr.ingresos) / Decimal(count_emp)

        # 6) KPIs
        coste_mes_f = float(coste_mes)
        ingresos_f = float(ingresos_mes)
        margen = ingresos_f - coste_mes_f
        margen_pct = (margen / ingresos_f * 100.0) if ingresos_f else 0.0
        objetivo = getattr(emp_prof, 'objetivo_horas_mes', 160) or 160
        utilizacion_pct = (horas_emp / float(objetivo) * 100.0) if objetivo else 0.0
        coste_hora = (coste_mes_f / horas_emp) if horas_emp else None

        return Response({
            "employee_id": emp.id,
            "period": f"{y:04d}-{m:02d}",
            "ubicacion": (emp_prof.ubicacion.nombre if (emp_prof and emp_prof.ubicacion_id) else None),
            "ingresos": round(ingresos_f, 2),
            "coste": round(coste_mes_f, 2),
            "margen": round(margen, 2),
            "margen_pct": round(margen_pct, 2),
            "horas": round(horas_emp, 2),
            "coste_hora": (round(coste_hora, 2) if coste_hora is not None else None),
            "utilizacion_pct": round(utilizacion_pct, 2),
        })
