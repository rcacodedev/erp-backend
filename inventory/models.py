from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils import timezone

from core.models import Organization  # ajusta import si tu core difiere

class OrgScopedModel(models.Model):
    org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="%(class)ss")
    class Meta:
        abstract = True

class Category(OrgScopedModel):
    name = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("org", "name")
        ordering = ["name"]

    def __str__(self):
        return self.name

class Product(OrgScopedModel):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    sku = models.CharField(max_length=64)
    name = models.CharField(max_length=200)
    uom = models.CharField(max_length=24, default="unidad")
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("21.00"))
    price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    cost_price = models.DecimalField(  # New field for cost price
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Cost price of the product"
    )
    is_service = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("org", "sku")
        indexes = [models.Index(fields=["org", "name"]), models.Index(fields=["org", "sku"])]
        ordering = ["name"]

    def __str__(self):
        return f"{self.sku} · {self.name}"

class Warehouse(OrgScopedModel):
    code = models.CharField(max_length=32)
    name = models.CharField(max_length=120)
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("org", "code")
        ordering = ["name"]

    def __str__(self):
        return f"{self.code} · {self.name}"

WORKSITE_TYPES = (
    ("office", "Office"),
    ("workshop", "Workshop"),
    ("store", "Store"),
    ("remote", "Remote"),
)

class Worksite(OrgScopedModel):
    code = models.CharField(max_length=32)
    name = models.CharField(max_length=120)
    type = models.CharField(max_length=16, choices=WORKSITE_TYPES, default="office")
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("org", "code")
        ordering = ["name"]

    def __str__(self):
        return f"{self.code} · {self.name}"

class InventoryItem(OrgScopedModel):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="inventory_items")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name="inventory_items")
    qty_on_hand = models.DecimalField(max_digits=16, decimal_places=3, default=Decimal("0.000"))
    qty_reserved = models.DecimalField(max_digits=16, decimal_places=3, default=Decimal("0.000"))

    class Meta:
        unique_together = ("org", "product", "warehouse")

class StockMove(OrgScopedModel):
    REASONS = (
        ("purchase", "Purchase"),
        ("sale", "Sale"),
        ("transfer", "Transfer"),
        ("adjustment", "Adjustment"),
        ("return", "Return"),
    )
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="stock_moves")
    qty = models.DecimalField(max_digits=16, decimal_places=3)  # signed (+/-)
    uom = models.CharField(max_length=24, default="unidad")
    warehouse_from = models.ForeignKey(Warehouse, null=True, blank=True, on_delete=models.PROTECT, related_name="moves_out")
    warehouse_to = models.ForeignKey(Warehouse, null=True, blank=True, on_delete=models.PROTECT, related_name="moves_in")
    reason = models.CharField(max_length=16, choices=REASONS)
    ref_type = models.CharField(max_length=64, blank=True, default="")
    ref_id = models.CharField(max_length=64, blank=True, default="")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]
