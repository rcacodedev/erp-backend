# analytics/models.py
from decimal import Decimal
from django.db import models
from django.utils import timezone

from core.models import Organization


class OrgScopedModel(models.Model):
    """
    Modelo base sencillo con FK a Organization.
    Igual que en inventory/sales pero local a analytics.
    """
    org = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="%(class)ss",
    )

    class Meta:
        abstract = True


class OrgFinancialYear(models.Model):
    """
    Config financiera por año para una organización.
    Permite meter saldos de apertura y objetivos.
    """
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name="financial_years",
    )
    year = models.PositiveIntegerField()  # ej: 2025

    # Saldos acumulados ANTES de usar el ERP (o fuera del ERP)
    opening_income = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    opening_expenses = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    # Objetivos anuales opcionales
    sales_budget = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    expenses_budget = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("organization", "year")
        ordering = ["year"]

    def __str__(self):
        return f"{self.organization.slug} - {self.year}"


class Expense(OrgScopedModel):
    """
    Gasto simple (v1) para poder calcular beneficio.
    Más adelante se integrará con Compras/facturas proveedor.
    """
    CATEGORY_CHOICES = (
        ("rent", "Alquiler"),
        ("payroll", "Nóminas"),
        ("utilities", "Suministros"),
        ("taxes", "Impuestos"),
        ("services", "Servicios externos"),
        ("other", "Otros"),
    )

    date = models.DateField(default=timezone.now)
    description = models.CharField(max_length=240, blank=True, default="")
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=Decimal("0.00"),
    )
    category = models.CharField(
        max_length=32,
        choices=CATEGORY_CHOICES,
        default="other",
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"{self.date} - {self.amount} ({self.get_category_display()})"
