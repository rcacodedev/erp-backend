# analytics/services.py
from decimal import Decimal
from collections import defaultdict, Counter
from datetime import date, datetime

from django.db import models
from django.db.models import Sum, Count, Value, F, DecimalField as D
from django.db.models.functions import (
    ExtractYear,
    ExtractMonth,
    ExtractQuarter,
    Coalesce,
    TruncDay,
    TruncWeek,
    TruncMonth,
)
from django.utils import timezone

from core.models import Organization
from sales.models import Invoice, Quote, InvoiceLine
from .models import OrgFinancialYear, Expense
from purchases.models import SupplierInvoice
from inventory.models import Product
from django.db.models import CharField as C

# Cero decimal tipado para evitar "mixed types" en expresiones/aggregates
DEC0 = Value(Decimal("0.00"), output_field=D(max_digits=24, decimal_places=6))
STR_DASH = Value("—", output_field=C())


def get_yearly_summary(org: Organization):
    """
    Devuelve lista de dicts por año:
    [{"year": 2023, "income": ..., "expenses": ..., "profit": ...}, ...]
    """
    result = defaultdict(
        lambda: {
            "year": None,
            "income": Decimal("0.00"),
            "expenses": Decimal("0.00"),
            "profit": Decimal("0.00"),
        }
    )

    # 1) Ingresos por año (facturas "posted")
    inv_qs = (
        Invoice.objects.filter(org=org, status="posted")
        .annotate(year=ExtractYear("date_issue"))
        .values("year")
        .annotate(income=Sum("totals_base"))
    )
    for row in inv_qs:
        year = row["year"]
        if year is None:
            continue
        result[year]["year"] = year
        result[year]["income"] += row["income"] or Decimal("0.00")

    # 2) Gastos por año (Expense)
    exp_qs = (
        Expense.objects.filter(org=org)
        .annotate(year=ExtractYear("date"))
        .values("year")
        .annotate(expenses=Sum("amount"))
    )
    for row in exp_qs:
        year = row["year"]
        if year is None:
            continue
        result[year]["year"] = year
        result[year]["expenses"] += row["expenses"] or Decimal("0.00")

    # 3) Saldos iniciales
    fy_qs = OrgFinancialYear.objects.filter(organization=org)
    for fy in fy_qs:
        year = fy.year
        result[year]["year"] = year
        result[year]["income"] += fy.opening_income or Decimal("0.00")
        result[year]["expenses"] += fy.opening_expenses or Decimal("0.00")

    # 4) Beneficio
    for _, data in result.items():
        data["profit"] = (data["income"] or Decimal("0.00")) - (
            data["expenses"] or Decimal("0.00")
        )

    # Lista ordenada
    items = sorted(result.values(), key=lambda x: x["year"])
    return items


