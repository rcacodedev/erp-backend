# f7_seed_data.py
# -----------------------------------------------------------------------------
# Generador de datos de prueba para F7 – Analítica & KPIs PRO
# Ejecuta dentro del proyecto Django:
#     python manage.py shell < f7_seed_data.py
# Crea:
#  - Organización "Acme, S.L." (slug: acme) si no existe
#  - 2 categorías, 6 productos (con cost_price), 1 almacén
#  - 5 clientes (mixto persona/empresa)
#  - 30 facturas de venta "posted" con líneas y algunos pagos (parciales/total)
#  - 12 facturas de proveedor "posted" con due_date
#  - Deja due_date en ventas si el modelo lo soporta
# -----------------------------------------------------------------------------
from decimal import Decimal
import random
from datetime import date, timedelta
from django.utils import timezone
from django.db import transaction

from core.models import Organization
from contacts.models import Contact
from inventory.models import Category, Product, Warehouse
from sales.models import Invoice, InvoiceLine, Payment
from purchases.models import SupplierInvoice, SupplierInvoiceLine, SupplierPayment

# Helpers ----------------------------------------------------------------------
def d(y, m, d): return date(y, m, d)
TODAY = timezone.now().date()

def ensure_due_date(obj, dt):
    # Algunas instalaciones pueden no tener due_date en ventas; si existe, lo ponemos.
    if hasattr(obj, "due_date"):
        obj.due_date = dt

def posted(obj):
    obj.status = "posted"
    if hasattr(obj, "payment_status") and not getattr(obj, "payment_status"):
        obj.payment_status = "unpaid"
    obj.save()
    return obj

def compute_invoice_totals(inv):
    base = Decimal("0.00")
    tax  = Decimal("0.00")
    for line in inv.lines.all():
        line_base = (line.qty * line.unit_price) * (Decimal("1.00") - (line.discount_pct/Decimal("100")))
        line_tax  = line_base * (line.tax_rate/Decimal("100"))
        base += line_base
        tax  += line_tax
    inv.totals_base = base.quantize(Decimal("0.01"))
    inv.totals_tax  = tax.quantize(Decimal("0.01"))
    inv.total       = (base + tax).quantize(Decimal("0.01"))
    inv.save(update_fields=["totals_base","totals_tax","total"])

def compute_supplier_totals(inv):
    base = Decimal("0.00")
    tax  = Decimal("0.00")
    for line in inv.lines.all():
        line_base = (line.qty * line.unit_price) * (Decimal("1.00") - (line.discount_pct/Decimal("100")))
        line_tax  = line_base * (line.tax_rate/Decimal("100"))
        base += line_base
        tax  += line_tax
    inv.total_base = base.quantize(Decimal("0.01"))
    inv.total_tax  = tax.quantize(Decimal("0.01"))
    inv.total      = (base + tax).quantize(Decimal("0.01"))
    inv.save(update_fields=["total_base","total_tax","total"])

random.seed(42)

