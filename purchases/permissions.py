# purchases/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS
from core.models import Membership

ALLOWED_WRITE_ROLES = {"owner", "admin", "manager"}


class CanManagePurchases(BasePermission):
    """
    Permite escritura en Compras sólo a owner/admin/manager de la org.
    Lectura: cualquier miembro autenticado de esa org.
    (El chequeo de org viene por request.org desde TenantMiddleware).
    """
    def has_permission(self, request, view):
        org = getattr(request, "org", None)
        user = getattr(request, "user", None)

        if not user or not user.is_authenticated or not org:
            return False

        if request.method in SAFE_METHODS:
            # lectura: basta ser miembro
            return Membership.objects.filter(organization=org, user=user).exists()

        # escritura: rol elevado
        return Membership.objects.filter(
            organization=org,
            user=user,
            role__in=ALLOWED_WRITE_ROLES,
        ).exists()
