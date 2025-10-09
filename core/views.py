from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

class PingTenantView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, org_slug: str):
        if not getattr(request, "org", None) or request.org.slug != org_slug:
            return Response({"detail": "Organización no válida"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "ok": True,
            "org": {"id": str(request.org.id), "slug": request.org.slug, "trial_active": request.org.is_trial_active}
        })
