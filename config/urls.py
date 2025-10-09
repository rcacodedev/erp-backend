from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema")),
    path("api/core/", include("core.urls")),
    path("api/billing/", include("billing.urls")),
    path("api/contacts/", include("contacts.urls")),
    path("api/inventory/", include("inventory.urls")),
    path("api/sales/", include("sales.urls")),
    path("api/purchases/", include("purchases.urls")),
    path("api/analytics/", include("analytics.urls")),
]
