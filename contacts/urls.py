from django.urls import path, include
from django.http import JsonResponse
from rest_framework.routers import DefaultRouter

# Base contacts
from contacts.views.contact import ContactViewSet
from contacts.views.client import ClientViewSet  # listado/CRUD de clientes (Contact tipo "client")
from contacts.views.address import AddressViewSet
from contacts.views.attachments import AttachmentViewSet
from contacts.views.consent import ConsentViewSet

# Empleados
from contacts.views.employee_hours import EmployeeHoursViewSet
from contacts.views.hours_import import EmployeeHoursImportView
from contacts.views.compensation import EmployeeCompensationViewSet
from contacts.views.employee_financials import EmployeeFinancialsView

# Locations / ingresos ubicación (puente V1)
from contacts.views.location_lite import LocationLiteViewSet
from contacts.views.location_revenue import LocationRevenueViewSet

# Clientes: eventos/adjuntos/notas/facturas placeholder
from contacts.views.client_events import ClientEventViewSet
from contacts.views.client_attachments import ClientAttachmentViewSet
from contacts.views.client_notes import ClientNoteViewSet
from contacts.views.client_invoices import ClientInvoicesListView

# Suppliers (distribuidores)
from contacts.views.supplier import SupplierViewSet
from contacts.views.supplier_attachments import SupplierAttachmentViewSet
from contacts.views.supplier_notes import SupplierNoteViewSet
from contacts.views.supplier_prices import SupplierPriceViewSet
from contacts.views.supplier_certifications import SupplierCertificationViewSet
from contacts.views.supplier_kpis import SupplierKPIsView

router = DefaultRouter()


# Clientes y suppliers como endpoints dedicados
router.register(r'clients', ClientViewSet, basename='clients')
router.register(r'suppliers', SupplierViewSet, basename='suppliers')

# Locations & revenues (puente)
router.register(r'locations', LocationLiteViewSet, basename='locations')
router.register(r'location-revenues', LocationRevenueViewSet, basename='locationrevenues')
# Contactos base (incluye empleados/suppliers/clients si usas este endpoint genérico)
router.register(r'', ContactViewSet, basename='contacts')

def health(_request):
    return JsonResponse({"app": "contacts", "status": "ok"})

urlpatterns = [
    path("health/", health, name="contacts-health"),
    path("", include(router.urls)),

    # --- Nested por Contact (empleado) ---
    path("<int:contact_pk>/addresses/", AddressViewSet.as_view({"get": "list", "post": "create"})),
    path("<int:contact_pk>/addresses/<int:pk>/", AddressViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"})),

    path("<int:contact_pk>/attachments/", AttachmentViewSet.as_view({"get": "list", "post": "create"})),
    path("<int:contact_pk>/attachments/<int:pk>/", AttachmentViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"})),
    path("<int:contact_pk>/attachments/<int:pk>/download/", AttachmentViewSet.as_view({"get": "download"})),

    path("<int:contact_pk>/consents/", ConsentViewSet.as_view({"get": "list", "post": "create"})),
    path("<int:contact_pk>/consents/<int:pk>/", ConsentViewSet.as_view({"get": "retrieve"})),

    path("<int:contact_pk>/hours/", EmployeeHoursViewSet.as_view({"get": "list", "post": "create"})),
    path("<int:contact_pk>/hours/<int:pk>/", EmployeeHoursViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"})),
    path("<int:contact_pk>/hours/summary/", EmployeeHoursViewSet.as_view({"get": "summary"})),
    path("<int:contact_pk>/hours/import/", EmployeeHoursImportView.as_view()),

    path("<int:contact_pk>/compensations/", EmployeeCompensationViewSet.as_view({"get": "list", "post": "create"})),
    path("<int:contact_pk>/compensations/<int:pk>/", EmployeeCompensationViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"})),

    path("<int:contact_pk>/financials/", EmployeeFinancialsView.as_view()),

    # --- Nested por Cliente ---
    path("clients/<int:client_pk>/events/", ClientEventViewSet.as_view({"get": "list", "post": "create"})),
    path("clients/<int:client_pk>/events/<int:pk>/", ClientEventViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"})),
    path("clients/<int:client_pk>/events/<int:pk>/pdf/", ClientEventViewSet.as_view({"get": "pdf"})),

    path("clients/<int:client_pk>/attachments/", ClientAttachmentViewSet.as_view({"get": "list", "post": "create"})),
    path("clients/<int:client_pk>/attachments/<int:pk>/", ClientAttachmentViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"})),

    path("clients/<int:client_pk>/notes/", ClientNoteViewSet.as_view({"get": "list", "post": "create"})),
    path("clients/<int:client_pk>/notes/<int:pk>/", ClientNoteViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"})),

    path("clients/<int:client_pk>/invoices/", ClientInvoicesListView.as_view()),

    # --- Nested por Supplier ---
    path("suppliers/<int:supplier_pk>/attachments/", SupplierAttachmentViewSet.as_view({"get": "list", "post": "create"})),
    path("suppliers/<int:supplier_pk>/attachments/<int:pk>/", SupplierAttachmentViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"})),

    path("suppliers/<int:supplier_pk>/notes/", SupplierNoteViewSet.as_view({"get": "list", "post": "create"})),
    path("suppliers/<int:supplier_pk>/notes/<int:pk>/", SupplierNoteViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"})),

    path("suppliers/<int:supplier_pk>/prices/", SupplierPriceViewSet.as_view({"get": "list", "post": "create"})),
    path("suppliers/<int:supplier_pk>/prices/<int:pk>/", SupplierPriceViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"})),
    path("suppliers/<int:supplier_pk>/prices/import/", SupplierPriceViewSet.as_view({"post": "import_csv"})),

    path("suppliers/<int:supplier_pk>/certifications/", SupplierCertificationViewSet.as_view({"get": "list", "post": "create"})),
    path("suppliers/<int:supplier_pk>/certifications/<int:pk>/", SupplierCertificationViewSet.as_view({"get": "retrieve", "patch": "partial_update", "delete": "destroy"})),

    path("suppliers/<int:supplier_pk>/kpis/", SupplierKPIsView.as_view()),
]
