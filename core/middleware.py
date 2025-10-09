from typing import Optional
from django.utils.deprecation import MiddlewareMixin
from django.db import connection
from django.http import HttpRequest
from core.models import Organization

PG_SETTING = "app.current_org"  # debe cuadrar con .env si lo parametrizas

def resolve_org_from_path(path: str) -> Optional[str]:
    # Esperamos rutas tipo /api/v1/t/{org_slug}/...
    parts = [p for p in path.split("/") if p]
    try:
        idx = parts.index("t")
        return parts[idx + 1]
    except Exception:
        return None

class TenantMiddleware(MiddlewareMixin):
    def process_request(self, request: HttpRequest):
        org_slug = resolve_org_from_path(request.path)
        request.org = None
        if org_slug:
            try:
                org = Organization.objects.only("id","slug").get(slug=org_slug)
                request.org = org
                with connection.cursor() as c:
                    c.execute("SET LOCAL {} = %s".format(PG_SETTING), [str(org.id)])
            except Organization.DoesNotExist:
                pass
