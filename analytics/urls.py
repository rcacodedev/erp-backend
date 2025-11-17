# analytics/urls.py
from django.urls import path
from .views import health, YearlySummaryView, SalesTimeseriesView, ExpensesTimeseriesView, ReceivablesView, VatSummaryView, TopCustomersView, QuotesVsInvoicesView

urlpatterns = [
    path("health/", health, name="analytics-health"),
    path("yearly-summary/", YearlySummaryView.as_view(), name="analytics-yearly-summary"),
    path("sales-timeseries/", SalesTimeseriesView.as_view(), name="analytics-sales-timeseries"),
    path("expenses-timeseries/", ExpensesTimeseriesView.as_view(), name="analytics-expenses-timeseries"),
    path("receivables/", ReceivablesView.as_view(), name="analytics-receivables"),
    path("vat/", VatSummaryView.as_view(), name="analytics-vat"),
    path("top-customers/", TopCustomersView.as_view(), name="analytics-top-customers"),
    path("quotes-vs-invoices/", QuotesVsInvoicesView.as_view(), name="analytics-quotes-vs-invoices"),
]

