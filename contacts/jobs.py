# contacts/jobs.py
import csv, os, tempfile
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model
from contacts.models import Contact
from django_rq import get_queue

# Columnas base aceptadas (csv, case-insensitive de cabeceras)
CSV_COLUMNS = [
    "tipo", "es_persona", "nombre", "apellidos", "razon_social", "nombre_comercial",
    "email", "telefono", "movil", "web", "documento_id",
    "condiciones_pago", "iban", "moneda_preferida", "retencion",
    "marketing_opt_in", "rgpd_aceptado", "rgpd_version_texto",
    "etiquetas", "segmento", "origen", "vendedor_responsable",
    "notas", "activo", "bloqueado", "motivo_bloqueo",
]

def _norm_bool(v):
    s = (str(v or "").strip().lower())
    return s in ("1","true","t","yes","y","si","sí")

def import_contacts_job(org_id: str, user_id: int, file_path: str, default_tipo: str = None):
    """
    Lee un CSV y crea/actualiza Contact por (org, documento_id) o (org, email) si existe.
    Retorna dict con métricas y errores; pensado para consultarse vía Job.meta
    """
    from core.models import Organization
    User = get_user_model()
    created = updated = 0
    errors = []
    processed = 0

    try:
        org = Organization.objects.get(pk=org_id)
        user = User.objects.get(pk=user_id)
    except Exception as e:
        return {"ok": False, "error": f"Org/User inválidos: {e}"}

    with open(file_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        headers = [h.strip() for h in reader.fieldnames or []]
        missing = [c for c in ("tipo","nombre","razon_social","email","documento_id") if c not in [h.lower() for h in headers]]
        # No exigimos todas; validamos fila a fila
        for i, row in enumerate(reader, start=2):
            processed += 1
            try:
                data = { (k.lower()): (v.strip() if isinstance(v,str) else v) for k,v in row.items() if k }
                tipo = (data.get("tipo") or default_tipo or "").strip().lower()
                if tipo not in ("client","employee","supplier"):
                    raise ValueError("Columna 'tipo' inválida o vacía (usa client|employee|supplier)")

                # match por documento_id o email
                qmatch = {"org_id": org_id}
                docid = data.get("documento_id") or ""
                email = data.get("email") or ""

                obj = None
                if docid:
                    obj = Contact.objects.filter(org_id=org_id, documento_id=docid).first()
                if obj is None and email:
                    obj = Contact.objects.filter(org_id=org_id, email=email).first()

                payload = {}
                for c in CSV_COLUMNS:
                    if c in ("tipo",):  # set explicito abajo
                        continue
                    if c in data:
                        payload[c] = data[c]

                # booleanos
                for b in ("es_persona","marketing_opt_in","rgpd_aceptado","activo","bloqueado"):
                    if b in payload:
                        payload[b] = _norm_bool(payload[b])

                # etiquetas: csv → lista json
                if "etiquetas" in payload and payload["etiquetas"]:
                    payload["etiquetas"] = [e.strip() for e in payload["etiquetas"].split(",") if e.strip()]

                with transaction.atomic():
                    if obj is None:
                        obj = Contact.objects.create(
                            org_id=org_id,
                            tipo=tipo,
                            created_by=user, updated_by=user,
                            **payload
                        )
                        created += 1
                    else:
                        for k,v in payload.items():
                            setattr(obj, k, v)
                        obj.tipo = tipo
                        obj.updated_by = user
                        obj.save()
                        updated += 1

            except Exception as e:
                errors.append({"row": i, "error": str(e)})

    return {
        "ok": True,
        "processed": processed,
        "created": created,
        "updated": updated,
        "errors": errors[:2000],  # evita payloads gigantes
        "finished_at": timezone.now().isoformat(),
    }

def export_contacts_job(org_id: str, tipo: str = None, filters: dict = None, columns: list = None):
    from contacts.filters import ContactFilter
    qs = Contact.objects.filter(org_id=org_id)
    if tipo in ("client","employee","supplier"):
        qs = qs.filter(tipo=tipo)

    # aplica filtros (search, activo, bloqueado, etiquetas, ordering…)
    params = filters or {}
    f = ContactFilter(params, queryset=qs)
    qs = f.qs

    cols = columns or ["id","tipo","nombre","apellidos","razon_social","email","telefono","documento_id","activo","bloqueado","etiquetas"]
    fd, path = tempfile.mkstemp(prefix="contacts_export_", suffix=".csv")
    os.close(fd)
    with open(path, "w", encoding="utf-8", newline="") as out:
        w = csv.writer(out)
        w.writerow(cols)
        for c in qs.iterator(chunk_size=2000):
            row = []
            for col in cols:
                v = getattr(c, col, "")
                if col == "etiquetas" and isinstance(v, list):
                    v = ", ".join(v)
                row.append("" if v is None else v)
            w.writerow(row)

    return {"ok": True, "path": path, "count": qs.count()}
