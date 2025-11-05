# inventory/serializers.py
from rest_framework import serializers
from .models import Category, Product, Warehouse, Worksite, InventoryItem, StockMove

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "is_active"]

class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)
    class Meta:
        model = Product
        fields = ["id","sku","name","category","category_name","uom","tax_rate","price","is_service","is_active","created_at","updated_at"]

class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ["id","code","name","is_primary","is_active"]

class WorksiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Worksite
        fields = ["id","code","name","type","is_active"]

class InventoryItemSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name", read_only=True)
    product_sku = serializers.CharField(source="product.sku", read_only=True)
    warehouse_code = serializers.CharField(source="warehouse.code", read_only=True)
    class Meta:
        model = InventoryItem
        fields = ["id","product","product_sku","product_name","warehouse","warehouse_code","qty_on_hand","qty_reserved"]

class StockMoveSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMove
        fields = ["id","product","qty","uom","warehouse_from","warehouse_to","reason","ref_type","ref_id","created_by","created_at"]
        read_only_fields = ["created_by","created_at"]
