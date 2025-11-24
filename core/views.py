from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import UserPreference
from .serializers import KpisPrefsSerializer

class PingTenantView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, org_slug: str):
        if not getattr(request, "org", None) or request.org.slug != org_slug:
            return Response({"detail": "Organización no válida"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "ok": True,
            "org": {"id": str(request.org.id), "slug": request.org.slug, "trial_active": request.org.is_trial_active}
        })

class MeKpisPrefsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        pref, _ = UserPreference.objects.get_or_create(
            user=request.user, key="kpis", defaults={"value": {}}
        )
        # Defaults por si vienen vacías
        value = {
            "rangePreset": "current_year",
            "groupBy": "category",
            "bucket": "month",
            "topBy": "revenue",
            **(pref.value or {}),
        }
        return Response(value)

    def put(self, request):
        serializer = KpisPrefsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pref, _ = UserPreference.objects.get_or_create(
            user=request.user, key="kpis", defaults={"value": {}}
        )
        pref.value = serializer.validated_data
        pref.save(update_fields=["value", "updated_at"])
        return Response(pref.value)