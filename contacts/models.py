from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.postgres.indexes import GinIndex
from django.db.models import Q

# Usa tus modelos reales del core
from core.models import TimeStampedModel, Organization

from .choices import (
    ContactType, AddressType, WorkLocationType, ContractType, JornadaType,
    AntivirusState,
)
from .validators import (
    validate_email_basic, validate_phone_basic, validate_iban_basic, validate_id_document_basic,
)

User = settings.AUTH_USER_MODEL


# ==========
# AUDITORÍA
# ==========
class AuditMixin(TimeStampedModel):
    """
    Extiende tu TimeStampedModel con created_by/updated_by para auditoría.
    """
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="%(class)s_created"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="%(class)s_updated"
    )

    class Meta:
        abstract = True


# =====================
# FUNCIONES AUXILIARES
# =====================
def attachment_upload_to(instance, filename):
    """
    Ruta S3/local: org/<org_id>/contacts/<contact_id>/<uuid>__<filename>
    (Organization.id es UUID → usamos org_id)
    """
    import uuid, os
    safe_name = os.path.basename(filename)
    return f"org/{instance.contact.org_id}/contacts/{instance.contact_id}/{uuid.uuid4()}__{safe_name}"


# ==================
# ENTIDADES PRINCIPALES
# ==================

class Contact(AuditMixin):
    org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='contacts')
    tipo = models.CharField(max_length=12, choices=ContactType.CHOICES)

    # Identidad
    es_persona = models.BooleanField(default=True)
    nombre = models.CharField(max_length=120, blank=True)
    apellidos = models.CharField(max_length=160, blank=True)
    razon_social = models.CharField(max_length=200, blank=True)
    nombre_comercial = models.CharField(max_length=200, blank=True)

    # Identificadores
    email = models.CharField(max_length=200, blank=True, validators=[validate_email_basic])
    telefono = models.CharField(max_length=30, blank=True, validators=[validate_phone_basic])
    movil = models.CharField(max_length=30, blank=True, validators=[validate_phone_basic])
    web = models.URLField(blank=True)
    documento_id = models.CharField(max_length=20, blank=True, validators=[validate_id_document_basic])

    # Facturación/Compras
    condiciones_pago = models.CharField(max_length=120, blank=True)
    iban = models.CharField(max_length=34, blank=True, validators=[validate_iban_basic])
    moneda_preferida = models.CharField(max_length=10, blank=True, default="EUR")
    retencion = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                    validators=[MinValueValidator(0), MaxValueValidator(100)])

    # Consentimientos
    marketing_opt_in = models.BooleanField(default=False)
    marketing_opt_in_at = models.DateTimeField(null=True, blank=True)
    marketing_opt_in_method = models.CharField(max_length=50, blank=True)
    rgpd_aceptado = models.BooleanField(default=False)
    rgpd_aceptado_at = models.DateTimeField(null=True, blank=True)
    rgpd_version_texto = models.CharField(max_length=50, blank=True)

    # Clasificación
    etiquetas = models.JSONField(default=list, blank=True)
    segmento = models.CharField(max_length=100, blank=True)
    origen = models.CharField(max_length=50, blank=True)
    vendedor_responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name='contacts_responsable'
    )

    # Otros
    notas = models.TextField(blank=True)
    activo = models.BooleanField(default=True)
    bloqueado = models.BooleanField(default=False)
    motivo_bloqueo = models.CharField(max_length=255, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['org', 'tipo']),
            models.Index(fields=['org', 'razon_social']),
            models.Index(fields=['org', 'email']),
            models.Index(fields=['org', 'documento_id']),
            models.Index(fields=['org', 'nombre']),
            models.Index(fields=['org', 'telefono']),
            models.Index(fields=['org', 'updated_by']),  # útil para auditoría en listados
            models.Index(fields=['org', 'activo']),
            models.Index(fields=['org', 'bloqueado']),
            GinIndex(name='idx_contacts_etiquetas_gin', fields=['etiquetas']),
        ]
        # Evita colisión por email/documento vacío: solo únicos si no están vacíos
        constraints = [
            models.UniqueConstraint(
                fields=['org', 'tipo', 'email'],
                name='uq_contact_email_nonempty',
                condition=~Q(email="")
            ),
            models.UniqueConstraint(
                fields=['org', 'documento_id'],
                name='uq_contact_docid_nonempty',
                condition=~Q(documento_id="")
            ),
        ]

    def __str__(self):
        base = self.razon_social or f"{self.nombre} {self.apellidos}".strip()
        return base or f"Contacto {self.pk}"


