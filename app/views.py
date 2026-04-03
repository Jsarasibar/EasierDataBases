import csv
import json
import logging
from pathlib import Path
from urllib.parse import urlencode

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Q, TextField
from django.db.models.functions import Cast
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.clickjacking import xframe_options_exempt

from .forms import CSVImportForm, CSVMappingForm, CustomFieldForm, MembershipForm, RecordForm, RegisterForm, SaveViewForm, WizardOptionsForm, WizardSetupForm, WizardTemplateForm
from .models import AppDatabase, CustomField, DatabaseActivity, DatabaseMembership, Record, SavedView

logger = logging.getLogger(__name__)

DETAIL_TABS = {"summary", "daily", "records", "structure", "manage", "history"}


SUGGESTED_EXTRA_FIELDS = {
    "inventory": [
        ("inventory_supplier", "Proveedor"),
        ("inventory_cost", "Costo"),
        ("inventory_barcode", "Codigo de barras"),
    ],
    "students": [
        ("students_document", "Documento"),
        ("students_guardian", "Tutor / responsable"),
        ("students_attendance", "Asistencia"),
    ],
    "clients": [
        ("clients_stage", "Etapa comercial"),
        ("clients_origin", "Origen"),
        ("clients_owner", "Vendedor responsable"),
    ],
    "generic": [
        ("generic_notes", "Notas"),
        ("generic_status", "Semaforo"),
        ("generic_owner", "Responsable secundario"),
    ],
}

STARTER_TEMPLATE_FIELD_DEFINITIONS = {
    "inventory": [
        ("inventory_nombre", "Nombre", CustomField.FieldType.TEXT, True, True, "Nombre del producto", ""),
        ("inventory_sku", "SKU", CustomField.FieldType.TEXT, False, True, "Codigo interno o referencia", ""),
        ("inventory_precio", "Precio", CustomField.FieldType.CURRENCY, True, True, "Valor de venta", ""),
        ("inventory_stock", "Stock", CustomField.FieldType.NUMBER, True, True, "Cantidad disponible", ""),
        ("inventory_categoria", "Categoria", CustomField.FieldType.TEXT, False, True, "Linea o familia del producto", ""),
        ("inventory_reponer", "Reponer", CustomField.FieldType.BOOLEAN, False, True, "Marca si necesita reposicion", ""),
    ],
    "students": [
        ("students_nombre", "Nombre", CustomField.FieldType.TEXT, True, True, "Nombre completo del alumno", ""),
        ("students_curso", "Curso", CustomField.FieldType.TEXT, True, True, "Programa o curso asignado", ""),
        ("students_email", "Email", CustomField.FieldType.EMAIL, False, True, "Contacto principal", ""),
        ("students_telefono", "Telefono", CustomField.FieldType.PHONE, False, False, "Telefono del alumno", ""),
        ("students_fecha_inicio", "Fecha de inicio", CustomField.FieldType.DATE, False, True, "Inicio de cursada", ""),
        ("students_cuota_dia", "Cuota al dia", CustomField.FieldType.BOOLEAN, False, True, "Marca si esta al dia", ""),
    ],
    "clients": [
        ("clients_nombre", "Nombre", CustomField.FieldType.TEXT, True, True, "Nombre del contacto", ""),
        ("clients_empresa", "Empresa", CustomField.FieldType.TEXT, False, True, "Empresa o razon social", ""),
        ("clients_email", "Email", CustomField.FieldType.EMAIL, False, True, "Correo de contacto", ""),
        ("clients_telefono", "Telefono", CustomField.FieldType.PHONE, False, False, "Numero principal", ""),
        ("clients_ultimo_contacto", "Ultimo contacto", CustomField.FieldType.DATE, False, True, "Fecha del ultimo seguimiento", ""),
        ("clients_activo", "Activo", CustomField.FieldType.BOOLEAN, False, True, "Cliente activo o prospecto", ""),
    ],
    "generic": [
        ("generic_nombre", "Nombre", CustomField.FieldType.TEXT, True, True, "Nombre principal del registro", ""),
        ("generic_estado", "Estado", CustomField.FieldType.TEXT, False, True, "Situacion o etapa del registro", ""),
        ("generic_responsable", "Responsable", CustomField.FieldType.TEXT, False, True, "Persona a cargo", ""),
        ("generic_fecha_objetivo", "Fecha objetivo", CustomField.FieldType.DATE, False, True, "Fecha estimada", ""),
        ("generic_importe", "Importe", CustomField.FieldType.CURRENCY, False, True, "Valor economico opcional", ""),
    ],
    "blank": [],
}


EXTRA_FIELD_DEFINITIONS = {
    "inventory_supplier": ("Proveedor", CustomField.FieldType.TEXT, False, True, "Proveedor principal"),
    "inventory_cost": ("Costo", CustomField.FieldType.CURRENCY, False, True, "Costo interno"),
    "inventory_barcode": ("Codigo de barras", CustomField.FieldType.TEXT, False, False, "Codigo escaneable"),
    "students_document": ("Documento", CustomField.FieldType.TEXT, False, True, "DNI o identificacion"),
    "students_guardian": ("Tutor / responsable", CustomField.FieldType.TEXT, False, False, "Contacto responsable"),
    "students_attendance": ("Asistencia", CustomField.FieldType.SELECT, False, True, "Estado de asistencia"),
    "clients_stage": ("Etapa comercial", CustomField.FieldType.SELECT, False, True, "Prospecto, activo, pausado"),
    "clients_origin": ("Origen", CustomField.FieldType.TEXT, False, False, "Canal de ingreso"),
    "clients_owner": ("Vendedor responsable", CustomField.FieldType.TEXT, False, True, "Persona a cargo"),
    "generic_notes": ("Notas", CustomField.FieldType.TEXT, False, False, "Comentarios utiles"),
    "generic_status": ("Semaforo", CustomField.FieldType.SELECT, False, True, "Estado visual"),
    "generic_owner": ("Responsable secundario", CustomField.FieldType.TEXT, False, False, "Apoyo o seguimiento"),
}


def home(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "home.html")


def register_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")

    form = RegisterForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Tu cuenta fue creada. Ya podes empezar a construir tu base.")
        return redirect("dashboard")
    return render(request, "auth/register.html", {"form": form})


def _get_database_for_user(user, slug):
    database = get_object_or_404(
        AppDatabase.objects.prefetch_related("fields", "memberships__user"),
        slug=slug,
    )
    membership = database.memberships.filter(user=user).first()
    if not membership:
        raise Http404()
    return database, membership


def _accessible_databases_for_user(user):
    return AppDatabase.objects.filter(memberships__user=user).distinct()


def _field_has_data(field):
    for record in field.database.records.only("data"):
        if field.key in (record.data or {}) and record.data.get(field.key) not in ("", None):
            return True
    return False


