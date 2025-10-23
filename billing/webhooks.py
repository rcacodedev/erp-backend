import datetime
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .stripe_utils import stripe
from .models import Subscription, BillingPlan

def _plan_from_price(price_id: str):
    if price_id == settings.STRIPE_PRICE_STARTER: return BillingPlan.STARTER
    if price_id == settings.STRIPE_PRICE_PRO: return BillingPlan.PRO
    if price_id == settings.STRIPE_PRICE_ENTERPRISE: return BillingPlan.ENTERPRISE
    return None

@csrf_exempt
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
    except Exception:
        return HttpResponse(status=400)

    t = event["type"]
    obj = event["data"]["object"]

    if t == "checkout.session.completed":
        customer_id = obj.get("customer")
        subscription_id = obj.get("subscription")
        md = obj.get("metadata") or {}
        org_id = md.get("organization_id")
        plan_code = md.get("plan_code")
        if all([customer_id, subscription_id, org_id]):
            sub = Subscription.objects.filter(organization_id=org_id).first()
            if sub:
                sub.stripe_customer_id = customer_id
                sub.stripe_subscription_id = subscription_id
                if plan_code in {"starter","pro","enterprise"}:
                    sub.current_plan = plan_code
                sub.status = "active"
                sub.save()

    elif t in {"customer.subscription.created","customer.subscription.updated","customer.subscription.deleted"}:
        sub_id = obj.get("id")
        status = obj.get("status")
        cpe = obj.get("current_period_end")
        cancel = obj.get("cancel_at_period_end", False)
        items = obj.get("items", {}).get("data", [])
        price_id = items[0].get("price", {}).get("id") if items else None

        rec = Subscription.objects.filter(stripe_subscription_id=sub_id).first()
        if rec:
            plan = _plan_from_price(price_id) or rec.current_plan
            rec.current_plan = plan
            rec.status = status or rec.status
            if cpe:
                rec.current_period_end = datetime.datetime.utcfromtimestamp(cpe).replace(tzinfo=datetime.timezone.utc)
            rec.cancel_at_period_end = bool(cancel)
            rec.save()

    elif t == "invoice.payment_failed":
        # Aquí puedes marcar flags o notificar
        pass

    return HttpResponse(status=200)
