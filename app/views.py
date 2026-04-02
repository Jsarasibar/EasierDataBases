import csv
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

from .forms import CSVImportForm, CSVMappingForm, CustomFieldForm, MembershipForm, RecordForm, RegisterForm, SaveViewForm, WizardOptionsForm, WizardSetupForm, WizardTemplateForm
from .models import AppDatabase, CustomField, DatabaseMembership, Record, SavedView

logger = logging.getLogger(__name__)


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


def _create_inventory_template(database):
    default_fields = [
        ("Nombre", CustomField.FieldType.TEXT, True, True, "Nombre del producto"),
        ("SKU", CustomField.FieldType.TEXT, False, True, "Codigo interno o referencia"),
        ("Precio", CustomField.FieldType.CURRENCY, True, True, "Valor de venta"),
        ("Stock", CustomField.FieldType.NUMBER, True, True, "Cantidad disponible"),
        ("Categoria", CustomField.FieldType.TEXT, False, True, "Linea o familia del producto"),
        ("Reponer", CustomField.FieldType.BOOLEAN, False, True, "Marca si necesita reposicion"),
    ]
    for position, (label, field_type, required, show_in_table, help_text) in enumerate(default_fields, start=1):
        CustomField.objects.create(
            database=database,
            label=label,
            field_type=field_type,
            required=required,
            show_in_table=show_in_table,
            help_text=help_text,
            position=position,
        )


def _create_students_template(database):
    default_fields = [
        ("Nombre", CustomField.FieldType.TEXT, True, True, "Nombre completo del alumno"),
        ("Curso", CustomField.FieldType.TEXT, True, True, "Programa o curso asignado"),
        ("Email", CustomField.FieldType.EMAIL, False, True, "Contacto principal"),
        ("Telefono", CustomField.FieldType.PHONE, False, False, "Telefono del alumno"),
        ("Fecha de inicio", CustomField.FieldType.DATE, False, True, "Inicio de cursada"),
        ("Cuota al dia", CustomField.FieldType.BOOLEAN, False, True, "Marca si esta al dia"),
    ]
    for position, (label, field_type, required, show_in_table, help_text) in enumerate(default_fields, start=1):
        CustomField.objects.create(
            database=database,
            label=label,
            field_type=field_type,
            required=required,
            show_in_table=show_in_table,
            help_text=help_text,
            position=position,
        )


def _create_clients_template(database):
    default_fields = [
        ("Nombre", CustomField.FieldType.TEXT, True, True, "Nombre del contacto"),
        ("Empresa", CustomField.FieldType.TEXT, False, True, "Empresa o razon social"),
        ("Email", CustomField.FieldType.EMAIL, False, True, "Correo de contacto"),
        ("Telefono", CustomField.FieldType.PHONE, False, False, "Numero principal"),
        ("Ultimo contacto", CustomField.FieldType.DATE, False, True, "Fecha del ultimo seguimiento"),
        ("Activo", CustomField.FieldType.BOOLEAN, False, True, "Cliente activo o prospecto"),
    ]
    for position, (label, field_type, required, show_in_table, help_text) in enumerate(default_fields, start=1):
        CustomField.objects.create(
            database=database,
            label=label,
            field_type=field_type,
            required=required,
            show_in_table=show_in_table,
            help_text=help_text,
            position=position,
        )


def _create_generic_template(database):
    default_fields = [
        ("Nombre", CustomField.FieldType.TEXT, True, True, "Nombre principal del registro"),
        ("Estado", CustomField.FieldType.TEXT, False, True, "Situacion o etapa del registro"),
        ("Responsable", CustomField.FieldType.TEXT, False, True, "Persona a cargo"),
        ("Fecha objetivo", CustomField.FieldType.DATE, False, True, "Fecha estimada"),
        ("Importe", CustomField.FieldType.CURRENCY, False, True, "Valor economico opcional"),
    ]
    for position, (label, field_type, required, show_in_table, help_text) in enumerate(default_fields, start=1):
        CustomField.objects.create(
            database=database,
            label=label,
            field_type=field_type,
            required=required,
            show_in_table=show_in_table,
            help_text=help_text,
            position=position,
        )


