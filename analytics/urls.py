# analytics/urls.py
from django.urls import path
from .views import (
    health, YearlySummaryView, SalesTimeseriesView, ExpensesTimeseriesView,
    ReceivablesView, VatSummaryView, TopCustomersView, QuotesVsInvoicesView,
    MarginsView, AgingReceivablesView, AgingPayablesView,
    CashflowView, CustomersABCView, CohortsView, TopProductsView,
)

urlpatterns = [
    path("health/", health, name="analytics-health"),
    path("yearly-summary/", YearlySummaryView.as_view(), name="analytics-yearly-summary"),
    path("sales-timeseries/", SalesTimeseriesView.as_view(), name="analytics-sales-timeseries"),
    path("expenses-timeseries/", ExpensesTimeseriesView.as_view(), name="analytics-expenses-timeseries"),
    path("receivables/", ReceivablesView.as_view(), name="analytics-receivables"),
    path("vat/", VatSummaryView.as_view(), name="analytics-vat"),
    path("top-customers/", TopCustomersView.as_view(), name="analytics-top-customers"),
    path("quotes-vs-invoices/", QuotesVsInvoicesView.as_view(), name="analytics-quotes-vs-invoices"),
    # --- F7 PRO ---
    path("margins/", MarginsView.as_view(), name="analytics-margins"),
    path("aging/receivables/", AgingReceivablesView.as_view(), name="analytics-aging-receivables"),
    path("aging/payables/", AgingPayablesView.as_view(), name="analytics-aging-payables"),
    path("cashflow/", CashflowView.as_view(), name="analytics-cashflow"),
    path("customers/abc/", CustomersABCView.as_view(), name="analytics-customers-abc"),
    path("customers/cohorts/", CohortsView.as_view(), name="analytics-customers-cohorts"),
    path("products/top/", TopProductsView.as_view(), name="analytics-products-top"),
]