def get_sales_timeseries(org: Organization, date_from=None, date_to=None, group_by: str = "month"):
    """
    Serie temporal de ventas (ingresos) agrupadas por month|quarter|year.
    """
    qs = Invoice.objects.filter(org=org, status="posted")
    if date_from is not None:
        qs = qs.filter(date_issue__gte=date_from)
    if date_to is not None:
        qs = qs.filter(date_issue__lte=date_to)

    group_by = (group_by or "month").lower()
    if group_by not in ("month", "quarter", "year"):
        group_by = "month"

    items = []

    if group_by == "year":
        qs = (
            qs.annotate(year=ExtractYear("date_issue"))
            .values("year")
            .annotate(
                total_base=Sum("totals_base"),
                total_tax=Sum("totals_tax"),
                invoices_count=Count("id"),
            )
            .order_by("year")
        )
        for row in qs:
            year = row["year"]
            if year is None:
                continue
            items.append(
                {
                    "period": str(year),
                    "invoiced_base": row["total_base"] or Decimal("0.00"),
                    "invoiced_tax": row["total_tax"] or Decimal("0.00"),
                    "invoices_count": row["invoices_count"] or 0,
                }
            )

    elif group_by == "quarter":
        qs = (
            qs.annotate(year=ExtractYear("date_issue"), quarter=ExtractQuarter("date_issue"))
            .values("year", "quarter")
            .annotate(
                total_base=Sum("totals_base"),
                total_tax=Sum("totals_tax"),
                invoices_count=Count("id"),
            )
            .order_by("year", "quarter")
        )
        for row in qs:
            year = row["year"]
            quarter = row["quarter"]
            if year is None or quarter is None:
                continue
            items.append(
                {
                    "period": f"{year}-Q{quarter}",
                    "invoiced_base": row["total_base"] or Decimal("0.00"),
                    "invoiced_tax": row["total_tax"] or Decimal("0.00"),
                    "invoices_count": row["invoices_count"] or 0,
                }
            )

    else:  # month
        qs = (
            qs.annotate(year=ExtractYear("date_issue"), month=ExtractMonth("date_issue"))
            .values("year", "month")
            .annotate(
                total_base=Sum("totals_base"),
                total_tax=Sum("totals_tax"),
                invoices_count=Count("id"),
            )
            .order_by("year", "month")
        )
        for row in qs:
            year = row["year"]
            month = row["month"]
            if year is None or month is None:
                continue
            items.append(
                {
                    "period": f"{year}-{int(month):02d}",
                    "invoiced_base": row["total_base"] or Decimal("0.00"),
                    "invoiced_tax": row["total_tax"] or Decimal("0.00"),
                    "invoices_count": row["invoices_count"] or 0,
                }
            )

    total_base = sum(item["invoiced_base"] for item in items) or Decimal("0.00")
    total_tax = sum(item["invoiced_tax"] for item in items) or Decimal("0.00")
    total_count = sum(item["invoices_count"] for item in items) or 0

    return {
        "group_by": group_by,
        "items": items,
        "totals": {
            "invoiced_base": total_base,
            "invoiced_tax": total_tax,
            "invoices_count": total_count,
        },
    }


def get_expenses_timeseries(org: Organization, date_from=None, date_to=None, group_by: str = "month"):
    """
    Serie temporal de gastos agrupados por month|quarter|year.
    """
    qs = Expense.objects.filter(org=org)
    if date_from is not None:
        qs = qs.filter(date__gte=date_from)
    if date_to is not None:
        qs = qs.filter(date__lte=date_to)

    group_by = (group_by or "month").lower()
    if group_by not in ("month", "quarter", "year"):
        group_by = "month"

    items = []

    if group_by == "year":
        qs = (
            qs.annotate(year=ExtractYear("date"))
            .values("year")
            .annotate(total_amount=Sum("amount"), expenses_count=Count("id"))
            .order_by("year")
        )
        for row in qs:
            year = row["year"]
            if year is None:
                continue
            items.append(
                {
                    "period": str(year),
                    "expenses_amount": row["total_amount"] or Decimal("0.00"),
                    "expenses_count": row["expenses_count"] or 0,
                }
            )

    elif group_by == "quarter":
        qs = (
            qs.annotate(year=ExtractYear("date"), quarter=ExtractQuarter("date"))
            .values("year", "quarter")
            .annotate(total_amount=Sum("amount"), expenses_count=Count("id"))
            .order_by("year", "quarter")
        )
        for row in qs:
            year = row["year"]
            quarter = row["quarter"]
            if year is None or quarter is None:
                continue
            items.append(
                {
                    "period": f"{year}-Q{quarter}",
                    "expenses_amount": row["total_amount"] or Decimal("0.00"),
                    "expenses_count": row["expenses_count"] or 0,
                }
            )

    else:  # month
        qs = (
            qs.annotate(year=ExtractYear("date"), month=ExtractMonth("date"))
            .values("year", "month")
            .annotate(total_amount=Sum("amount"), expenses_count=Count("id"))
            .order_by("year", "month")
        )
        for row in qs:
            year = row["year"]
            month = row["month"]
            if year is None or month is None:
                continue
            items.append(
                {
                    "period": f"{year}-{int(month):02d}",
                    "expenses_amount": row["total_amount"] or Decimal("0.00"),
                    "expenses_count": row["expenses_count"] or 0,
                }
            )

    total_amount = sum(item["expenses_amount"] for item in items) or Decimal("0.00")
    total_count = sum(item["expenses_count"] for item in items) or 0

    return {
        "group_by": group_by,
        "items": items,
        "totals": {
            "expenses_amount": total_amount,
            "expenses_count": total_count,
        },
    }


