# sales/services_delivery.py
from decimal import Decimal
from django.db import transaction
from rest_framework.exceptions import ValidationError

from inventory import services as inv_services
from .models import DeliveryNote, DeliveryNoteLine


@transaction.atomic
def add_line(
    dn: DeliveryNote,
    *,
    product,
    description: str,
    qty: Decimal,
    uom: str,
    unit_price,
    tax_rate,
    discount_pct=0,
):
    if dn.status != "draft":
        raise ValidationError("El albarán no está en borrador")
    return DeliveryNoteLine.objects.create(
        delivery_note=dn,
        product=product,
        description=description or (product.name if product else ""),
        qty=qty,
        uom=uom,
        unit_price=unit_price,
        tax_rate=tax_rate,
        discount_pct=discount_pct,
    )


@transaction.atomic
def confirm(dn: DeliveryNote, *, user):
    if dn.status != "draft":
        raise ValidationError("El albarán ya está confirmado")
    # salida de stock por cada línea con producto
    for ln in dn.lines.select_related("product"):
        if ln.product:
            inv_services.confirm_outgoing(
                org=dn.org,
                user=user,
                product_id=ln.product_id,
                warehouse_id=dn.warehouse_id,
                qty=ln.qty,
                reason="sale",
                ref_type="DN",
                ref_id=str(dn.id),
            )
    dn.status = "done"
    dn.save(update_fields=["status"])
    return dn
