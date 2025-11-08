# sales/services_payments.py
from decimal import Decimal
from django.db import transaction
from django.db.models import Sum
from rest_framework.exceptions import ValidationError

from .models import Payment, Invoice


@transaction.atomic
def register_payment(inv: Invoice, *, amount: Decimal, date, method: str, notes=""):
    if inv.status != "posted":
        raise ValidationError("La factura debe estar 'posted' para registrar pagos")

    pay = Payment.objects.create(
        org=inv.org,
        invoice=inv,
        amount=amount,
        date=date,
        method=method,
        notes=notes,
    )

    # actualizar estado de cobro
    paid_sum = inv.payments.aggregate(s=Sum("amount"))["s"] or Decimal("0.00")
    if paid_sum == 0:
        inv.payment_status = "unpaid"
    elif paid_sum < inv.total:
        inv.payment_status = "partial"
    else:
        inv.payment_status = "paid"
    inv.save(update_fields=["payment_status"])

    return pay
