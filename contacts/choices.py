from django.utils.translation import gettext_lazy as _


class ContactType:
    CLIENT = "client"
    EMPLOYEE = "employee"
    SUPPLIER = "supplier"
    CHOICES = (
    (CLIENT, _("Cliente")),
    (EMPLOYEE, _("Empleado")),
    (SUPPLIER, _("Proveedor")),
)


class AddressType:
    FISCAL = "fiscal"
    ENVIO = "envio"
    OTRA = "otra"
    CHOICES = (
    (FISCAL, _("Fiscal")),
    (ENVIO, _("Envío")),
    (OTRA, _("Otra")),
)


class WorkLocationType:
    OFICINA = "oficina"
    ALMACEN = "almacen"
    FABRICA = "fabrica"
    TIENDA = "tienda"
    OTRO = "otro"
    CHOICES = (
    (OFICINA, _("Oficina")),
    (ALMACEN, _("Almacén")),
    (FABRICA, _("Fábrica")),
    (TIENDA, _("Tienda")),
    (OTRO, _("Otro")),
)


class ContractType:
    INDEFINIDO = "indefinido"
    TEMPORAL = "temporal"
    PRACTICAS = "practicas"
    AUTONOMO = "autonomo"
    OTRO = "otro"
    CHOICES = (
    (INDEFINIDO, _("Indefinido")),
    (TEMPORAL, _("Temporal")),
    (PRACTICAS, _("Prácticas")),
    (AUTONOMO, _("Autónomo")),
    (OTRO, _("Otro")),
)


class JornadaType:
    COMPLETA = "completa"
    PARCIAL = "parcial"
    HORAS = "horas"
    CHOICES = (
    (COMPLETA, _("Completa")),
    (PARCIAL, _("Parcial")),
    (HORAS, _("Horas")),
)


class AntivirusState:
    PENDIENTE = "pending"
    LIMPIO = "clean"
    BLOQUEADO = "blocked"
    CHOICES = (
    (PENDIENTE, _("Pendiente")),
    (LIMPIO, _("Limpio")),
    (BLOQUEADO, _("Bloqueado")),
)