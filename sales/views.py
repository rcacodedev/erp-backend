# sales/views.py
from decimal import Decimal
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from core.mixins import OrgScopedModelViewSet
from .models import DeliveryNote, Invoice, Payment, Quote
from .serializers import (
    DeliveryNoteSerializer,
    DeliveryNoteLineSerializer,
    InvoiceSerializer,
    InvoiceLineSerializer,
    PaymentSerializer, QuoteSerializer, QuoteLineSerializer
)
from inventory.models import Product
from .services_delivery import add_line as dn_add_line, confirm as dn_confirm
from .services_invoice import (
    add_line as inv_add_line,
    recompute_totals,
    post_invoice,
    replace_lines as inv_replace_lines,   # 👈 nuevo
)
from .services_payment import register_payment
from .services_quote import (
    add_line as quote_add_line,
    recompute_totals as quote_recompute,
    change_status as quote_change_status,
    convert_to_invoice as quote_convert_to_invoice,
    replace_lines as quote_replace_lines,
)


class DeliveryNoteViewSet(OrgScopedModelViewSet):
    serializer_class = DeliveryNoteSerializer
    queryset = DeliveryNote.objects.select_related("customer", "warehouse").prefetch_related("lines")

    @action(detail=True, methods=["post"])
    def add_line(self, request, pk=None, *args, **kwargs):
        dn = self.get_object()
        data = request.data

        product = None
        if data.get("product"):
            product = Product.objects.get(org=self.org, id=data["product"])

        line = dn_add_line(
            dn,
            product=product,
            description=data.get("description", ""),
            qty=Decimal(str(data["qty"])),
            uom=data.get("uom", product.uom if product else "unidad"),
            unit_price=Decimal(str(data.get("unit_price", "0.00"))),
            tax_rate=Decimal(str(data.get("tax_rate", "21.00"))),
            discount_pct=Decimal(str(data.get("discount_pct", "0.00"))),
        )
        return Response(DeliveryNoteLineSerializer(line).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None, *args, **kwargs):
        dn = self.get_object()
        dn = dn_confirm(dn, user=request.user)
        return Response(DeliveryNoteSerializer(dn).data, status=status.HTTP_200_OK)