def _import_session_key(database):
    return f"csv_import_{database.pk}"


def _cleanup_import_file(file_path):
    if not file_path:
        return
    path = Path(file_path)
    if path.exists():
        path.unlink()


def _database_tab_url(database, tab):
    return f"{reverse('database_detail', args=[database.slug])}?tab={tab}"


def _log_database_activity(database, actor, action, detail, payload=None):
    DatabaseActivity.objects.create(
        database=database,
        actor=actor if getattr(actor, "pk", None) else None,
        action=action,
        detail=detail[:220],
        payload=payload or {},
    )


def _serialize_value_for_history(database, field_key, value):
    if value in ("", None, False):
        return "-"
    field = database.fields.filter(key=field_key).first()
    if not field:
        return str(value)
    if field.field_type == CustomField.FieldType.BOOLEAN:
        return "Si" if bool(value) else "No"
    if field.field_type == CustomField.FieldType.RELATION and field.relation_database:
        related_record, relation_error = _resolve_related_record(field, value)
        if related_record:
            return related_record.title
        return relation_error or f"ID {value}"
    return str(value)


def _record_changes_for_history(database, previous_data, new_data):
    changes = []
    for field in database.fields.all():
        before = _serialize_value_for_history(database, field.key, (previous_data or {}).get(field.key, ""))
        after = _serialize_value_for_history(database, field.key, (new_data or {}).get(field.key, ""))
        if before != after:
            changes.append(
                {
                    "label": field.label,
                    "before": before,
                    "after": after,
                }
            )
    return changes


def _history_payload_for_activity(activity):
    payload = activity.payload or {}
    return {
        "action": activity.action,
        "detail": activity.detail,
        "actor": activity.actor.username if activity.actor else "Sistema",
        "created_at": activity.created_at.strftime("%d/%m/%Y %H:%M"),
        "summary": payload.get("summary", []),
        "changes": payload.get("changes", []),
    }


DEMO_RECORDS = {
    "inventory": [
        {"title": "Cafe tostado", "priority": "high", "data": {"nombre": "Cafe tostado", "sku": "CAF-001", "precio": "12500", "stock": "18", "categoria": "Bebidas", "reponer": True}},
        {"title": "Taza negra", "priority": "normal", "data": {"nombre": "Taza negra", "sku": "HOG-014", "precio": "4800", "stock": "44", "categoria": "Accesorios", "reponer": False}},
    ],
    "students": [
        {"title": "Lucia Perez", "priority": "normal", "data": {"nombre": "Lucia Perez", "curso": "Excel inicial", "email": "lucia@example.com", "telefono": "1133445566", "fecha_de_inicio": "2026-03-10", "cuota_al_dia": True}},
        {"title": "Martin Rios", "priority": "high", "data": {"nombre": "Martin Rios", "curso": "Bases de datos", "email": "martin@example.com", "telefono": "1166889900", "fecha_de_inicio": "2026-03-15", "cuota_al_dia": False}},
    ],
    "clients": [
        {"title": "Acme SA", "priority": "high", "data": {"nombre": "Marina Costa", "empresa": "Acme SA", "email": "marina@acme.com", "telefono": "1144556677", "ultimo_contacto": "2026-03-20", "activo": True}},
        {"title": "Globex", "priority": "normal", "data": {"nombre": "Diego Mora", "empresa": "Globex", "email": "diego@globex.com", "telefono": "1122334455", "ultimo_contacto": "2026-03-18", "activo": True}},
    ],
    "generic": [
        {"title": "Implementar cartelera", "priority": "normal", "data": {"nombre": "Implementar cartelera", "estado": "En curso", "responsable": "Laura", "fecha_objetivo": "2026-04-15", "importe": "0"}},
        {"title": "Revisar sucursal", "priority": "urgent", "data": {"nombre": "Revisar sucursal", "estado": "Pendiente", "responsable": "Nicolas", "fecha_objetivo": "2026-04-07", "importe": "0"}},
    ],
}

ASSISTANT_COPY = {
    "inventory": {
        "goal": "Te conviene arrancar con una estructura pensada para stock y precios.",
        "watchout": "Luego puedes renombrar campos o mover la base a otro uso sin perder datos.",
        "suggested_name": "Catalogo de productos",
    },
    "students": {
        "goal": "Esta plantilla ya ordena alumnos, contacto y seguimiento basico.",
        "watchout": "Si despues quieres llevar asistencias o comisiones, se puede ampliar.",
        "suggested_name": "Seguimiento de alumnos",
    },
    "clients": {
        "goal": "Sirve para contactos, prospectos y seguimiento comercial.",
        "watchout": "Si luego necesitas oportunidades o pedidos, puedes relacionar otras listas.",
        "suggested_name": "Base de clientes",
    },
    "generic": {
        "goal": "Es la opcion mas flexible si todavia no tienes tan claro el modelo.",
        "watchout": "No te preocupes por dejarla perfecta: la estructura se puede ajustar despues.",
        "suggested_name": "Lista operativa",
    },
    "blank": {
        "goal": "Solo elige esta opcion si realmente quieres empezar sin ayudas.",
        "watchout": "Puedes sumar campos base manualmente en el siguiente paso.",
        "suggested_name": "Nueva lista",
    },
}


def _template_catalog():
    return [
        {
            "key": "inventory",
            "title": "Productos / Inventario",
            "description": "Ideal para stock, catalogos, listas de precios y reposicion.",
            "fields": [item[1] for item in STARTER_TEMPLATE_FIELD_DEFINITIONS["inventory"]],
        },
        {
            "key": "students",
            "title": "Alumnos / Cursos",
            "description": "Pensada para academias, talleres y capacitaciones.",
            "fields": [item[1] for item in STARTER_TEMPLATE_FIELD_DEFINITIONS["students"]],
        },
        {
            "key": "clients",
            "title": "Clientes / Contactos",
            "description": "Sirve para relaciones comerciales, prospectos o soporte.",
            "fields": [item[1] for item in STARTER_TEMPLATE_FIELD_DEFINITIONS["clients"]],
        },
        {
            "key": "generic",
            "title": "Otra base",
            "description": "Una estructura neutra para procesos internos, tareas, pedidos o cualquier otra cosa.",
            "fields": [item[1] for item in STARTER_TEMPLATE_FIELD_DEFINITIONS["generic"]],
        },
        {
            "key": "blank",
            "title": "Desde cero",
            "description": "Empieza vacio y define cada campo manualmente.",
            "fields": [],
        },
    ]


def _get_suggested_choices(template_key):
    return SUGGESTED_EXTRA_FIELDS.get(template_key, ())


def _base_field_keys(template_key):
    return [item[0] for item in STARTER_TEMPLATE_FIELD_DEFINITIONS.get(template_key, [])]


