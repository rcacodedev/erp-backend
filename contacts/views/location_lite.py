from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from contacts.models import LocationLite
from contacts.serializers.location_lite import LocationLiteSerializer
from .mixins import OrgScopedViewSet

class LocationLiteViewSet(OrgScopedViewSet, viewsets.ModelViewSet):
    queryset = LocationLite.objects.all()
    serializer_class = LocationLiteSerializer
    permission_classes = (IsAuthenticated,)
