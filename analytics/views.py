# analytics/views.py
from datetime import date

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError

from django.http import JsonResponse

from .services import get_yearly_summary, get_sales_timeseries, get_expenses_timeseries, get_receivables_overview, get_vat_summary, get_top_customers, get_quotes_vs_invoices, get_margins, get_aging_receivables, get_aging_payables, get_cashflow, get_customers_abc, get_cohorts, get_top_products
from billing.decorators import require_plan

def health(_request):
    return JsonResponse({"app": "analytics", "status": "ok"})

class BaseAnalyticsView(APIView):
    """
    Base para views de analytics, para reutilizar get_org.
    """
    permission_classes = [IsAuthenticated]

    def get_org(self, request):
        org = getattr(request, "org", None)
        if org is None:
            raise ValidationError("No se ha podido resolver la organización (org) desde la URL.")
        return org


class YearlySummaryView(APIView):
    """
    GET /api/v1/t/{org_slug}/analytics/yearly-summary/

    Devuelve ingresos, gastos y beneficio por año para la org de la request.
    """
    permission_classes = [IsAuthenticated]

    def get_org(self, request):
        org = getattr(request, "org", None)
        if org is None:
            raise ValidationError("No se ha podido resolver la organización (org) desde la URL.")
        return org

    def get(self, request, *args, **kwargs):
        org = self.get_org(request)
        items = get_yearly_summary(org)

        # Año con mayor beneficio (por si quieres mostrarlo en el frontend)
        best_year = None
        if items:
            best_year = max(items, key=lambda x: x["profit"])

        return Response({
            "items": items,
            "best_year": best_year,  # puede ser null si no hay datos
        })

class SalesTimeseriesView(BaseAnalyticsView):
    """
    GET /api/v1/t/{org_slug}/analytics/sales-timeseries/?from=YYYY-MM-DD&to=YYYY-MM-DD&group_by=month|quarter|year

    Devuelve la serie temporal de ingresos agrupada según group_by.
    """

    def parse_date(self, value, field_name):
        if not value:
            return None
        try:
            return date.fromisoformat(value)
        except ValueError:
            raise ValidationError({field_name: "Formato de fecha inválido. Usa YYYY-MM-DD."})

    def get(self, request, *args, **kwargs):
        org = self.get_org(request)

        from_str = request.query_params.get("from")
        to_str = request.query_params.get("to")
        group_by = request.query_params.get("group_by", "month")

        date_from = self.parse_date(from_str, "from")
        date_to = self.parse_date(to_str, "to")

        data = get_sales_timeseries(
            org=org,
            date_from=date_from,
            date_to=date_to,
            group_by=group_by,
        )

        return Response(data)

class ExpensesTimeseriesView(BaseAnalyticsView):
    """
    GET /api/v1/t/{org_slug}/analytics/expenses-timeseries/?from=YYYY-MM-DD&to=YYYY-MM-DD&group_by=month|quarter|year

    Devuelve la serie temporal de gastos agrupada según group_by.
    """

    def parse_date(self, value, field_name):
        if not value:
            return None
        try:
            return date.fromisoformat(value)
        except ValueError:
            raise ValidationError({field_name: "Formato de fecha inválido. Usa YYYY-MM-DD."})

    def get(self, request, *args, **kwargs):
        org = self.get_org(request)

        from_str = request.query_params.get("from")
        to_str = request.query_params.get("to")
        group_by = request.query_params.get("group_by", "month")

        date_from = self.parse_date(from_str, "from")
        date_to = self.parse_date(to_str, "to")

        data = get_expenses_timeseries(
            org=org,
            date_from=date_from,
            date_to=date_to,
            group_by=group_by,
        )

        return Response(data)

class ReceivablesView(BaseAnalyticsView):
    """
    GET /api/v1/t/{org_slug}/analytics/receivables/?as_of=YYYY-MM-DD&limit=10

    Devuelve total pendiente, desglose por estado y top facturas pendientes.
    """

    def parse_date(self, value, field_name):
        if not value:
            return None
        try:
            return date.fromisoformat(value)
        except ValueError:
            raise ValidationError({field_name: "Formato de fecha inválido. Usa YYYY-MM-DD."})

    def get(self, request, *args, **kwargs):
        org = self.get_org(request)

        as_of_str = request.query_params.get("as_of")
        limit_str = request.query_params.get("limit")

        as_of = self.parse_date(as_of_str, "as_of")
        if as_of is None:
            # Si no viene, usamos hoy dentro del servicio
            data = get_receivables_overview(org=org)
        else:
            # Limit opcional
            try:
                limit = int(limit_str) if limit_str else 10
            except ValueError:
                raise ValidationError({"limit": "Debe ser un entero."})

            data = get_receivables_overview(
                org=org,
                as_of=as_of,
                limit=limit,
            )

        return Response(data)