STARTER_TEMPLATES = {
    "inventory": _create_inventory_template,
    "students": _create_students_template,
    "clients": _create_clients_template,
    "generic": _create_generic_template,
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
            "fields": ["Nombre", "SKU", "Precio", "Stock", "Categoria", "Reponer"],
        },
        {
            "key": "students",
            "title": "Alumnos / Cursos",
            "description": "Pensada para academias, talleres y capacitaciones.",
            "fields": ["Nombre", "Curso", "Email", "Telefono", "Fecha de inicio", "Cuota al dia"],
        },
        {
            "key": "clients",
            "title": "Clientes / Contactos",
            "description": "Sirve para relaciones comerciales, prospectos o soporte.",
            "fields": ["Nombre", "Empresa", "Email", "Telefono", "Ultimo contacto", "Activo"],
        },
        {
            "key": "generic",
            "title": "Otra base",
            "description": "Una estructura neutra para procesos internos, tareas, pedidos o cualquier otra cosa.",
            "fields": ["Nombre", "Estado", "Responsable", "Fecha objetivo", "Importe"],
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


def _assistant_context(template_key):
    return ASSISTANT_COPY.get(template_key, ASSISTANT_COPY["generic"])


def _create_extra_fields(database, selected_extra_keys):
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


def _load_demo_records(database, user, template_key):
    for item in DEMO_RECORDS.get(template_key, []):
        Record.objects.create(
            database=database,
            title=item["title"],
            priority=item["priority"],
            data=item["data"],
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
        "name": request.POST.get("name") or "",
        "description": request.POST.get("description") or "",
        "suggested_fields": request.POST.getlist("suggested_fields"),
        "load_demo_data": request.POST.get("load_demo_data") in {"on", "true", "1"},
        "preferred_mode": request.POST.get("preferred_mode") or "basic",
    }
    templates_catalog = _template_catalog()
    template_key = wizard_state["starter_template"]
    assistant = _assistant_context(template_key)
    template_form = WizardTemplateForm(
        request.POST if request.method == "POST" and step == "1" else None,
        initial={
            "starter_template": wizard_state["starter_template"],
            "use_case": wizard_state["use_case"],
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
        suggested_choices=_get_suggested_choices(template_key),
        initial={
            "suggested_fields": wizard_state["suggested_fields"],
            "load_demo_data": wizard_state["load_demo_data"] if request.method == "POST" else True,
            "preferred_mode": wizard_state["preferred_mode"],
        },
    )

    if request.method == "POST":
        if step == "1" and template_form.is_valid():
            cleaned = template_form.cleaned_data
            return redirect(f"{request.path}?{urlencode({'step': 2, 'starter_template': cleaned['starter_template'], 'use_case': cleaned['use_case']})}")
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
            wizard_state["suggested_fields"] = options_form.cleaned_data["suggested_fields"]
            wizard_state["load_demo_data"] = options_form.cleaned_data["load_demo_data"]
            wizard_state["preferred_mode"] = options_form.cleaned_data["preferred_mode"]
            step = "4"
        elif step == "4":
            database = AppDatabase.objects.create(
                name=wizard_state["name"],
                description=wizard_state["description"],
                use_case=wizard_state["use_case"],
                created_by=request.user,
            )
            DatabaseMembership.objects.create(
                database=database,
                user=request.user,
                role=DatabaseMembership.Role.ADMIN,
            )
            selected_template = wizard_state["starter_template"]
            if selected_template in STARTER_TEMPLATES:
                STARTER_TEMPLATES[selected_template](database)
            _create_extra_fields(database, wizard_state["suggested_fields"])
            if wizard_state["load_demo_data"]:
                _load_demo_records(database, request.user, selected_template)
            messages.success(request, "La lista fue creada. El asistente te dejo una base lista para empezar.")
            return redirect(f"/bases/{database.slug}/?tab=daily&mode={wizard_state['preferred_mode']}")
    return render(
        request,
        "database_create.html",
        {
            "templates_catalog": templates_catalog,
            "step": step,
            "wizard_state": wizard_state,
            "assistant": assistant,
            "template_form": template_form,
            "setup_form": setup_form,
            "options_form": options_form,
            "preview_template_fields": next((item["fields"] for item in templates_catalog if item["key"] == template_key), []),
            "preview_extras": [
                EXTRA_FIELD_DEFINITIONS[key][0]
                for key in wizard_state["suggested_fields"]
                if key in EXTRA_FIELD_DEFINITIONS
            ],
        },
    )


@login_required
def database_detail(request, slug):
    database, membership = _get_database_for_user(request.user, slug)
    active_tab = request.GET.get("tab", "summary")
    if active_tab not in {"summary", "daily", "records", "structure", "manage"}:
        active_tab = "summary"
    edit_field_id = request.GET.get("edit_field")
    mode = request.GET.get("mode", "basic")
    if mode not in {"basic", "advanced"}:
        mode = "basic"
    saved_view_id = request.GET.get("saved_view")
    q = request.GET.get("q", "").strip()
    priority = request.GET.get("priority", "").strip()
    view_mode = request.GET.get("view", "table")
    if view_mode not in {"table", "cards"}:
        view_mode = "table"
    sort = request.GET.get("sort", "updated")
    sort_map = {
        "updated": "-updated_at",
        "title": "title",
        "priority": "priority",
        "created": "-created_at",
    }

    records = database.records.all().annotate(data_text=Cast("data", output_field=TextField()))
    if q:
        records = records.filter(Q(title__icontains=q) | Q(data_text__icontains=q))
    if priority:
        records = records.filter(priority=priority)
    if saved_view_id:
        saved_view = database.saved_views.filter(user=request.user, pk=saved_view_id).first()
        if saved_view:
            q = saved_view.query
            priority = saved_view.priority
            sort = saved_view.sort
            view_mode = saved_view.view_mode
            records = database.records.all().annotate(data_text=Cast("data", output_field=TextField()))
            if q:
                records = records.filter(Q(title__icontains=q) | Q(data_text__icontains=q))
            if priority:
                records = records.filter(priority=priority)
    records = records.order_by(sort_map.get(sort, "-updated_at"))
    paginator = Paginator(records, 20)
    page_obj = paginator.get_page(request.GET.get("page") or 1)

    total_records = database.records.count()
    high_priority_count = database.records.filter(priority=Record.Priority.HIGH).count()
    urgent_count = database.records.filter(priority=Record.Priority.URGENT).count()
    relation_fields = database.fields.filter(field_type=CustomField.FieldType.RELATION).select_related("relation_database")
    select_fields = database.fields.filter(field_type=CustomField.FieldType.SELECT)
    field_cards = [
        {
            "field": field,
            "form": CustomFieldForm(database=database, actor=request.user, instance=field),
            "is_editing": str(field.pk) == str(edit_field_id),
            "has_data": _field_has_data(field),
        }
        for field in database.fields.all()
    ]
    daily_records = database.records.exclude(priority=Record.Priority.NORMAL)[:8]
    basic_fields_preview = database.fields.filter(show_in_table=True)[:4]
    import_summary = request.session.pop(_import_session_key(database) + "_summary", None)

    context = {
        "database": database,
        "membership": membership,
        "active_tab": active_tab,
        "mode": mode,
        "table_fields": database.fields.filter(show_in_table=True),
        "all_fields": database.fields.all(),
        "field_cards": field_cards,
        "relation_fields": relation_fields,
        "select_fields": select_fields,
        "records": page_obj.object_list,
        "page_obj": page_obj,
        "daily_records": daily_records,
        "basic_fields_preview": basic_fields_preview,
        "query": q,
        "selected_priority": priority,
        "priority_choices": Record.Priority.choices,
        "view_mode": view_mode,
        "sort": sort,
        "sort_choices": [
            ("updated", "Actualizados recientemente"),
            ("created", "Mas nuevos"),
            ("title", "Nombre"),
            ("priority", "Prioridad"),
        ],
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
        "save_view_form": SaveViewForm(),
        "saved_views": database.saved_views.filter(user=request.user),
        "import_summary": import_summary,
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
                "priority": request.POST.get("priority", "").strip(),
                "sort": request.POST.get("sort", "updated"),
                "view_mode": request.POST.get("view_mode", "table"),
            },
        )
        messages.success(request, "La vista fue guardada para reutilizarla.")
    return redirect("database_detail", slug=database.slug)


@login_required
def field_create(request, slug):
    database, membership = _get_database_for_user(request.user, slug)
    if membership.role != DatabaseMembership.Role.ADMIN:
        return HttpResponseForbidden("Solo los administradores pueden crear campos.")

    form = CustomFieldForm(database, request.POST or None, actor=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "El campo fue agregado.")
    else:
        messages.error(request, "Revisa los datos del campo.")
    return redirect(f"{reverse('database_detail', args=[database.slug])}?tab=structure&mode=advanced")


@login_required
def field_update(request, slug, field_id):
    database, membership = _get_database_for_user(request.user, slug)
    if membership.role != DatabaseMembership.Role.ADMIN:
        return HttpResponseForbidden("Solo los administradores pueden editar campos.")

    custom_field = get_object_or_404(database.fields, pk=field_id)
    form = CustomFieldForm(database, request.POST or None, actor=request.user, instance=custom_field)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, f"El campo {custom_field.label} fue actualizado.")
    else:
        messages.error(request, "No se pudo actualizar el campo.")
    return redirect(f"{reverse('database_detail', args=[database.slug])}?tab=structure&mode=advanced")


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
            return redirect(f"{reverse('database_detail', args=[database.slug])}?tab=structure&mode=advanced")
        field_name = custom_field.label
        custom_field.delete()
        messages.success(request, f"El campo {field_name} fue eliminado.")
    return redirect(f"{reverse('database_detail', args=[database.slug])}?tab=structure&mode=advanced")