def _field_option_catalog(template_key):
    catalog = []
    for field_key, label, field_type, required, show_in_table, help_text, options_text in STARTER_TEMPLATE_FIELD_DEFINITIONS.get(template_key, []):
        catalog.append(
            {
                "key": field_key,
                "label": label,
                "field_type": field_type,
                "kind": "base",
                "help_text": help_text,
            }
        )
    catalog.append(
        {
            "key": "__priority__",
            "label": "Prioridad",
            "field_type": "priority",
            "kind": "system",
            "help_text": "Te permite destacar elementos normales, altos o urgentes en esta base.",
        }
    )
    for extra_key, label in SUGGESTED_EXTRA_FIELDS.get(template_key, []):
        definition = EXTRA_FIELD_DEFINITIONS.get(extra_key)
        if not definition:
            continue
        catalog.append(
            {
                "key": extra_key,
                "label": label,
                "field_type": definition[1],
                "kind": "extra",
                "help_text": definition[4],
            }
        )
    return catalog


def _assistant_context(template_key):
    return ASSISTANT_COPY.get(template_key, ASSISTANT_COPY["generic"])


def _template_use_case(template_key):
    mapping = {
        "inventory": AppDatabase.UseCase.INVENTORY,
        "students": AppDatabase.UseCase.STUDENTS,
        "clients": AppDatabase.UseCase.CLIENTS,
        "generic": AppDatabase.UseCase.GENERIC,
        "blank": AppDatabase.UseCase.GENERIC,
    }
    return mapping.get(template_key, AppDatabase.UseCase.GENERIC)


def _preview_template_fields(templates_catalog, template_key):
    return next((item["fields"] for item in templates_catalog if item["key"] == template_key), [])


def _wizard_render_context(
    *,
    templates_catalog,
    step,
    wizard_state,
    assistant,
    template_form,
    setup_form,
    options_form,
):
    template_key = wizard_state["starter_template"]
    return {
        "templates_catalog": templates_catalog,
        "step": step,
        "wizard_state": wizard_state,
        "assistant": assistant,
        "template_form": template_form,
        "setup_form": setup_form,
        "options_form": options_form,
        "preview_template_fields": _preview_template_fields(templates_catalog, template_key),
        "field_option_catalog": _field_option_catalog(template_key),
        "base_field_keys": _base_field_keys(template_key),
        "preview_extras": [
            EXTRA_FIELD_DEFINITIONS[key][0]
            for key in wizard_state["selected_fields"]
            if key in EXTRA_FIELD_DEFINITIONS
        ],
        "preview_manual_fields": wizard_state["custom_fields"],
    }


def _create_extra_fields(database, selected_extra_keys):
    created_fields = []
    max_position = database.fields.count()
    for extra_key in selected_extra_keys:
        definition = EXTRA_FIELD_DEFINITIONS.get(extra_key)
        if not definition:
            continue
        max_position += 1
        label, field_type, required, show_in_table, help_text = definition
        field = CustomField(
            database=database,
            label=label,
            field_type=field_type,
            required=required,
            show_in_table=show_in_table,
            help_text=help_text,
            position=max_position,
        )
        if extra_key in {"students_attendance", "clients_stage", "generic_status"}:
            field.options_text = "Pendiente\nEn curso\nResuelto" if extra_key == "generic_status" else "Regular\nInestable\nBaja" if extra_key == "students_attendance" else "Prospecto\nActivo\nPausado"
        field.save()
        created_fields.append(field)
    return created_fields


def _create_selected_template_fields(database, template_key, selected_field_keys):
    definitions = STARTER_TEMPLATE_FIELD_DEFINITIONS.get(template_key, [])
    selected_keys = set(selected_field_keys)
    position = 0
    created_fields = []
    for field_key, label, field_type, required, show_in_table, help_text, options_text in definitions:
        if field_key not in selected_keys:
            continue
        position += 1
        created_fields.append(CustomField.objects.create(
            database=database,
            label=label,
            field_type=field_type,
            required=required,
            show_in_table=show_in_table,
            help_text=help_text,
            options_text=options_text,
            position=position,
        ))
    return created_fields


def _create_manual_fields(database, custom_fields):
    created_fields = []
    max_position = database.fields.count()
    for item in custom_fields:
        if not item.get("label") or not item.get("field_type"):
            continue
        max_position += 1
        created_fields.append(CustomField.objects.create(
            database=database,
            label=item["label"],
            field_type=item["field_type"],
            options_text=item.get("options_text", ""),
            required=False,
            show_in_table=True,
            help_text="Campo agregado durante la configuracion inicial",
            position=max_position,
        ))
    return created_fields


def _record_title_from_value(field, value):
    if value in ("", None):
        return ""
    if field.field_type == CustomField.FieldType.BOOLEAN:
        return "Si" if value else "No"
    if field.field_type == CustomField.FieldType.RELATION and field.relation_database:
        related_record = field.relation_database.records.filter(pk=value).first()
        return related_record.title if related_record else str(value)
    return str(value).strip()


def _resolve_related_record(field, raw_value):
    if not field.relation_database:
        return None, "La base relacionada ya no esta disponible."
    lookup_value = str(raw_value).strip()
    if not lookup_value:
        return None, "No se informo ningun valor para la relacion."
    if lookup_value.isdigit():
        related_record = field.relation_database.records.filter(pk=int(lookup_value)).first()
        if related_record:
            return related_record, None
    matches = list(field.relation_database.records.filter(title__iexact=lookup_value)[:2])
    if len(matches) == 1:
        return matches[0], None
    if len(matches) > 1:
        return None, (
            f"Hay varios registros llamados '{lookup_value}' en {field.relation_database.name}. "
            "Importa usando el ID del registro relacionado."
        )
    return None, f"No se encontro '{lookup_value}' en {field.relation_database.name}."


def _relation_preview_payload(related_record):
    preview_fields = []
    for related_field in related_record.database.fields.filter(show_in_table=True)[:4]:
        preview_fields.append(
            {
                "label": related_field.label,
                "value": related_record.get_display_value(related_field) or "-",
            }
        )
    return {
        "title": related_record.title,
        "database_name": related_record.database.name,
        "detail_url": reverse("record_detail", args=[related_record.database.slug, related_record.pk]),
        "edit_url": reverse("record_edit", args=[related_record.database.slug, related_record.pk]),
        "fields": preview_fields,
    }


def _sync_record_titles_for_field(database, primary_field):
    updated = 0
    for record in database.records.all():
        raw_value = record.data.get(primary_field.key)
        new_title = _record_title_from_value(primary_field, raw_value).strip()
        if new_title and record.title != new_title:
            record.title = new_title
            record.save(update_fields=["title", "updated_at"])
            updated += 1
    return updated


def _set_primary_field(database, custom_field):
    custom_field.is_primary = True
    custom_field.save(update_fields=["is_primary"])
    return _sync_record_titles_for_field(database, custom_field)


