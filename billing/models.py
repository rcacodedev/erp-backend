from django.db import models

class BillingPlan(models.TextChoices):
    STARTER = "starter", "Starter"
    PRO = "pro", "Pro"
    ENTERPRISE = "enterprise", "Enterprise"
    NONE = "none", "None"

class Subscription(models.Model):
    organization = models.OneToOneField("core.Organization", on_delete=models.CASCADE, related_name="subscription")
    stripe_customer_id = models.CharField(max_length=64, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=64, blank=True, null=True)
    current_plan = models.CharField(max_length=32, choices=BillingPlan.choices, default=BillingPlan.NONE)
    status = models.CharField(max_length=32, default="inactive")  # active, trialing, past_due, canceled, etc.
    current_period_end = models.DateTimeField(blank=True, null=True)
    cancel_at_period_end = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def is_active(self) -> bool:
        return self.status in {"active", "trialing", "past_due"}