class Address(AuditMixin):
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='direcciones')
    tipo = models.CharField(max_length=10, choices=AddressType.CHOICES, default=AddressType.FISCAL)
    linea1 = models.CharField(max_length=150)
    linea2 = models.CharField(max_length=150, blank=True)
    cp = models.CharField(max_length=12, blank=True)
    ciudad = models.CharField(max_length=100, blank=True)
    provincia = models.CharField(max_length=100, blank=True)
    pais = models.CharField(max_length=2, default='ES')
    es_principal = models.BooleanField(default=False)

    class Meta:
        indexes = [models.Index(fields=['tipo'])]

    def __str__(self):
        return f"{self.linea1} ({self.ciudad})"


class ClientProfile(AuditMixin):
    contact = models.OneToOneField(Contact, on_delete=models.CASCADE, related_name='cliente')
    cliente_desde = models.DateField(null=True, blank=True)
    sector = models.CharField(max_length=120, blank=True)
    tamano = models.CharField(max_length=50, blank=True)
    rating = models.PositiveSmallIntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(5)])
    riesgo_credito = models.CharField(max_length=50, blank=True)
    limite_credito = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    condiciones_comerciales = models.TextField(blank=True)

    def __str__(self):
        return f"Cliente<{self.contact_id}>"


class SupplierProfile(AuditMixin):
    contact = models.OneToOneField(Contact, on_delete=models.CASCADE, related_name='proveedor')
    proveedor_desde = models.DateField(null=True, blank=True)
    categorias_suministro = models.JSONField(default=list, blank=True)
    plazo_pago = models.CharField(max_length=50, blank=True)
    es_preferente = models.BooleanField(default=False)
    calidad_rating = models.PositiveSmallIntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(5)])

    def __str__(self):
        return f"Proveedor<{self.contact_id}>"


class EmployeeProfile(AuditMixin):
    contact = models.OneToOneField(Contact, on_delete=models.CASCADE, related_name='empleado')
    fecha_alta = models.DateField(null=True, blank=True)
    fecha_baja = models.DateField(null=True, blank=True)
    puesto = models.CharField(max_length=120, blank=True)
    departamento = models.CharField(max_length=120, blank=True)
    tipo_contrato = models.CharField(max_length=20, choices=ContractType.CHOICES, blank=True)
    jornada = models.CharField(max_length=20, choices=JornadaType.CHOICES, blank=True)
    salario_bruto_anual = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    nss = models.CharField(max_length=20, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    direccion_fiscal = models.ForeignKey(
        Address, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='empleados_direccion_fiscal'
    )
    # Nota: responsable_directo como EmployeeProfile (jerarquía)
    responsable_directo = models.ForeignKey(
        'self', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='subordinados'
    )
    ubicacion = models.ForeignKey(
        'contacts.LocationLite', null=True, blank=True,
        on_delete=models.SET_NULL, related_name='empleados'
    )
    centro_coste = models.CharField(max_length=50, blank=True)
    documentos_confidenciales = models.BooleanField(default=True)
    activo = models.BooleanField(default=True)
    observaciones = models.TextField(blank=True)
    objetivo_horas_mes = models.PositiveIntegerField(default=160)

    def __str__(self):
        return f"Empleado<{self.contact_id}>"


class Attachment(AuditMixin):
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='adjuntos')
    nombre_original = models.CharField(max_length=255)
    tipo_mime = models.CharField(max_length=120, blank=True)
    tamano_bytes = models.BigIntegerField(default=0)
    file = models.FileField(upload_to=attachment_upload_to, max_length=500)
    sha256 = models.CharField(max_length=64, blank=True)
    categoria = models.CharField(max_length=30, blank=True)
    confidencial = models.BooleanField(default=False)
    antivirus_estado = models.CharField(max_length=20, choices=AntivirusState.CHOICES,
                                        default=AntivirusState.PENDIENTE)
    periodo_nomina = models.DateField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['contact', 'categoria', 'periodo_nomina'],
                name='unique_payslip_per_month',
                condition=models.Q(categoria='nomina'),
            )
        ]
        indexes = [
            models.Index(fields=['contact', 'categoria', 'periodo_nomina']),
        ]

    def __str__(self):
        return self.nombre_original or f"Adjunto<{self.pk}>"