def _filter_records_queryset(records, *, query="", record_id="", priority="", has_priority=False):
    if record_id.isdigit():
        records = records.filter(pk=int(record_id))
    if query:
        id_query = Q(pk=int(query)) if query.isdigit() else Q()
        records = records.filter(id_query | Q(title__icontains=query) | Q(data_text__icontains=query))
    if priority and has_priority:
        records = records.filter(priority=priority)
    return records


def _load_demo_records(database, user, template_key):
    primary_field = database.get_primary_field()
    available_field_keys = {field.key for field in database.fields.all()}
    if not primary_field:
        return
    for item in DEMO_RECORDS.get(template_key, []):
        data = {
            key: value
            for key, value in item["data"].items()
            if key in available_field_keys
        }
        title = _record_title_from_value(primary_field, data.get(primary_field.key)) or item["title"]
        Record.objects.create(
            database=database,
            title=title,
            priority=item["priority"] if database.has_priority else Record.Priority.NORMAL,
            data=data,
            created_by=user,
            updated_by=user,
        )


@login_required
def dashboard(request):
    memberships = (
        DatabaseMembership.objects.select_related("database")
        .filter(user=request.user)
        .order_by("database__name")
    )
    stats = {
        "databases": memberships.count(),
        "records": Record.objects.filter(database__memberships__user=request.user).distinct().count(),
        "urgent": Record.objects.filter(
            database__memberships__user=request.user,
            priority=Record.Priority.URGENT,
        )
        .distinct()
        .count(),
    }
    quick_starts = [
        {
            "title": "Productos",
            "description": "Stock, precios y reposicion para comercios o catalogos internos.",
        },
        {
            "title": "Clientes y pedidos",
            "description": "Crea una base comercial y conecta sus relaciones para una demo realista.",
        },
        {
            "title": "Alumnos",
            "description": "Seguimiento de cursos, contacto y fechas clave.",
        },
        {
            "title": "General",
            "description": "Cualquier lista operativa con campos personalizados.",
        },
    ]
    return render(
        request,
        "dashboard.html",
        {
            "memberships": memberships,
            "stats": stats,
            "recent_records": Record.objects.filter(database__memberships__user=request.user).select_related("database")[:6],
            "quick_starts": quick_starts,
        },
    )


@login_required
def database_create(request):
    step = request.POST.get("step") or request.GET.get("step") or "1"
    if step not in {"1", "2", "3", "4"}:
        step = "1"

    wizard_state = {
        "starter_template": request.POST.get("starter_template") or request.GET.get("starter_template") or "inventory",
        "use_case": request.POST.get("use_case") or request.GET.get("use_case") or AppDatabase.UseCase.INVENTORY,
        "name": request.POST.get("name") or request.GET.get("name") or "",
        "description": request.POST.get("description") or request.GET.get("description") or "",
        "selected_fields": request.POST.getlist("selected_fields"),
        "load_demo_data": request.POST.get("load_demo_data") in {"on", "true", "1"},
        "custom_fields": [],
    }
    templates_catalog = _template_catalog()
    template_key = wizard_state["starter_template"]
    wizard_state["use_case"] = _template_use_case(template_key)
    if request.method != "POST" and not wizard_state["selected_fields"]:
        wizard_state["selected_fields"] = _base_field_keys(template_key)
    assistant = _assistant_context(template_key)
    template_form = WizardTemplateForm(
        request.POST if request.method == "POST" and step == "1" else None,
        initial={
            "starter_template": wizard_state["starter_template"],
        },
    )
    setup_form = WizardSetupForm(
        request.POST if request.method == "POST" and step == "2" else None,
        initial={
            "name": wizard_state["name"] or assistant["suggested_name"],
            "description": wizard_state["description"],
        },
    )
    options_form = WizardOptionsForm(
        request.POST if request.method == "POST" and step == "3" else None,
        field_choices=[(item["key"], item["label"]) for item in _field_option_catalog(template_key)],
        initial={
            "selected_fields": wizard_state["selected_fields"],
            "load_demo_data": wizard_state["load_demo_data"] if request.method == "POST" else True,
            "custom_fields_json": "[]",
        },
    )

    if request.method == "POST":
        if request.POST.get("nav") == "back":
            wizard_state["selected_fields"] = request.POST.getlist("selected_fields")
            wizard_state["load_demo_data"] = request.POST.get("load_demo_data") in {"on", "true", "1"}
            custom_fields_json = request.POST.get("custom_fields_json", "[]")
            try:
                wizard_state["custom_fields"] = json.loads(custom_fields_json)
            except json.JSONDecodeError:
                wizard_state["custom_fields"] = []
            options_form = WizardOptionsForm(
                initial={
                    "selected_fields": wizard_state["selected_fields"],
                    "load_demo_data": wizard_state["load_demo_data"],
                    "custom_fields_json": custom_fields_json,
                },
                field_choices=[(item["key"], item["label"]) for item in _field_option_catalog(template_key)],
            )
            return render(
                request,
                "database_create.html",
                _wizard_render_context(
                    templates_catalog=templates_catalog,
                    step="3",
                    wizard_state=wizard_state,
                    assistant=assistant,
                    template_form=template_form,
                    setup_form=setup_form,
                    options_form=options_form,
                ),
            )
        if step == "1" and template_form.is_valid():
            cleaned = template_form.cleaned_data
            selected_use_case = _template_use_case(cleaned["starter_template"])
            return redirect(f"{request.path}?{urlencode({'step': 2, 'starter_template': cleaned['starter_template'], 'use_case': selected_use_case})}")
        if step == "2" and setup_form.is_valid():
            cleaned = setup_form.cleaned_data
            return redirect(
                f"{request.path}?{urlencode({
                    'step': 3,
                    'starter_template': wizard_state['starter_template'],
                    'use_case': wizard_state['use_case'],
                    'name': cleaned['name'],
                    'description': cleaned['description'],
                })}"
            )
        if step == "3" and options_form.is_valid():
            wizard_state["selected_fields"] = options_form.cleaned_data["selected_fields"]
            wizard_state["load_demo_data"] = options_form.cleaned_data["load_demo_data"]
            wizard_state["custom_fields"] = options_form.cleaned_data["custom_fields"]
            step = "4"
        elif step == "4":
            wizard_state["selected_fields"] = request.POST.getlist("selected_fields")
            custom_fields_json = request.POST.get("custom_fields_json", "[]")
            try:
                wizard_state["custom_fields"] = json.loads(custom_fields_json)
            except json.JSONDecodeError:
                wizard_state["custom_fields"] = []
            database = AppDatabase.objects.create(
                name=wizard_state["name"],
                description=wizard_state["description"],
                has_priority="__priority__" in wizard_state["selected_fields"],
                use_case=wizard_state["use_case"],
                created_by=request.user,
            )
            DatabaseMembership.objects.create(
                database=database,
                user=request.user,
                role=DatabaseMembership.Role.ADMIN,
            )
            selected_template = wizard_state["starter_template"]
            _create_selected_template_fields(database, selected_template, wizard_state["selected_fields"])
            selected_extra_keys = [
                key for key in wizard_state["selected_fields"]
                if key in dict(SUGGESTED_EXTRA_FIELDS.get(selected_template, []))
            ]
            _create_extra_fields(database, selected_extra_keys)
            _create_manual_fields(database, wizard_state["custom_fields"])
            if wizard_state["load_demo_data"]:
                _load_demo_records(database, request.user, selected_template)
            _log_database_activity(
                database,
                request.user,
                "Base creada",
                "Se creo la base y quedo lista para empezar a trabajar.",
                payload={
                    "summary": [
                        {"label": "Base", "value": database.name},
                        {"label": "Tipo inicial", "value": database.get_use_case_display()},
                    ]
                },
            )
            messages.success(request, "La lista fue creada. El asistente te dejo una base lista para empezar.")
            return redirect(_database_tab_url(database, "daily"))
    return render(
        request,
        "database_create.html",
        _wizard_render_context(
            templates_catalog=templates_catalog,
            step=step,
            wizard_state=wizard_state,
            assistant=assistant,
            template_form=template_form,
            setup_form=setup_form,
            options_form=options_form,
        ),
    )


