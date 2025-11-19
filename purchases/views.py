# purchases/views.py
from decimal import Decimal

from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from core.mixins import OrgScopedModelViewSet
from inventory.models import Product
from inventory.models import StockMove
from .models import (
    PurchaseOrder,
    PurchaseOrderLine,
    SupplierInvoice,
    SupplierInvoiceLine,
    SupplierPayment,
)
from .serializers import (
    PurchaseOrderSerializer,
    PurchaseOrderLineSerializer,
    SupplierInvoiceSerializer,
    SupplierInvoiceLineSerializer,
    SupplierPaymentSerializer,
)
from .permissions import CanManagePurchases
from analytics.hooks import (
    register_supplier_invoice_posted,
    register_supplier_payment_created,
    register_supplier_payment_deleted,
)



# --------- HELPERS COMUNES ---------

def _calc_line_amounts(qty, unit_price, tax_rate, discount_pct):
    """
    Devuelve (base, tax, total) con dos decimales.
    """
    qty = Decimal(str(qty))
    unit_price = Decimal(str(unit_price))
    tax_rate = Decimal(str(tax_rate))
    discount_pct = Decimal(str(discount_pct))

    if qty <= 0:
        base = Decimal("0.00")
    else:
        base = qty * unit_price * (Decimal("1") - (discount_pct / Decimal("100")))
    base = base.quantize(Decimal("0.01"))
    tax = (base * tax_rate / Decimal("100")).quantize(Decimal("0.01"))
    total = base + tax
    return base, tax, total


def _recalc_order_totals(order: PurchaseOrder):
    base = Decimal("0.00")
    tax = Decimal("0.00")
    for ln in order.lines.all():
        base += ln.line_base
        tax += ln.line_tax
    order.total_base = base
    order.total_tax = tax
    order.total = base + tax
    order.save(update_fields=["total_base", "total_tax", "total"])


def _recalc_invoice_totals(inv: SupplierInvoice):
    base = Decimal("0.00")
    tax = Decimal("0.00")
    for ln in inv.lines.all():
        base += ln.line_base
        tax += ln.line_tax
    inv.total_base = base
    inv.total_tax = tax
    inv.total = base + tax
    inv.save(update_fields=["total_base", "total_tax", "total"])


def _recalc_payment_status(inv: SupplierInvoice):
    total_paid = sum(p.amount for p in inv.payments.all())
    total = inv.total

    if total <= 0:
        status = "unpaid"
    elif total_paid <= Decimal("0.00"):
        status = "unpaid"
    elif total_paid + Decimal("0.01") < total:
        status = "partial"
    else:
        status = "paid"

    inv.payment_status = status
    inv.save(update_fields=["payment_status"])


def _create_stock_moves_for_invoice(inv: SupplierInvoice, user):
    """
    Crea movimientos de stock de tipo 'purchase' para cada línea de producto
    al contabilizar la factura. Idempotente respecto al estado: solo se llama
    al pasar de draft -> posted.
    """
    for ln in inv.lines.all():
        if not ln.product or ln.qty <= 0:
            continue

        StockMove.objects.create(
            org=inv.org,
            product=ln.product,
            qty=ln.qty,  # positivo (entra stock)
            uom=ln.uom,
            warehouse_from=None,
            warehouse_to=inv.warehouse,
            reason="purchase",
            ref_type="supplier_invoice",
            ref_id=str(inv.id),
            created_by=user,
        )


# --------- VIEWSETS ---------

