from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from .limits import get_limits
from django.conf import settings

def enforce_limit(resource_key: str, count_fn):
    """
    resource_key: p.ej. "max_products"
    count_fn: callable (request, org) -> int
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(self, request, *args, **kwargs):
            org = request.user.organization  # ajusta a tu relación
            limits = get_limits(org)
            limit = limits.get(resource_key)
            if limit is None:
                return view_func(self, request, *args, **kwargs)
            current = count_fn(request, org)
            if current >= limit:
                return Response({"detail": f"Límite de plan alcanzado: {resource_key}={limit}"}, status=status.HTTP_402_PAYMENT_REQUIRED)
            return view_func(self, request, *args, **kwargs)
        return _wrapped_view
    return decorator

def require_plan(min_plan: str):
    order = {"free": 0, "starter": 1, "pro": 2, "enterprise": 3}
    def deco(view_func):
        @wraps(view_func)
        def _wrapped(view, request, *args, **kwargs):
            # BYPASS en desarrollo o para staff
            if getattr(settings, "DEBUG", False) or getattr(request.user, "is_staff", False) or getattr(request.user, "is_superuser", False):
                return view_func(view, request, *args, **kwargs)

            org = getattr(request, "org", None)
            if org is None:
                return Response({"detail": "Org no resuelta"}, status=status.HTTP_400_BAD_REQUEST)

            current = getattr(org, "subscription_plan", "starter")
            if order.get(current, 0) < order.get(min_plan, 0):
                return Response(
                    {"detail": f"Disponible en plan {min_plan} o superior."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            return view_func(view, request, *args, **kwargs)
        return _wrapped
    return deco