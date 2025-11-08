# sales/models.py
from decimal import Decimal
from django.db import models
from django.utils import timezone

from core.models import Organization
from inventory.models import Product, Warehouse
from contacts.models import Contact  # <-- ESTE es tu “cliente” base


class OrgScopedModel(models.Model):
    org = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="%(class)ss",
    )

    class Meta:
        abstract = True


class InvoiceSequence(OrgScopedModel):
    """
    Lleva el control de numeración por serie y año.
    Se usa desde services_numbering.next_invoice_number.
    """
    series = models.CharField(max_length=8, default="A")
    year = models.IntegerField()
    last_number = models.IntegerField(default=0)

    class Meta:
        unique_together = ("org", "series", "year")


class DeliveryNote(OrgScopedModel):
    number = models.CharField(max_length=32)  # usamos unique_together con org
    date = models.DateField(default=timezone.now)
    # Cliente: usamos contacts.Contact (filtraremos por tipo cliente en la vista/UI)
    customer = models.ForeignKey(Contact, on_delete=models.PROTECT)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    status = models.CharField(
        max_length=16,
        choices=(("draft", "Draft"), ("done", "Done")),
        default="draft",
    )

    class Meta:
        unique_together = ("org", "number")


class DeliveryNoteLine(models.Model):
    delivery_note = models.ForeignKey(
        DeliveryNote,
        on_delete=models.CASCADE,
        related_name="lines",
    )
    product = models.ForeignKey(
        Product,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
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


class Invoice(OrgScopedModel):
    series = models.CharField(max_length=8, default="A")
    number = models.IntegerField()
    date_issue = models.DateField(default=timezone.now)
    customer = models.ForeignKey(Contact, on_delete=models.PROTECT)
    billing_address = models.CharField(max_length=240, blank=True, default="")
    status = models.CharField(
        max_length=16,
        choices=(
            ("draft", "Draft"),
            ("posted", "Posted"),
            ("cancelled", "Cancelled"),
        ),
        default="draft",
    )
    payment_status = models.CharField(
        max_length=16,
        choices=(("unpaid", "Unpaid"), ("partial", "Partial"), ("paid", "Paid")),
        default="unpaid",
    )
    currency = models.CharField(max_length=3, default="EUR")
    totals_base = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    totals_tax = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    # --- Verifactu (PREPARADO, no operativo aún) ---
    verifactu_status = models.CharField(
        max_length=16,
        choices=(
            ("pending", "Pending"),
            ("sent", "Sent"),
            ("ack", "Ack"),
            ("error", "Error"),
        ),
        default="pending",
    )
    verifactu_hash = models.CharField(max_length=128, blank=True, default="")
    verifactu_sent_at = models.DateTimeField(null=True, blank=True)
    verifactu_ack_payload = models.TextField(blank=True, default="")
    verifactu_error = models.TextField(blank=True, default="")
    verifactu_qr_text = models.TextField(blank=True, default="")  # texto QR para PDF

    # TODO VERIFACTU: cuando vuelvas de la asesoría:
    # - decidir formato exacto de verifactu_hash/verifactu_qr_text
    # - implementar envío AEAT y logs.

    class Meta:
        unique_together = ("org", "series", "number")


class InvoiceLine(models.Model):
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name="lines",
    )
    product = models.ForeignKey(
        Product,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
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


class Payment(OrgScopedModel):
    METHOD = (("transfer", "Transfer"), ("card", "Card"), ("cash", "Cash"))
    invoice = models.ForeignKey(
        Invoice,
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

class Quote(OrgScopedModel):
    STATUS_CHOICES = (
        ("draft", "Draft"),
        ("sent", "Sent"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
        ("expired", "Expired"),
    )

    number = models.CharField(max_length=32)  # ej: Q-2025-0001
    date = models.DateField(default=timezone.now)
    valid_until = models.DateField(null=True, blank=True)
    customer = models.ForeignKey(Contact, on_delete=models.PROTECT)
    billing_address = models.CharField(max_length=240, blank=True, default="")
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="draft")
    currency = models.CharField(max_length=3, default="EUR")

    totals_base = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    totals_tax = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))

    # vínculo opcional a la factura generada
    invoice = models.ForeignKey(
        Invoice,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="from_quotes",
    )

    class Meta:
        unique_together = ("org", "number")

    def __str__(self):
        return f"{self.number} ({self.customer_id})"


class QuoteLine(models.Model):
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.PROTECT)
    description = models.CharField(max_length=240, blank=True, default="")
    qty = models.DecimalField(max_digits=16, decimal_places=3)
    uom = models.CharField(max_length=24, default="unidad")
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("21.00"))
    discount_pct = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))