class Consent(AuditMixin):
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='consentimientos')
    tipo = models.CharField(max_length=20)  # 'rgpd' | 'marketing'
    estado = models.CharField(max_length=20)  # 'opt_in' | 'opt_out'
    metodo = models.CharField(max_length=20, blank=True)  # 'web' | 'manual' | 'import'
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=255, blank=True)
    version_texto = models.CharField(max_length=50, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tipo}:{self.estado} for {self.contact_id}"


class CustomField(AuditMixin):
    org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='contacts_custom_fields')
    para_tipo = models.CharField(max_length=12, choices=ContactType.CHOICES)
    name = models.SlugField(max_length=50)
    label = models.CharField(max_length=80)
    field_type = models.CharField(max_length=20)  # text, number, date, bool, enum, url
    required = models.BooleanField(default=False)
    unique_in_org = models.BooleanField(default=False)
    options = models.JSONField(default=list, blank=True)  # for enum
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        unique_together = (('org', 'para_tipo', 'name'),)

    def __str__(self):
        return f"{self.label} ({self.para_tipo})"


class CustomFieldValue(AuditMixin):
    field = models.ForeignKey(CustomField, on_delete=models.CASCADE, related_name='values')
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='custom_values')
    value = models.JSONField()

    class Meta:
        unique_together = (('field', 'contact'),)

    def __str__(self):
        return f"CFV field={self.field_id} contact={self.contact_id}"

class EmployeeHours(AuditMixin):
    """
    Registro de horas de un empleado por día (posibles múltiples entradas/salidas resumidas).
    Permite importación desde CSV/XLSX de apps externas.
    """
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='horas_trabajadas')
    fecha = models.DateField()
    horas_totales = models.DecimalField(max_digits=5, decimal_places=2)  # ej. 7.50
    entrada = models.TimeField(null=True, blank=True)
    salida = models.TimeField(null=True, blank=True)
    descanso_minutos = models.PositiveIntegerField(default=0)
    fuente = models.CharField(max_length=50, blank=True)  # ej. 'csv', 'factorial', 'sesame', 'clockify'
    referencia = models.CharField(max_length=100, blank=True)  # id externo u observación

    class Meta:
        unique_together = (('contact', 'fecha', 'referencia'),)  # evita duplicados obvios
        indexes = [
            models.Index(fields=['contact', 'fecha']),
        ]

    def __str__(self):
        return f"{self.contact_id} {self.fecha} {self.horas_totales}h"

class LocationLite(AuditMixin):
    org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='location_lite')
    nombre = models.CharField(max_length=120)

    class Meta:
        unique_together = (('org', 'nombre'),)
        indexes = [models.Index(fields=['org', 'nombre'])]

    def __str__(self):
        return self.nombre

class EmployeeCompensation(AuditMixin):
    """
    Historial de compensación. Un registro activo por fecha.
    """
    contact = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='compensaciones')
    inicio = models.DateField()             # desde (incl.)
    fin = models.DateField(null=True, blank=True)  # hasta (incl.) - null = vigente
    salario_bruto_anual = models.DecimalField(max_digits=12, decimal_places=2)  # € brutos
    coste_empresa_pct = models.DecimalField(max_digits=5, decimal_places=2, default=30.00)  # SS + otros (aprox.)
    plus_mensual = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # bonus/var.
    # (opcional) tarifa_interna_hora si quieres fijar un “coste hora” pactado:
    tarifa_interna_hora = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=['contact', 'inicio'])]

class LocationRevenue(AuditMixin):
    org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='location_revenues')
    location = models.ForeignKey('contacts.LocationLite', on_delete=models.CASCADE, related_name='revenues')
    periodo = models.DateField()  # usar primer día del mes (YYYY-MM-01)
    ingresos = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        unique_together = (('location','periodo'),)
        indexes = [models.Index(fields=['location','periodo'])]

