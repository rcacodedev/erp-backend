from rest_framework.permissions import BasePermission, SAFE_METHODS
from core.models import Membership

ALLOWED_WRITE_ROLES = {"owner", "admin", "manager"}

class IsOrgMember(BasePermission):
    """
    Requiere que el usuario esté autenticado y sea miembro de la org del path.
    """
    def has_permission(self, request, view):
        org = getattr(request, "org", None)
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated or not org:
            return False
        return Membership.objects.filter(organization=org, user=user).exists()

class CanManageContacts(BasePermission):
    """
    Permite escritura sólo a owner/admin/manager en esa org.
    Lectura para cualquier miembro.
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
            organization=org, user=user, role__in=ALLOWED_WRITE_ROLES
        ).exists()


class CanViewConfidentialDocs(BasePermission):
    def has_permission(self, request, view):
        return getattr(request.user, 'has_role', lambda *a, **k: False)(request.org, roles=("owner","admin",))