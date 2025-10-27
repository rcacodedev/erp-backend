from django.urls import path, include
from django.http import JsonResponse
from rest_framework.routers import DefaultRouter

from contacts.views.contact import ContactViewSet
from contacts.views.client import ClientViewSet
from contacts.views.address import AddressViewSet
from contacts.views.attachments import AttachmentViewSet
from contacts.views.consent import ConsentViewSet

from contacts.views.employee_hours import EmployeeHoursViewSet
from contacts.views.hours_import import EmployeeHoursImportView
from contacts.views.location_lite import LocationLiteViewSet
from contacts.views.compensation import EmployeeCompensationViewSet
from contacts.views.location_revenue import LocationRevenueViewSet

from contacts.views.client_events import ClientEventViewSet
from contacts.views.client_attachments import ClientAttachmentViewSet
from contacts.views.client_notes import ClientNoteViewSet
from contacts.views.client_invoices import ClientInvoicesListView

router = DefaultRouter()
router.register(r'', ContactViewSet, basename='contacts')                    # contactos raíz
router.register(r'locations', LocationLiteViewSet, basename='locations')     # LocationLite (empleados)
router.register(r'clients', ClientViewSet, basename='clients')               # clientes (Contact tipo client)
router.register(r'location-revenues', LocationRevenueViewSet, basename='locationrevenues')  # puente V1

def health(_request):
    return JsonResponse({"app":"contacts","status":"ok"})

urlpatterns = [
    path("health/", health, name="contacts-health"),
    path('', include(router.urls)),

    # --- Nested por Contact (empleados) ---
    path('<int:contact_pk>/addresses/', AddressViewSet.as_view({'get':'list','post':'create'})),
    path('<int:contact_pk>/addresses/<int:pk>/', AddressViewSet.as_view({'get':'retrieve','patch':'partial_update','delete':'destroy'})),
    path('<int:contact_pk>/attachments/', AttachmentViewSet.as_view({'get':'list','post':'create'})),
    path('<int:contact_pk>/attachments/<int:pk>/', AttachmentViewSet.as_view({'get':'retrieve','patch':'partial_update','delete':'destroy'})),
    path('<int:contact_pk>/attachments/<int:pk>/download/', AttachmentViewSet.as_view({'get':'download'})),
    path('<int:contact_pk>/consents/', ConsentViewSet.as_view({'get':'list','post':'create'})),
    path('<int:contact_pk>/consents/<int:pk>/', ConsentViewSet.as_view({'get':'retrieve'})),
    path('<int:contact_pk>/hours/', EmployeeHoursViewSet.as_view({'get':'list','post':'create'})),
    path('<int:contact_pk>/hours/<int:pk>/', EmployeeHoursViewSet.as_view({'get':'retrieve','patch':'partial_update','delete':'destroy'})),
    path('<int:contact_pk>/hours/summary/', EmployeeHoursViewSet.as_view({'get':'summary'})),
    path('<int:contact_pk>/hours/import/', EmployeeHoursImportView.as_view()),
    path('<int:contact_pk>/compensations/', EmployeeCompensationViewSet.as_view({'get':'list','post':'create'})),
    path('<int:contact_pk>/compensations/<int:pk>/', EmployeeCompensationViewSet.as_view({'get':'retrieve','patch':'partial_update','delete':'destroy'})),

    # --- Nested por Cliente (ClientViewSet) ---
    path('clients/<int:client_pk>/events/', ClientEventViewSet.as_view({'get':'list','post':'create'})),
    path('clients/<int:client_pk>/events/<int:pk>/', ClientEventViewSet.as_view({'get':'retrieve','patch':'partial_update','delete':'destroy'})),
    path('clients/<int:client_pk>/events/<int:pk>/pdf/', ClientEventViewSet.as_view({'get':'pdf'})),
    path('clients/<int:client_pk>/attachments/', ClientAttachmentViewSet.as_view({'get':'list','post':'create'})),
    path('clients/<int:client_pk>/attachments/<int:pk>/', ClientAttachmentViewSet.as_view({'get':'retrieve','patch':'partial_update','delete':'destroy'})),
    path('clients/<int:client_pk>/notes/', ClientNoteViewSet.as_view({'get':'list','post':'create'})),
    path('clients/<int:client_pk>/notes/<int:pk>/', ClientNoteViewSet.as_view({'get':'retrieve','patch':'partial_update','delete':'destroy'})),
    path('clients/<int:client_pk>/invoices/', ClientInvoicesListView.as_view()),
]
