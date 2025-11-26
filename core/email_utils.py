# --- FILE: core/email_utils.py
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from core.models import OrganizationEmailSettings, Organization


def get_org_email_settings(org: Organization) -> OrganizationEmailSettings | None:
    try:
        return org.email_settings
    except OrganizationEmailSettings.DoesNotExist:
        return None


def send_org_email(
    organization: Organization,
    to_emails,
    subject: str,
    template_base_name: str,
    context: dict | None = None,
    reply_to: str | None = None,
):
    """
    template_base_name: ej. "emails/org_email_test" → buscará
    - templates/emails/org_email_test.txt
    - templates/emails/org_email_test.html
    """
    context = context or {}
    context["organization"] = organization

    text_body = render_to_string(f"{template_base_name}.txt", context)
    try:
        html_body = render_to_string(f"{template_base_name}.html", context)
    except Exception:
        html_body = None

    email_settings = get_org_email_settings(organization)
    if email_settings:
        from_email = email_settings.get_from_address()
        bcc = [email_settings.bcc_on_outgoing] if email_settings.bcc_on_outgoing else None
    else:
        from_email = getattr(settings, "DEFAULT_FROM_EMAIL", "no-reply@preator.es")
        bcc = None

    reply_to_list = []
    if reply_to:
        reply_to_list.append(reply_to)
    elif email_settings and email_settings.reply_to_email:
        reply_to_list.append(email_settings.reply_to_email)

    to_list = to_emails if isinstance(to_emails, (list, tuple)) else [to_emails]

    msg = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=from_email,
        to=to_list,
        reply_to=reply_to_list or None,
        bcc=bcc,
    )

    if html_body:
        msg.attach_alternative(html_body, "text/html")

    return msg.send()