@login_required
def database_detail(request, slug):
    database, membership = _get_database_for_user(request.user, slug)
    primary_field = database.get_primary_field()
    active_tab = request.GET.get("tab", "records")
    if active_tab not in DETAIL_TABS:
        active_tab = "records"
    saved_view_id = request.GET.get("saved_view")
    q = request.GET.get("q", "").strip()
    record_id = request.GET.get("record_id", "").strip()
    priority = request.GET.get("priority", "").strip()
    view_mode = request.GET.get("view", "table")
    if view_mode not in {"table", "cards"}:
        view_mode = "table"
    sort = request.GET.get("sort", "updated")
    sort_map = {
        "updated": "-updated_at",
        "title": "title",
        "created": "-created_at",
    }
    if database.has_priority:
        sort_map["priority"] = "priority"

    records = _filter_records_queryset(
        database.records.all().annotate(data_text=Cast("data", output_field=TextField())),
        query=q,
        record_id=record_id,
        priority=priority,
        has_priority=database.has_priority,
    )
    if saved_view_id:
        saved_view = database.saved_views.filter(user=request.user, pk=saved_view_id).first()
        if saved_view:
            q = saved_view.query
            priority = saved_view.priority if database.has_priority else ""
            sort = saved_view.sort
            view_mode = saved_view.view_mode
            records = _filter_records_queryset(
                database.records.all().annotate(data_text=Cast("data", output_field=TextField())),
                query=q,
                record_id=record_id,
                priority=priority,
                has_priority=database.has_priority,
            )
    records = records.order_by(sort_map.get(sort, "-updated_at"))
    paginator = Paginator(records, 20)
    page_obj = paginator.get_page(request.GET.get("page") or 1)

    total_records = database.records.count()
    high_priority_count = database.records.filter(priority=Record.Priority.HIGH).count() if database.has_priority else 0
    urgent_count = database.records.filter(priority=Record.Priority.URGENT).count() if database.has_priority else 0
    relation_fields = database.fields.filter(field_type=CustomField.FieldType.RELATION).select_related("relation_database")
    select_fields = database.fields.filter(field_type=CustomField.FieldType.SELECT)
    relation_previews = {}
    accessible_database_ids = set(_accessible_databases_for_user(request.user).values_list("pk", flat=True))
    for record in page_obj.object_list:
        for field in relation_fields:
            raw_value = record.data.get(field.key)
            if not raw_value or not field.relation_database or field.relation_database_id not in accessible_database_ids:
                continue
            related_record, relation_error = _resolve_related_record(field, raw_value)
            if related_record:
                relation_previews[f"{record.pk}:{field.key}"] = _relation_preview_payload(related_record)
            elif relation_error:
                relation_previews[f"{record.pk}:{field.key}"] = {
                    "title": "Relacion no disponible",
                    "database_name": field.relation_database.name,
                    "detail_url": "",
                    "edit_url": "",
                    "fields": [{"label": "Estado", "value": relation_error}],
                }
    field_cards = [
        {
            "field": field,
            "form": CustomFieldForm(database=database, actor=request.user, instance=field),
            "has_data": _field_has_data(field),
        }
        for field in database.fields.all()
    ]
    daily_records = (
        database.records.exclude(priority=Record.Priority.NORMAL)[:8]
        if database.has_priority
        else database.records.all()[:8]
    )
    import_summary = request.session.pop(_import_session_key(database) + "_summary", None)
    history_page = Paginator(database.activities.select_related("actor"), 25).get_page(request.GET.get("history_page") or 1)
    history_payloads = {str(item.pk): _history_payload_for_activity(item) for item in history_page.object_list}
    recent_activities = database.activities.all()
    today = timezone.localdate()
    history_stats = {
        "total": recent_activities.count(),
        "today": recent_activities.filter(created_at__date=today).count(),
        "actors": recent_activities.exclude(actor=None).values("actor").distinct().count(),
    }

    context = {
        "database": database,
        "primary_field": primary_field,
        "has_priority": database.has_priority,
        "membership": membership,
        "active_tab": active_tab,
        "table_fields": database.fields.filter(show_in_table=True),
        "all_fields": database.fields.all(),
        "field_cards": field_cards,
        "relation_fields": relation_fields,
        "relation_previews": relation_previews,
        "select_fields": select_fields,
        "records": page_obj.object_list,
        "page_obj": page_obj,
        "daily_records": daily_records,
        "query": q,
        "selected_record_id": record_id,
        "selected_priority": priority,
        "priority_choices": Record.Priority.choices if database.has_priority else [],
        "view_mode": view_mode,
        "sort": sort,
        "sort_choices": [
            ("updated", "Actualizados recientemente"),
            ("created", "Mas nuevos"),
            ("title", "Nombre"),
        ] + ([("priority", "Prioridad")] if database.has_priority else []),
        "stats": {
            "records": total_records,
            "high": high_priority_count,
            "urgent": urgent_count,
            "fields": database.fields.count(),
            "relations": relation_fields.count(),
            "selects": select_fields.count(),
        },
        "field_form": CustomFieldForm(database=database, actor=request.user),
        "member_form": MembershipForm(database=database),
        "import_form": CSVImportForm(database=database),
        "import_summary": import_summary,
        "history_page": history_page,
        "history_payloads": history_payloads,
        "history_stats": history_stats,
    }
    return render(request, "database_detail.html", context)


