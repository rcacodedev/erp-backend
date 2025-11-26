# integrations/utils.py
import os          # 👈 nuevo
import json
import hmac
import hashlib
from django.utils import timezone
from django.conf import settings   # 👈 nuevo
from django_rq import enqueue

from .models import WebhookEndpoint, WebhookDelivery


def trigger_webhook_event(org, event_name: str, payload: dict):
    """
    Crea entregas de webhook para todos los endpoints activos
    de la organización que escuchen ese evento y las procesa
    vía RQ o en modo síncrono (según entorno).
    """
    endpoints = WebhookEndpoint.objects.filter(
        organization=org,
        is_active=True,
        event=event_name,
    )

    deliveries = []
    for ep in endpoints:
        delivery = WebhookDelivery.objects.create(
            endpoint=ep,
            event_name=event_name,
            payload=payload,
        )
        deliveries.append(delivery)

        # 🔹 En dev sobre Windows (os.name == "nt"), lo hacemos síncrono:
        if settings.DEBUG and os.name == "nt":
            # Ejecutar en la misma petición, sin RQ
            process_webhook_delivery(delivery.id)
        else:
            # Producción / Linux: encolar en RQ
            enqueue(process_webhook_delivery, delivery.id)

    return deliveries


def _make_signature(secret: str, body_bytes: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()


def process_webhook_delivery(delivery_id: int):
    """
    Job RQ: envía realmente la petición HTTP y actualiza el estado.
    """
    from .models import WebhookDelivery  # import local para evitar bucles

    # Import aquí para no forzar dependencia si no se usan webhooks
    import requests  # asegúrate de añadir 'requests' en requirements.txt

    try:
        delivery = WebhookDelivery.objects.select_related("endpoint").get(id=delivery_id)
    except WebhookDelivery.DoesNotExist:
        return

    endpoint = delivery.endpoint
    url = endpoint.target_url

    body_json = json.dumps(delivery.payload, ensure_ascii=False, default=str)
    body_bytes = body_json.encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "PREATOR-Webhook/1.0",
        "X-Preator-Event": delivery.event_name,
    }

    if endpoint.secret:
        sig = _make_signature(endpoint.secret, body_bytes)
        headers["X-Preator-Signature"] = sig

    delivery.attempt_count += 1
    delivery.last_attempt_at = timezone.now()

    try:
        resp = requests.post(
            url,
            data=body_bytes,
            headers=headers,
            timeout=10,
        )
        delivery.last_status_code = resp.status_code
        delivery.response_body = resp.text[:2000]

        if 200 <= resp.status_code < 300:
            delivery.status = WebhookDelivery.STATUS_SUCCESS
            delivery.last_error = ""
            endpoint.last_status = "success"
            endpoint.last_status_code = resp.status_code
            endpoint.last_error = ""
        else:
            delivery.status = WebhookDelivery.STATUS_ERROR
            delivery.last_error = f"HTTP {resp.status_code}"
            endpoint.last_status = "error"
            endpoint.last_status_code = resp.status_code
            endpoint.last_error = delivery.last_error

    except Exception as e:
        msg = str(e)[:2000]
        delivery.status = WebhookDelivery.STATUS_ERROR
        delivery.last_error = msg
        endpoint.last_status = "error"
        endpoint.last_error = msg

    endpoint.save(update_fields=["last_status", "last_status_code", "last_error"])
    delivery.save(
        update_fields=[
            "status",
            "attempt_count",
            "last_status_code",
            "last_error",
            "response_body",
            "last_attempt_at",
        ]
    )

    # (Opcional más adelante: reintentos si status == error y attempt_count < N)
