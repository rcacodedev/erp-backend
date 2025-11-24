import uuid
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator
from django.conf import settings

slug_validator = RegexValidator(
    regex=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    message="Solo minúsculas, números y guiones medios; no empezar/terminar por '-'"
)

class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True

class Organization(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True, validators=[slug_validator], max_length=40)

    # Free trial
    trial_starts_at = models.DateTimeField(default=timezone.now)
    trial_ends_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.trial_ends_at:
            self.trial_ends_at = timezone.now() + timezone.timedelta(days=7)
        super().save(*args, **kwargs)

    @property
    def is_trial_active(self) -> bool:
        return timezone.now() < self.trial_ends_at

    def __str__(self):
        return f"{self.name} ({self.slug})"

ROLE_CHOICES = [
    ("owner","Owner"),
    ("admin","Admin"),
    ("manager","Manager"),
    ("member","Member"),
    ("viewer","Viewer"),
]

class Membership(TimeStampedModel):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey("accounts.User", on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=16, choices=ROLE_CHOICES, default="member")

    class Meta:
        unique_together = [("organization","user")]

class UserPreference(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="preferences")
    key = models.CharField(max_length=100)  # ej.: "kpis"
    value = models.JSONField(default=dict, blank=True)  # {"rangePreset": "...", ...}
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "key")

    def __str__(self):
        return f"{self.user_id}:{self.key}"