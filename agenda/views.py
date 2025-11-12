from datetime import datetime, timedelta
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q

from core.mixins import OrgScopedModelViewSet
from sales.models import Invoice
from .models import Event, Note
from .serializers import EventSerializer, NoteSerializer

def _parse_range(request):
    start = request.query_params.get("start")
    end = request.query_params.get("end")
    return start, end

class EventViewSet(OrgScopedModelViewSet):
    serializer_class = EventSerializer
    queryset = Event.objects

    def get_queryset(self):
        qs = super().get_queryset().select_related("contact", "invoice").filter(org=self.org)

        start, end = _parse_range(self.request)
        if start and end:
            qs = (
                qs.filter(start__lt=end, end__gte=start) |
                qs.filter(start__gte=start, start__lt=end)
            ).distinct()

        status_q = self.request.query_params.get("status")
        if status_q:
            qs = qs.filter(status=status_q)

        if self.request.query_params.get("important") == "true":
            qs = qs.filter(is_important=True)

        contact_id = self.request.query_params.get("contact_id")
        if contact_id:
            qs = qs.filter(contact_id=contact_id)

        return qs

    def perform_create(self, serializer):
        serializer.save(org=self.org)

class NoteViewSet(OrgScopedModelViewSet):
    serializer_class = NoteSerializer
    queryset = Note.objects

    def get_queryset(self):
        # Base: notas de mi org
        qs = super().get_queryset().select_related("contact", "invoice").filter(org=self.org)

        # Visibilidad (si tienes owner/visibility en el modelo)
        user = self.request.user
        qs = qs.filter(Q(visibility="org") | Q(visibility="private", owner=user))

        # Filtros de rango
        start, end = _parse_range(self.request)
        include_undated = self.request.query_params.get("include_undated") == "true"

        if start and end:
            dated_qs = qs.filter(
                due_date__gte=start.split("T")[0],
                due_date__lt=end.split("T")[0],
            )
            if include_undated:
                undated_qs = qs.filter(due_date__isnull=True)
                qs = (dated_qs | undated_qs).distinct()
            else:
                qs = dated_qs

        # Filtro por contacto
        contact_id = self.request.query_params.get("contact_id")
        if contact_id:
            qs = qs.filter(contact_id=contact_id)

        return qs

    def perform_create(self, serializer):
        serializer.save(org=self.org)

class AlertsViewSet(OrgScopedModelViewSet):
    """Solo para exponer un GET simple que agregue 'avisos' de hoy/mañana/vencidos (notas/citas importantes)."""
    serializer_class = None
    queryset = Event.objects.none()  # no se usa

    def list(self, request, *args, **kwargs):
        today = timezone.localdate()
        tomorrow = today + timedelta(days=1)

        # Notas importantes fijadas (pinned)
        notes_pinned = list(Note.objects.filter(org=self.org, is_pinned=True).order_by("-updated_at")[:8]
                            .values("id","title","color","is_important","is_pinned","due_date"))

        # Eventos importantes hoy/mañana
        ev_today = list(Event.objects.filter(org=self.org, is_important=True, start__date=today)
                        .values("id","title","start","end","color","is_important","status"))
        ev_tomorrow = list(Event.objects.filter(org=self.org, is_important=True, start__date=tomorrow)
                           .values("id","title","start","end","color","is_important","status"))

        # Notas/tareas vencidas importantes (due_date < hoy)
        notes_overdue = list(Note.objects.filter(org=self.org, is_important=True, due_date__lt=today, status__in=["pending"])
                             .values("id","title","due_date","color","is_important","status"))

        return Response({
            "notes_pinned": notes_pinned,
            "events_today": ev_today,
            "events_tomorrow": ev_tomorrow,
            "notes_overdue": notes_overdue,
        })

class OverlaysViewSet(OrgScopedModelViewSet):
    """Overlays utilitarios. De momento: facturas 'no pagadas' como hitos (sin due_date real)."""
    serializer_class = None
    queryset = Invoice.objects.none()

    @action(detail=False, methods=["get"], url_path="invoice-dues")
    def invoice_dues(self, request, *args, **kwargs):
        start, end = _parse_range(request)
        qs = Invoice.objects.filter(org=self.org).exclude(payment_status="paid")
        # No tenemos due_date aún → usamos date_issue como marcador temporal dentro del rango
        if start and end:
            qs = qs.filter(date_issue__gte=start.split("T")[0], date_issue__lt=end.split("T")[0])
        data = [{
            "id": f"inv-{inv.id}",
            "title": f"Factura {inv.number} pendiente",
            "date": inv.date_issue,
            "invoice_id": inv.id,
            "amount": str(inv.total),
            "currency": inv.currency,
            "status": inv.payment_status,
            "kind": "invoice_due_stub"
        } for inv in qs.order_by("date_issue")[:200]]
        return Response(data)
