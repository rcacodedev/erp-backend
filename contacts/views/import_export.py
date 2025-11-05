# contacts/views/import_export.py
import os, tempfile
from django.http import FileResponse, Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from contacts.permissions import IsOrgMember, CanManageContacts
from django_rq import enqueue, get_queue
from rq.job import Job
from django.conf import settings
from contacts.jobs import import_contacts_job, export_contacts_job

class ContactsImportView(APIView):
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = (IsAuthenticated, IsOrgMember, CanManageContacts)

    def post(self, request, *args, **kwargs):
        org = getattr(request, "org", None)
        if not org:
            return Response({"detail":"Org no resuelta"}, status=400)
        f = request.FILES.get("file")
        default_tipo = (request.data.get("tipo") or "").strip().lower() or None
        if not f:
            return Response({"detail":"Sube un archivo CSV en 'file'."}, status=400)

        # guarda temporal
        fd, path = tempfile.mkstemp(prefix="contacts_import_", suffix=".csv")
        try:
            with os.fdopen(fd, "wb") as tmp:
                for chunk in f.chunks():
                    tmp.write(chunk)
        except Exception as e:
            return Response({"detail": f"Error guardando archivo: {e}"}, status=400)

        q = get_queue("default")
        job = q.enqueue(import_contacts_job, org.id, request.user.id, path, default_tipo)
        return Response({"job_id": job.id}, status=202)

class ContactsExportView(APIView):
    permission_classes = (IsAuthenticated, IsOrgMember)

    def post(self, request, *args, **kwargs):
        org = getattr(request, "org", None)
        if not org:
            return Response({"detail":"Org no resuelta"}, status=400)
        tipo = (request.data.get("tipo") or "").strip().lower() or None
        filters = request.data.get("filters") or {}
        columns = request.data.get("columns") or None

        q = get_queue("default")
        job = q.enqueue(export_contacts_job, org.id, tipo, filters, columns)
        return Response({"job_id": job.id}, status=202)

class JobStatusView(APIView):
    permission_classes = (IsAuthenticated, IsOrgMember)

    def get(self, request, job_id: str, *args, **kwargs):
        try:
            job = Job.fetch(job_id, connection=get_queue("default").connection)
        except Exception:
            raise Http404("Job no encontrado")
        status = job.get_status()
        data = job.result if status == "finished" else None
        return Response({"status": status, "result": data})

class JobDownloadView(APIView):
    permission_classes = (IsAuthenticated, IsOrgMember)

    def get(self, request, job_id: str, *args, **kwargs):
        try:
            job = Job.fetch(job_id, connection=get_queue("default").connection)
        except Exception:
            raise Http404("Job no encontrado")
        if job.get_status() != "finished":
            return Response({"detail":"Aún no finalizado."}, status=409)
        result = job.result or {}
        path = result.get("path")
        if not path or not os.path.exists(path):
            raise Http404("Archivo no disponible")
        return FileResponse(open(path, "rb"), as_attachment=True, filename=os.path.basename(path))
