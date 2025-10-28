from rest_framework import serializers
from contacts.models import SupplierPrice

class SupplierPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierPrice
        fields = (
            "id", "sku_proveedor", "producto_sku_interno",
            "precio", "moneda", "min_qty", "lead_time_dias",
            "valido_desde", "valido_hasta", "created_at", "updated_at"
        )
        read_only_fields = ("id", "created_at", "updated_at")  # y 'org' no aparece
