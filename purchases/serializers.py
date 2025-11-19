# purchases/serializers.py
from rest_framework import serializers

from contacts.models import Contact
from contacts.choices import ContactType
from inventory.models import Product, Warehouse
from .models import (
    PurchaseOrder,
    PurchaseOrderLine,
    SupplierInvoice,
    SupplierInvoiceLine,
    SupplierPayment,
)


class ContactMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ["id", "razon_social", "nombre", "apellidos"]


class WarehouseMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ["id", "code", "name"]


# ---------- PEDIDOS A PROVEEDOR ----------

class PurchaseOrderLineSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = PurchaseOrderLine
        fields = [
            "id",
            "product",
            "product_name",
            "description",
            "qty",
            "uom",
            "unit_price",
            "tax_rate",
            "discount_pct",
            "line_base",
            "line_tax",
            "line_total",
        ]
        read_only_fields = ["line_base", "line_tax", "line_total"]


class PurchaseOrderSerializer(serializers.ModelSerializer):
    supplier_detail = ContactMiniSerializer(source="supplier", read_only=True)
    warehouse_detail = WarehouseMiniSerializer(source="warehouse", read_only=True)
    lines = PurchaseOrderLineSerializer(many=True, read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = [
            "id",
            "number",
            "date",
            "expected_date",
            "supplier",
            "supplier_detail",
            "warehouse",
            "warehouse_detail",
            "currency",
            "status",
            "total_base",
            "total_tax",
            "total",
            "notes_internal",
            "notes_supplier",
            "lines",
        ]

    def validate_supplier(self, supplier: Contact):
        org = self.context.get("org")
        if supplier.org_id != getattr(org, "id", None):
            raise serializers.ValidationError("El proveedor debe pertenecer a esta organización.")
        if supplier.tipo != ContactType.SUPPLIER:
            raise serializers.ValidationError("El contacto debe ser de tipo proveedor.")
        return supplier


# ---------- FACTURAS PROVEEDOR ----------

class SupplierInvoiceLineSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = SupplierInvoiceLine
        fields = [
            "id",
            "product",
            "product_name",
            "description",
            "qty",
            "uom",
            "unit_price",
            "tax_rate",
            "discount_pct",
            "line_base",
            "line_tax",
            "line_total",
        ]
        read_only_fields = ["line_base", "line_tax", "line_total"]


class SupplierInvoiceSerializer(serializers.ModelSerializer):
    supplier_detail = ContactMiniSerializer(source="supplier", read_only=True)
    warehouse_detail = WarehouseMiniSerializer(source="warehouse", read_only=True)
    lines = SupplierInvoiceLineSerializer(many=True, read_only=True)

    class Meta:
        model = SupplierInvoice
        fields = [
            "id",
            "number",
            "supplier_invoice_number",
            "date",
            "due_date",
            "supplier",
            "supplier_detail",
            "warehouse",
            "warehouse_detail",
            "currency",
            "status",
            "payment_status",
            "purchase_order",
            "total_base",
            "total_tax",
            "total",
            "notes",
            "lines",
        ]
        read_only_fields = ["status", "payment_status", "total_base", "total_tax", "total"]

    def validate_supplier(self, supplier: Contact):
        org = self.context.get("org")
        if supplier.org_id != getattr(org, "id", None):
            raise serializers.ValidationError("El proveedor debe pertenecer a esta organización.")
        if supplier.tipo != ContactType.SUPPLIER:
            raise serializers.ValidationError("El contacto debe ser de tipo proveedor.")
        return supplier


# ---------- PAGOS A PROVEEDOR ----------

class SupplierPaymentSerializer(serializers.ModelSerializer):
    invoice_detail = SupplierInvoiceSerializer(source="invoice", read_only=True)

    class Meta:
        model = SupplierPayment
        fields = [
            "id",
            "invoice",
            "invoice_detail",
            "amount",
            "date",
            "method",
            "notes",
        ]
