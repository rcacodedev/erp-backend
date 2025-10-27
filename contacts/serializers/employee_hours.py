# contacts/serializers/employee_hours.py
from rest_framework import serializers
from contacts.models import EmployeeHours

class EmployeeHoursSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeHours
        fields = (
            'id', 'fecha', 'horas_totales', 'entrada', 'salida',
            'descanso_minutos', 'fuente', 'referencia',
        )
