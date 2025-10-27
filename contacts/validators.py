import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


_IBAN_RE = re.compile(r"^[A-Z]{2}\d{2}[A-Z0-9]{1,30}$")
_PHONE_RE = re.compile(r"^[+]?\d[\d\s\-]{6,20}$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_NIF_RE = re.compile(r"^[0-9A-Z]{8,10}$") # Simplificado (NIF/CIF/NIE)




def validate_email_basic(value: str):
    if value and not _EMAIL_RE.match(value):
        raise ValidationError(_("Email no válido"))




def validate_phone_basic(value: str):
    if value and not _PHONE_RE.match(value):
        raise ValidationError(_("Teléfono no válido"))




def validate_iban_basic(value: str):
    if value and not _IBAN_RE.match(value.replace(" ", "").upper()):
        raise ValidationError(_("IBAN no válido"))




def validate_id_document_basic(value: str):
    if value and not _NIF_RE.match(value.upper()):
        raise ValidationError(_("Documento identificativo no válido"))