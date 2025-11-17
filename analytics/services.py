# analytics/services.py
from decimal import Decimal
from collections import defaultdict

from django.db.models import Sum, Count, Value
from django.db.models.functions import ExtractYear, ExtractMonth, ExtractQuarter, Coalesce
from django.utils import timezone

from core.models import Organization
from sales.models import Invoice, Quote
from .models import OrgFinancialYear, Expense


def get_yearly_summary(org: Organization):
    """
    Devuelve un dict:
    {
      2023: {"year": 2023, "income": Decimal(...), "expenses": Decimal(...), "profit": Decimal(...)},
      2024: {...},
      ...
    }
    Donde:
      income   = opening_income + sum(totals_base de facturas posted ese año)
      expenses = opening_expenses + sum(expenses.amount ese año)
      profit   = income - expenses
    """
    result = defaultdict(lambda: {
        "year": None,
        "income": Decimal("0.00"),
        "expenses": Decimal("0.00"),
        "profit": Decimal("0.00"),
    })

    # 1) Facturas de venta (ingresos) por año
    inv_qs = (
        Invoice.objects
        .filter(org=org, status="posted")
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

    # 2) Gastos (Expense) por año
    exp_qs = (
        Expense.objects
        .filter(org=org)
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

    # 3) Saldos iniciales + presupuestos en OrgFinancialYear
    fy_qs = OrgFinancialYear.objects.filter(organization=org)
    for fy in fy_qs:
        year = fy.year
        result[year]["year"] = year
        result[year]["income"] += fy.opening_income or Decimal("0.00")
        result[year]["expenses"] += fy.opening_expenses or Decimal("0.00")

    # 4) Calcular beneficio
    for year, data in result.items():
        data["profit"] = (data["income"] or Decimal("0.00")) - (data["expenses"] or Decimal("0.00"))

    # Devolver como lista ordenada
    items = sorted(result.values(), key=lambda x: x["year"])
    return items

def get_sales_timeseries(
    org: Organization,
    date_from=None,
    date_to=None,
    group_by: str = "month",
):
    """
    Devuelve una serie temporal de ventas (ingresos) agrupadas por mes / trimestre / año.

    Params:
        org       -> Organization
        date_from -> date o None
        date_to   -> date o None
        group_by  -> "month" (default) | "quarter" | "year"

    Respuesta tipo:
    {
      "group_by": "month",
      "items": [
        {
          "period": "2025-01",
          "invoiced_base": Decimal(...),
          "invoiced_tax": Decimal(...),
          "invoices_count": 12,
        },
        ...
      ],
      "totals": {
        "invoiced_base": Decimal(...),
        "invoiced_tax": Decimal(...),
        "invoices_count": 100,
      }
    }
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
            items.append({
                "period": str(year),  # "2025"
                "invoiced_base": row["total_base"] or Decimal("0.00"),
                "invoiced_tax": row["total_tax"] or Decimal("0.00"),
                "invoices_count": row["invoices_count"] or 0,
            })

    elif group_by == "quarter":
        qs = (
            qs.annotate(
                year=ExtractYear("date_issue"),
                quarter=ExtractQuarter("date_issue"),
            )
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
            period_label = f"{year}-Q{quarter}"  # "2025-Q1"
            items.append({
                "period": period_label,
                "invoiced_base": row["total_base"] or Decimal("0.00"),
                "invoiced_tax": row["total_tax"] or Decimal("0.00"),
                "invoices_count": row["invoices_count"] or 0,
            })

    else:  # "month"
        qs = (
            qs.annotate(
                year=ExtractYear("date_issue"),
                month=ExtractMonth("date_issue"),
            )
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
            period_label = f"{year}-{int(month):02d}"  # "2025-01"
            items.append({
                "period": period_label,
                "invoiced_base": row["total_base"] or Decimal("0.00"),
                "invoiced_tax": row["total_tax"] or Decimal("0.00"),
                "invoices_count": row["invoices_count"] or 0,
            })

    # Totales globales
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

def get_expenses_timeseries(
    org: Organization,
    date_from=None,
    date_to=None,
    group_by: str = "month",
):
    """
    Devuelve una serie temporal de gastos agrupados por mes / trimestre / año.

    Params:
        org       -> Organization
        date_from -> date o None
        date_to   -> date o None
        group_by  -> "month" (default) | "quarter" | "year"

    Respuesta tipo:
    {
      "group_by": "month",
      "items": [
        {
          "period": "2025-01",
          "expenses_amount": Decimal(...),
          "expenses_count": 5
        },
        ...
      ],
      "totals": {
        "expenses_amount": Decimal(...),
        "expenses_count": 42
      }
    }
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
            .annotate(
                total_amount=Sum("amount"),
                expenses_count=Count("id"),
            )
            .order_by("year")
        )

        for row in qs:
            year = row["year"]
            if year is None:
                continue
            items.append({
                "period": str(year),  # "2025"
                "expenses_amount": row["total_amount"] or Decimal("0.00"),
                "expenses_count": row["expenses_count"] or 0,
            })

    elif group_by == "quarter":
        qs = (
            qs.annotate(
                year=ExtractYear("date"),
                quarter=ExtractQuarter("date"),
            )
            .values("year", "quarter")
            .annotate(
                total_amount=Sum("amount"),
                expenses_count=Count("id"),
            )
            .order_by("year", "quarter")
        )

        for row in qs:
            year = row["year"]
            quarter = row["quarter"]
            if year is None or quarter is None:
                continue
            period_label = f"{year}-Q{quarter}"
            items.append({
                "period": period_label,
                "expenses_amount": row["total_amount"] or Decimal("0.00"),
                "expenses_count": row["expenses_count"] or 0,
            })

    else:  # "month"
        qs = (
            qs.annotate(
                year=ExtractYear("date"),
                month=ExtractMonth("date"),
            )
            .values("year", "month")
            .annotate(
                total_amount=Sum("amount"),
                expenses_count=Count("id"),
            )
            .order_by("year", "month")
        )

        for row in qs:
            year = row["year"]
            month = row["month"]
            if year is None or month is None:
                continue
            period_label = f"{year}-{int(month):02d}"  # "2025-01"
            items.append({
                "period": period_label,
                "expenses_amount": row["total_amount"] or Decimal("0.00"),
                "expenses_count": row["expenses_count"] or 0,
            })

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

def get_receivables_overview(
    org: Organization,
    as_of=None,
    limit: int = 10,
):
    """
    Devuelve resumen de cobros pendientes:

    {
      "as_of": "2025-11-17",
      "currency": "EUR",
      "total_pending": Decimal(...),
      "by_status": {
        "unpaid": Decimal(...),
        "partial": Decimal(...),
      },
      "top_invoices": [
        {
          "invoice_id": 1,
          "series": "A",
          "number": 25,
          "date_issue": date(...),
          "customer_name": "Cliente S.A.",
          "pending_amount": Decimal(...),
          "days_since_issue": 32,
          "payment_status": "partial"
        },
        ...
      ]
    }
    """
    if as_of is None:
        as_of = timezone.now().date()

    # Facturas "posted" que NO están totalmente pagadas
    qs = (
        Invoice.objects
        .filter(org=org, status="posted")
        .exclude(payment_status="paid")
    )

    # Annotate con lo pagado
    qs = qs.annotate(
        paid_amount=Coalesce(
            Sum("payments__amount"),
            Value(Decimal("0.00")),
        )
    )

    total_pending = Decimal("0.00")
    by_status = {
        "unpaid": Decimal("0.00"),
        "partial": Decimal("0.00"),
    }
    invoices_data = []

    for inv in qs:
        paid_amount = inv.paid_amount or Decimal("0.00")
        total = inv.total or Decimal("0.00")  # total = base + IVA
        pending = total - paid_amount

        # Si por redondeos o rarezas sale <= 0, lo ignoramos
        if pending <= Decimal("0.00"):
            continue

        total_pending += pending

        status = inv.payment_status or "unpaid"
        if status in by_status:
            by_status[status] += pending
        else:
            by_status[status] = by_status.get(status, Decimal("0.00")) + pending

        days_since_issue = (as_of - inv.date_issue).days if inv.date_issue else None

        invoices_data.append({
            "invoice_id": inv.id,
            "series": inv.series,
            "number": inv.number,
            "date_issue": inv.date_issue,
            "customer_name": str(inv.customer),
            "pending_amount": pending,
            "days_since_issue": days_since_issue,
            "payment_status": status,
        })

    # Ordenar: primero las que más deben, luego las más antiguas
    invoices_data.sort(
        key=lambda x: (x["pending_amount"], x["days_since_issue"] or 0),
        reverse=True,
    )
    top_invoices = invoices_data[:limit]

    # Moneda: asumimos una sola por org; tomamos la de la primera factura o EUR
    first_inv = qs.first()
    currency = getattr(first_inv, "currency", "EUR") if first_inv else "EUR"

    return {
        "as_of": as_of,
        "currency": currency,
        "total_pending": total_pending,
        "by_status": by_status,
        "top_invoices": top_invoices,
    }

def get_vat_summary(
    org: Organization,
    date_from=None,
    date_to=None,
    group_by: str = "month",
):
    """
    IVA repercutido (ventas) agrupado por mes / trimestre / año.

    Usa Invoice.status = posted, sumando totals_base y totals_tax.

    Respuesta:
    {
      "group_by": "month",
      "items": [
        {
          "period": "2025-01",
          "base_amount": Decimal(...),
          "tax_amount": Decimal(...),
          "invoices_count": 10
        },
        ...
      ],
      "totals": {
        "base_amount": Decimal(...),
        "tax_amount": Decimal(...),
        "invoices_count": 123
      }
    }
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
            items.append({
                "period": str(year),
                "base_amount": row["base_amount"] or Decimal("0.00"),
                "tax_amount": row["tax_amount"] or Decimal("0.00"),
                "invoices_count": row["invoices_count"] or 0,
            })

    elif group_by == "quarter":
        qs = (
            qs.annotate(
                year=ExtractYear("date_issue"),
                quarter=ExtractQuarter("date_issue"),
            )
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
            period_label = f"{year}-Q{quarter}"
            items.append({
                "period": period_label,
                "base_amount": row["base_amount"] or Decimal("0.00"),
                "tax_amount": row["tax_amount"] or Decimal("0.00"),
                "invoices_count": row["invoices_count"] or 0,
            })

    else:  # month
        qs = (
            qs.annotate(
                year=ExtractYear("date_issue"),
                month=ExtractMonth("date_issue"),
            )
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
            period_label = f"{year}-{int(month):02d}"
            items.append({
                "period": period_label,
                "base_amount": row["base_amount"] or Decimal("0.00"),
                "tax_amount": row["tax_amount"] or Decimal("0.00"),
                "invoices_count": row["invoices_count"] or 0,
            })

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

def get_top_customers(
    org: Organization,
    date_from=None,
    date_to=None,
    limit: int = 5,
):
    """
    Top clientes por facturación (base) en un rango.

    Devuelve:
    {
      "items": [
        {
          "customer_id": 1,
          "customer_name": "Cliente S.A.",
          "total_base": Decimal(...),
          "total_tax": Decimal(...),
          "invoices_count": 3,
        },
        ...
      ]
    }
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

    # Cargar los contactos en un dict para resolver el nombre
    # (para evitar N+1 queries si luego queremos el nombre)
    customer_ids = [row["customer_id"] for row in qs]
    from contacts.models import Contact  # import local para evitar ciclos

    contacts_by_id = {
        c.id: str(c)
        for c in Contact.objects.filter(id__in=customer_ids)
    }

    items = []
    for row in qs[:limit]:
        cid = row["customer_id"]
        items.append({
            "customer_id": cid,
            "customer_name": contacts_by_id.get(cid, f"ID {cid}"),
            "total_base": row["total_base"] or Decimal("0.00"),
            "total_tax": row["total_tax"] or Decimal("0.00"),
            "invoices_count": row["invoices_count"] or 0,
        })

    return {"items": items}

def get_quotes_vs_invoices(
    org: Organization,
    date_from=None,
    date_to=None,
):
    """
    Total presupuestado vs total facturado en un rango.

    Regla v1:
      - Presupuestado: Quote con status != 'draft'
      - Facturado: Invoice posted en el mismo rango

    Devuelve:
    {
      "total_quoted": Decimal(...),
      "total_invoiced": Decimal(...),
      "conversion_ratio": Decimal(...)  # 0-1
    }
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

    if quoted > Decimal("0.00"):
        conversion_ratio = invoiced / quoted
    else:
        conversion_ratio = Decimal("0.00")

    return {
        "total_quoted": quoted,
        "total_invoiced": invoiced,
        "conversion_ratio": conversion_ratio,
    }
