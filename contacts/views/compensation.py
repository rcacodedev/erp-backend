# contacts/views/compensation.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from contacts.models import EmployeeCompensation
from contacts.serializers.compensation import EmployeeCompensationSerializer
from .mixins import OrgScopedViewSet

class EmployeeCompensationViewSet(OrgScopedViewSet, viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = EmployeeCompensationSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ("inicio", "fin")  # añade los que te interesen

    def get_queryset(self):
        # ⚠️ No llamamos a super(): este modelo no tiene 'org'
        return (
            EmployeeCompensation.objects
            .select_related("contact")
            .filter(
                contact_id=self.kwargs["contact_pk"],
                contact__org=self.get_org(),
            )
            .order_by("-inicio", "-id")
        )

    def perform_create(self, serializer):
        # ⚠️ No pasar 'org'
        serializer.save(
            contact_id=self.kwargs["contact_pk"],
            created_by=self.request.user,
            updated_by=self.request.user,
        )

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