def client_upload_to(instance, filename):
    import uuid, os
    safe = os.path.basename(filename)
    return f"org/{instance.cliente.org_id}/clients/{instance.cliente_id}/docs/{uuid.uuid4()}__{safe}"

class ClientAttachment(AuditMixin):
    cliente = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='documentos')
    categoria = models.CharField(max_length=30, blank=True)  # 'rgpd','contrato','otro'
    file = models.FileField(upload_to=client_upload_to, max_length=500)
    nombre_original = models.CharField(max_length=255)
    confidencial = models.BooleanField(default=False)
    sha256 = models.CharField(max_length=64, blank=True)

class ClientNote(AuditMixin):
    cliente = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='client_notes')
    titulo = models.CharField(max_length=150)
    texto = models.TextField()
    importante = models.BooleanField(default=False)

class ClientEvent(AuditMixin):
    org = models.ForeignKey(Organization, on_delete=models.CASCADE)
    cliente = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='citas')
    tipo = models.CharField(max_length=20, choices=[('cita','Cita'),('visita','Visita'),('reunion','Reunión')], default='cita')
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    inicio = models.DateTimeField()
    fin = models.DateTimeField()
    empleado_asignado = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    estado = models.CharField(max_length=20, choices=[('pendiente','Pendiente'),('realizada','Realizada'),('cancelada','Cancelada')], default='pendiente')
    ubicacion = models.CharField(max_length=200, blank=True)

# ===== SUPPLIERS =====

def supplier_upload_to(instance, filename):
    import uuid, os
    safe = os.path.basename(filename)
    return f"org/{instance.supplier.org_id}/suppliers/{instance.supplier_id}/docs/{uuid.uuid4()}__{safe}"

def supplier_cert_upload_to(instance, filename):
    import uuid, os
    safe = os.path.basename(filename)
    return f"org/{instance.supplier.org_id}/suppliers/{instance.supplier_id}/certs/{uuid.uuid4()}__{safe}"

class SupplierAttachment(AuditMixin):
    supplier = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='supplier_docs')
    categoria = models.CharField(max_length=30, blank=True)  # 'contrato','certificado','homologacion','rgpd','otro'
    file = models.FileField(upload_to=supplier_upload_to, max_length=500)
    nombre_original = models.CharField(max_length=255)
    confidencial = models.BooleanField(default=False)
    sha256 = models.CharField(max_length=64, blank=True)

class SupplierNote(AuditMixin):
    supplier = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='supplier_notes')
    titulo = models.CharField(max_length=150)
    texto = models.TextField()
    importante = models.BooleanField(default=False)

class SupplierPrice(AuditMixin):
    org = models.ForeignKey(Organization, on_delete=models.CASCADE)
    supplier = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='prices')
    sku_proveedor = models.CharField(max_length=120)
    producto_sku_interno = models.CharField(max_length=120, blank=True)  # V2: migrar a FK inventory.Product
    precio = models.DecimalField(max_digits=12, decimal_places=4)
    moneda = models.CharField(max_length=10, default='EUR')
    min_qty = models.PositiveIntegerField(default=1)
    lead_time_dias = models.PositiveIntegerField(default=0)
    valido_desde = models.DateField()
    valido_hasta = models.DateField(null=True, blank=True)

    class Meta:
        unique_together = (('supplier','sku_proveedor','valido_desde'),)
        indexes = [
            models.Index(fields=['supplier','sku_proveedor','valido_desde']),
            models.Index(fields=['org']),
        ]

class SupplierCertification(AuditMixin):
    supplier = models.ForeignKey(Contact, on_delete=models.CASCADE, related_name='certifications')
    tipo = models.CharField(max_length=50)  # ISO9001, CE, etc.
    codigo = models.CharField(max_length=80, blank=True)
    fecha_emision = models.DateField(null=True, blank=True)
    fecha_caducidad = models.DateField(null=True, blank=True)
    adjunto = models.FileField(upload_to=supplier_cert_upload_to, null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=['supplier','tipo','fecha_caducidad'])]
