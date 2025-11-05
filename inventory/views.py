# inventory/views.py
from decimal import Decimal
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q, Sum, F

from .models import Category, Product, Warehouse, Worksite, InventoryItem, StockMove
from .serializers import (
    CategorySerializer, ProductSerializer, WarehouseSerializer, WorksiteSerializer,
    InventoryItemSerializer, StockMoveSerializer
)
from . import services

from core.mixins import OrgScopedModelViewSet

class CategoryViewSet(OrgScopedModelViewSet, viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    queryset = Category.objects.all()

class ProductViewSet(OrgScopedModelViewSet, viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    queryset = Product.objects.select_related("category").all()

    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.query_params.get("q")
        category = self.request.query_params.get("category")
        is_service = self.request.query_params.get("is_service")
        tax_rate = self.request.query_params.get("tax_rate")
        in_stock = self.request.query_params.get("in_stock")
        warehouse = self.request.query_params.get("warehouse")

        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(sku__icontains=q))
        if category:
            qs = qs.filter(category_id=category)
        if is_service in ("0","1"):
            qs = qs.filter(is_service=(is_service=="1"))
        if tax_rate:
            qs = qs.filter(tax_rate=tax_rate)
        # filtro in_stock por warehouse (si no hay, considerar suma en todos)
        if in_stock in ("1","true","True"):
            if warehouse:
                qs = qs.filter(inventory_items__warehouse_id=warehouse, inventory_items__qty_on_hand__gt=0)
            else:
                qs = qs.filter(inventory_items__qty_on_hand__gt=0)
        return qs.distinct()

class WarehouseViewSet(OrgScopedModelViewSet, viewsets.ModelViewSet):
    serializer_class = WarehouseSerializer
    queryset = Warehouse.objects.all()

    def perform_update(self, serializer):
        obj = serializer.save()
        if not obj.is_active:
            # impedir desactivar si hay stock
            has_stock = InventoryItem.objects.filter(org=obj.org, warehouse=obj, qty_on_hand__gt=0).exists()
            if has_stock:
                raise ValueError("No se puede desactivar un almacén con stock > 0")

class WorksiteViewSet(OrgScopedModelViewSet, viewsets.ModelViewSet):
    serializer_class = WorksiteSerializer
    queryset = Worksite.objects.all()

class StockViewSet(OrgScopedModelViewSet, mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = InventoryItemSerializer
    queryset = InventoryItem.objects.select_related("product","warehouse").all()

    def get_queryset(self):
        qs = super().get_queryset()
        product = self.request.query_params.get("product")
        warehouse = self.request.query_params.get("warehouse")
        if product:
            qs = qs.filter(product_id=product)
        if warehouse:
            qs = qs.filter(warehouse_id=warehouse)
        return qs

class MoveActionsViewSet(OrgScopedModelViewSet, viewsets.GenericViewSet):
    serializer_class = StockMoveSerializer
    queryset = StockMove.objects.all()

    @action(detail=False, methods=["post"])
    def receive(self, request, *args, **kwargs):
        data = request.data
        item = services.receive_stock(
            org=self.org, user=request.user,
            product_id=data["product"], warehouse_id=data["warehouse"], qty=Decimal(str(data["qty"]))
        )
        return Response(InventoryItemSerializer(item).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"])
    def adjust(self, request, *args, **kwargs):
        # ajuste es receive con reason=adjustment y qty signed
        data = request.data
        qty = Decimal(str(data["qty"]))
        reason = "adjustment"
        if qty >= 0:
            item = services.receive_stock(org=self.org, user=request.user,
                                          product_id=data["product"], warehouse_id=data["warehouse"], qty=qty, reason=reason)
        else:
            item = services.confirm_outgoing(org=self.org, user=request.user,
                                             product_id=data["product"], warehouse_id=data["warehouse"], qty=abs(qty), reason=reason)
        return Response(InventoryItemSerializer(item).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"])
    def transfer(self, request, *args, **kwargs):
        data = request.data
        services.transfer_stock(
            org=self.org, user=request.user,
            product_id=data["product"],
            wh_from_id=data["warehouse_from"],
            wh_to_id=data["warehouse_to"],
            qty=Decimal(str(data["qty"]))
        )
        return Response({"ok": True})
