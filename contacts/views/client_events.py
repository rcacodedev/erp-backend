from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django.http import HttpResponse
from contacts.models import ClientEvent, Contact
from contacts.serializers.client_event import ClientEventSerializer
from .mixins import OrgScopedViewSet

class ClientEventViewSet(OrgScopedViewSet, viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = ClientEventSerializer
    # Si tu modelo tiene FK directa a org (lo parece), este queryset funciona con el mixin
    queryset = ClientEvent.objects.select_related('cliente', 'org')

    def get_queryset(self):
        # Filtra por cliente y org del path. NO dependemos solo del mixin.
        return (ClientEvent.objects
                .select_related('cliente', 'org')
                .filter(cliente_id=self.kwargs['client_pk'], org=self.get_org())
                .order_by('-id'))

    def perform_create(self, serializer):
        cliente = Contact.objects.get(pk=self.kwargs['client_pk'], org=self.get_org())
        serializer.save(org=cliente.org, cliente=cliente,
                        created_by=self.request.user, updated_by=self.request.user)

    @action(detail=True, methods=['get'])
    def pdf(self, request, *args, **kwargs):
        """
        Justificante PDF del evento (usa reportlab).
        Acepta org_slug/client_pk/pk vía kwargs.
        """
        ev = self.get_object()  # respeta client_pk + org via get_queryset

        buf = BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        c.setTitle("Justificante de asistencia")
        y = 800

        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, y, "Justificante de asistencia")
        y -= 30

        c.setFont("Helvetica", 11)
        nombre_cliente = (
            ev.cliente.razon_social
            or ("{} {}".format(ev.cliente.nombre or "", ev.cliente.apellidos or "").strip())
            or f"Cliente {ev.cliente_id}"
        )
        c.drawString(50, y, f"Cliente: {nombre_cliente}"); y -= 18
        c.drawString(50, y, f"Título: {getattr(ev, 'titulo', '')}"); y -= 18

        if getattr(ev, "inicio", None):
            fini = ev.inicio.strftime('%d/%m/%Y %H:%M')
            fend = ev.fin.strftime('%H:%M') if getattr(ev, "fin", None) else ''
            c.drawString(50, y, f"Fecha/Hora: {fini}{' - ' + fend if fend else ''}")
            y -= 18

        if getattr(ev, "estado", None):
            c.drawString(50, y, f"Estado: {ev.estado}"); y -= 18

        if getattr(ev, "ubicacion", None):
            c.drawString(50, y, f"Ubicación: {ev.ubicacion}"); y -= 18

        c.showPage()
        c.save()
        pdf_bytes = buf.getvalue()
        buf.close()

        resp = HttpResponse(pdf_bytes, content_type='application/pdf')
        resp['Content-Disposition'] = f'inline; filename="justificante_{ev.id}.pdf"'
        return resp
