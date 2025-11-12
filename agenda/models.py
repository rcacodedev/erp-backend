from django.db import models
from django.utils import timezone
from core.models import Organization
from contacts.models import Contact
from sales.models import Invoice
from django.conf import settings

HEX_COLOR_MAXLEN = 9  # admite #RRGGBB o #RRGGBBAA si alguna vez quieres alpha

class Event(models.Model):
    """Cita de agenda (agenda semanal/mes)."""
    org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="events")
    title = models.CharField(max_length=200)
    start = models.DateTimeField()
    end = models.DateTimeField(null=True, blank=True)
    all_day = models.BooleanField(default=False)

    # Visual y prioridad
    color = models.CharField(max_length=HEX_COLOR_MAXLEN, blank=True, default="")  # ej. "#2563eb"
    is_important = models.BooleanField(default=False)

    # Relaciones opcionales
    contact = models.ForeignKey(Contact, null=True, blank=True, on_delete=models.SET_NULL)
    invoice = models.ForeignKey(Invoice, null=True, blank=True, on_delete=models.SET_NULL)

    location = models.CharField(max_length=200, blank=True, default="")
    notes = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=20,
        choices=[("scheduled","Scheduled"), ("done","Done"), ("cancelled","Cancelled")],
        default="scheduled"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["org","start","end"]),
            models.Index(fields=["org","is_important"]),
            models.Index(fields=["org","contact","start"]),   # NUEVO
        ]
        ordering = ["start"]

class Note(models.Model):
    """Nota / tarea ligera (noteList) que puede integrarse a la agenda por fecha."""
    org = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="notes")
    title = models.CharField(max_length=240)
    body = models.TextField(blank=True, default="")
    # Si es tarea, podemos marcar estado done/pending
    is_task = models.BooleanField(default=False)
    status = models.CharField(
        max_length=16,
        choices=[("pending","Pending"), ("done","Done"), ("cancelled","Cancelled")],
        default="pending"
    )
    # Fecha objetivo opcional para aparecer en agenda
    due_date = models.DateField(null=True, blank=True)

    # Visual y prioridad
    color = models.CharField(max_length=HEX_COLOR_MAXLEN, blank=True, default="")
    is_important = models.BooleanField(default=False)
    is_pinned = models.BooleanField(default=False)  # para la banda superior de avisos

    # Relaciones opcionales
    contact = models.ForeignKey(Contact, null=True, blank=True, on_delete=models.SET_NULL)
    invoice = models.ForeignKey(Invoice, null=True, blank=True, on_delete=models.SET_NULL)

    # Notas Privadas
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notes", blank=True, null=True)
    visibility = models.CharField(
        max_length=12,
        choices=[("private","Private"), ("org","Organization")],
        default="org"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["org","due_date"]),
            models.Index(fields=["org","is_important"]),
            models.Index(fields=["org","is_pinned"]),
            models.Index(fields=["org","contact","due_date"]),  # NUEVO
        ]
        ordering = ["-is_pinned","due_date","-created_at"]
