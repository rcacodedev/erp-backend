# sales/pricing.py
from decimal import Decimal, ROUND_HALF_EVEN

def money(x):
    return (x.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
            if isinstance(x, Decimal) else Decimal(x).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN))

def compute_invoice_totals(lines):
    """
    lines: iterable de dicts con keys: qty, unit_price, discount_pct, tax_rate
    """
    bases_por_iva = {}
    for ln in lines:
        qty = Decimal(ln["qty"])
        unit = Decimal(ln["unit_price"])
        disc = Decimal(ln.get("discount_pct", 0))
        rate = Decimal(ln["tax_rate"])
        base_line = qty * unit * (Decimal("1.00") - disc/Decimal("100"))
        base_line = money(base_line)
        bases_por_iva[rate] = bases_por_iva.get(rate, Decimal("0.00")) + base_line

    total_base = sum(bases_por_iva.values(), Decimal("0.00"))
    total_tax = sum((b * r/Decimal("100") for r, b in bases_por_iva.items()), Decimal("0.00"))
    total_base = money(total_base)
    total_tax = money(total_tax)
    total = money(total_base + total_tax)
    return total_base, total_tax, total
