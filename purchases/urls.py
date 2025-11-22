# purchases/urls.py
from django.urls import path, include
from django.http import JsonResponse
from rest_framework.routers import DefaultRouter

from .views import PurchaseOrderViewSet, SupplierInvoiceViewSet, SupplierPaymentViewSet, PurchasesKPIsViewSet


def health(_request):
    return JsonResponse({"app": "purchases", "status": "ok"})


router = DefaultRouter()
router.register(r"orders", PurchaseOrderViewSet, basename="purchases-orders")
router.register(r"invoices", SupplierInvoiceViewSet, basename="purchases-invoices")
router.register(r"payments", SupplierPaymentViewSet, basename="purchases-payments")
router.register(r'kpis', PurchasesKPIsViewSet, basename='purchases-kpis')

urlpatterns = [
    path("health/", health, name="purchases-health"),
    path("", include(router.urls)),
]
