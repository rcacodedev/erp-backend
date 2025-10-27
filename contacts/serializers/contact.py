from rest_framework import serializers
from contacts.models import Contact, ClientProfile, SupplierProfile, EmployeeProfile
from .address import AddressSerializer
from .attachments import AttachmentSerializer
from .consent import ConsentSerializer

class ClientProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientProfile
        fields = ("cliente_desde", "sector", "tamano", "rating", "riesgo_credito", "limite_credito", "condiciones_comerciales")

class SupplierProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierProfile
        fields = ("proveedor_desde", "categorias_suministro", "plazo_pago", "es_preferente", "calidad_rating")

class EmployeeProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeProfile
        fields = (
            "fecha_alta","fecha_baja","puesto","departamento","tipo_contrato","jornada",
            "salario_bruto_anual","nss","fecha_nacimiento","direccion_fiscal","responsable_directo",
            "ubicacion","centro_coste","objetivo_horas_mes",
            "documentos_confidenciales","activo","observaciones",
        )

class ContactListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = (
        "id", "tipo", "es_persona", "nombre", "apellidos", "razon_social", "email", "telefono", "activo", "bloqueado",
        "etiquetas", "segmento"
        )

class ContactDetailSerializer(serializers.ModelSerializer):
    direcciones = AddressSerializer(many=True, required=False)
    adjuntos = AttachmentSerializer(many=True, read_only=True)
    consentimientos = ConsentSerializer(many=True, read_only=True)
    cliente = ClientProfileSerializer(required=False)
    proveedor = SupplierProfileSerializer(required=False)
    empleado = EmployeeProfileSerializer(required=False)

    class Meta:
        model = Contact
        fields = (
        "id", "tipo", "es_persona", "nombre", "apellidos", "razon_social", "nombre_comercial",
        "email", "telefono", "movil", "web", "documento_id",
        "condiciones_pago", "iban", "moneda_preferida", "retencion",
        "marketing_opt_in", "marketing_opt_in_at", "marketing_opt_in_method",
        "rgpd_aceptado", "rgpd_aceptado_at", "rgpd_version_texto",
        "etiquetas", "segmento", "origen", "vendedor_responsable",
        "notas", "activo", "bloqueado", "motivo_bloqueo",
        "direcciones", "adjuntos", "consentimientos",
        "cliente", "proveedor", "empleado",
        )
        read_only_fields = ("marketing_opt_in_at", "rgpd_aceptado_at")

    def create(self, validated):
        dirs = validated.pop('direcciones', [])
        client = validated.pop('cliente', None)
        supplier = validated.pop('proveedor', None)
        employee = validated.pop('empleado', None)
        contact = super().create(validated)
        for d in dirs:
            self.fields['direcciones'].Meta.model.objects.create(contact=contact, **d)
        if contact.tipo == 'client' and client:
            ClientProfile.objects.create(contact=contact, **client)
        if contact.tipo == 'supplier' and supplier:
            SupplierProfile.objects.create(contact=contact, **supplier)
        if contact.tipo == 'employee' and employee:
            EmployeeProfile.objects.create(contact=contact, **employee)
        return contact


    def update(self, instance, validated):
        dirs = validated.pop('direcciones', None)
        client = validated.pop('cliente', None)
        supplier = validated.pop('proveedor', None)
        employee = validated.pop('empleado', None)
        contact = super().update(instance, validated)
        if dirs is not None:
            # reemplazo simple; para edición granular usar endpoint de direcciones
            instance.direcciones.all().delete()
            for d in dirs:
                self.fields['direcciones'].Meta.model.objects.create(contact=contact, **d)
        if contact.tipo == 'client' and client is not None:
            obj, _ = ClientProfile.objects.get_or_create(contact=contact)
            for k, v in client.items(): setattr(obj, k, v)
            obj.save()
        if contact.tipo == 'supplier' and supplier is not None:
            obj, _ = SupplierProfile.objects.get_or_create(contact=contact)
            for k, v in supplier.items(): setattr(obj, k, v)
            obj.save()
        if contact.tipo == 'employee' and employee is not None:
            obj, _ = EmployeeProfile.objects.get_or_create(contact=contact)
            for k, v in employee.items(): setattr(obj, k, v)
            obj.save()
        return contact