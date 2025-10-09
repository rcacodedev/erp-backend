import uuid
from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator

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
