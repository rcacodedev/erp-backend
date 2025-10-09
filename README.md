# ERP Backend (Django + DRF + Stripe + PostgreSQL)

Backend principal del ERP SaaS modular para gestión de empresas.
Implementado con **Django 5**, **Django REST Framework**, **PostgreSQL**, **Redis + RQ**, y autenticación **JWT**.
Arquitectura multi-tenant con roles, auditoría, seguridad avanzada y facturación integrada con **Stripe**.

---

## 🚀 Características

- 🔐 **Core & Auth**: login por email, 2FA, organizaciones, roles y permisos (RBAC)
- 💳 **Billing**: planes y cuotas por Stripe (Starter, Pro, Enterprise)
- 👥 **Contactos**: clientes, proveedores y empleados con adjuntos y exportaciones
- 📦 **Inventario & Almacén**: productos, stock, movimientos, valoraciones
- 🧾 **Ventas & Facturación**: presupuestos → pedidos → albaranes → facturas (**Verifactu ES**)
- 🧮 **Compras**: pedidos, entradas, facturas proveedor, pagos
- 📊 **Analítica**: KPIs por semana/mes/trimestre/año
- 🧠 **Extras futuros**: RRHH, fichajes, marketing, SEPA, DMS avanzado, etc.

---

## 🛠️ Instalación local

### 1️⃣ Clonar el repositorio

```bash
git clone https://github.com/rcacodedev/erp-backend.git
cd erp-backend
```