@login_required
def saved_view_create(request, slug):
    database, membership = _get_database_for_user(request.user, slug)
    form = SaveViewForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        SavedView.objects.update_or_create(
            database=database,
            user=request.user,
            name=form.cleaned_data["name"],
            defaults={
                "query": request.POST.get("query", "").strip(),
                "priority": request.POST.get("priority", "").strip() if database.has_priority else "",
                "sort": request.POST.get("sort", "updated"),
                "view_mode": request.POST.get("view_mode", "table"),
            },
        )
        messages.success(request, "La vista fue guardada para reutilizarla.")
    return redirect("database_detail", slug=database.slug)


@login_required
def database_statistics(request, slug):
    database, membership = _get_database_for_user(request.user, slug)
    chart_ready_fields = database.fields.filter(
        field_type__in=[
            CustomField.FieldType.SELECT,
            CustomField.FieldType.NUMBER,
            CustomField.FieldType.CURRENCY,
            CustomField.FieldType.DATE,
            CustomField.FieldType.BOOLEAN,
        ]
    )
    return render(
        request,
        "database_statistics.html",
        {
            "database": database,
            "membership": membership,
            "chart_ready_fields": chart_ready_fields,
            "total_records": database.records.count(),
        },
    )


@login_required
def database_delete(request, slug):
    database, membership = _get_database_for_user(request.user, slug)
    if membership.role != DatabaseMembership.Role.ADMIN:
        return HttpResponseForbidden("Solo los administradores pueden eliminar una base.")

    expected_phrase = "ELIMINAR"
    if request.method == "POST":
        confirmation_name = request.POST.get("confirmation_name", "").strip()
        confirmation_phrase = request.POST.get("confirmation_phrase", "").strip().upper()
        if confirmation_name != database.name or confirmation_phrase != expected_phrase:
            messages.error(
                request,
                "La confirmacion no coincide. Escribe el nombre exacto de la base y la palabra ELIMINAR para continuar.",
            )
        else:
            database_name = database.name
            database.delete()
            messages.success(request, f"La base {database_name} fue eliminada.")
            return redirect("dashboard")

    return render(
        request,
        "database_confirm_delete.html",
        {
            "database": database,
            "membership": membership,
            "expected_phrase": expected_phrase,
        },
    )


@login_required
def field_create(request, slug):
    database, membership = _get_database_for_user(request.user, slug)
    if membership.role != DatabaseMembership.Role.ADMIN:
        return HttpResponseForbidden("Solo los administradores pueden crear campos.")

    form = CustomFieldForm(database, request.POST or None, actor=request.user)
    if request.method == "POST" and form.is_valid():
        field = form.save()
        _log_database_activity(
            database,
            request.user,
            "Campo agregado",
            f"Se agrego el campo {field.label}.",
            payload={
                "summary": [
                    {"label": "Campo", "value": field.label},
                    {"label": "Tipo", "value": field.get_field_type_display()},
                ]
            },
        )
        messages.success(request, "El campo fue agregado.")
    else:
        messages.error(request, "Revisa los datos del campo.")
    return redirect(_database_tab_url(database, "structure"))


@login_required
def field_update(request, slug, field_id):
    database, membership = _get_database_for_user(request.user, slug)
    if membership.role != DatabaseMembership.Role.ADMIN:
        return HttpResponseForbidden("Solo los administradores pueden editar campos.")

    custom_field = get_object_or_404(database.fields, pk=field_id)
    previous_label = custom_field.label
    previous_type = custom_field.get_field_type_display()
    form = CustomFieldForm(database, request.POST or None, actor=request.user, instance=custom_field)
    if request.method == "POST" and form.is_valid():
        updated_field = form.save()
        _log_database_activity(
            database,
            request.user,
            "Campo editado",
            f"Se actualizo el campo {updated_field.label}.",
            payload={
                "changes": [
                    {"label": "Nombre", "before": previous_label, "after": updated_field.label},
                    {"label": "Tipo", "before": previous_type, "after": updated_field.get_field_type_display()},
                ]
            },
        )
        messages.success(request, f"El campo {custom_field.label} fue actualizado.")
    else:
        messages.error(request, "No se pudo actualizar el campo.")
    return redirect(_database_tab_url(database, "structure"))


@login_required
def field_set_primary_select(request, slug):
    database, membership = _get_database_for_user(request.user, slug)
    if membership.role != DatabaseMembership.Role.ADMIN:
        return HttpResponseForbidden("Solo los administradores pueden definir el nombre visible del registro.")

    if request.method == "POST":
        selected_field_id = request.POST.get("primary_field_id", "").strip()
        custom_field = database.fields.filter(pk=selected_field_id).first()
        if custom_field:
            synced = _set_primary_field(database, custom_field)
            _log_database_activity(
                database,
                request.user,
                "Columna principal actualizada",
                f"{custom_field.label} ahora identifica el nombre visible de los registros.",
                payload={
                    "summary": [
                        {"label": "Nueva columna principal", "value": custom_field.label},
                    ]
                },
            )
            if synced:
                messages.success(
                    request,
                    f"{custom_field.label} ahora define el nombre visible del registro. Se actualizaron {synced} registros existentes.",
                )
            else:
                messages.success(request, f"{custom_field.label} ahora define el nombre visible del registro.")
        else:
            messages.error(request, "No se encontro el campo seleccionado para el registro.")
    return redirect(_database_tab_url(database, "structure"))


@login_required
def field_set_primary(request, slug, field_id):
    database, membership = _get_database_for_user(request.user, slug)
    if membership.role != DatabaseMembership.Role.ADMIN:
        return HttpResponseForbidden("Solo los administradores pueden definir el nombre visible del registro.")

    custom_field = get_object_or_404(database.fields, pk=field_id)
    if request.method == "POST":
        synced = _set_primary_field(database, custom_field)
        _log_database_activity(
            database,
            request.user,
            "Columna principal actualizada",
            f"{custom_field.label} ahora identifica el nombre visible de los registros.",
            payload={
                "summary": [
                    {"label": "Nueva columna principal", "value": custom_field.label},
                ]
            },
        )
        if synced:
            messages.success(
                request,
                f"{custom_field.label} ahora define el nombre visible del registro. Se actualizaron {synced} registros existentes.",
            )
        else:
            messages.success(request, f"{custom_field.label} ahora define el nombre visible del registro.")
    return redirect(_database_tab_url(database, "structure"))


