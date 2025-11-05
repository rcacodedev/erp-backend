# inventory/signals.py
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from core.models import Organization
from .models import Warehouse

@receiver(post_migrate)
def ensure_primary_warehouse(sender, **kwargs):
    if sender.label != "inventory":
        return
    for org in Organization.objects.all():
        if not Warehouse.objects.filter(org=org).exists():
            Warehouse.objects.create(org=org, code="MAIN", name="Principal", is_primary=True)
