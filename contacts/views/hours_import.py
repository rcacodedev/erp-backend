# contacts/views/hours_import.py
import csv, io
from datetime import datetime
from decimal import Decimal

from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from contacts.models import EmployeeHours


class EmployeeHoursImportView(APIView):
    """
    POST /contacts/{contact_pk}/hours/import/
    Body (multipart/form-data):
      - file: CSV con cabecera:
        fecha, horas_totales, [entrada], [salida], [descanso_minutos], [fuente], [referencia]
      Formatos:
        fecha: YYYY-MM-DD
        horas_totales: 7.5 o 7.50
        entrada/salida: HH:MM o HH:MM:SS (se aceptan ambas)
    """
    permission_classes = (IsAuthenticated,)
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, org_slug=None, contact_pk=None):
        f = request.FILES.get("file")
        if not f:
            return Response({"detail": 'Falta archivo "file".'}, status=400)

        # Leemos como texto
        data = f.read().decode("utf-8", errors="ignore")
        reader = csv.DictReader(io.StringIO(data))

        required = {"fecha", "horas_totales"}
        headers = {h.strip() for h in (reader.fieldnames or [])}
        if not required.issubset(headers):
            return Response(
                {
                    "detail": "CSV inválido.",
                    "required": sorted(list(required)),
                    "optional": ["entrada", "salida", "descanso_minutos", "fuente", "referencia"],
                    "got": list(headers),
                },
                status=400,
            )

        created = 0
        updated = 0
        errors = []

        def parse_time(val):
            if not val:
                return None
            val = val.strip()
            for fmt in ("%H:%M:%S", "%H:%M"):
                try:
                    return datetime.strptime(val, fmt).time()
                except ValueError:
                    continue
            raise ValueError(f"Hora inválida: {val} (usa HH:MM o HH:MM:SS)")

        for i, row in enumerate(reader, start=2):  # linea 1 = cabecera
            try:
                fecha = datetime.strptime((row.get("fecha") or "").strip(), "%Y-%m-%d").date()
                horas_totales = Decimal(str(row.get("horas_totales", "0") or "0"))
                entrada = parse_time(row.get("entrada", "").strip())
                salida = parse_time(row.get("salida", "").strip())
                descanso = int((row.get("descanso_minutos") or 0) or 0)
                fuente = (row.get("fuente") or "csv").strip()
                referencia = (row.get("referencia") or "").strip()

                obj, created_flag = EmployeeHours.objects.update_or_create(
                    contact_id=contact_pk,
                    fecha=fecha,
                    referencia=referencia,  # permite upsert si repites la misma referencia
                    defaults={
                        "horas_totales": horas_totales,
                        "entrada": entrada,
                        "salida": salida,
                        "descanso_minutos": descanso,
                        "fuente": fuente,
                        "created_by": request.user,
                        "updated_by": request.user,
                    },
                )
                if created_flag:
                    created += 1
                else:
                    updated += 1
            except Exception as e:
                errors.append({"row": i, "error": str(e)})

        status_code = status.HTTP_200_OK if not errors else status.HTTP_207_MULTI_STATUS
        return Response({"created": created, "updated": updated, "errors": errors}, status=status_code)
