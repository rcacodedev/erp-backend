# inventory/services.py
from decimal import Decimal
from django.db import transaction
from django.db.models import F
from .models import InventoryItem, StockMove

def _get_item_for_update(org, product_id, warehouse_id):
    item, _ = InventoryItem.objects.select_for_update().get_or_create(
        org=org, product_id=product_id, warehouse_id=warehouse_id,
        defaults={}
    )
    return item

@transaction.atomic
def receive_stock(org, user, product_id, warehouse_id, qty: Decimal, reason="purchase", ref_type="", ref_id=""):
    item = _get_item_for_update(org, product_id, warehouse_id)
    item.qty_on_hand = F("qty_on_hand") + qty
    item.save(update_fields=["qty_on_hand"])
    # 👇 refrescamos valores reales desde BD para evitar F() en memoria
    item.refresh_from_db(fields=["qty_on_hand", "qty_reserved"])
    StockMove.objects.create(
        org=org, product_id=product_id, qty=qty, uom=item.product.uom,
        warehouse_to_id=warehouse_id, reason=reason,
        ref_type=ref_type, ref_id=ref_id, created_by=user
    )
    return item

@transaction.atomic
def reserve_stock(org, user, product_id, warehouse_id, qty: Decimal):
    item = _get_item_for_update(org, product_id, warehouse_id)
    item.refresh_from_db(fields=["qty_on_hand", "qty_reserved"])
    if item.qty_on_hand - item.qty_reserved < qty:
        raise ValueError("Stock insuficiente para reservar")
    item.qty_reserved = F("qty_reserved") + qty
    item.save(update_fields=["qty_reserved"])
    item.refresh_from_db(fields=["qty_on_hand", "qty_reserved"])
    return item

@transaction.atomic
def release_reservation(org, user, product_id, warehouse_id, qty: Decimal):
    item = _get_item_for_update(org, product_id, warehouse_id)
    item.refresh_from_db(fields=["qty_on_hand", "qty_reserved"])
    if item.qty_reserved < qty:
        qty = item.qty_reserved
    item.qty_reserved = F("qty_reserved") - qty
    item.save(update_fields=["qty_reserved"])
    item.refresh_from_db(fields=["qty_on_hand", "qty_reserved"])
    return item

@transaction.atomic
def confirm_outgoing(org, user, product_id, warehouse_id, qty: Decimal, reason="sale", ref_type="", ref_id=""):
    item = _get_item_for_update(org, product_id, warehouse_id)
    item.refresh_from_db(fields=["qty_on_hand", "qty_reserved"])
    if item.qty_on_hand < qty:
        raise ValueError("Stock insuficiente para salida")
    reserve_to_consume = min(item.qty_reserved, qty)
    updates = []
    if reserve_to_consume:
        item.qty_reserved = F("qty_reserved") - reserve_to_consume
        updates.append("qty_reserved")
    item.qty_on_hand = F("qty_on_hand") - qty
    updates.append("qty_on_hand")
    item.save(update_fields=updates)
    item.refresh_from_db(fields=["qty_on_hand", "qty_reserved"])
    StockMove.objects.create(
        org=org, product_id=product_id, qty=-qty, uom=item.product.uom,
        warehouse_from_id=warehouse_id, reason=reason,
        ref_type=ref_type, ref_id=ref_id, created_by=user
    )
    return item

@transaction.atomic
def transfer_stock(org, user, product_id, wh_from_id, wh_to_id, qty: Decimal, ref_type="", ref_id=""):
    if wh_from_id == wh_to_id:
        raise ValueError("El almacén de origen y destino no pueden ser el mismo")
    confirm_outgoing(org, user, product_id, wh_from_id, qty, reason="transfer", ref_type=ref_type, ref_id=ref_id)
    receive_stock(org, user, product_id, wh_to_id, qty, reason="transfer", ref_type=ref_type, ref_id=ref_id)