def get_receivables_overview(org: Organization, as_of=None, limit: int = 10):
    """
    Resumen de cobros pendientes (ventas no pagadas totalmente).
    """
    if as_of is None:
        as_of = timezone.now().date()

    qs = Invoice.objects.filter(org=org, status="posted").exclude(payment_status="paid")

    # paid_amount con Coalesce tipado
    qs = qs.annotate(paid_amount=Coalesce(Sum("payments__amount"), DEC0))

    total_pending = Decimal("0.00")
    by_status = {"unpaid": Decimal("0.00"), "partial": Decimal("0.00")}
    invoices_data = []

    for inv in qs:
        paid_amount = inv.paid_amount or Decimal("0.00")
        total = inv.total or Decimal("0.00")
        pending = total - paid_amount
        if pending <= Decimal("0.00"):
            continue

        total_pending += pending
        status = inv.payment_status or "unpaid"
        by_status[status] = by_status.get(status, Decimal("0.00")) + pending

        days_since_issue = (as_of - inv.date_issue).days if inv.date_issue else None
        invoices_data.append(
            {
                "invoice_id": inv.id,
                "series": inv.series,
                "number": inv.number,
                "date_issue": inv.date_issue,
                "customer_name": str(inv.customer),
                "pending_amount": pending,
                "days_since_issue": days_since_issue,
                "payment_status": status,
            }
        )

    invoices_data.sort(key=lambda x: (x["pending_amount"], x["days_since_issue"] or 0), reverse=True)
    top_invoices = invoices_data[:limit]

    first_inv = qs.first()
    currency = getattr(first_inv, "currency", "EUR") if first_inv else "EUR"

    return {
        "as_of": as_of,
        "currency": currency,
        "total_pending": total_pending,
        "by_status": by_status,
        "top_invoices": top_invoices,
    }


def get_vat_summary(org: Organization, date_from=None, date_to=None, group_by: str = "month"):
    """
    IVA repercutido (ventas) agrupado por month|quarter|year.
    """
    qs = Invoice.objects.filter(org=org, status="posted")
    if date_from is not None:
        qs = qs.filter(date_issue__gte=date_from)
    if date_to is not None:
        qs = qs.filter(date_issue__lte=date_to)

    group_by = (group_by or "month").lower()
    if group_by not in ("month", "quarter", "year"):
        group_by = "month"

    items = []

    if group_by == "year":
        qs = (
            qs.annotate(year=ExtractYear("date_issue"))
            .values("year")
            .annotate(
                base_amount=Sum("totals_base"),
                tax_amount=Sum("totals_tax"),
                invoices_count=Count("id"),
            )
            .order_by("year")
        )
        for row in qs:
            year = row["year"]
            if year is None:
                continue
            items.append(
                {
                    "period": str(year),
                    "base_amount": row["base_amount"] or Decimal("0.00"),
                    "tax_amount": row["tax_amount"] or Decimal("0.00"),
                    "invoices_count": row["invoices_count"] or 0,
                }
            )

    elif group_by == "quarter":
        qs = (
            qs.annotate(year=ExtractYear("date_issue"), quarter=ExtractQuarter("date_issue"))
            .values("year", "quarter")
            .annotate(
                base_amount=Sum("totals_base"),
                tax_amount=Sum("totals_tax"),
                invoices_count=Count("id"),
            )
            .order_by("year", "quarter")
        )
        for row in qs:
            year = row["year"]
            quarter = row["quarter"]
            if year is None or quarter is None:
                continue
            items.append(
                {
                    "period": f"{year}-Q{quarter}",
                    "base_amount": row["base_amount"] or Decimal("0.00"),
                    "tax_amount": row["tax_amount"] or Decimal("0.00"),
                    "invoices_count": row["invoices_count"] or 0,
                }
            )

    else:  # month
        qs = (
            qs.annotate(year=ExtractYear("date_issue"), month=ExtractMonth("date_issue"))
            .values("year", "month")
            .annotate(
                base_amount=Sum("totals_base"),
                tax_amount=Sum("totals_tax"),
                invoices_count=Count("id"),
            )
            .order_by("year", "month")
        )
        for row in qs:
            year = row["year"]
            month = row["month"]
            if year is None or month is None:
                continue
            items.append(
                {
                    "period": f"{year}-{int(month):02d}",
                    "base_amount": row["base_amount"] or Decimal("0.00"),
                    "tax_amount": row["tax_amount"] or Decimal("0.00"),
                    "invoices_count": row["invoices_count"] or 0,
                }
            )

    total_base = sum(i["base_amount"] for i in items) or Decimal("0.00")
    total_tax = sum(i["tax_amount"] for i in items) or Decimal("0.00")
    total_count = sum(i["invoices_count"] for i in items) or 0

    return {
        "group_by": group_by,
        "items": items,
        "totals": {
            "base_amount": total_base,
            "tax_amount": total_tax,
            "invoices_count": total_count,
        },
    }


