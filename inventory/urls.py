from django.urls import path, include
from django.http import JsonResponse
from rest_framework.routers import DefaultRouter
from .views import CategoryViewSet, ProductViewSet, WarehouseViewSet, WorksiteViewSet, StockViewSet, MoveActionsViewSet

def health(_request):
    return JsonResponse({"app": "inventory", "status": "ok"})

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='inv-category')
router.register(r'products', ProductViewSet, basename='inv-product')
router.register(r'warehouses', WarehouseViewSet, basename='inv-warehouse')
router.register(r'worksites', WorksiteViewSet, basename='inv-worksite')
router.register(r'stock', StockViewSet, basename='inv-stock')
router.register(r'moves', MoveActionsViewSet, basename='inv-moves')

urlpatterns = [
    path("health/", health, name="inventory-health"),
    path('', include(router.urls)),
]