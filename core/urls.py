from django.urls import path
from django.http import JsonResponse
from core.views import PingTenantView

def health(_request):
    return JsonResponse({"app": "core", "status": "ok"})

urlpatterns = [
    path("health/", health, name="core-health"),
    path("ping", PingTenantView.as_view(), name="core-ping"),
]
