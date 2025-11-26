# integrations/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import WebhookEndpointViewSet, WebhookDeliveryListView

router = DefaultRouter()
router.register("webhooks", WebhookEndpointViewSet, basename="webhook-endpoint")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "webhooks/<int:endpoint_id>/logs/",
        WebhookDeliveryListView.as_view(),
        name="webhook-delivery-list",
    ),
]
