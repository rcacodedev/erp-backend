from django.db import models


class WebhookEndpoint(models.Model):
    EVENT_INVOICE_CREATED = "invoice.created"
    EVENT_INVOICE_PAID = "invoice.paid"
    EVENT_CLIENT_CREATED = "client.created"

    EVENT_CHOICES = [
        (EVENT_INVOICE_CREATED, "Factura creada"),
        (EVENT_INVOICE_PAID, "Factura cobrada"),
        (EVENT_CLIENT_CREATED, "Cliente creado"),
    ]

    organization = models.ForeignKey(
        "core.Organization",
        on_delete=models.CASCADE,
        related_name="webhook_endpoints",
    )
    name = models.CharField(max_length=200)
    target_url = models.URLField()
    event = models.CharField(max_length=50, choices=EVENT_CHOICES)
    secret = models.CharField(
        max_length=255,
        blank=True,
        help_text="Se usará para firmar la cabecera X-Preator-Signature",
    )
    is_active = models.BooleanField(default=True)

    last_status = models.CharField(
        max_length=20,
        blank=True,
        help_text="success / error / pending",
    )
    last_status_code = models.IntegerField(null=True, blank=True)
    last_error = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Webhook endpoint"
        verbose_name_plural = "Webhook endpoints"

    def __str__(self):
        return f"{self.organization.slug} → {self.event} @ {self.target_url}"


class WebhookDelivery(models.Model):
    STATUS_PENDING = "pending"
    STATUS_SUCCESS = "success"
    STATUS_ERROR = "error"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_SUCCESS, "Success"),
        (STATUS_ERROR, "Error"),
    ]

    endpoint = models.ForeignKey(
        WebhookEndpoint,
        on_delete=models.CASCADE,
        related_name="deliveries",
    )
    event_name = models.CharField(max_length=50)
    payload = models.JSONField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    attempt_count = models.PositiveIntegerField(default=0)
    last_status_code = models.IntegerField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    response_body = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_attempt_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.event_name} → {self.endpoint.target_url} ({self.status})"
