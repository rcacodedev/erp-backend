from django.urls import path
from django.http import JsonResponse
from core.views import PingTenantView, MeKpisPrefsView

def health(_request):
    return JsonResponse({"app": "core", "status": "ok"})

urlpatterns = [
    path("health/", health, name="core-health"),
    path("ping", PingTenantView.as_view(), name="core-ping"),
    path("me/prefs/kpis/", MeKpisPrefsView.as_view(), name="me-kpis-prefs"),
]