class VatSummaryView(BaseAnalyticsView):
    """
    GET /api/v1/t/{org_slug}/analytics/vat/?from=YYYY-MM-DD&to=YYYY-MM-DD&group_by=month|quarter|year
    """

    def parse_date(self, value, field_name):
        if not value:
            return None
        try:
            return date.fromisoformat(value)
        except ValueError:
            raise ValidationError({field_name: "Formato de fecha inválido. Usa YYYY-MM-DD."})

    def get(self, request, *args, **kwargs):
        org = self.get_org(request)

        from_str = request.query_params.get("from")
        to_str = request.query_params.get("to")
        group_by = request.query_params.get("group_by", "month")

        date_from = self.parse_date(from_str, "from")
        date_to = self.parse_date(to_str, "to")

        data = get_vat_summary(
            org=org,
            date_from=date_from,
            date_to=date_to,
            group_by=group_by,
        )

        return Response(data)

class TopCustomersView(BaseAnalyticsView):
    """
    GET /api/v1/t/{org_slug}/analytics/top-customers/?from=YYYY-MM-DD&to=YYYY-MM-DD&limit=5
    """

    def parse_date(self, value, field_name):
        if not value:
            return None
        try:
            return date.fromisoformat(value)
        except ValueError:
            raise ValidationError({field_name: "Formato de fecha inválido. Usa YYYY-MM-DD."})

    def get(self, request, *args, **kwargs):
        org = self.get_org(request)

        from_str = request.query_params.get("from")
        to_str = request.query_params.get("to")
        limit_str = request.query_params.get("limit", "5")

        date_from = self.parse_date(from_str, "from")
        date_to = self.parse_date(to_str, "to")

        try:
            limit = int(limit_str)
        except ValueError:
            raise ValidationError({"limit": "Debe ser un entero."})

        data = get_top_customers(
            org=org,
            date_from=date_from,
            date_to=date_to,
            limit=limit,
        )

        return Response(data)

class QuotesVsInvoicesView(BaseAnalyticsView):
    """
    GET /api/v1/t/{org_slug}/analytics/quotes-vs-invoices/?from=YYYY-MM-DD&to=YYYY-MM-DD
    """

    def parse_date(self, value, field_name):
        if not value:
            return None
        try:
            return date.fromisoformat(value)
        except ValueError:
            raise ValidationError({field_name: "Formato de fecha inválido. Usa YYYY-MM-DD."})

    def get(self, request, *args, **kwargs):
        org = self.get_org(request)

        from_str = request.query_params.get("from")
        to_str = request.query_params.get("to")

        date_from = self.parse_date(from_str, "from")
        date_to = self.parse_date(to_str, "to")

        data = get_quotes_vs_invoices(
            org=org,
            date_from=date_from,
            date_to=date_to,
        )

        return Response(data)


class MarginsView(BaseAnalyticsView):
    @require_plan("pro")
    def get(self, request, *args, **kwargs):
        org = self.get_org(request)
        group_by = request.query_params.get("group_by", "product")
        dfrom = request.query_params.get("from")
        dto = request.query_params.get("to")
        return Response(get_margins(org, dfrom, dto, group_by))

class AgingReceivablesView(BaseAnalyticsView):
    def get(self, request, *args, **kwargs):
        org = self.get_org(request)
        as_of = request.query_params.get("as_of")
        return Response(get_aging_receivables(org, as_of))

class AgingPayablesView(BaseAnalyticsView):
    def get(self, request, *args, **kwargs):
        org = self.get_org(request)
        as_of = request.query_params.get("as_of")
        return Response(get_aging_payables(org, as_of))

class CashflowView(BaseAnalyticsView):
    @require_plan("pro")
    def get(self, request, *args, **kwargs):
        org = self.get_org(request)
        dfrom = request.query_params.get("from")
        dto = request.query_params.get("to")
        bucket = request.query_params.get("bucket", "day")
        return Response(get_cashflow(org, dfrom, dto, bucket))

class CustomersABCView(BaseAnalyticsView):
    @require_plan("pro")
    def get(self, request, *args, **kwargs):
        org = self.get_org(request)
        dfrom = request.query_params.get("from")
        dto = request.query_params.get("to")
        rule = request.query_params.get("rule", "80-15-5")
        return Response(get_customers_abc(org, dfrom, dto, rule))

class CohortsView(BaseAnalyticsView):
    @require_plan("pro")
    def get(self, request, *args, **kwargs):
        org = self.get_org(request)
        months = int(request.query_params.get("months", "6"))
        return Response(get_cohorts(org, months))

class TopProductsView(BaseAnalyticsView):
    def get(self, request, *args, **kwargs):
        org = self.get_org(request)
        dfrom = request.query_params.get("from")
        dto = request.query_params.get("to")
        by = request.query_params.get("by", "revenue")
        limit = int(request.query_params.get("limit", "10"))
        return Response(get_top_products(org, dfrom, dto, by, limit))