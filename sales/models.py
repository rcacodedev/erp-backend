# sales/models.py
from decimal import Decimal
from django.db import models
from django.utils import timezone
from core.models import Organization
from inventory.models import Product, Warehouse

class OrgScopedModel(models.Model):
    org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="%(class)ss")
    class Meta:
        abstract = True

class Customer(models.Model):
    """Si ya tienes cliente en contacts, ajusta: usa FK a ese modelo y elimina esto."""
    name = models.CharField(max_length=200)
    # placeholder: sustituir por FK real

class DeliveryNote(OrgScopedModel):
    number = models.CharField(max_length=32, unique=True)
    date = models.DateField(default=timezone.now)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    status = models.CharField(max_length=16, choices=(("draft","Draft"),("done","Done")), default="draft")

class DeliveryNoteLine(models.Model):
    delivery_note = models.ForeignKey(DeliveryNote, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.PROTECT)
    description = models.CharField(max_length=240, blank=True, default="")
    qty = models.DecimalField(max_digits=16, decimal_places=3)
    uom = models.CharField(max_length=24, default="unidad")
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("21.00"))
    discount_pct = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))

class Invoice(OrgScopedModel):
    series = models.CharField(max_length=8, default="A")
    number = models.IntegerField()
    date_issue = models.DateField(default=timezone.now)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT)
    billing_address = models.CharField(max_length=240, blank=True, default="")
    status = models.CharField(max_length=16, choices=(("draft","Draft"),("posted","Posted"),("cancelled","Cancelled")), default="draft")
    payment_status = models.CharField(max_length=16, choices=(("unpaid","Unpaid"),("partial","Partial"),("paid","Paid")), default="unpaid")
    currency = models.CharField(max_length=3, default="EUR")
    totals_base = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    totals_tax = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))

    verifactu_status = models.CharField(max_length=16, choices=(("pending","Pending"),("sent","Sent"),("ack","Ack"),("error","Error")), default="pending")
    verifactu_hash = models.CharField(max_length=128, blank=True, default="")
    verifactu_sent_at = models.DateTimeField(null=True, blank=True)
    verifactu_ack_payload = models.TextField(blank=True, default="")
    verifactu_error = models.TextField(blank=True, default="")

    class Meta:
        unique_together = ("org", "series", "number")

class InvoiceLine(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(Product, null=True, blank=True, on_delete=models.PROTECT)
    description = models.CharField(max_length=240, blank=True, default="")
    qty = models.DecimalField(max_digits=16, decimal_places=3)
    uom = models.CharField(max_length=24, default="unidad")
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("21.00"))
    discount_pct = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))

class Payment(models.Model):
    METHOD = (("transfer","Transfer"),("card","Card"),("cash","Cash"))
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    date = models.DateField(default=timezone.now)
    method = models.CharField(max_length=16, choices=METHOD, default="transfer")
    notes = models.CharField(max_length=240, blank=True, default="")