with transaction.atomic():
    # Organización ----------------------------------------------------------------
    org, _ = Organization.objects.get_or_create(
        slug="acme",
        defaults={"name": "Acme, S.L.", "subscription_plan": "pro"},
    )

    # Almacén ----------------------------------------------------------------------
    wh, _ = Warehouse.objects.get_or_create(org=org, code="WH1", defaults={"name": "Principal", "is_primary": True})

    # Categorías y productos -------------------------------------------------------
    cat1, _ = Category.objects.get_or_create(org=org, name="Material")
    cat2, _ = Category.objects.get_or_create(org=org, name="Servicio")

    def mkprod(sku, name, cat, price, cost):
        p, _ = Product.objects.get_or_create(
            org=org, sku=sku,
            defaults={
                "name": name, "category": cat, "price": Decimal(price),
                "cost_price": Decimal(cost), "uom": "ud", "tax_rate": Decimal("21.00"),
            }
        )
        return p

    p1 = mkprod("P-001", "Tornillos", cat1, "2.00", "0.80")
    p2 = mkprod("P-002", "Arandelas", cat1, "1.50", "0.40")
    p3 = mkprod("P-003", "Bridas", cat1, "3.00", "0.90")
    p4 = mkprod("S-001", "Mano de obra", cat2, "30.00", "0.00")
    p5 = mkprod("S-002", "Instalación", cat2, "45.00", "5.00")
    p6 = mkprod("P-004", "Caja herramientas", cat1, "25.00", "12.00")

    # Clientes ---------------------------------------------------------------------
    # Nota: Contact no tiene "name"; usamos razon_social/nombre_comercial/nombre
    cust1, _ = Contact.objects.get_or_create(org=org, razon_social="Cliente Uno S.A.", defaults={"tipo": "cliente"})
    cust2, _ = Contact.objects.get_or_create(org=org, razon_social="Cliente Dos S.L.", defaults={"tipo": "cliente"})
    cust3, _ = Contact.objects.get_or_create(org=org, nombre_comercial="Ferretería Paco", defaults={"tipo": "cliente"})
    cust4, _ = Contact.objects.get_or_create(org=org, nombre="María López", defaults={"tipo": "cliente", "es_persona": True})
    cust5, _ = Contact.objects.get_or_create(org=org, nombre="Juan Pérez", defaults={"tipo": "cliente", "es_persona": True})
    customers = [cust1, cust2, cust3, cust4, cust5]

    # Proveedores (reutilizamos algunos)
    sup1, _ = Contact.objects.get_or_create(org=org, razon_social="Metal Distribuciones SL", defaults={"tipo": "proveedor"})
    sup2, _ = Contact.objects.get_or_create(org=org, razon_social="Suministros Industriales SA", defaults={"tipo": "proveedor"})
    suppliers = [sup1, sup2]

    # Ventas: 30 facturas "posted" distribuidas a lo largo del año vigente ---------
    year = TODAY.year
    series = "A"
    from django.db.models import Max
    next_num = (Invoice.objects.filter(org=org, series=series).aggregate(m=Max("number"))["m"] or 0) + 1

    for i in range(30):
        issue = d(year, (i % 12) + 1, min(25, (i % 27) + 1))
        cust = random.choice(customers)
        inv = Invoice.objects.create(
            org=org,
            series=series,
            number=next_num + i,
            date_issue=issue,
            customer=cust,
            billing_address="C/ Mayor 1",
            status="draft",
            currency="EUR",
            payment_status="unpaid",
        )
        # due_date (si existe) a 30 días vista
        ensure_due_date(inv, issue + timedelta(days=30))

        # Añadir 1-3 líneas
        prod_choices = [p1,p2,p3,p4,p5,p6]
        for _ in range(random.randint(1,3)):
            prod = random.choice(prod_choices)
            qty = Decimal(random.choice([1,2,3,5,10]))
            price = prod.price
            InvoiceLine.objects.create(
                invoice=inv,
                product=prod,
                description=prod.name,
                qty=qty,
                uom=prod.uom,
                unit_price=price,
                tax_rate=prod.tax_rate,
                discount_pct=Decimal("0.00"),
            )
        compute_invoice_totals(inv)
        posted(inv)

        # Pagos: 1/3 pagadas, 1/3 parciales, 1/3 impagadas
        r = i % 3
        if r == 0:
            Payment.objects.create(org=org, invoice=inv, amount=inv.total, date=issue + timedelta(days=10), method="transfer")
            inv.payment_status = "paid"
            inv.save(update_fields=["payment_status"])
        elif r == 1:
            part = (inv.total * Decimal("0.40")).quantize(Decimal("0.01"))
            Payment.objects.create(org=org, invoice=inv, amount=part, date=issue + timedelta(days=15), method="transfer")
            inv.payment_status = "partial"
            inv.save(update_fields=["payment_status"])
        else:
            inv.payment_status = "unpaid"
            inv.save(update_fields=["payment_status"])

    # Compras: 12 facturas proveedor "posted"
    for i in range(12):
        day = d(year, (i % 12) + 1, min(25, (i % 27) + 1))
        sup = suppliers[i % len(suppliers)]
        si = SupplierInvoice.objects.create(
            org=org,
            number=f"SI-{year}-{i+1:04d}",
            supplier=sup,
            warehouse=wh,
            date=day,
            due_date=day + timedelta(days=30),
            currency="EUR",
            status="draft",
            payment_status="unpaid",
        )
        # 1-2 líneas
        for _ in range(random.randint(1,2)):
            prod = random.choice([p1,p2,p3,p5,p6])
            qty = Decimal(random.choice([5,10,20]))
            SupplierInvoiceLine.objects.create(
                invoice=si,
                product=prod,
                description=f"Compra {prod.name}",
                qty=qty,
                uom=prod.uom,
                unit_price=prod.cost_price,
                tax_rate=Decimal("21.00"),
                discount_pct=Decimal("0.00"),
                line_base=Decimal("0.00"),
                line_tax=Decimal("0.00"),
                line_total=Decimal("0.00"),
            )
        compute_supplier_totals(si)
        posted(si)

        # Pagos proveedores: mitad pagadas, mitad parciales
        if i % 2 == 0:
            SupplierPayment.objects.create(org=org, invoice=si, amount=si.total, date=day + timedelta(days=20), method="transfer")
            si.payment_status = "paid"
            si.save(update_fields=["payment_status"])
        else:
            part = (si.total * Decimal("0.50")).quantize(Decimal("0.01"))
            SupplierPayment.objects.create(org=org, invoice=si, amount=part, date=day + timedelta(days=25), method="transfer")
            si.payment_status = "partial"
            si.save(update_fields=["payment_status"])

print("OK: Datos de prueba F7 generados para la organización 'acme'.")
