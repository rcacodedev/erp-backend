# contacts/views/template.py
from django.http import HttpResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from contacts.permissions import IsOrgMember

import csv
from io import TextIOWrapper

# Cabeceras oficiales (en minúsculas)
CSV_HEADERS = [
    "tipo","es_persona","nombre","apellidos","razon_social","nombre_comercial",
    "email","telefono","movil","web","documento_id",
    "condiciones_pago","iban","moneda_preferida","retencion",
    "marketing_opt_in","rgpd_aceptado","rgpd_version_texto",
    "etiquetas","segmento","origen","vendedor_responsable",
    "notas","activo","bloqueado","motivo_bloqueo",
]

# Filas de ejemplo (1 por tipo), puedes ajustar textos
SAMPLE_ROWS = [
    {
        "tipo": "client", "nombre": "Panadería Marta", "razon_social": "Panadería Marta S.L.",
        "email": "marta@pan.es", "documento_id": "ESX123", "telefono": "913001122",
        "etiquetas": "vip, pago30", "activo": "1"
    },
    {
        "tipo": "supplier", "nombre": "Carnes Pepe", "razon_social": "Carnes Pepe S.A.",
        "email": "proveedor@carnespepe.es", "documento_id": "ESX124", "telefono": "913004455",
        "etiquetas": "cárnico", "activo": "1"
    },
    {
        "tipo": "employee", "nombre": "Juan", "apellidos": "García",
        "email": "juan@example.com", "documento_id": "DNI123", "activo": "1"
    },
]

class ContactsTemplateCSVView(APIView):
    permission_classes = (IsAuthenticated, IsOrgMember)

    def get(self, request, *args, **kwargs):
        # Preparamos respuesta CSV con BOM para que Excel abra en UTF-8
        response = HttpResponse(content_type="text/csv; charset=utf-8")
        response["Content-Disposition"] = 'attachment; filename="contacts_template.csv"'
        response.write("\ufeff")  # BOM UTF-8 para Excel

        writer = csv.DictWriter(response, fieldnames=CSV_HEADERS, extrasaction="ignore")
        writer.writeheader()

        for row in SAMPLE_ROWS:
            writer.writerow(row)

        return response
