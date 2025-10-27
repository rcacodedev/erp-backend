from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from contacts.models import LocationRevenue
from contacts.serializers.location_revenue import LocationRevenueSerializer
from .mixins import OrgScopedViewSet

class LocationRevenueViewSet(OrgScopedViewSet, viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = LocationRevenueSerializer
    queryset = LocationRevenue.objects.select_related('location')
