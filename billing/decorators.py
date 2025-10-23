from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from .limits import get_limits

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
