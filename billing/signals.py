from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models import Organization
from .models import Subscription

@receiver(post_save, sender=Organization)
def create_subscription_for_org(sender, instance, created, **kwargs):
    if created:
        Subscription.objects.get_or_create(organization=instance)