def get_top_customers(org: Organization, date_from=None, date_to=None, limit: int = 5):
    """
    Top clientes por facturación (base) en un rango.
    """
    qs = Invoice.objects.filter(org=org, status="posted")
    if date_from is not None:
        qs = qs.filter(date_issue__gte=date_from)
    if date_to is not None:
        qs = qs.filter(date_issue__lte=date_to)

    qs = (
        qs.values("customer_id")
        .annotate(
            total_base=Sum("totals_base"),
            total_tax=Sum("totals_tax"),
            invoices_count=Count("id"),
        )
        .order_by("-total_base")
    )

    from contacts.models import Contact  # import local para evitar ciclos
    customer_ids = [row["customer_id"] for row in qs]
    contacts_by_id = {c.id: str(c) for c in Contact.objects.filter(id__in=customer_ids)}

    items = []
    for row in qs[:limit]:
        cid = row["customer_id"]
        items.append(
            {
                "customer_id": cid,
                "customer_name": contacts_by_id.get(cid, f"ID {cid}"),
                "total_base": row["total_base"] or Decimal("0.00"),
                "total_tax": row["total_tax"] or Decimal("0.00"),
                "invoices_count": row["invoices_count"] or 0,
            }
        )

    return {"items": items}


def get_quotes_vs_invoices(org: Organization, date_from=None, date_to=None):
    """
    Total presupuestado vs total facturado en un rango.
    """
    quotes_qs = Quote.objects.filter(org=org).exclude(status="draft")
    inv_qs = Invoice.objects.filter(org=org, status="posted")

    if date_from is not None:
        quotes_qs = quotes_qs.filter(date__gte=date_from)
        inv_qs = inv_qs.filter(date_issue__gte=date_from)
    if date_to is not None:
        quotes_qs = quotes_qs.filter(date__lte=date_to)
        inv_qs = inv_qs.filter(date_issue__lte=date_to)

    quoted = quotes_qs.aggregate(total=Sum("totals_base"))["total"] or Decimal("0.00")
    invoiced = inv_qs.aggregate(total=Sum("totals_base"))["total"] or Decimal("0.00")
    conversion_ratio = (invoiced / quoted) if quoted > Decimal("0.00") else Decimal("0.00")

    return {"total_quoted": quoted, "total_invoiced": invoiced, "conversion_ratio": conversion_ratio}


def _parse_date(s):
    if not s:
        return None
    return datetime.fromisoformat(s).date()


