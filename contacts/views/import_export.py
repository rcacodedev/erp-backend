from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated

class ContactsImportView(APIView):
    parser_classes = (MultiPartParser,)
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        # Recibir archivo, validar cabeceras, encolar job RQ, devolver job_id
        # TODO: implementar
        return Response({"job_id": "stub"})

class ContactsExportView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        # Recibir filtros/columnas, encolar export, devolver URL cuando finalice
        # TODO: implementar
        return Response({"url": "stub"})