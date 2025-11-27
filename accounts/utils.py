# accounts/utils.py
import secrets
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import EmailVerificationToken, PasswordResetToken


# ========= VERIFICACIÓN DE EMAIL =========

def create_email_verification_token(user):
    """
    Crea un nuevo token de verificación para el usuario.
    Invalida tokens anteriores no usados.
    """
    EmailVerificationToken.objects.filter(user=user, is_used=False).update(
        is_used=True, used_at=timezone.now()
    )

    token = secrets.token_urlsafe(32)  # ~43 chars, ok para max_length=64
    evt = EmailVerificationToken.objects.create(user=user, token=token)
    return evt


def build_verification_url(token: str) -> str:
    """
    Construye la URL que usará el frontend. Ej: https://app.preator.es/verify-email?token=...
    """
    base = getattr(settings, "FRONTEND_BASE_URL", "http://localhost:5173")
    return f"{base.rstrip('/')}/verify-email?token={token}"


def send_verification_email(user):
    """
    Envía el email de verificación al usuario.
    No lanza excepciones hacia fuera: si falla, devuelve False.
    """
    if not user.email:
        return False

    evt = create_email_verification_token(user)
    verify_url = build_verification_url(evt.token)

    subject = "Verifica tu correo en PREATOR"
    message = (
        "Hola,\n\n"
        "Gracias por registrarte en PREATOR.\n\n"
        "Para confirmar tu dirección de correo, haz clic en el siguiente enlace:\n\n"
        f"{verify_url}\n\n"
        "Si no has creado esta cuenta, puedes ignorar este mensaje.\n\n"
        "Un saludo,\n"
        "El equipo de PREATOR"
    )

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@preator.es")

    try:
        sent = send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[user.email],
            fail_silently=True,
        )
        return bool(sent)
    except Exception:
        return False


# ========= RESET DE CONTRASEÑA =========

def create_password_reset_token(user):
    """
    Crea un nuevo token de reset de contraseña.
    Opcional: invalidar tokens antiguos no usados.
    """
    PasswordResetToken.objects.filter(user=user, is_used=False).update(
        is_used=True, used_at=timezone.now()
    )

    token = secrets.token_urlsafe(32)
    prt = PasswordResetToken.objects.create(user=user, token=token)
    return prt


def build_password_reset_url(token: str) -> str:
    """
    URL que usará el frontend. Ej: https://app.preator.es/reset-password?token=...
    """
    base = getattr(settings, "FRONTEND_BASE_URL", "http://localhost:5173")
    return f"{base.rstrip('/')}/reset-password?token={token}"


def send_password_reset_email(user):
    """
    Envía email con enlace para restablecer contraseña.
    No revela si el email existe o no al usuario final.
    """
    if not user.email or not user.is_active:
        return False

    prt = create_password_reset_token(user)
    reset_url = build_password_reset_url(prt.token)

    subject = "Restablece tu contraseña en PREATOR"
    message = (
        "Hola,\n\n"
        "Hemos recibido una solicitud para restablecer la contraseña de tu cuenta en PREATOR.\n\n"
        "Si has sido tú, usa este enlace para establecer una nueva contraseña:\n\n"
        f"{reset_url}\n\n"
        "Si no has solicitado este cambio, puedes ignorar este mensaje.\n\n"
        "Un saludo,\n"
        "El equipo de PREATOR"
    )

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@preator.es")

    try:
        sent = send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[user.email],
            fail_silently=True,
        )
        return bool(sent)
    except Exception:
        return False

def send_password_changed_notification(user):
    """
    Envía un email avisando de que la contraseña se ha cambiado.
    Ideal para detectar cambios no autorizados.
    """
    if not user.email:
        return False

    subject = "Tu contraseña de PREATOR se ha cambiado"
    message = (
        "Hola,\n\n"
        "Te informamos de que la contraseña de tu cuenta en PREATOR se ha cambiado.\n\n"
        "Si has sido tú, no tienes que hacer nada más.\n"
        "Si NO has sido tú, cambia la contraseña de inmediato y contacta con tu gestor o con soporte.\n\n"
        "Un saludo,\n"
        "El equipo de PREATOR"
    )

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@preator.es")

    try:
        sent = send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[user.email],
            fail_silently=True,
        )
        return bool(sent)
    except Exception:
        return False


def send_email_changed_notification(old_email: str, new_email: str):
    """
    Helper preparado para cuando implementemos cambio de email en la cuenta.
    De momento no se usa, pero lo dejamos listo.
    """
    if not old_email:
        return False

    subject = "Tu email de acceso a PREATOR ha cambiado"
    message = (
        "Hola,\n\n"
        "Te informamos de que el email asociado a tu cuenta de PREATOR se ha cambiado.\n\n"
        f"Email anterior: {old_email}\n"
        f"Nuevo email: {new_email}\n\n"
        "Si no reconoces este cambio, contacta con soporte lo antes posible.\n\n"
        "Un saludo,\n"
        "El equipo de PREATOR"
    )

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@preator.es")

    try:
        sent = send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[old_email],
            fail_silently=True,
        )
        return bool(sent)
    except Exception:
        return False