def get_margins(org, dfrom, dto, group_by="product"):
    dfrom = _parse_date(dfrom)
    dto = _parse_date(dto)

    qs = (
        InvoiceLine.objects.filter(invoice__org=org, invoice__status="posted")
        .select_related("product", "invoice", "invoice__customer")
    )
    if dfrom:
        qs = qs.filter(invoice__date_issue__gte=dfrom)
    if dto:
        qs = qs.filter(invoice__date_issue__lte=dto)

    qs = qs.annotate(
        revenue=Coalesce(F("qty") * F("unit_price"), DEC0),
        cogs=Coalesce(F("qty") * F("product__cost_price"), DEC0),
    )

    # Elegir clave de agrupación
    if group_by == "product":
        vals = qs.values(key=F("product__name"))
    elif group_by == "category":
        vals = qs.values(key=F("product__category__name"))
    elif group_by == "customer":
        # Contact no tiene 'name'. Usamos Coalesce sobre campos reales:
        # preferencia: razon_social -> nombre_comercial -> nombre
        customer_key = Coalesce(
            F("invoice__customer__razon_social"),
            F("invoice__customer__nombre_comercial"),
            F("invoice__customer__nombre"),
            STR_DASH,
        )
        vals = qs.values(key=customer_key)
    elif group_by == "seller":
        vals = qs.values(key=STR_DASH)
    else:
        vals = qs.values(key=F("product__name"))

    agg = vals.annotate(
        revenue=Coalesce(Sum("revenue"), DEC0),
        cogs=Coalesce(Sum("cogs"),   DEC0),
    )

    rows = []
    total_rev = Decimal("0")
    total_cogs = Decimal("0")
    for r in agg:
        rev = r["revenue"] or Decimal("0")
        c = r["cogs"] or Decimal("0")
        m = rev - c
        pct = (m / rev) if rev else Decimal("0")
        rows.append({
            "key": r["key"] or "—",
            "revenue": rev,
            "cogs": c,
            "margin": m,
            "margin_pct": pct,
        })
        total_rev += rev
        total_cogs += c

    rows.sort(key=lambda x: x["margin"], reverse=True)
    totals = {
        "revenue": total_rev,
        "cogs": total_cogs,
        "margin": total_rev - total_cogs,
        "margin_pct": ((total_rev - total_cogs) / total_rev) if total_rev else Decimal("0"),
    }
    return {"rows": rows, "totals": totals}



def _bucket_days(overdue_days):
    if overdue_days <= 30:
        return "0-30"
    if overdue_days <= 60:
        return "31-60"
    if overdue_days <= 90:
        return "61-90"
    return ">90"


def get_aging_receivables(org, as_of=None):
    """
    Aging de clientes por due_date (requiere Invoice.due_date).
    """
    as_of = _parse_date(as_of) or date.today()
    inv = Invoice.objects.filter(org=org, status="posted").exclude(due_date__isnull=True)
    buckets = Counter()
    for x in inv.values("due_date", "total"):
        days = (as_of - x["due_date"]).days
        overdue = max(0, days)
        buckets[_bucket_days(overdue)] += x["total"] or Decimal("0")
    return {"as_of": str(as_of), "buckets": buckets}


def get_aging_payables(org, as_of=None):
    """
    Aging de proveedores por due_date.
    """
    as_of = _parse_date(as_of) or date.today()
    inv = SupplierInvoice.objects.filter(org=org, status="posted").exclude(due_date__isnull=True)
    buckets = Counter()
    for x in inv.values("due_date", "total"):
        days = (as_of - x["due_date"]).days
        overdue = max(0, days)
        buckets[_bucket_days(overdue)] += x["total"] or Decimal("0")
    return {"as_of": str(as_of), "buckets": buckets}