@login_required
def member_create(request, slug):
    database, membership = _get_database_for_user(request.user, slug)
    if membership.role != DatabaseMembership.Role.ADMIN:
        return HttpResponseForbidden("Solo los administradores pueden asignar miembros.")

    form = MembershipForm(database, request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "El rol fue actualizado.")
    else:
        messages.error(request, "No se pudo actualizar el miembro.")
    return redirect("database_detail", slug=database.slug)


@login_required
def record_create(request, slug):
    database, membership = _get_database_for_user(request.user, slug)
    form = RecordForm(database, request.POST or None, actor=request.user)
    if request.method == "POST" and form.is_valid():
        form.save(user=request.user)
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
        related_record = field.relation_database.records.filter(pk=raw_value).first()
        if related_record:
            outgoing_relations.append(
                {
                    "field": field,
                    "database": field.relation_database,
                    "record": related_record,
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
    form = RecordForm(database, request.POST or None, record=record, actor=request.user)
    if request.method == "POST" and form.is_valid():
        form.save(user=request.user)
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
        record.delete()
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
        if "title" not in mapping.values():
            messages.error(request, "Debes asignar una columna al nombre principal antes de importar.")
            return redirect("records_import_map", slug=database.slug)
        valid_priorities = {choice[0] for choice in Record.Priority.choices}
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

                title = str(normalized.get("title", "")).strip()
                if not title:
                    skipped += 1
                    row_errors.append(f"Fila {row_number}: falta el nombre principal.")
                    continue

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
                        related_record = field.relation_database.records.filter(title__iexact=str(value).strip()).first()
                        if not related_record:
                            skipped += 1
                            row_errors.append(
                                f"Fila {row_number}: no se encontro '{value}' en {field.relation_database.name}."
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
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{database.slug}.csv"'
    response.write("\ufeff")

    writer = csv.writer(response)
    fields = list(database.fields.all())
    writer.writerow(["title", "priority", *[field.label for field in fields]])
    for record in database.records.all():
        row = [record.title, record.priority]
        for field in fields:
            row.append(record.get_display_value(field))
        writer.writerow(row)
    return response
