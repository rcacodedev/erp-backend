from datetime import date
from calendar import monthrange
from django.db.models import Sum
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from contacts.models import Contact, EmployeeCompensation, EmployeeHours, LocationRevenue

class EmployeeFinancialsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get_month_range(self, y, m):
        start = date(y, m, 1)
        end = date(y, m, monthrange(y, m)[1])
        return start, end

    def get(self, request, org_slug=None, contact_pk=None):
        # Param month=YYYY-MM
        month = request.query_params.get('month')
        if not month:
            return Response({"detail":"Parámetro 'month=YYYY-MM' requerido"}, status=400)
        y, m = map(int, month.split('-'))
        start, end = self.get_month_range(y, m)

        emp = Contact.objects.select_related('empleado__ubicacion').get(pk=contact_pk, org__slug=org_slug, tipo='employee')
        emp_prof = emp.empleado

        # 1) Compensación vigente en el mes (choose last by inicio <= end and (fin is null or fin >= start))
        comp = (EmployeeCompensation.objects
                .filter(contact=emp, inicio__lte=end)
                .filter(models.Q(fin__isnull=True) | models.Q(fin__gte=start))
                .order_by('-inicio')
                .first())
        if comp:
            sueldo_mensual = comp.salario_bruto_anual / 12
            coste_mes = sueldo_mensual * (1 + (comp.coste_empresa_pct/100)) + comp.plus_mensual
        else:
            sueldo_mensual = 0
            coste_mes = 0

        # 2) Horas del mes del empleado
        horas_emp = (EmployeeHours.objects
                     .filter(contact=emp, fecha__range=(start, end))
                     .aggregate(total=Sum('horas_totales'))['total']) or 0

        # 3) Ingresos del mes (puente V1: por ubicacion)
        ingresos_mes = 0
        if getattr(emp_prof, 'ubicacion_id', None):
            lr = LocationRevenue.objects.filter(location_id=emp_prof.ubicacion_id, periodo=start).first()
            if lr:
                # reparto por horas entre empleados de esa ubicación en ese mes
                same_loc_contacts = (Contact.objects
                                     .filter(org=emp.org, tipo='employee', empleado__ubicacion_id=emp_prof.ubicacion_id)
                                     .values_list('id', flat=True))
                horas_loc_total = (EmployeeHours.objects
                                   .filter(contact_id__in=list(same_loc_contacts), fecha__range=(start, end))
                                   .aggregate(total=Sum('horas_totales'))['total']) or 0
                if horas_loc_total and horas_emp:
                    ingresos_mes = float(lr.ingresos) * float(horas_emp / horas_loc_total)
                else:
                    # fallback: si no hay horas, atribuye partes iguales entre empleados de la ubicación
                    count_emp = len(set(same_loc_contacts)) or 1
                    ingresos_mes = float(lr.ingresos) / count_emp

        # 4) KPIs
        margen = float(ingresos_mes) - float(coste_mes)
        margen_pct = (margen / ingresos_mes * 100) if ingresos_mes else 0.0
        objetivo = getattr(emp_prof, 'objetivo_horas_mes', 160) or 160
        utilizacion_pct = (float(horas_emp) / float(objetivo) * 100) if objetivo else 0.0
        coste_hora = (float(coste_mes) / float(horas_emp)) if horas_emp else None

        return Response({
            "employee_id": emp.id,
            "period": month,
            "ubicacion": emp_prof.ubicacion.nombre if emp_prof and emp_prof.ubicacion_id else None,
            "ingresos": round(float(ingresos_mes), 2),
            "coste": round(float(coste_mes), 2),
            "margen": round(float(margen), 2),
            "margen_pct": round(float(margen_pct), 2),
            "horas": float(horas_emp),
            "coste_hora": round(float(coste_hora), 2) if coste_hora is not None else None,
            "utilizacion_pct": round(float(utilizacion_pct), 2),
        })
