PLAN_LIMITS = {
    "starter": {"max_users": 3, "max_products": 100},
    "pro": {"max_users": 10, "max_products": 1000},
    "enterprise": {"max_users": 1000, "max_products": 100000},
}

def get_limits(org) -> dict:
    plan = getattr(getattr(org, "subscription", None), "current_plan", "none") or "none"
    return PLAN_LIMITS.get(plan, {})
