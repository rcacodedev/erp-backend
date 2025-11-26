from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from core.models import UserPreference, OrganizationEmailSettings
from core.serializers import KpisPrefsSerializer, OrganizationEmailSettingsSerializer
from core.email_utils import send_org_email



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

class OrgEmailSettingsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, org_slug: str):
        org = getattr(request, "org", None)
        if not org or org.slug != org_slug:
            return Response({"detail": "Organización no válida"}, status=status.HTTP_400_BAD_REQUEST)

        settings_obj, _ = OrganizationEmailSettings.objects.get_or_create(
            organization=org,
            defaults={"from_name": "PREATOR"},
        )
        data = OrganizationEmailSettingsSerializer(settings_obj).data
        data["default_from_email"] = settings.DEFAULT_FROM_EMAIL
        data["support_email"] = settings.SUPPORT_EMAIL
        data["billing_email"] = settings.BILLING_EMAIL
        return Response(data)

    def put(self, request, org_slug: str):
        org = getattr(request, "org", None)
        if not org or org.slug != org_slug:
            return Response({"detail": "Organización no válida"}, status=status.HTTP_400_BAD_REQUEST)

        settings_obj, _ = OrganizationEmailSettings.objects.get_or_create(
            organization=org,
            defaults={"from_name": "PREATOR"},
        )
        serializer = OrganizationEmailSettingsSerializer(settings_obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class OrgEmailTestView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, org_slug: str):
        org = getattr(request, "org", None)
        if not org or org.slug != org_slug:
            return Response({"detail": "Organización no válida"}, status=status.HTTP_400_BAD_REQUEST)

        user_email = request.user.email
        if not user_email:
            return Response(
                {"detail": "El usuario no tiene email configurado"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            send_org_email(
                organization=org,
                to_emails=[user_email],
                subject="[PREATOR] Correo de prueba de organización",
                template_base_name="emails/org_email_test",
                context={"user": request.user},
            )
        except Exception as e:
            return Response({"success": False, "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({"success": True})
