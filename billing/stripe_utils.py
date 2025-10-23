import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY

def get_price_id(plan_code: str) -> str:
    mapping = {
        "starter": settings.STRIPE_PRICE_STARTER,
        "pro": settings.STRIPE_PRICE_PRO,
        "enterprise": settings.STRIPE_PRICE_ENTERPRISE,
    }
    price_id = mapping.get(plan_code)
    if not price_id:
        raise ValueError(f"Falta STRIPE_PRICE_* para plan '{plan_code}'")
    return price_id