def get_cashflow(org, dfrom, dto, bucket="day"):
    """
    Inflows: Invoice.total por due_date
    Outflows: SupplierInvoice.total por due_date
    """
    dfrom = _parse_date(dfrom)
    dto = _parse_date(dto)

    ar = Invoice.objects.filter(org=org, status="posted").exclude(due_date__isnull=True)
    ap = SupplierInvoice.objects.filter(org=org, status="posted").exclude(due_date__isnull=True)
    if dfrom:
        ar = ar.filter(due_date__gte=dfrom)
        ap = ap.filter(due_date__gte=dfrom)
    if dto:
        ar = ar.filter(due_date__lte=dto)
        ap = ap.filter(due_date__lte=dto)

    trunc = TruncDay if bucket == "day" else (TruncWeek if bucket == "week" else TruncMonth)

    ar = ar.annotate(b=trunc("due_date")).values("b").annotate(inflows=Coalesce(Sum("total"), DEC0))
    ap = ap.annotate(b=trunc("due_date")).values("b").annotate(outflows=Coalesce(Sum("total"), DEC0))

    by_date = defaultdict(lambda: {"inflows": Decimal("0"), "outflows": Decimal("0")})

    for r in ar:
        b = r["b"]
        key = b.date() if hasattr(b, "date") else b  # normaliza a date
        by_date[key]["inflows"] += r["inflows"]

    for r in ap:
        b = r["b"]
        key = b.date() if hasattr(b, "date") else b  # normaliza a date
        by_date[key]["outflows"] += r["outflows"]

    series = []
    for d in sorted(by_date.keys()):
        v = by_date[d]
        series.append({
            "date": str(d),
            "inflows": v["inflows"],
            "outflows": v["outflows"],
            "net": v["inflows"] - v["outflows"],
        })
    return {"bucket": "day" if bucket not in ("day", "week", "month") else bucket, "series": series}



def get_customers_abc(org, dfrom, dto, rule="80-15-5"):
    dfrom = _parse_date(dfrom)
    dto = _parse_date(dto)
    a, b, c = map(int, rule.split("-"))

    # Construimos la "customer_key" de forma robusta según tus campos reales
    customer_key = Coalesce(
        F("customer__razon_social"),
        F("customer__nombre_comercial"),
        F("customer__nombre"),
        STR_DASH,
    )

    qs = (
        Invoice.objects.filter(org=org, status="posted")
    )
    if dfrom:
        qs = qs.filter(date_issue__gte=dfrom)
    if dto:
        qs = qs.filter(date_issue__lte=dto)

    # Primero anotamos la clave, luego values() y luego agregamos
    qs = (
        qs.annotate(customer_key=customer_key)
          .values("customer_key")
          .annotate(revenue=Coalesce(Sum("total"), DEC0))  # o Sum("totals_base") si prefieres base
          .order_by("-revenue")
    )

    rows = list(qs)
    total = sum((r["revenue"] for r in rows), Decimal("0"))
    a_cut = total * Decimal(a / 100)
    b_cut = total * Decimal((a + b) / 100)

    A, B, Cc = [], [], []
    acc = Decimal("0")
    for r in rows:
        acc += r["revenue"]
        item = {"customer_name": r["customer_key"], "revenue": r["revenue"]}
        if acc <= a_cut:
            A.append(item)
        elif acc <= b_cut:
            B.append(item)
        else:
            Cc.append(item)

    return {"rule": rule, "a": A, "b": B, "c": Cc, "total": total}


def get_cohorts(org, months=6):
    # Placeholder; implementaremos cuando fijemos la definición de cohorte.
    return {"months": months, "cohorts": []}


def get_top_products(org, dfrom, dto, by="revenue", limit=10):
    dfrom = _parse_date(dfrom)
    dto = _parse_date(dto)

    qs = (
        InvoiceLine.objects.filter(invoice__org=org, invoice__status="posted")
        .select_related("product", "invoice")
    )
    if dfrom:
        qs = qs.filter(invoice__date_issue__gte=dfrom)
    if dto:
        qs = qs.filter(invoice__date_issue__lte=dto)

    qs = qs.annotate(
        revenue=Coalesce(F("qty") * F("unit_price"), DEC0),
        margin=Coalesce(F("qty") * F("unit_price"), DEC0) - Coalesce(F("qty") * F("product__cost_price"), DEC0),
    ).values("product__name").annotate(
        revenue=Coalesce(Sum("revenue"), DEC0),
        margin=Coalesce(Sum("margin"), DEC0),
    )

    key = "margin" if by == "margin" else "revenue"
    rows = sorted(qs, key=lambda x: x[key], reverse=True)[:limit]
    return {"by": key, "rows": rows}
