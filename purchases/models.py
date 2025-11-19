# purchases/models.py
from decimal import Decimal

from django.db import models
from django.utils import timezone

from core.models import Organization
from contacts.models import Contact
from inventory.models import Product, Warehouse


class OrgScopedModel(models.Model):
    """
    Igual patrón que en inventory/analytics/sales:
    todos los modelos de compras cuelgan de una Organization.
    """
    org = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="%(class)ss",
    )

    class Meta:
        abstract = True


class PurchaseOrder(OrgScopedModel):
    """
    Pedido a proveedor (no necesariamente vinculante, pero útil
    para planificar compras y futuras recepciones).
    """
    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("sent", "Sent"),
        ("partially_received", "Partially received"),
        ("received", "Received"),
        ("cancelled", "Cancelled"),
    )

    number = models.CharField(
        max_length=32,
        help_text="Identificador interno del pedido (ej: PO-2025-0001)",
    )
    date = models.DateField(default=timezone.now)
    expected_date = models.DateField(null=True, blank=True)

    supplier = models.ForeignKey(
        Contact,
        on_delete=models.PROTECT,
        related_name="purchase_orders",
        help_text="Debe ser un contacto de tipo proveedor (se filtrará en la UI/API).",
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name="purchase_orders",
    )

    currency = models.CharField(max_length=3, default="EUR")

    status = models.CharField(
        max_length=24,
        choices=STATUS_CHOICES,
        default="draft",
    )

    total_base = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    total_tax = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    notes_internal = models.TextField(blank=True, default="")
    notes_supplier = models.TextField(blank=True, default="")

    class Meta:
        unique_together = ("org", "number")
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"PO {self.number} ({self.supplier_id})"


class PurchaseOrderLine(models.Model):
    """
    Líneas de pedido. No necesitan org porque van colgadas del pedido.
    """
    order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name="lines",
    )
    product = models.ForeignKey(
        Product,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="purchase_order_lines",
    )
    description = models.CharField(max_length=240, blank=True, default="")
    qty = models.DecimalField(max_digits=16, decimal_places=3)
    uom = models.CharField(max_length=24, default="unidad")
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("21.00"),
    )
    discount_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    line_base = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    line_tax = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    line_total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    def __str__(self):
        return f"{self.order_id} · {self.description or self.product_id}"


class SupplierInvoice(OrgScopedModel):
    """
    Factura de proveedor: es la pieza clave para stock y gastos.
    """
    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("posted", "Posted"),
        ("cancelled", "Cancelled"),
    )
    PAYMENT_STATUS_CHOICES = (
        ("unpaid", "Unpaid"),
        ("partial", "Partial"),
        ("paid", "Paid"),
    )

    # Número interno nuestro (similar a DeliveryNote/Quote)
    number = models.CharField(max_length=32)
    # Número que trae la factura del proveedor (opcional)
    supplier_invoice_number = models.CharField(
        max_length=64,
        blank=True,
        default="",
        help_text="Número tal cual aparece en la factura del proveedor.",
    )

    date = models.DateField(default=timezone.now)
    due_date = models.DateField(null=True, blank=True)

    supplier = models.ForeignKey(
        Contact,
        on_delete=models.PROTECT,
        related_name="supplier_invoices",
    )
    warehouse = models.ForeignKey(
        Warehouse,
        on_delete=models.PROTECT,
        related_name="supplier_invoices",
    )

    currency = models.CharField(max_length=3, default="EUR")

    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default="draft",
    )
    payment_status = models.CharField(
        max_length=16,
        choices=PAYMENT_STATUS_CHOICES,
        default="unpaid",
    )

    purchase_order = models.ForeignKey(
        PurchaseOrder,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="invoices",
        help_text="Opcional: si la factura viene de un pedido.",
    )

    total_base = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    total_tax = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    notes = models.TextField(blank=True, default="")

    class Meta:
        unique_together = ("org", "number")
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"SI {self.number} ({self.supplier_id})"


class SupplierInvoiceLine(models.Model):
    """
    Línea de factura de proveedor.
    """
    invoice = models.ForeignKey(
        SupplierInvoice,
        on_delete=models.CASCADE,
        related_name="lines",
    )
    product = models.ForeignKey(
        Product,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="supplier_invoice_lines",
    )
    description = models.CharField(max_length=240, blank=True, default="")
    qty = models.DecimalField(max_digits=16, decimal_places=3)
    uom = models.CharField(max_length=24, default="unidad")
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("21.00"),
    )
    discount_pct = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    line_base = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    line_tax = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    line_total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    def __str__(self):
        return f"{self.invoice_id} · {self.description or self.product_id}"


class SupplierPayment(OrgScopedModel):
    """
    Pagos a proveedor por factura (como sales.Payment pero para compras).
    """
    METHOD = (
        ("transfer", "Transfer"),
        ("card", "Card"),
        ("cash", "Cash"),
    )

    invoice = models.ForeignKey(
        SupplierInvoice,
        on_delete=models.CASCADE,
        related_name="payments",
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    date = models.DateField(default=timezone.now)
    method = models.CharField(
        max_length=16,
        choices=METHOD,
        default="transfer",
    )
    notes = models.CharField(max_length=240, blank=True, default="")

    class Meta:
        ordering = ["-date", "-id"]

    def __str__(self):
        return f"Payment {self.amount} → {self.invoice_id}"
