from django.shortcuts import render
from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from accounts.serializers import RegisterSerializer, LoginSerializer, TenantAwareTokenObtainPairSerializer
from rest_framework.throttling import ScopedRateThrottle


REFRESH_COOKIE_NAME = getattr(settings, "REFRESH_COOKIE_NAME", "refresh_token")
COOKIE_KW = dict(
    httponly=True,
    samesite=getattr(settings, "REFRESH_COOKIE_SAMESITE", "Lax"),
    secure=getattr(settings, "REFRESH_COOKIE_SECURE", False),
    path=getattr(settings, "REFRESH_COOKIE_PATH", "/"),
)

class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        ser = RegisterSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        user = ser.save()
        return Response({"ok": True, "user": {"email": user.email}}, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        # Reutilizamos lógica de TokenObtain pero controlamos cookie
        token_ser = TenantAwareTokenObtainPairSerializer(data=request.data, context={"request": request})
        token_ser.is_valid(raise_exception=True)
        refresh = RefreshToken.for_user(token_ser.user)
        resp = Response(token_ser.validated_data, status=200)
        resp.set_cookie(REFRESH_COOKIE_NAME, str(refresh), **COOKIE_KW)
        return resp

class RefreshCookieView(APIView):
    """
    Lee el refresh desde la cookie HttpOnly y devuelve un nuevo access.
    No muta request.data; usa un dict local.
    """
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request, *args, **kwargs):
        # Copia segura del payload (puede ser dict o QueryDict)
        try:
            data = request.data.copy()
        except AttributeError:
            data = dict(request.data or {})

        if REFRESH_COOKIE_NAME in request.COOKIES and "refresh" not in data:
            data["refresh"] = request.COOKIES[REFRESH_COOKIE_NAME]

        # Si seguimos sin refresh, devolvemos 401 claro
        if "refresh" not in data or not data["refresh"]:
            return Response(
                {"detail": "Falta refresh token (cookie no encontrada). Haz login primero."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        ser = TokenRefreshSerializer(data=data)
        ser.is_valid(raise_exception=True)
        return Response(ser.validated_data, status=status.HTTP_200_OK)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        resp = Response({"ok": True}, status=200)
        resp.delete_cookie(REFRESH_COOKIE_NAME, path=COOKIE_KW["path"])
        return resp

class MeView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        # listamos orgs y roles
        from core.models import Membership
        mems = Membership.objects.select_related("organization").filter(user=user)
        orgs = [
            {
                "id": str(m.organization.id),
                "name": m.organization.name,
                "slug": m.organization.slug,
                "role": m.role,
                "trial_active": m.organization.is_trial_active,
                "trial_ends_at": m.organization.trial_ends_at,
            }
            for m in mems
        ]
        return Response({
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "organizations": orgs,
        })