class InvoiceViewSet(OrgScopedModelViewSet):
    serializer_class = InvoiceSerializer
    queryset = Invoice.objects.select_related("customer").prefetch_related("lines", "payments")

    @action(detail=True, methods=["post"])
    def add_line(self, request, pk=None, *args, **kwargs):
        inv = self.get_object()
        data = request.data

        product = None
        if data.get("product"):
            product = Product.objects.get(org=self.org, id=data["product"])

        line = inv_add_line(
            inv,
            product=product,
            description=data.get("description", ""),
            qty=Decimal(str(data["qty"])),
            uom=data.get("uom", product.uom if product else "unidad"),
            unit_price=Decimal(str(data.get("unit_price", "0.00"))),
            tax_rate=Decimal(str(data.get("tax_rate", "21.00"))),
            discount_pct=Decimal(str(data.get("discount_pct", "0.00"))),
        )
        # recalculamos totales en cada línea
        recompute_totals(inv)
        return Response(InvoiceLineSerializer(line).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def replace_lines(self, request, pk=None, *args, **kwargs):
        """
        Reemplaza todas las líneas de la factura (solo si no está contabilizada).
        Body igual que en Quote.replace_lines.
        """
        inv = self.get_object()
        raw_lines = request.data.get("lines", [])

        if not isinstance(raw_lines, list):
            raise ValidationError("El campo 'lines' debe ser una lista.")

        processed = []
        for ln in raw_lines:
            product_obj = None
            product_id = ln.get("product")
            if product_id:
                product_obj = Product.objects.get(org=self.org, id=product_id)

            qty = Decimal(str(ln.get("qty", 0)))
            unit_price = Decimal(str(ln.get("unit_price", "0.00")))
            tax_rate = Decimal(str(ln.get("tax_rate", "21.00")))
            discount_pct = Decimal(str(ln.get("discount_pct", "0.00")))
            uom = ln.get("uom") or (getattr(product_obj, "uom", "unidad") if product_obj else "unidad")

            processed.append(
                {
                    "product": product_obj,
                    "description": ln.get("description", ""),
                    "qty": qty,
                    "uom": uom,
                    "unit_price": unit_price,
                    "tax_rate": tax_rate,
                    "discount_pct": discount_pct,
                }
            )

        inv = inv_replace_lines(inv, lines=processed)
        return Response(InvoiceSerializer(inv).data, status=status.HTTP_200_OK)


    @action(detail=True, methods=["post"])
    def post(self, request, pk=None, *args, **kwargs):
        inv = self.get_object()
        inv = post_invoice(inv, series_default="A")
        return Response(InvoiceSerializer(inv).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def register_payment(self, request, pk=None, *args, **kwargs):
        inv = self.get_object()
        data = request.data
        pay = register_payment(
            inv,
            amount=Decimal(str(data["amount"])),
            date=data.get("date"),  # 'YYYY-MM-DD'
            method=data.get("method", "transfer"),
            notes=data.get("notes", ""),
        )
        return Response(PaymentSerializer(pay).data, status=status.HTTP_201_CREATED)


class PaymentViewSet(OrgScopedModelViewSet):
    serializer_class = PaymentSerializer
    queryset = Payment.objects.select_related("invoice")

class QuoteViewSet(OrgScopedModelViewSet):
    serializer_class = QuoteSerializer
    queryset = Quote.objects.select_related("customer").prefetch_related("lines")

    def perform_create(self, serializer):
        # Si el cliente no envía número, generamos uno automáticamente
        quote = serializer.save(org=self.org)
        if not quote.number:
            # Ejemplo super sencillo: Q-<año>-<id>
            from datetime import date
            today = date.today()
            quote.number = f"Q-{today.year}-{quote.id:05d}"
            quote.save(update_fields=["number"])

    @action(detail=True, methods=["post"])
    def add_line(self, request, pk=None, *args, **kwargs):
        quote = self.get_object()
        data = request.data

        product = None
        if data.get("product"):
            from inventory.models import Product
            product = Product.objects.get(org=self.org, id=data["product"])

        line = quote_add_line(
            quote,
            product=product,
            description=data.get("description", ""),
            qty=Decimal(str(data["qty"])),
            uom=data.get("uom", product.uom if product else "unidad"),
            unit_price=Decimal(str(data.get("unit_price", "0.00"))),
            tax_rate=Decimal(str(data.get("tax_rate", "21.00"))),
            discount_pct=Decimal(str(data.get("discount_pct", "0.00"))),
        )
        quote_recompute(quote)
        return Response(QuoteLineSerializer(line).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def replace_lines(self, request, pk=None, *args, **kwargs):
        """
        Reemplaza todas las líneas del presupuesto por las recibidas.

        Body esperado:
        {
          "lines": [
            {
              "product": 1 | null,
              "description": "texto",
              "qty": 3,
              "unit_price": 10.5,
              "tax_rate": 21,
              "uom": "unidad" | "kg" | ...,
              "discount_pct": 0
            },
            ...
          ]
        }
        """
        quote = self.get_object()
        raw_lines = request.data.get("lines", [])

        if not isinstance(raw_lines, list):
            raise ValidationError("El campo 'lines' debe ser una lista.")

        processed = []
        for ln in raw_lines:
            product_obj = None
            if ln.get("product"):
                product_obj = Product.objects.get(org=self.org, id=ln["product"])

            qty = Decimal(str(ln.get("qty", 0)))
            unit_price = Decimal(str(ln.get("unit_price", "0.00")))
            tax_rate = Decimal(str(ln.get("tax_rate", "21.00")))
            discount_pct = Decimal(str(ln.get("discount_pct", "0.00")))

            processed.append(
                {
                    "product": product_obj,
                    "description": ln.get("description", ""),
                    "qty": qty,
                    "uom": ln.get("uom") or (getattr(product_obj, "uom", "unidad") if product_obj else "unidad"),
                    "unit_price": unit_price,
                    "tax_rate": tax_rate,
                    "discount_pct": discount_pct,
                }
            )

        quote = quote_replace_lines(quote, lines=processed)
        return Response(QuoteSerializer(quote).data, status=status.HTTP_200_OK)


    @action(detail=True, methods=["post"])
    def mark_sent(self, request, pk=None, *args, **kwargs):
        quote = self.get_object()
        quote = quote_change_status(quote, "sent")
        return Response(QuoteSerializer(quote).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def mark_accepted(self, request, pk=None, *args, **kwargs):
        quote = self.get_object()
        quote = quote_change_status(quote, "accepted")
        return Response(QuoteSerializer(quote).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def mark_rejected(self, request, pk=None, *args, **kwargs):
        quote = self.get_object()
        quote = quote_change_status(quote, "rejected")
        return Response(QuoteSerializer(quote).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def replace_lines(self, request, pk=None, *args, **kwargs):
        """
        Reemplaza todas las líneas del presupuesto.
        Espera en body:
        {
          "lines": [
            {
              "product": 1 | null,
              "description": "...",
              "qty": 3,
              "uom": "kg" | "unidad" | ...,
              "unit_price": 10.5,
              "tax_rate": 21,
              "discount_pct": 0
            },
            ...
          ]
        }
        """
        quote = self.get_object()
        raw_lines = request.data.get("lines", [])

        if not isinstance(raw_lines, list):
            raise ValidationError("El campo 'lines' debe ser una lista.")

        processed = []
        for ln in raw_lines:
            product_obj = None
            product_id = ln.get("product")
            if product_id:
                product_obj = Product.objects.get(org=self.org, id=product_id)

            qty = Decimal(str(ln.get("qty", 0)))
            unit_price = Decimal(str(ln.get("unit_price", "0.00")))
            tax_rate = Decimal(str(ln.get("tax_rate", "21.00")))
            discount_pct = Decimal(str(ln.get("discount_pct", "0.00")))
            uom = ln.get("uom") or (getattr(product_obj, "uom", "unidad") if product_obj else "unidad")

            processed.append(
                {
                    "product": product_obj,
                    "description": ln.get("description", ""),
                    "qty": qty,
                    "uom": uom,
                    "unit_price": unit_price,
                    "tax_rate": tax_rate,
                    "discount_pct": discount_pct,
                }
            )

        quote = quote_replace_lines(quote, lines=processed)
        return Response(QuoteSerializer(quote).data, status=status.HTTP_200_OK)


    @action(detail=True, methods=["post"])
    def to_invoice(self, request, pk=None, *args, **kwargs):
        quote = self.get_object()
        inv = quote_convert_to_invoice(quote)
        # devolvemos la factura generada
        return Response(InvoiceSerializer(inv).data, status=status.HTTP_201_CREATED)
