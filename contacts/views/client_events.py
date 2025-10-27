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
    queryset = ClientEvent.objects.select_related('cliente')

    def get_queryset(self):
        return super().get_queryset().filter(cliente_id=self.kwargs['client_pk'])

    def perform_create(self, serializer):
        cliente = Contact.objects.get(pk=self.kwargs['client_pk'])
        serializer.save(org=cliente.org, cliente=cliente, created_by=self.request.user, updated_by=self.request.user)

    @action(detail=True, methods=['get'])
    def pdf(self, request, client_pk=None, pk=None):
        ev = self.get_object()
        buf = BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        c.setTitle("Justificante de asistencia")
        y = 800
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, y, "Justificante de asistencia")
        y -= 30
        c.setFont("Helvetica", 11)
        c.drawString(50, y, f"Cliente: {ev.cliente.razon_social or (ev.cliente.nombre + ' ' + ev.cliente.apellidos).strip()}")
        y -= 18
        c.drawString(50, y, f"Título: {ev.titulo}")
        y -= 18
        c.drawString(50, y, f"Fecha/Hora: {ev.inicio.strftime('%d/%m/%Y %H:%M')} - {ev.fin.strftime('%H:%M')}")
        y -= 18
        c.drawString(50, y, f"Estado: {ev.estado}")
        y -= 18
        if ev.ubicacion:
            c.drawString(50, y, f"Ubicación: {ev.ubicacion}")
            y -= 18
        c.showPage()
        c.save()
        pdf_bytes = buf.getvalue()
        buf.close()
        resp = HttpResponse(pdf_bytes, content_type='application/pdf')
        resp['Content-Disposition'] = f'inline; filename="justificante_{ev.id}.pdf"'
        return resp
