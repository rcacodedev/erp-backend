# sales/services_quote.py
from decimal import Decimal
from django.db import transaction
from rest_framework.exceptions import ValidationError

from .models import Quote, QuoteLine, Invoice, InvoiceLine
from .pricing import compute_invoice_totals


@transaction.atomic
def add_line(
    quote: Quote,
    *,
    product,
    description: str,
    qty: Decimal,
    uom: str,
    unit_price,
    tax_rate,
    discount_pct=0,
):
    if quote.status not in ("draft", "sent"):
        raise ValidationError("Solo se pueden modificar presupuestos en borrador o enviados")

    return QuoteLine.objects.create(
        quote=quote,
        product=product,
        description=description or (product.name if product else ""),
        qty=qty,
        uom=uom,
        unit_price=unit_price,
        tax_rate=tax_rate,
        discount_pct=discount_pct,
    )

@transaction.atomic
def replace_lines(quote: Quote, *, lines: list[dict]):
    """
    Reemplaza TODAS las líneas de un presupuesto por las indicadas en `lines`.

    Cada elemento de `lines` debe ser un dict con las claves compatibles con
    add_line(...): product, description, qty, uom, unit_price, tax_rate, discount_pct.
    """
    if quote.status not in ("draft", "sent"):
        raise ValidationError("Solo se pueden modificar presupuestos en borrador o enviados")

    # Borramos las líneas actuales
    QuoteLine.objects.filter(quote=quote).delete()

    # Volvemos a crearlas usando el servicio add_line (valida estados, etc.)
    for ln in lines:
        add_line(
            quote,
            product=ln.get("product"),
            description=ln.get("description", ""),
            qty=ln.get("qty", Decimal("0")),
            uom=ln.get("uom", "unidad"),
            unit_price=ln.get("unit_price", Decimal("0.00")),
            tax_rate=ln.get("tax_rate", Decimal("21.00")),
            discount_pct=ln.get("discount_pct", Decimal("0.00")),
        )

    # Recalcular totales del presupuesto
    recompute_totals(quote)
    return quote


@transaction.atomic
def recompute_totals(quote: Quote):
    lines = quote.lines.all().values("qty", "unit_price", "discount_pct", "tax_rate")
    total_base, total_tax, total = compute_invoice_totals(lines)
    quote.totals_base = total_base
    quote.totals_tax = total_tax
    quote.total = total
    quote.save(update_fields=["totals_base", "totals_tax", "total"])
    return quote


@transaction.atomic
def change_status(quote: Quote, new_status: str):
    valid = {"draft", "sent", "accepted", "rejected", "expired"}
    if new_status not in valid:
        raise ValidationError("Estado de presupuesto no válido")
    quote.status = new_status
    quote.save(update_fields=["status"])
    return quote


@transaction.atomic
def convert_to_invoice(quote: Quote):
    """
    Crea una Invoice a partir del presupuesto aceptado.
    No toca stock ni Verifactu; solo crea la estructura base.
    """
    if quote.status != "accepted":
        raise ValidationError("Solo se pueden convertir presupuestos aceptados")

    if quote.invoice_id:
        # ya convertido antes
        return quote.invoice

    inv = Invoice.objects.create(
        org=quote.org,
        series="A",          # se reenumerará en post_invoice
        date_issue=quote.date,
        customer=quote.customer,
        billing_address=quote.billing_address,
        status="draft",
        payment_status="unpaid",
        currency=quote.currency,
    )

    for ln in quote.lines.all():
        InvoiceLine.objects.create(
            invoice=inv,
            product=ln.product,
            description=ln.description,
            qty=ln.qty,
            uom=ln.uom,
            unit_price=ln.unit_price,
            tax_rate=ln.tax_rate,
            discount_pct=ln.discount_pct,
        )

    # recalculamos totales de la factura
    # (usando el servicio de invoice)
    from .services_invoice import recompute_totals as invoice_recompute

    invoice_recompute(inv)

    quote.invoice = inv
    quote.save(update_fields=["invoice"])

    return inv

@transaction.atomic
def replace_lines(quote: Quote, *, lines: list[dict]):
    """
    Reemplaza TODAS las líneas de un presupuesto por las indicadas en `lines`.

    Cada elemento de `lines` debe ser un dict con:
      product (objeto Product o None)
      description, qty, uom, unit_price, tax_rate, discount_pct
    """
    if quote.status not in ("draft", "sent"):
        raise ValidationError("Solo se pueden modificar presupuestos en borrador o enviados.")

    # Borramos las líneas actuales
    QuoteLine.objects.filter(quote=quote).delete()

    # Creamos las nuevas
    for ln in lines:
        QuoteLine.objects.create(
            quote=quote,
            product=ln.get("product"),
            description=ln.get("description", ""),
            qty=ln.get("qty", Decimal("0")),
            uom=ln.get("uom", "unidad"),
            unit_price=ln.get("unit_price", Decimal("0.00")),
            tax_rate=ln.get("tax_rate", Decimal("21.00")),
            discount_pct=ln.get("discount_pct", Decimal("0.00")),
        )

    recompute_totals(quote)
    return quote
