# sales/views.py
from decimal import Decimal

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

from core.mixins import OrgScopedModelViewSet
from .models import DeliveryNote, Invoice, Payment
from .serializers import (
    DeliveryNoteSerializer,
    DeliveryNoteLineSerializer,
    InvoiceSerializer,
    InvoiceLineSerializer,
    PaymentSerializer,
)
from inventory.models import Product
from .services_delivery import add_line as dn_add_line, confirm as dn_confirm
from .services_invoice import add_line as inv_add_line, recompute_totals, post_invoice
from .services_payment import register_payment


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
