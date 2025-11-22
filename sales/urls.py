from django.urls import path, include
from django.http import JsonResponse
from rest_framework.routers import DefaultRouter

from .views import (
    DeliveryNoteViewSet,
    InvoiceViewSet,
    PaymentViewSet,
    QuoteViewSet,
    InvoicePrintView,
    SalesKPIsViewSet,
)

router = DefaultRouter()
router.register(r"delivery-notes", DeliveryNoteViewSet, basename="sales-dn")
router.register(r"invoices", InvoiceViewSet, basename="sales-inv")
router.register(r"payments", PaymentViewSet, basename="sales-pay")
router.register(r"quotes", QuoteViewSet, basename="sales-quote")
router.register(r'kpis', SalesKPIsViewSet, basename='sales-kpis')


def health(_request):
    return JsonResponse({"app": "sales", "status": "ok"})

urlpatterns = [
    path("health/", health, name="sales-health"),

    # Vista imprimible de factura (HTML)
    path(
        "invoices/<int:pk>/print/",
        InvoicePrintView.as_view(),
        name="invoice-print",
    ),

    path("", include(router.urls)),
]

