# contacts/serializers/compensation.py
from rest_framework import serializers
from contacts.models import EmployeeCompensation

class EmployeeCompensationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeCompensation
        fields = [
            "id", "inicio", "fin",
            "salario_bruto_anual", "coste_empresa_pct",
            "plus_mensual", "tarifa_interna_hora",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, data):
        inicio = data.get("inicio", getattr(self.instance, "inicio", None))
        fin = data.get("fin", getattr(self.instance, "fin", None))
        if fin and inicio and fin < inicio:
            raise serializers.ValidationError({"fin": "Debe ser >= inicio o null."})
        return data
