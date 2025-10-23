from rest_framework import permissions, views, status
from rest_framework.response import Response
from django.conf import settings
from .stripe_utils import stripe, get_price_id
from .models import Subscription, BillingPlan
from core.models import Organization  # ajusta si tu path es distinto

class BillingHealthView(views.APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request, org_slug: str, *args, **kwargs):
        return Response({"ok": True, "org_slug": org_slug})

class CreateCheckoutSessionView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, org_slug: str, *args, **kwargs):
        plan_code = request.data.get("plan")
        if plan_code not in {"starter","pro","enterprise"}:
            return Response({"detail":"Plan inválido"}, status=400)

        org = Organization.objects.get(slug=org_slug)
        # Solo el owner/admin debería suscribir (si tienes RBAC, valida aquí)
        sub, _ = Subscription.objects.get_or_create(organization=org)

        if not sub.stripe_customer_id:
            customer = stripe.Customer.create(
                email=request.user.email,
                metadata={"organization_id": str(org.id), "organization_slug": org.slug}
            )
            sub.stripe_customer_id = customer.id
            sub.save(update_fields=["stripe_customer_id"])

        session = stripe.checkout.Session.create(
            mode="subscription",
            customer=sub.stripe_customer_id,
            line_items=[{"price": get_price_id(plan_code), "quantity": 1}],
            success_url=settings.BILLING_SUCCESS_URL + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=settings.BILLING_CANCEL_URL,
            allow_promotion_codes=True,
            subscription_data={"metadata":{"organization_id": str(org.id), "plan_code": plan_code}},
            metadata={"organization_id": str(org.id), "plan_code": plan_code},
        )
        return Response({"checkout_url": session.url}, status=200)

class CreatePortalSessionView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, org_slug: str, *args, **kwargs):
        org = Organization.objects.get(slug=org_slug)
        sub = Subscription.objects.filter(organization=org).first()
        if not sub or not sub.stripe_customer_id:
            return Response({"detail":"No hay cliente Stripe asociado."}, status=400)
        portal = stripe.billing_portal.Session.create(
            customer=sub.stripe_customer_id,
            return_url=settings.PORTAL_RETURN_URL,
        )
        return Response({"portal_url": portal.url}, status=200)

class GetSubscriptionView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, org_slug: str, *args, **kwargs):
        org = Organization.objects.get(slug=org_slug)
        sub = Subscription.objects.filter(organization=org).first()
        if not sub:
            return Response({"current_plan":"none","status":"inactive"}, status=200)
        from .serializers import SubscriptionSerializer
        return Response(SubscriptionSerializer(sub).data, status=200)
