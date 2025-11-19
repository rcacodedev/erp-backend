# analytics/hooks.py

import logging

logger = logging.getLogger(__name__)

"""
Hooks ligeros para registrar eventos de Compras (F6).
No hacen nada complejo todavía. Solo dejan trazas para confirmar
que los eventos se emiten correctamente y sirven de puente
para F7 (Analítica).
"""

def register_supplier_invoice_posted(inv):
    logger.info(f"[Analytics] Factura proveedor contabilizada: {inv.id} – total={inv.total}")
    # más adelante aquí crearemos: AnalyticsExpense.create_from_invoice(inv)
    return True


def register_supplier_payment_created(payment):
    logger.info(
        f"[Analytics] Pago proveedor creado: {payment.id} – "
        f"invoice={payment.invoice_id}, amount={payment.amount}"
    )
    return True


def register_supplier_payment_deleted(payment):
    logger.info(
        f"[Analytics] Pago proveedor eliminado: {payment.id} – "
        f"invoice={payment.invoice_id}"
    )
    return True
