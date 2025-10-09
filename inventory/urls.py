from django.urls import path
from django.http import JsonResponse

def health(_request):
    return JsonResponse({"app": "inventory", "status": "ok"})

urlpatterns = [
    path("health/", health, name="inventory-health"),
]
