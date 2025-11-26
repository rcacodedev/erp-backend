from rest_framework import viewsets, filters as drf_filters
from django_filters.rest_framework import DjangoFilterBackend
from contacts.models import Contact
from contacts.serializers.contact import ContactListSerializer, ContactDetailSerializer
from contacts.filters import ContactFilter
from contacts.permissions import IsOrgMember, CanManageContacts
from .mixins import OrgScopedViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from agenda.models import Event, Note
from agenda.serializers import EventSerializer, NoteSerializer
from contacts.choices import ContactType
from integrations.utils import trigger_webhook_event


class ContactViewSet(OrgScopedViewSet, viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    permission_classes = (IsAuthenticated,)
    filter_backends = (DjangoFilterBackend, drf_filters.OrderingFilter, drf_filters.SearchFilter)
    filterset_class = ContactFilter
    ordering_fields = ("nombre", "apellidos", "razon_social", "updated_at")
    search_fields = ("nombre", "apellidos", "razon_social", "email", "telefono")

    def get_permissions(self):
        base = super().get_permissions()
        if self.request.method in ("POST", "PUT", "PATCH", "DELETE"):
            base.append(CanManageContacts())
        return base

    def get_serializer_class(self):
        if self.action == "list":
            return ContactListSerializer
        return ContactDetailSerializer

    def perform_create(self, serializer):
        # Asegurar que se asigna la organización actual
        org = self.request.org
        contact = serializer.save(org=org)

        # Solo disparamos webhook para clientes
        if contact.tipo == ContactType.CLIENT:
            try:
                trigger_webhook_event(
                    org,
                    "client.created",
                    {
                        "id": contact.id,
                        "org_slug": org.slug,
                        "tipo": contact.tipo,
                        "nombre": contact.nombre,
                        "apellidos": contact.apellidos,
                        "razon_social": contact.razon_social,
                        "nombre_comercial": contact.nombre_comercial,
                        "email": contact.email,
                        "telefono": contact.telefono,
                        "movil": contact.movil,
                    },
                )
            except Exception:
                # No rompemos la creación del contacto si el webhook falla
                pass

    @action(detail=True, methods=["get"], url_path="agenda")
    def agenda(self, request, pk=None, org_slug=None):
        contact = self.get_object()  # ya validado por org
        start = request.query_params.get("start")
        end = request.query_params.get("end")

        ev_qs = Event.objects.filter(org=request.org, contact=contact)
        nt_qs = Note.objects.filter(org=request.org, contact=contact)

        if start and end:
            ev_qs = ev_qs.filter(start__lt=end).filter(end__gte=start) | ev_qs.filter(start__gte=start, start__lt=end)
            nt_qs = nt_qs.filter(due_date__gte=start.split("T")[0], due_date__lt=end.split("T")[0])

        events = EventSerializer(ev_qs.select_related("contact","invoice"), many=True, context={"request":request}).data
        notes  = NoteSerializer(nt_qs.select_related("contact","invoice"), many=True, context={"request":request}).data

        return Response({"events": events, "notes": notes})