@login_required
def field_delete(request, slug, field_id):
    database, membership = _get_database_for_user(request.user, slug)
    if membership.role != DatabaseMembership.Role.ADMIN:
        return HttpResponseForbidden("Solo los administradores pueden eliminar campos.")

    custom_field = get_object_or_404(database.fields, pk=field_id)
    if request.method == "POST":
        if _field_has_data(custom_field):
            messages.error(
                request,
                f"No se puede eliminar {custom_field.label} porque ya tiene datos cargados. Vacia o migra esos registros primero.",
            )
            return redirect(_database_tab_url(database, "structure"))
        field_name = custom_field.label
        was_primary = custom_field.is_primary
        custom_field.delete()
        _log_database_activity(
            database,
            request.user,
            "Campo eliminado",
            f"Se elimino el campo {field_name}.",
            payload={"summary": [{"label": "Campo eliminado", "value": field_name}]},
        )
        if was_primary:
            next_field = database.fields.order_by("position", "id").first()
            if next_field:
                _set_primary_field(database, next_field)
        messages.success(request, f"El campo {field_name} fue eliminado.")
    return redirect(_database_tab_url(database, "structure"))


@login_required
def member_create(request, slug):
    database, membership = _get_database_for_user(request.user, slug)
    if membership.role != DatabaseMembership.Role.ADMIN:
        return HttpResponseForbidden("Solo los administradores pueden asignar miembros.")

    form = MembershipForm(database, request.POST or None)
    if request.method == "POST" and form.is_valid():
        membership = form.save()
        _log_database_activity(
            database,
            request.user,
            "Permisos actualizados",
            f"{membership.user.username} quedo con rol {membership.get_role_display().lower()}.",
            payload={
                "summary": [
                    {"label": "Usuario", "value": membership.user.username},
                    {"label": "Rol", "value": membership.get_role_display()},
                ]
            },
        )
        messages.success(request, "El rol fue actualizado.")
    else:
        messages.error(request, "No se pudo actualizar el miembro.")
    return redirect("database_detail", slug=database.slug)


@login_required
@xframe_options_exempt
def record_create(request, slug):
    database, membership = _get_database_for_user(request.user, slug)
    form = RecordForm(database, request.POST or None, actor=request.user)
    if request.method == "POST" and form.is_valid():
        record = form.save(user=request.user)
        _log_database_activity(
            database,
            request.user,
            "Registro agregado",
            f"Se creo el registro {record.title}.",
            payload={
                "summary": [
                    {"label": "Registro", "value": record.title},
                    {"label": "ID", "value": str(record.pk)},
                ]
            },
        )
        if request.GET.get("popup") == "1" and request.GET.get("relation_field"):
            return render(
                request,
                "related_record_popup_done.html",
                {
                    "record": record,
                    "relation_field": request.GET.get("relation_field"),
                },
            )
        messages.success(request, "Registro creado.")
        return redirect("database_detail", slug=database.slug)
    return render(
        request,
        "record_form.html",
        {"form": form, "database": database, "mode": "create"},
    )


@login_required
def record_detail(request, slug, pk):
    database, membership = _get_database_for_user(request.user, slug)
    record = get_object_or_404(database.records, pk=pk)
    accessible_databases = _accessible_databases_for_user(request.user)
    accessible_database_ids = set(accessible_databases.values_list("pk", flat=True))

    outgoing_relations = []
    for field in database.fields.filter(field_type=CustomField.FieldType.RELATION).select_related("relation_database"):
        raw_value = record.data.get(field.key)
        if not raw_value or not field.relation_database or field.relation_database_id not in accessible_database_ids:
            continue
        related_record, relation_error = _resolve_related_record(field, raw_value)
        outgoing_relations.append(
            {
                "field": field,
                "database": field.relation_database,
                "record": related_record,
                "error": relation_error,
                "raw_value": raw_value,
            }
        )

    incoming_relations = []
    relation_fields = (
        CustomField.objects.filter(
            field_type=CustomField.FieldType.RELATION,
            relation_database=database,
            database__in=accessible_databases,
        )
        .select_related("database", "relation_database")
        .order_by("database__name", "label")
    )
    for relation_field in relation_fields:
        linked_records = relation_field.database.records.filter(**{f"data__{relation_field.key}": str(record.pk)})
        if linked_records.exists():
            incoming_relations.append(
                {
                    "field": relation_field,
                    "database": relation_field.database,
                    "records": linked_records,
                }
            )

    return render(
        request,
        "record_detail.html",
        {
            "database": database,
            "membership": membership,
            "record": record,
            "fields": database.fields.all(),
            "outgoing_relations": outgoing_relations,
            "incoming_relations": incoming_relations,
        },
    )


@login_required
def record_edit(request, slug, pk):
    database, membership = _get_database_for_user(request.user, slug)
    record = get_object_or_404(database.records, pk=pk)
    previous_title = record.title
    previous_data = dict(record.data or {})
    previous_priority = record.priority
    form = RecordForm(database, request.POST or None, record=record, actor=request.user)
    if request.method == "POST" and form.is_valid():
        updated_record = form.save(user=request.user)
        changes = _record_changes_for_history(database, previous_data, updated_record.data)
        if database.has_priority and previous_priority != updated_record.priority:
            changes.append(
                {
                    "label": "Prioridad",
                    "before": dict(Record.Priority.choices).get(previous_priority, previous_priority),
                    "after": updated_record.get_priority_display(),
                }
            )
        if previous_title != updated_record.title:
            changes.insert(0, {"label": "Nombre visible", "before": previous_title, "after": updated_record.title})
        _log_database_activity(
            database,
            request.user,
            "Registro editado",
            f"Se actualizo el registro {updated_record.title}.",
            payload={
                "summary": [
                    {"label": "Registro", "value": updated_record.title},
                    {"label": "ID", "value": str(updated_record.pk)},
                ],
                "changes": changes,
            },
        )
        messages.success(request, "Registro actualizado.")
        return redirect("database_detail", slug=database.slug)
    return render(
        request,
        "record_form.html",
        {"form": form, "database": database, "record": record, "mode": "edit"},
    )


@login_required
def record_delete(request, slug, pk):
    database, membership = _get_database_for_user(request.user, slug)
    record = get_object_or_404(database.records, pk=pk)
    if request.method == "POST":
        record_title = record.title
        record.delete()
        _log_database_activity(
            database,
            request.user,
            "Registro eliminado",
            f"Se elimino el registro {record_title}.",
            payload={"summary": [{"label": "Registro eliminado", "value": record_title}]},
        )
        messages.success(request, "Registro eliminado.")
        return redirect("database_detail", slug=database.slug)
    return render(
        request,
        "record_confirm_delete.html",
        {"database": database, "record": record},
    )


