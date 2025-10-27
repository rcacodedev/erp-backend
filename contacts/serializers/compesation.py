from rest_framework import serializers
from contacts.models import EmployeeCompensation

class EmployeeCompensationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeCompensation
        fields = ('id','inicio','fin','salario_bruto_anual','coste_empresa_pct','plus_mensual','tarifa_interna_hora')
