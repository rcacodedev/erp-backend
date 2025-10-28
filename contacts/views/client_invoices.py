from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from contacts.models import Contact

class ClientInvoicesListView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, org_slug=None, client_pk=None):
        # Validación mínima del cliente dentro del tenant
        exists = Contact.objects.filter(pk=client_pk, org__slug=org_slug, tipo='client').exists()
        if not exists:
            return Response({"detail": "Cliente no encontrado en esta organización."},
                            status=status.HTTP_404_NOT_FOUND)

        # Placeholder: aquí devolveremos facturas reales cuando esté Sales
        return Response([], status=status.HTTP_200_OK)