@login_required
def records_import_start(request, slug):
    database, membership = _get_database_for_user(request.user, slug)
    if request.method != "POST":
        return redirect(f"{reverse('database_detail', args=[database.slug])}?tab=manage")

    form = CSVImportForm(database, request.POST, request.FILES)
    if not form.is_valid():
        for errors in form.errors.values():
            for error in errors:
                messages.error(request, error)
        return redirect(f"{reverse('database_detail', args=[database.slug])}?tab=manage")

    try:
        temp_path = form.save_temporary_upload()
        inspection = form.inspect_file(temp_path)
    except (UnicodeDecodeError, ValidationError) as exc:
        _cleanup_import_file(locals().get("temp_path"))
        logger.warning("No se pudo inspeccionar el CSV de %s: %s", database.slug, exc)
        messages.error(request, f"No se pudo leer el CSV: {exc}")
        return redirect(f"{reverse('database_detail', args=[database.slug])}?tab=manage")
    if inspection["total_rows"] == 0:
        _cleanup_import_file(temp_path)
        messages.error(request, "El archivo no contiene filas para importar.")
        return redirect(f"{reverse('database_detail', args=[database.slug])}?tab=manage")

    request.session[_import_session_key(database)] = {
        "headers": inspection["headers"],
        "preview_rows": inspection["preview_rows"],
        "total_rows": inspection["total_rows"],
        "file_path": temp_path,
        "has_header": form.cleaned_data["has_header"],
    }
    return redirect("records_import_map", slug=database.slug)


@login_required
def records_import_map(request, slug):
    database, membership = _get_database_for_user(request.user, slug)
    primary_field = database.get_primary_field()
    session_key = _import_session_key(database)
    payload = request.session.get(session_key)
    if not payload:
        messages.error(request, "Primero sube un CSV para mapear columnas.")
        return redirect(f"{reverse('database_detail', args=[database.slug])}?tab=manage")

    headers = payload.get("headers", [])
    preview_rows = payload.get("preview_rows", [])
    total_rows = payload.get("total_rows", 0)
    file_path = payload.get("file_path")
    has_header = payload.get("has_header", True)
    form = CSVMappingForm(database, headers, request.POST or None)

    if request.method == "POST" and form.is_valid():
        mapping = {
            header: form.cleaned_data[f"map_{header}"]
            for header in headers
            if form.cleaned_data[f"map_{header}"] != "__ignore__"
        }
        if not primary_field:
            messages.error(request, "Esta base no tiene un campo principal definido todavia.")
            return redirect("records_import_map", slug=database.slug)
        if primary_field.key not in mapping.values():
            messages.error(request, f"Debes asignar una columna al campo {primary_field.label} antes de importar.")
            return redirect("records_import_map", slug=database.slug)
        valid_priorities = {choice[0] for choice in Record.Priority.choices} if database.has_priority else set()
        imported = 0
        skipped = 0
        row_errors = []
        csv_form = CSVImportForm(database=database, data={"has_header": has_header})
        csv_form.cleaned_data = {"has_header": has_header}
        try:
            for row_number, row in enumerate(csv_form.iter_rows(file_path), start=1):
                normalized = {}
                for header, target in mapping.items():
                    normalized[target] = row.get(header, "")

                title = str(normalized.get(primary_field.key, "")).strip()
                if not title:
                    skipped += 1
                    row_errors.append(f"Fila {row_number}: falta el valor para {primary_field.label}.")
                    continue

                priority = Record.Priority.NORMAL
                if database.has_priority:
                    priority = str(normalized.get("priority", Record.Priority.NORMAL)).lower().strip() or Record.Priority.NORMAL
                    if priority not in valid_priorities:
                        priority = Record.Priority.NORMAL

                record_data = {}
                for field in database.fields.all():
                    value = normalized.get(field.key, "")
                    if value in ("", None):
                        record_data[field.key] = False if field.field_type == CustomField.FieldType.BOOLEAN else ""
                    elif field.field_type == CustomField.FieldType.BOOLEAN:
                        record_data[field.key] = str(value).strip().lower() in {"1", "true", "si", "yes", "x"}
                    elif field.field_type == CustomField.FieldType.RELATION and field.relation_database:
                        if not field.relation_database.memberships.filter(user=request.user).exists():
                            raise ValidationError(
                                f"No tienes acceso a la base relacionada {field.relation_database.name} para importar este campo."
                            )
                        related_record, relation_error = _resolve_related_record(field, value)
                        if not related_record:
                            skipped += 1
                            row_errors.append(
                                f"Fila {row_number}: {relation_error}"
                            )
                            record_data = None
                            break
                        record_data[field.key] = str(related_record.pk)
                    else:
                        record_data[field.key] = str(value).strip()
                if record_data is None:
                    continue

                Record.objects.create(
                    database=database,
                    title=title,
                    priority=priority,
                    data=record_data,
                    created_by=request.user,
                    updated_by=request.user,
                )
                imported += 1
        except ValidationError as exc:
            logger.warning("No se pudo importar CSV en %s: %s", database.slug, exc)
            messages.error(request, f"No se pudo importar: {exc}")
            return redirect("records_import_map", slug=database.slug)

        _cleanup_import_file(file_path)
        request.session.pop(session_key, None)
        summary = {
            "imported": imported,
            "skipped": skipped,
            "errors": row_errors[:8],
            "total_rows": total_rows,
        }
        request.session[session_key + "_summary"] = summary
        _log_database_activity(
            database,
            request.user,
            "Importacion CSV",
            f"Se importaron {imported} filas y se omitieron {skipped} desde un archivo CSV.",
            payload={
                "summary": [
                    {"label": "Filas importadas", "value": str(imported)},
                    {"label": "Filas omitidas", "value": str(skipped)},
                ]
            },
        )
        messages.success(request, f"Se importaron {imported} de {total_rows} filas usando el mapeo guiado.")
        if skipped:
            messages.error(request, f"Se omitieron {skipped} filas por errores de validacion.")
            for error in row_errors[:5]:
                messages.error(request, error)
        return redirect(f"{reverse('database_detail', args=[database.slug])}?tab=records")

    return render(
        request,
        "import_map.html",
        {
            "database": database,
            "form": form,
            "headers": headers,
            "preview_rows": preview_rows,
            "total_rows": total_rows,
        },
    )


def error_404(request, exception):
    return render(request, "errors/404.html", status=404)


def error_500(request):
    return render(request, "errors/500.html", status=500)


@login_required
def records_export(request, slug):
    database, membership = _get_database_for_user(request.user, slug)
    _log_database_activity(
        database,
        request.user,
        "Exportacion CSV",
        "Se exporto la base completa en formato CSV.",
        payload={"summary": [{"label": "Formato", "value": "CSV"}]},
    )
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{database.slug}.csv"'
    response.write("\ufeff")

    writer = csv.writer(response)
    fields = list(database.fields.all())
    headers = [field.label for field in fields]
    if database.has_priority:
        headers.append("Prioridad")
    writer.writerow(headers)
    for record in database.records.all():
        row = []
        for field in fields:
            row.append(record.get_display_value(field))
        if database.has_priority:
            row.append(record.priority)
        writer.writerow(row)
    return response
