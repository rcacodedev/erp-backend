from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from contacts.models import EmployeeCompensation
from contacts.serializers.compensation import EmployeeCompensationSerializer
from .mixins import OrgScopedViewSet

class EmployeeCompensationViewSet(OrgScopedViewSet, viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = EmployeeCompensationSerializer
    queryset = EmployeeCompensation.objects.all()

    def get_queryset(self):
        return super().get_queryset().filter(contact_id=self.kwargs['contact_pk'])
