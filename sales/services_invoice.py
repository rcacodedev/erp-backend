# sales/services_invoice.py
from decimal import Decimal
from django.db import transaction
from rest_framework.exceptions import ValidationError

from .models import Invoice, InvoiceLine
from .services_numbering import next_invoice_number
from .pricing import compute_invoice_totals


@transaction.atomic
def add_line(
    inv: Invoice,
    *,
    product,
    description: str,
    qty: Decimal,
    uom: str,
    unit_price,
    tax_rate,
    discount_pct=0,
):
    if inv.status != "draft":
        raise ValidationError("La factura no está en borrador")
    return InvoiceLine.objects.create(
        invoice=inv,
        product=product,
        description=description or (product.name if product else ""),
        qty=qty,
        uom=uom,
        unit_price=unit_price,
        tax_rate=tax_rate,
        discount_pct=discount_pct,
    )


@transaction.atomic
def recompute_totals(inv: Invoice):
    lines = inv.lines.all().values("qty", "unit_price", "discount_pct", "tax_rate")
    total_base, total_tax, total = compute_invoice_totals(lines)
    inv.totals_base = total_base
    inv.totals_tax = total_tax
    inv.total = total
    inv.save(update_fields=["totals_base", "totals_tax", "total"])
    return inv


@transaction.atomic
def post_invoice(inv: Invoice, *, series_default="A"):
    if inv.status != "draft":
        raise ValidationError("La factura no está en borrador")

    series = inv.series or series_default
    year, number = next_invoice_number(inv.org, series)

    inv.series = series
    inv.number = number
    # Totales finales
    recompute_totals(inv)
    inv.status = "posted"
    inv.save(update_fields=["series", "number", "status", "totals_base", "totals_tax", "total"])

    # TODO VERIFACTU:
    # Aquí será buen sitio para:
    # - generar verifactu_hash
    # - generar verifactu_qr_text
    # - y lanzar tarea de envío a AEAT

    return inv
