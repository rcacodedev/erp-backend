# integrations/views.py
from rest_framework import viewsets, generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound

from .models import WebhookEndpoint, WebhookDelivery
from .serializers import WebhookEndpointSerializer, WebhookDeliverySerializer
from .permissions import CanManageIntegrations


class WebhookEndpointViewSet(viewsets.ModelViewSet):
    """
    CRUD de endpoints de webhook para la organización actual.
    """
    serializer_class = WebhookEndpointSerializer
    permission_classes = (IsAuthenticated, CanManageIntegrations)

    def get_queryset(self):
        org = getattr(self.request, "org", None)
        if not org:
            return WebhookEndpoint.objects.none()
        return WebhookEndpoint.objects.filter(organization=org).order_by("id")

    def perform_create(self, serializer):
        org = getattr(self.request, "org", None)
        if not org:
            raise NotFound("Organización no encontrada")
        serializer.save(organization=org)

    def perform_update(self, serializer):
        org = getattr(self.request, "org", None)
        if not org:
            raise NotFound("Organización no encontrada")
        serializer.save(organization=org)


class WebhookDeliveryListView(generics.ListAPIView):
    """
    Lista de entregas (logs) para un endpoint concreto de la organización.
    """
    serializer_class = WebhookDeliverySerializer
    permission_classes = (IsAuthenticated, CanManageIntegrations)

    def get_queryset(self):
        org = getattr(self.request, "org", None)
        endpoint_id = self.kwargs.get("endpoint_id")
        if not org:
            return WebhookDelivery.objects.none()

        return WebhookDelivery.objects.filter(
            endpoint__organization=org,
            endpoint_id=endpoint_id,
        ).order_by("-created_at")
