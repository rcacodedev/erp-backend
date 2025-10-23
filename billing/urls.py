from django.urls import path
from .views import (
    BillingHealthView,
    CreateCheckoutSessionView,
    CreatePortalSessionView,
    GetSubscriptionView,
)

urlpatterns = [
    path("health/", BillingHealthView.as_view(), name="billing-health"),
    path("stripe/checkout/", CreateCheckoutSessionView.as_view(), name="stripe-checkout"),
    path("stripe/portal/", CreatePortalSessionView.as_view(), name="stripe-portal"),
    path("subscription/", GetSubscriptionView.as_view(), name="billing-subscription"),
]
