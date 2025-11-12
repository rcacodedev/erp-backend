from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from accounts.views import RegisterView, LoginView, RefreshCookieView, LogoutView, MeView
from billing.webhooks import stripe_webhook

urlpatterns = [
    path("admin/", admin.site.urls),

    # Docs
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/v1/docs/", SpectacularSwaggerView.as_view(url_name="schema")),

    # Rutas globales (sin tenant)
    path("api/v1/auth/register", RegisterView.as_view(), name="auth-register"),
    path("api/v1/auth/login", LoginView.as_view(), name="auth-login"),
    path("api/v1/auth/refresh", RefreshCookieView.as_view(), name="auth-refresh"),
    path("api/v1/auth/logout", LogoutView.as_view(), name="auth-logout"),
    path("api/v1/auth/me", MeView.as_view(), name="auth-me"),

    # Multi-tenant (todas las apps con org_slug)
    path("api/v1/t/<slug:org_slug>/core/", include("core.urls")),
    path("api/v1/t/<slug:org_slug>/billing/", include("billing.urls")),
    path("api/v1/t/<slug:org_slug>/contacts/", include("contacts.urls")),
    path("api/v1/t/<slug:org_slug>/inventory/", include("inventory.urls")),
    path("api/v1/t/<slug:org_slug>/sales/", include("sales.urls")),
    path("api/v1/t/<slug:org_slug>/purchases/", include("purchases.urls")),
    path("api/v1/t/<slug:org_slug>/analytics/", include("analytics.urls")),
    path("api/v1/t/<slug:org_slug>/agenda/", include("agenda.urls")),

    path("api/v1/billing/stripe/webhook/", stripe_webhook, name="stripe-webhook"),  # GLOBAL (sin slug)
]
