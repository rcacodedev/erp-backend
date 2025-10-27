from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

class ClientInvoicesListView(IsAuthenticated, APIView):
    permission_classes = (IsAuthenticated,)
    def get(self, request, org_slug=None, client_pk=None):
        # V1: devolver lista simple (hasta que sales/billing esté)
        # TODO V2: leer de sales.Invoice filtrando por cliente
        return Response([
            # ejemplo: {"numero":"F2025-0012","fecha":"2025-10-22","total":350.00,"estado":"Pagada"}
        ])
