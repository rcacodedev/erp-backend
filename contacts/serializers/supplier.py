from rest_framework import serializers
from contacts.models import Contact

class SupplierListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = (
            "id", "razon_social", "nombre", "apellidos",
            "email", "telefono", "activo", "segmento", "etiquetas"
        )

class SupplierDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = (
            "id", "tipo",
            # Identidad
            "es_persona", "razon_social", "nombre", "apellidos", "nombre_comercial",
            # Identificadores
            "email", "telefono", "movil", "web", "documento_id",
            # Facturación/Compras
            "condiciones_pago", "iban", "moneda_preferida", "retencion",
            # Consentimientos
            "marketing_opt_in", "marketing_opt_in_at", "marketing_opt_in_method",
            "rgpd_aceptado", "rgpd_aceptado_at", "rgpd_version_texto",
            # Clasificación
            "etiquetas", "segmento", "origen", "vendedor_responsable",
            # Otros
            "notas", "activo", "bloqueado", "motivo_bloqueo",
            # Auditoría
            "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at", "tipo")
        extra_kwargs = {
            # Haz opcionales los que no quieras exigir al crear:
            "email": {"required": False, "allow_blank": True},
            "telefono": {"required": False, "allow_blank": True},
            "movil": {"required": False, "allow_blank": True},
            "documento_id": {"required": False, "allow_blank": True},
            "iban": {"required": False, "allow_blank": True},
            "condiciones_pago": {"required": False, "allow_blank": True},
            "notas": {"required": False, "allow_blank": True},
        }

    def create(self, validated_data):
        validated_data["tipo"] = "supplier"
        return super().create(validated_data)
