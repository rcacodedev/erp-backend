# sales/services_numbering.py
from django.db import transaction
from django.utils import timezone

from .models import InvoiceSequence


@transaction.atomic
def next_invoice_number(org, series: str):
    """
    Devuelve (year, number) para la siguiente factura de esa serie.
    """
    year = timezone.now().year
    seq, _ = InvoiceSequence.objects.select_for_update().get_or_create(
        org=org,
        series=series,
        year=year,
        defaults={"last_number": 0},
    )
    seq.last_number += 1
    seq.save(update_fields=["last_number"])
    return year, seq.last_number