class PurchaseOrderViewSet(OrgScopedModelViewSet):
    """
    CRUD de pedidos a proveedor + acciones rápidas (send, receive, add_line).
    Escritura restringida a owner/admin/manager vía CanManagePurchases.
    """
    serializer_class = PurchaseOrderSerializer
    queryset = PurchaseOrder.objects.select_related(
        "supplier",
        "warehouse",
    ).prefetch_related("lines", "lines__product")
    permission_classes = (IsAuthenticated,)

    def get_permissions(self):
        base = list(super().get_permissions())
        if self.request.method in ("POST", "PUT", "PATCH", "DELETE"):
            base.append(CanManagePurchases())
        return base

    def get_queryset(self):
        return super().get_queryset()

    @action(detail=True, methods=["post"])
    def add_line(self, request, pk=None, *args, **kwargs):
        order = self.get_object()
        data = request.data

        product_obj = None
        product_id = data.get("product")
        if product_id:
            product_obj = get_object_or_404(Product, org=self.org, id=product_id)

        qty = data.get("qty", 0)
        unit_price = data.get("unit_price", "0.00")
        tax_rate = data.get("tax_rate", "21.00")
        discount_pct = data.get("discount_pct", "0.00")

        base, tax, total = _calc_line_amounts(qty, unit_price, tax_rate, discount_pct)

        line = PurchaseOrderLine.objects.create(
            order=order,
            product=product_obj,
            description=data.get("description", "") or (
                product_obj.name if product_obj else ""
            ),
            qty=qty,
            uom=data.get("uom", "unidad"),
            unit_price=unit_price,
            tax_rate=tax_rate,
            discount_pct=discount_pct,
            line_base=base,
            line_tax=tax,
            line_total=total,
        )

        _recalc_order_totals(order)

        ser = PurchaseOrderLineSerializer(line)
        return Response(ser.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def send(self, request, pk=None, *args, **kwargs):
        """
        Marcar pedido como 'sent'.
        """
        order = self.get_object()
        if order.status not in ("draft",):
            raise ValidationError("Solo se puede enviar un pedido en estado 'draft'.")
        order.status = "sent"
        order.save(update_fields=["status"])
        return Response({"status": order.status})

    @action(detail=True, methods=["post"])
    def receive(self, request, pk=None, *args, **kwargs):
        """
        Marcar pedido como 'received'. (De momento solo cambia estado;
        el stock real lo disparamos al contabilizar la factura de proveedor).
        """
        order = self.get_object()
        if order.status not in ("draft", "sent", "partially_received"):
            raise ValidationError("No se puede recibir un pedido en este estado.")
        order.status = "received"
        order.save(update_fields=["status"])
        return Response({"status": order.status})


class SupplierInvoiceViewSet(OrgScopedModelViewSet):
    """
    Facturas de proveedor. Incluye:
    - add_line: añadir líneas
    - post: contabilizar (calcula totales + crea StockMoves)
    - cancel: marcar cancelada
    Escritura restringida a owner/admin/manager.
    """
    serializer_class = SupplierInvoiceSerializer
    queryset = SupplierInvoice.objects.select_related(
        "supplier",
        "warehouse",
        "purchase_order",
    ).prefetch_related("lines", "lines__product", "payments")
    permission_classes = (IsAuthenticated,)

    def get_permissions(self):
        base = list(super().get_permissions())
        if self.request.method in ("POST", "PUT", "PATCH", "DELETE"):
            base.append(CanManagePurchases())
        return base

    def get_queryset(self):
        return super().get_queryset()

    @action(detail=True, methods=["post"])
    def add_line(self, request, pk=None, *args, **kwargs):
        inv = self.get_object()
        data = request.data

        if inv.status != "draft":
            raise ValidationError("Solo se pueden añadir líneas en estado 'draft'.")

        product_obj = None
        product_id = data.get("product")
        if product_id:
            product_obj = get_object_or_404(Product, org=self.org, id=product_id)

        qty = data.get("qty", 0)
        unit_price = data.get("unit_price", "0.00")
        tax_rate = data.get("tax_rate", "21.00")
        discount_pct = data.get("discount_pct", "0.00")

        base, tax, total = _calc_line_amounts(qty, unit_price, tax_rate, discount_pct)

        line = SupplierInvoiceLine.objects.create(
            invoice=inv,
            product=product_obj,
            description=data.get("description", "") or (
                product_obj.name if product_obj else ""
            ),
            qty=qty,
            uom=data.get("uom", "unidad"),
            unit_price=unit_price,
            tax_rate=tax_rate,
            discount_pct=discount_pct,
            line_base=base,
            line_tax=tax,
            line_total=total,
        )

        _recalc_invoice_totals(inv)

        ser = SupplierInvoiceLineSerializer(line)
        return Response(ser.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def post(self, request, pk=None, *args, **kwargs):
        """
        Contabiliza la factura:
        - recalcula totales
        - cambia estado a 'posted'
        - crea movimientos de stock de compra
        """
        inv = self.get_object()
        if inv.status == "posted":
            raise ValidationError("La factura ya está contabilizada.")
        if inv.status == "cancelled":
            raise ValidationError("No se puede contabilizar una factura cancelada.")

        if inv.lines.count() == 0:
            raise ValidationError("No se puede contabilizar una factura sin líneas.")

        _recalc_invoice_totals(inv)
        inv.status = "posted"
        inv.save(update_fields=["status", "total_base", "total_tax", "total"])

        _create_stock_moves_for_invoice(inv, request.user)

        # 🔹 gancho a analítica
        register_supplier_invoice_posted(inv)

        ser = SupplierInvoiceSerializer(inv, context={"request": request})
        return Response(ser.data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None, *args, **kwargs):
        inv = self.get_object()
        if inv.status == "cancelled":
            raise ValidationError("La factura ya está cancelada.")
        if inv.status == "posted":
            # Si más adelante quieres, aquí podríamos revertir stock.
            raise ValidationError(
                "No se puede cancelar una factura ya contabilizada (posted)."
            )
        inv.status = "cancelled"
        inv.save(update_fields=["status"])
        return Response({"status": inv.status})


class SupplierPaymentViewSet(OrgScopedModelViewSet):
    """
    CRUD de pagos a proveedor. Cada alta/edición/borrado recalcula
    payment_status en la factura asociada. No se permite pagar por encima
    del importe pendiente.
    """
    serializer_class = SupplierPaymentSerializer
    queryset = SupplierPayment.objects.select_related("invoice", "invoice__supplier")
    permission_classes = (IsAuthenticated,)

    def get_permissions(self):
        base = list(super().get_permissions())
        if self.request.method in ("POST", "PUT", "PATCH", "DELETE"):
            base.append(CanManagePurchases())
        return base

    def get_queryset(self):
        return super().get_queryset()

    def perform_create(self, serializer):
        data = serializer.validated_data
        invoice = data["invoice"]
        amount = data["amount"]

        total_paid_before = sum(p.amount for p in invoice.payments.all())
        total = invoice.total or Decimal("0.00")

        if total <= 0:
            raise ValidationError("No se puede registrar un pago para una factura sin total.")

        if total_paid_before + amount - total > Decimal("0.01"):
            raise ValidationError("El pago supera el importe pendiente de la factura.")

        payment = serializer.save(org=self.org)
        _recalc_payment_status(payment.invoice)

        # 💚 HOOK ANALYTICS
        register_supplier_payment_created(payment)

    def perform_update(self, serializer):
        data = serializer.validated_data
        invoice = data.get("invoice") or serializer.instance.invoice
        amount = data.get("amount", serializer.instance.amount)

        # Pagos de esa factura sin contar este (lo recalculamos como si fuese nuevo)
        total_paid_others = sum(
            p.amount for p in invoice.payments.exclude(id=serializer.instance.id)
        )
        total = invoice.total or Decimal("0.00")

        if total <= 0:
            raise ValidationError("No se puede registrar un pago para una factura sin total.")

        if total_paid_others + amount - total > Decimal("0.01"):
            raise ValidationError("El pago supera el importe pendiente de la factura.")

        payment = serializer.save(org=self.org)
        _recalc_payment_status(payment.invoice)



    def perform_destroy(self, instance):
        inv = instance.invoice
        super().perform_destroy(instance)
        _recalc_payment_status(inv)
        # 💚 HOOK ANALYTICS
        register_supplier_payment_deleted(instance)
