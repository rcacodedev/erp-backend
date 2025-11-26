# integrations/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS
from core.models import Membership

ALLOWED_WRITE_ROLES = {"owner", "admin", "manager"}


class CanManageIntegrations(BasePermission):
    """
    Lectura: cualquier miembro de la org.
    Escritura: sólo owner / admin / manager.
    """
    def has_permission(self, request, view):
        org = getattr(request, "org", None)
        user = getattr(request, "user", None)

        if not user or not user.is_authenticated or not org:
            return False

        if request.method in SAFE_METHODS:
            return Membership.objects.filter(organization=org, user=user).exists()

        return Membership.objects.filter(
            organization=org,
            user=user,
            role__in=ALLOWED_WRITE_ROLES,
        ).exists()
