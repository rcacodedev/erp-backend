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
from django.utils import timezone

from .models import EmailVerificationToken, PasswordResetToken
from .utils import send_verification_email, send_password_reset_email, send_password_changed_notification



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

        # Intentamos enviar email de verificación (no rompe si falla)
        email_sent = send_verification_email(user)

        return Response(
            {
                "ok": True,
                "user": {
                    "email": user.email,
                    "email_verified": user.email_verified,
                },
                "verification_email_sent": email_sent,
            },
            status=status.HTTP_201_CREATED,
        )

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
            "email_verified": user.email_verified,
            "email_verified_at": user.email_verified_at,
            "organizations": orgs,
        })


class SendVerificationEmailView(APIView):
    """
    Reenvía email de verificación al usuario logueado.
    """
    permission_classes = [IsAuthenticated]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        user = request.user
        if user.email_verified:
            return Response(
                {"detail": "El email ya está verificado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        email_sent = send_verification_email(user)
        if not email_sent:
            return Response(
                {"detail": "No se ha podido enviar el email de verificación."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"detail": "Hemos enviado un email de verificación a tu correo."},
            status=status.HTTP_200_OK,
        )

class VerifyEmailView(APIView):
    """
    Verifica el email usando un token.
    El frontend puede llamar a este endpoint con { "token": "..." }.
    """
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        token = request.data.get("token")
        if not token:
            return Response(
                {"detail": "Falta token."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            evt = EmailVerificationToken.objects.select_related("user").get(
                token=token,
                is_used=False,
            )
        except EmailVerificationToken.DoesNotExist:
            return Response(
                {"detail": "Token inválido o ya utilizado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = evt.user
        # Marcamos token como usado y usuario como verificado
        evt.mark_used()

        if not user.email_verified:
            user.email_verified = True
            user.email_verified_at = timezone.now()
            user.save(update_fields=["email_verified", "email_verified_at"])

        return Response(
            {
                "detail": "Email verificado correctamente.",
                "email": user.email,
                "email_verified": user.email_verified,
            },
            status=status.HTTP_200_OK,
        )

class RequestPasswordResetView(APIView):
    """
    Solicita un email de reset de contraseña.
    No revela si el email existe o no (respuesta siempre genérica).
    """
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        email = request.data.get("email", "").strip().lower()
        if not email:
            return Response(
                {"detail": "Debes indicar un email."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from .models import User  # para evitar import circular si lo hubiera

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            user = None

        if user and user.is_active:
            # No nos importa si falla el envío, no se revela al cliente
            send_password_reset_email(user)

        # Respuesta genérica siempre
        return Response(
            {
                "detail": (
                    "Si existe una cuenta asociada a ese correo, "
                    "hemos enviado un email con instrucciones para restablecer la contraseña."
                )
            },
            status=status.HTTP_200_OK,
        )

class ResetPasswordView(APIView):
    """
    Restablece la contraseña usando un token y una nueva contraseña.
    Espera: { "token": "...", "new_password": "..." }
    """
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"

    def post(self, request):
        token = request.data.get("token")
        new_password = request.data.get("new_password")

        if not token or not new_password:
            return Response(
                {"detail": "Token y nueva contraseña son obligatorios."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            evt = PasswordResetToken.objects.select_related("user").get(
                token=token,
                is_used=False,
            )
        except PasswordResetToken.DoesNotExist:
            return Response(
                {"detail": "Token inválido o ya utilizado."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Comprobamos caducidad
        max_age_hours = getattr(settings, "PASSWORD_RESET_TOKEN_HOURS", 24)
        age = timezone.now() - evt.created_at
        if age.total_seconds() > max_age_hours * 3600:
            # Marcamos como usado/expirado
            evt.mark_used()
            return Response(
                {"detail": "El token ha caducado. Solicita un nuevo enlace."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = evt.user
        # Cambiamos contraseña
        user.set_password(new_password)
        user.save(update_fields=["password"])

        # Marcamos el token como usado
        evt.mark_used()

        # Aviso de seguridad: la contraseña se ha cambiado
        send_password_changed_notification(user)

        return Response(
            {"detail": "Contraseña actualizada correctamente."},
            status=status.HTTP_200_OK,
        )