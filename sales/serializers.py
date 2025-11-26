# sales/serializers.py
from rest_framework import serializers
from .models import DeliveryNote, DeliveryNoteLine, Invoice, InvoiceLine, Payment, Quote, QuoteLine
from contacts.models import Contact


class ContactMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ["id", "razon_social", "nombre", "apellidos"]



class DeliveryNoteLineSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = DeliveryNoteLine
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
        ]


class DeliveryNoteSerializer(serializers.ModelSerializer):
    customer_detail = ContactMiniSerializer(source="customer", read_only=True)
    lines = DeliveryNoteLineSerializer(many=True, read_only=True)

    class Meta:
        model = DeliveryNote
        fields = [
            "id",
            "number",
            "date",
            "customer",
            "customer_detail",
            "warehouse",
            "status",
            "lines",
        ]
        extra_kwargs = {
            "number": {
                "required": False,
                "allow_blank": True,
                "allow_null": True,
            }
        }


class InvoiceLineSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = InvoiceLine
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
        ]


class InvoiceSerializer(serializers.ModelSerializer):
    customer_detail = ContactMiniSerializer(source="customer", read_only=True)
    lines = InvoiceLineSerializer(many=True, read_only=True)

    class Meta:
        model = Invoice
        fields = [
            "id",
            "series",
            "number",
            "date_issue",
            "customer",
            "customer_detail",
            "billing_address",
            "status",
            "payment_status",
            "currency",
            "totals_base",
            "totals_tax",
            "total",
            "verifactu_status",
            "verifactu_hash",
            "verifactu_sent_at",
            "verifactu_qr_text",
            "lines",
        ]
        extra_kwargs = {
            "number": {
                "required": False,
                "allow_null": True,
            }
        }


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "invoice", "amount", "date", "method", "notes"]

class QuoteLineSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)

    class Meta:
        model = QuoteLine
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
        ]


class QuoteSerializer(serializers.ModelSerializer):
    customer_detail = ContactMiniSerializer(source="customer", read_only=True)
    lines = QuoteLineSerializer(many=True, read_only=True)
    invoice_id = serializers.IntegerField(source="invoice.id", read_only=True)

    class Meta:
        model = Quote
        fields = [
            "id",
            "number",
            "date",
            "valid_until",
            "customer",
            "customer_detail",
            "billing_address",
            "status",
            "currency",
            "totals_base",
            "totals_tax",
            "total",
            "invoice_id",
            "lines",
        ]
        extra_kwargs = {
            "number": {
                "required": False,
                "allow_blank": True,
                "allow_null": True,
            }
        }