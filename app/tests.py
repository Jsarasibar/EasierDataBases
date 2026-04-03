from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
import json

from .forms import CustomFieldForm
from .models import AppDatabase, CustomField, DatabaseActivity, DatabaseMembership, Record
from .views import _base_field_keys


User = get_user_model()


class DatabaseFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="admin", password="secret123")

    def complete_creation_wizard(
        self,
        *,
        starter_template="inventory",
        use_case="inventory",
        name="Inventario central",
        description="Base de prueba",
        selected_fields=None,
        load_demo_data=False,
    ):
        selected_fields = selected_fields if selected_fields is not None else _base_field_keys(starter_template)
        response = self.client.post(
            reverse("database_create"),
            {"step": "1", "starter_template": starter_template, "use_case": use_case},
        )
        self.assertEqual(response.status_code, 302)
        response = self.client.post(
            reverse("database_create"),
            {
                "step": "2",
                "starter_template": starter_template,
                "use_case": use_case,
                "name": name,
                "description": description,
            },
        )
        self.assertEqual(response.status_code, 302)
        payload = {
            "step": "3",
            "starter_template": starter_template,
            "use_case": use_case,
            "name": name,
            "description": description,
        }
        for field in selected_fields:
            payload.setdefault("selected_fields", [])
            payload["selected_fields"].append(field)
        if load_demo_data:
            payload["load_demo_data"] = "on"
        response = self.client.post(reverse("database_create"), payload)
        self.assertEqual(response.status_code, 200)
        confirm_payload = {
            "step": "4",
            "starter_template": starter_template,
            "use_case": use_case,
            "name": name,
            "description": description,
        }
        for field in selected_fields:
            confirm_payload.setdefault("selected_fields", [])
            confirm_payload["selected_fields"].append(field)
        if load_demo_data:
            confirm_payload["load_demo_data"] = "on"
        return self.client.post(reverse("database_create"), confirm_payload)

    def test_create_database_with_template(self):
        self.client.login(username="admin", password="secret123")
        response = self.complete_creation_wizard()
        self.assertEqual(response.status_code, 302)
        database = AppDatabase.objects.get(name="Inventario central")
        self.assertTrue(database.fields.filter(label="Precio").exists())
        self.assertFalse(database.has_priority)
        self.assertEqual(database.get_primary_field().label, "Nombre")
        self.assertTrue(
            DatabaseMembership.objects.filter(
                database=database,
                user=self.user,
                role=DatabaseMembership.Role.ADMIN,
            ).exists()
        )

    def test_creation_wizard_keeps_written_name_between_steps(self):
        self.client.login(username="admin", password="secret123")

        response = self.client.post(
            reverse("database_create"),
            {
                "step": "2",
                "starter_template": "inventory",
                "use_case": "inventory",
                "name": "Productos abril",
                "description": "Base comercial",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("name=Productos+abril", response.url)

        preview_response = self.client.get(response.url)
        self.assertEqual(preview_response.status_code, 200)
        self.assertContains(preview_response, 'value="Productos abril"', html=False)

        confirm_response = self.client.post(
            reverse("database_create"),
            {
                "step": "3",
                "starter_template": "inventory",
                "use_case": "inventory",
                "name": "Productos abril",
                "description": "Base comercial",
                "selected_fields": "inventory_nombre",
            },
        )

        self.assertEqual(confirm_response.status_code, 200)
        self.assertContains(confirm_response, "Productos abril")

    def test_creation_wizard_back_from_confirm_keeps_selected_fields(self):
        self.client.login(username="admin", password="secret123")
        custom_fields_json = json.dumps(
            [
                {"label": "Proveedor alternativo", "field_type": CustomField.FieldType.TEXT, "options_text": ""},
            ]
        )

        response = self.client.post(
            reverse("database_create"),
            {
                "step": "4",
                "starter_template": "inventory",
                "use_case": "inventory",
                "name": "Productos abril",
                "description": "Base comercial",
                "selected_fields": ["inventory_nombre", "inventory_precio", "__priority__"],
                "custom_fields_json": custom_fields_json,
                "load_demo_data": "on",
                "nav": "back",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'value="inventory_nombre"', html=False)
        self.assertContains(response, 'value="inventory_precio"', html=False)
        self.assertContains(response, 'value="__priority__"', html=False)
        self.assertContains(response, "Proveedor alternativo")

    def test_create_record(self):
        self.client.login(username="admin", password="secret123")
        database = AppDatabase.objects.create(
            name="Productos",
            slug="productos",
            has_priority=True,
            created_by=self.user,
        )
        DatabaseMembership.objects.create(
            database=database,
            user=self.user,
            role=DatabaseMembership.Role.ADMIN,
        )
        CustomField.objects.create(
            database=database,
            label="Nombre",
            key="nombre",
            field_type=CustomField.FieldType.TEXT,
            required=True,
            position=1,
            is_primary=True,
        )
        CustomField.objects.create(
            database=database,
            label="Precio",
            key="precio",
            field_type=CustomField.FieldType.CURRENCY,
            required=True,
            position=2,
        )
        response = self.client.post(
            reverse("record_create", args=[database.slug]),
            {
                "nombre": "Cafe molido",
                "priority": Record.Priority.URGENT,
                "precio": "1500",
            },
        )
        self.assertEqual(response.status_code, 302)
        record = database.records.get()
        self.assertEqual(record.title, "Cafe molido")
        self.assertEqual(record.data["precio"], "1500")
        self.assertTrue(
            DatabaseActivity.objects.filter(
                database=database,
                action="Registro agregado",
                detail__icontains="Cafe molido",
            ).exists()
        )

    def test_history_tab_shows_logged_movements(self):
        self.client.login(username="admin", password="secret123")
        database = AppDatabase.objects.create(
            name="Base con historial",
            slug="base-con-historial",
            created_by=self.user,
        )
        DatabaseMembership.objects.create(
            database=database,
            user=self.user,
            role=DatabaseMembership.Role.ADMIN,
        )
        DatabaseActivity.objects.create(
            database=database,
            actor=self.user,
            action="Registro agregado",
            detail="Se creo el registro Cliente A.",
        )

        response = self.client.get(reverse("database_detail", args=[database.slug]), {"tab": "history"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Historial de la base")
        self.assertContains(response, "Registro agregado")
        self.assertContains(response, "Cliente A")
        self.assertContains(response, "admin")

    def test_record_edit_activity_stores_before_and_after_changes(self):
        self.client.login(username="admin", password="secret123")
        database = AppDatabase.objects.create(
            name="Productos historial",
            slug="productos-historial",
            created_by=self.user,
            has_priority=True,
        )
        DatabaseMembership.objects.create(
            database=database,
            user=self.user,
            role=DatabaseMembership.Role.ADMIN,
        )
        CustomField.objects.create(
            database=database,
            label="Nombre",
            key="nombre",
            field_type=CustomField.FieldType.TEXT,
            required=True,
            position=1,
            is_primary=True,
        )
        CustomField.objects.create(
            database=database,
            label="Stock",
            key="stock",
            field_type=CustomField.FieldType.NUMBER,
            required=False,
            position=2,
        )
        record = Record.objects.create(
            database=database,
            title="Cafe",
            priority=Record.Priority.NORMAL,
            data={"nombre": "Cafe", "stock": "10"},
            created_by=self.user,
            updated_by=self.user,
        )

        response = self.client.post(
            reverse("record_edit", args=[database.slug, record.pk]),
            {
                "nombre": "Cafe premium",
                "stock": "15",
                "priority": Record.Priority.HIGH,
            },
        )

        self.assertEqual(response.status_code, 302)
        activity = DatabaseActivity.objects.filter(database=database, action="Registro editado").latest("created_at")
        self.assertEqual(activity.payload["summary"][0]["value"], "Cafe premium")
        changes = {item["label"]: item for item in activity.payload["changes"]}
        self.assertEqual(changes["Nombre"]["before"], "Cafe")
        self.assertEqual(changes["Nombre"]["after"], "Cafe premium")
        self.assertEqual(changes["Stock"]["before"], "10")
        self.assertEqual(changes["Stock"]["after"], "15")
        self.assertEqual(changes["Prioridad"]["before"], "Normal")
        self.assertEqual(changes["Prioridad"]["after"], "Alta")

    def test_create_record_without_priority_uses_primary_field_as_title(self):
        self.client.login(username="admin", password="secret123")
        database = AppDatabase.objects.create(
            name="Clientes simples",
            slug="clientes-simples",
            created_by=self.user,
        )
        DatabaseMembership.objects.create(
            database=database,
            user=self.user,
            role=DatabaseMembership.Role.ADMIN,
        )
        CustomField.objects.create(
            database=database,
            label="Nombre",
            key="nombre",
            field_type=CustomField.FieldType.TEXT,
            required=True,
            position=1,
            is_primary=True,
        )

        form_response = self.client.get(reverse("record_create", args=[database.slug]))
        self.assertEqual(form_response.status_code, 200)
        self.assertNotContains(form_response, "Prioridad")

        create_response = self.client.post(
            reverse("record_create", args=[database.slug]),
            {"nombre": "Cliente uno"},
        )
        self.assertEqual(create_response.status_code, 302)
        record = database.records.get()
        self.assertEqual(record.title, "Cliente uno")
        self.assertEqual(record.priority, Record.Priority.NORMAL)

    def test_wizard_can_enable_priority_when_selected(self):
        self.client.login(username="admin", password="secret123")
        response = self.complete_creation_wizard(
            selected_fields=_base_field_keys("inventory") + ["__priority__"],
        )
        self.assertEqual(response.status_code, 302)
        database = AppDatabase.objects.get(name="Inventario central")
        self.assertTrue(database.has_priority)

    def test_create_database_with_students_template(self):
        self.client.login(username="admin", password="secret123")
        response = self.complete_creation_wizard(
            starter_template="students",
            use_case="students",
            name="Alumnos 2026",
            description="Seguimiento academico",
        )
        self.assertEqual(response.status_code, 302)
        database = AppDatabase.objects.get(name="Alumnos 2026")
        self.assertTrue(database.fields.filter(label="Curso").exists())
        self.assertTrue(database.fields.filter(label="Cuota al dia").exists())

    def test_import_records_from_csv(self):
        self.client.login(username="admin", password="secret123")
        database = AppDatabase.objects.create(
            name="Productos",
            slug="productos",
            has_priority=True,
            created_by=self.user,
        )
        DatabaseMembership.objects.create(
            database=database,
            user=self.user,
            role=DatabaseMembership.Role.ADMIN,
        )
        CustomField.objects.create(
            database=database,
            label="Nombre",
            key="nombre",
            field_type=CustomField.FieldType.TEXT,
            required=True,
            position=1,
            is_primary=True,
        )
        CustomField.objects.create(
            database=database,
            label="Precio",
            key="precio",
            field_type=CustomField.FieldType.CURRENCY,
            required=False,
            position=2,
        )
        csv_file = SimpleUploadedFile(
            "productos.csv",
            b"Nombre,Precio,Prioridad\nCafe,1200,urgent\nTe,900,high\n",
            content_type="text/csv",
        )
        response = self.client.post(
            reverse("records_import", args=[database.slug]),
            {"csv_file": csv_file, "has_header": "on"},
        )
        self.assertEqual(response.status_code, 302)
        mapping_response = self.client.post(
            reverse("records_import_map", args=[database.slug]),
            {
                "map_Nombre": "nombre",
                "map_Precio": "precio",
                "map_Prioridad": "priority",
            },
        )
        self.assertEqual(mapping_response.status_code, 302)
        self.assertEqual(database.records.count(), 2)
        self.assertTrue(database.records.filter(title="Cafe", priority="urgent").exists())

    def test_export_records_to_csv(self):
        self.client.login(username="admin", password="secret123")
        database = AppDatabase.objects.create(
            name="Clientes",
            slug="clientes",
            has_priority=True,
            created_by=self.user,
        )
        DatabaseMembership.objects.create(
            database=database,
            user=self.user,
            role=DatabaseMembership.Role.ADMIN,
        )
        primary_field = CustomField.objects.create(
            database=database,
            label="Nombre",
            key="nombre",
            field_type=CustomField.FieldType.TEXT,
            required=True,
            position=1,
            is_primary=True,
        )
        field = CustomField.objects.create(
            database=database,
            label="Empresa",
            key="empresa",
            field_type=CustomField.FieldType.TEXT,
            required=False,
            position=2,
        )
        Record.objects.create(
            database=database,
            title="Acme",
            priority=Record.Priority.HIGH,
            data={primary_field.key: "Acme", field.key: "Acme SA"},
            created_by=self.user,
            updated_by=self.user,
        )
        response = self.client.get(reverse("records_export", args=[database.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertIn("Nombre,Empresa,Prioridad", response.content.decode("utf-8-sig"))
        self.assertIn("Acme,Acme SA,high", response.content.decode("utf-8-sig"))

    def test_create_relation_field_and_record(self):
        self.client.login(username="admin", password="secret123")
        clients_db = AppDatabase.objects.create(
            name="Clientes",
            slug="clientes",
            created_by=self.user,
        )
        orders_db = AppDatabase.objects.create(
            name="Pedidos",
            slug="pedidos",
            has_priority=True,
            created_by=self.user,
        )
        DatabaseMembership.objects.create(database=clients_db, user=self.user, role=DatabaseMembership.Role.ADMIN)
        DatabaseMembership.objects.create(database=orders_db, user=self.user, role=DatabaseMembership.Role.ADMIN)

        client_record = Record.objects.create(
            database=clients_db,
            title="Acme SA",
            priority=Record.Priority.NORMAL,
            data={},
            created_by=self.user,
            updated_by=self.user,
        )
        CustomField.objects.create(
            database=orders_db,
            label="Pedido",
            key="pedido",
            field_type=CustomField.FieldType.TEXT,
            required=True,
            position=1,
            is_primary=True,
        )
        CustomField.objects.create(
            database=orders_db,
            label="Cliente",
            key="cliente",
            field_type=CustomField.FieldType.RELATION,
            relation_database=clients_db,
            required=True,
            position=2,
        )
        CustomField.objects.create(
            database=orders_db,
            label="Estado",
            key="estado",
            field_type=CustomField.FieldType.SELECT,
            options_text="Pendiente\nEntregado",
            required=True,
            position=3,
        )
        response = self.client.post(
            reverse("record_create", args=[orders_db.slug]),
            {
                "pedido": "Pedido 001",
                "priority": Record.Priority.HIGH,
                "cliente": str(client_record.pk),
                "estado": "Pendiente",
            },
        )
        self.assertEqual(response.status_code, 302)
        record = orders_db.records.get()
        self.assertEqual(record.data["cliente"], str(client_record.pk))
        self.assertEqual(record.get_display_value(orders_db.fields.get(key="cliente")), "Acme SA")

    def test_relation_field_in_record_form_exposes_create_related_option(self):
        self.client.login(username="admin", password="secret123")
        clients_db = AppDatabase.objects.create(name="Clientes", slug="clientes-popup", created_by=self.user)
        orders_db = AppDatabase.objects.create(name="Pedidos", slug="pedidos-popup", created_by=self.user)
        DatabaseMembership.objects.create(database=clients_db, user=self.user, role=DatabaseMembership.Role.ADMIN)
        DatabaseMembership.objects.create(database=orders_db, user=self.user, role=DatabaseMembership.Role.ADMIN)
        CustomField.objects.create(
            database=orders_db,
            label="Pedido",
            key="pedido",
            field_type=CustomField.FieldType.TEXT,
            required=True,
            position=1,
            is_primary=True,
        )
        CustomField.objects.create(
            database=orders_db,
            label="Cliente",
            key="cliente",
            field_type=CustomField.FieldType.RELATION,
            relation_database=clients_db,
            required=False,
            position=2,
        )

        response = self.client.get(reverse("record_create", args=[orders_db.slug]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-relation-create-url")
        self.assertContains(response, "data-relation-field-key")
        self.assertContains(response, "Agregar nuevo en Clientes")

    def test_popup_related_record_creation_returns_selection_payload(self):
        self.client.login(username="admin", password="secret123")
        clients_db = AppDatabase.objects.create(name="Clientes", slug="clientes-popup-create", created_by=self.user)
        DatabaseMembership.objects.create(database=clients_db, user=self.user, role=DatabaseMembership.Role.ADMIN)
        CustomField.objects.create(
            database=clients_db,
            label="Nombre",
            key="nombre",
            field_type=CustomField.FieldType.TEXT,
            required=True,
            position=1,
            is_primary=True,
        )

        response = self.client.post(
            f"{reverse('record_create', args=[clients_db.slug])}?popup=1&relation_field=cliente",
            {"nombre": "Cliente nuevo"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "easierdatabases:related-record-created")
        self.assertContains(response, "relationField: \"cliente\"")
        self.assertContains(response, "Cliente nuevo")
        self.assertTrue(clients_db.records.filter(title="Cliente nuevo").exists())

    def test_record_create_allows_embedding_for_related_modal(self):
        self.client.login(username="admin", password="secret123")
        database = AppDatabase.objects.create(name="Clientes", slug="clientes-frame", created_by=self.user)
        DatabaseMembership.objects.create(database=database, user=self.user, role=DatabaseMembership.Role.ADMIN)
        CustomField.objects.create(
            database=database,
            label="Nombre",
            key="nombre",
            field_type=CustomField.FieldType.TEXT,
            required=True,
            position=1,
            is_primary=True,
        )

        response = self.client.get(f"{reverse('record_create', args=[database.slug])}?popup=1&embedded=1&relation_field=cliente")

        self.assertEqual(response.status_code, 200)
        self.assertNotIn("X-Frame-Options", response.headers)

    def test_import_csv_with_relation_by_title(self):
        self.client.login(username="admin", password="secret123")
        clients_db = AppDatabase.objects.create(name="Clientes", slug="clientes", created_by=self.user)
        tasks_db = AppDatabase.objects.create(name="Tareas", slug="tareas", has_priority=True, created_by=self.user)
        DatabaseMembership.objects.create(database=clients_db, user=self.user, role=DatabaseMembership.Role.ADMIN)
        DatabaseMembership.objects.create(database=tasks_db, user=self.user, role=DatabaseMembership.Role.ADMIN)
        Record.objects.create(
            database=clients_db,
            title="Globex",
            priority=Record.Priority.NORMAL,
            data={},
            created_by=self.user,
            updated_by=self.user,
        )
        CustomField.objects.create(
            database=tasks_db,
            label="Tarea",
            key="tarea",
            field_type=CustomField.FieldType.TEXT,
            required=True,
            position=1,
            is_primary=True,
        )
        CustomField.objects.create(
            database=tasks_db,
            label="Cliente",
            key="cliente",
            field_type=CustomField.FieldType.RELATION,
            relation_database=clients_db,
            required=False,
            position=2,
        )
        csv_file = SimpleUploadedFile(
            "tareas.csv",
            b"Tarea,Cliente,Prioridad\nLlamar a cliente,Globex,high\n",
            content_type="text/csv",
        )
        response = self.client.post(
            reverse("records_import", args=[tasks_db.slug]),
            {"csv_file": csv_file, "has_header": "on"},
        )
        self.assertEqual(response.status_code, 302)
        mapping_response = self.client.post(
            reverse("records_import_map", args=[tasks_db.slug]),
            {
                "map_Tarea": "tarea",
                "map_Cliente": "cliente",
                "map_Prioridad": "priority",
            },
        )
        self.assertEqual(mapping_response.status_code, 302)
        imported = tasks_db.records.get()
        self.assertEqual(imported.get_display_value(tasks_db.fields.get(key="cliente")), "Globex")

    def test_record_detail_shows_bidirectional_relations(self):
        self.client.login(username="admin", password="secret123")
        clients_db = AppDatabase.objects.create(name="Clientes", slug="clientes", created_by=self.user)
        orders_db = AppDatabase.objects.create(name="Pedidos", slug="pedidos", has_priority=True, created_by=self.user)
        DatabaseMembership.objects.create(database=clients_db, user=self.user, role=DatabaseMembership.Role.ADMIN)
        DatabaseMembership.objects.create(database=orders_db, user=self.user, role=DatabaseMembership.Role.ADMIN)

        client = Record.objects.create(
            database=clients_db,
            title="Innova SRL",
            priority=Record.Priority.NORMAL,
            data={},
            created_by=self.user,
            updated_by=self.user,
        )
        CustomField.objects.create(
            database=orders_db,
            label="Pedido",
            key="pedido",
            field_type=CustomField.FieldType.TEXT,
            required=True,
            position=1,
            is_primary=True,
        )
        relation_field = CustomField.objects.create(
            database=orders_db,
            label="Cliente",
            key="cliente",
            field_type=CustomField.FieldType.RELATION,
            relation_database=clients_db,
            required=False,
            position=2,
        )
        order = Record.objects.create(
            database=orders_db,
            title="Pedido 900",
            priority=Record.Priority.HIGH,
            data={"pedido": "Pedido 900", relation_field.key: str(client.pk)},
            created_by=self.user,
            updated_by=self.user,
        )

        order_response = self.client.get(reverse("record_detail", args=[orders_db.slug, order.pk]))
        self.assertEqual(order_response.status_code, 200)
        self.assertContains(order_response, "Innova SRL")
        self.assertContains(order_response, "Relaciones salientes")

        client_response = self.client.get(reverse("record_detail", args=[clients_db.slug, client.pk]))
        self.assertEqual(client_response.status_code, 200)
        self.assertContains(client_response, "Relaciones entrantes")
        self.assertContains(client_response, "Pedido 900")

    def test_records_view_renders_relation_values_as_preview_actions(self):
        self.client.login(username="admin", password="secret123")
        clients_db = AppDatabase.objects.create(name="Clientes", slug="clientes-preview", created_by=self.user)
        orders_db = AppDatabase.objects.create(name="Pedidos", slug="pedidos-preview", created_by=self.user)
        DatabaseMembership.objects.create(database=clients_db, user=self.user, role=DatabaseMembership.Role.ADMIN)
        DatabaseMembership.objects.create(database=orders_db, user=self.user, role=DatabaseMembership.Role.ADMIN)
        client = Record.objects.create(
            database=clients_db,
            title="Acme SA",
            data={},
            created_by=self.user,
            updated_by=self.user,
        )
        CustomField.objects.create(
            database=orders_db,
            label="Pedido",
            key="pedido",
            field_type=CustomField.FieldType.TEXT,
            required=True,
            position=1,
            is_primary=True,
        )
        relation_field = CustomField.objects.create(
            database=orders_db,
            label="Cliente",
            key="cliente",
            field_type=CustomField.FieldType.RELATION,
            relation_database=clients_db,
            required=False,
            position=2,
        )
        Record.objects.create(
            database=orders_db,
            title="Pedido 42",
            data={"pedido": "Pedido 42", relation_field.key: str(client.pk)},
            created_by=self.user,
            updated_by=self.user,
        )

        response = self.client.get(reverse("database_detail", args=[orders_db.slug]), {"tab": "records"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-relation-preview-key")
        self.assertContains(response, "Acme SA")
        self.assertContains(response, "relation-previews-data")

    def test_database_tabs_render_specific_sections(self):
        self.client.login(username="admin", password="secret123")
        database = AppDatabase.objects.create(name="Operaciones", slug="operaciones", created_by=self.user)
        DatabaseMembership.objects.create(database=database, user=self.user, role=DatabaseMembership.Role.ADMIN)

        default_response = self.client.get(reverse("database_detail", args=[database.slug]))
        self.assertEqual(default_response.status_code, 200)
        self.assertContains(default_response, "Buscar y operar elementos")

        records_response = self.client.get(reverse("database_detail", args=[database.slug]), {"tab": "records"})
        self.assertEqual(records_response.status_code, 200)
        self.assertContains(records_response, "Buscar y operar elementos")
        self.assertContains(records_response, "Agregar registro")

        structure_response = self.client.get(reverse("database_detail", args=[database.slug]), {"tab": "structure"})
        self.assertEqual(structure_response.status_code, 200)
        self.assertContains(structure_response, "Mapa visual de la base")
        self.assertContains(structure_response, "Agregar campo o relacion")

    def test_records_view_shows_pk_and_can_filter_by_record_id(self):
        self.client.login(username="admin", password="secret123")
        database = AppDatabase.objects.create(name="Operaciones", slug="operaciones-id", created_by=self.user)
        DatabaseMembership.objects.create(database=database, user=self.user, role=DatabaseMembership.Role.ADMIN)
        CustomField.objects.create(
            database=database,
            label="Nombre",
            key="nombre",
            field_type=CustomField.FieldType.TEXT,
            required=True,
            position=1,
            is_primary=True,
        )
        record_one = Record.objects.create(
            database=database,
            title="Primer registro",
            data={"nombre": "Primer registro"},
            created_by=self.user,
            updated_by=self.user,
        )
        Record.objects.create(
            database=database,
            title="Segundo registro",
            data={"nombre": "Segundo registro"},
            created_by=self.user,
            updated_by=self.user,
        )

        response = self.client.get(reverse("database_detail", args=[database.slug]), {"tab": "records", "record_id": str(record_one.pk)})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<th>ID</th>", html=False)
        self.assertContains(response, f">{record_one.pk}</td>", html=False)
        self.assertContains(response, "Primer registro")
        self.assertNotContains(response, "Segundo registro")

    def test_statistics_placeholder_view_is_available_from_summary(self):
        self.client.login(username="admin", password="secret123")
        database = AppDatabase.objects.create(name="Analitica", slug="analitica", created_by=self.user)
        DatabaseMembership.objects.create(database=database, user=self.user, role=DatabaseMembership.Role.ADMIN)

        summary_response = self.client.get(reverse("database_detail", args=[database.slug]), {"tab": "summary"})
        self.assertEqual(summary_response.status_code, 200)
        self.assertContains(summary_response, "Graficos (estadisticas)")

        stats_response = self.client.get(reverse("database_statistics", args=[database.slug]))
        self.assertEqual(stats_response.status_code, 200)
        self.assertContains(stats_response, "Coming soon")
        self.assertContains(stats_response, "Graficos por campo")

    def test_admin_can_update_existing_field(self):
        self.client.login(username="admin", password="secret123")
        database = AppDatabase.objects.create(name="Catalogo", slug="catalogo", created_by=self.user)
        DatabaseMembership.objects.create(database=database, user=self.user, role=DatabaseMembership.Role.ADMIN)
        field = CustomField.objects.create(
            database=database,
            label="Categoria",
            key="categoria",
            field_type=CustomField.FieldType.TEXT,
            help_text="Categoria simple",
            required=False,
            show_in_table=True,
            position=1,
        )
        response = self.client.post(
            reverse("field_update", args=[database.slug, field.pk]),
            {
                "label": "Categoria principal",
                "field_type": CustomField.FieldType.SELECT,
                "help_text": "Elegir categoria",
                "options_text": "Cafe\nTe",
                "relation_database": "",
                "required": "on",
                "show_in_table": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        field.refresh_from_db()
        self.assertEqual(field.label, "Categoria principal")
        self.assertEqual(field.field_type, CustomField.FieldType.SELECT)
        self.assertEqual(field.get_options(), ["Cafe", "Te"])

    def test_admin_can_choose_which_field_is_record_name(self):
        self.client.login(username="admin", password="secret123")
        database = AppDatabase.objects.create(name="Catalogo", slug="catalogo-principal", created_by=self.user)
        DatabaseMembership.objects.create(database=database, user=self.user, role=DatabaseMembership.Role.ADMIN)
        name_field = CustomField.objects.create(
            database=database,
            label="Nombre",
            key="nombre",
            field_type=CustomField.FieldType.TEXT,
            required=True,
            position=1,
            is_primary=True,
        )
        sku_field = CustomField.objects.create(
            database=database,
            label="SKU",
            key="sku",
            field_type=CustomField.FieldType.TEXT,
            required=False,
            position=2,
        )
        record = Record.objects.create(
            database=database,
            title="Cafe molido",
            data={"nombre": "Cafe molido", "sku": "CAF-001"},
            created_by=self.user,
            updated_by=self.user,
        )

        response = self.client.post(reverse("field_set_primary", args=[database.slug, sku_field.pk]))

        self.assertEqual(response.status_code, 302)
        name_field.refresh_from_db()
        sku_field.refresh_from_db()
        record.refresh_from_db()
        self.assertFalse(name_field.is_primary)
        self.assertTrue(sku_field.is_primary)
        self.assertEqual(record.title, "CAF-001")

    def test_structure_tab_shows_primary_field_selector(self):
        self.client.login(username="admin", password="secret123")
        database = AppDatabase.objects.create(name="Catalogo", slug="catalogo-selector", created_by=self.user)
        DatabaseMembership.objects.create(database=database, user=self.user, role=DatabaseMembership.Role.ADMIN)
        CustomField.objects.create(
            database=database,
            label="Nombre",
            key="nombre",
            field_type=CustomField.FieldType.TEXT,
            required=True,
            position=1,
            is_primary=True,
        )
        CustomField.objects.create(
            database=database,
            label="SKU",
            key="sku",
            field_type=CustomField.FieldType.TEXT,
            required=False,
            position=2,
        )

        response = self.client.get(reverse("database_detail", args=[database.slug]), {"tab": "structure"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Columna que identifica cada registro")
        self.assertContains(response, "<option value=", html=False)
        self.assertContains(response, "Nombre")
        self.assertContains(response, "SKU")
        self.assertContains(response, "Columna que identifica cada registro")

    def test_admin_can_change_primary_field_from_structure_selector(self):
        self.client.login(username="admin", password="secret123")
        database = AppDatabase.objects.create(name="Catalogo", slug="catalogo-selector-cambio", created_by=self.user)
        DatabaseMembership.objects.create(database=database, user=self.user, role=DatabaseMembership.Role.ADMIN)
        name_field = CustomField.objects.create(
            database=database,
            label="Nombre",
            key="nombre",
            field_type=CustomField.FieldType.TEXT,
            required=True,
            position=1,
            is_primary=True,
        )
        sku_field = CustomField.objects.create(
            database=database,
            label="SKU",
            key="sku",
            field_type=CustomField.FieldType.TEXT,
            required=False,
            position=2,
        )
        record = Record.objects.create(
            database=database,
            title="Cafe molido",
            data={"nombre": "Cafe molido", "sku": "CAF-001"},
            created_by=self.user,
            updated_by=self.user,
        )

        response = self.client.post(
            reverse("field_set_primary_select", args=[database.slug]),
            {"primary_field_id": str(sku_field.pk)},
        )

        self.assertEqual(response.status_code, 302)
        name_field.refresh_from_db()
        sku_field.refresh_from_db()
        record.refresh_from_db()
        self.assertFalse(name_field.is_primary)
        self.assertTrue(sku_field.is_primary)
        self.assertEqual(record.title, "CAF-001")

    def test_renaming_field_keeps_existing_key_and_data(self):
        self.client.login(username="admin", password="secret123")
        database = AppDatabase.objects.create(name="Productos", slug="productos-renombre", created_by=self.user)
        DatabaseMembership.objects.create(database=database, user=self.user, role=DatabaseMembership.Role.ADMIN)
        field = CustomField.objects.create(
            database=database,
            label="Categoria",
            key="categoria",
            field_type=CustomField.FieldType.TEXT,
            required=False,
            position=1,
        )
        record = Record.objects.create(
            database=database,
            title="Cafe molido",
            priority=Record.Priority.NORMAL,
            data={"categoria": "Bebidas"},
            created_by=self.user,
            updated_by=self.user,
        )
        response = self.client.post(
            reverse("field_update", args=[database.slug, field.pk]),
            {
                "label": "Categoria principal",
                "field_type": CustomField.FieldType.TEXT,
                "help_text": "",
                "options_text": "",
                "relation_database": "",
                "show_in_table": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        field.refresh_from_db()
        record.refresh_from_db()
        self.assertEqual(field.key, "categoria")
        self.assertEqual(record.get_display_value(field), "Bebidas")

    def test_import_records_from_large_csv_imports_all_rows(self):
        self.client.login(username="admin", password="secret123")
        database = AppDatabase.objects.create(
            name="Productos masivos",
            slug="productos-masivos",
            has_priority=True,
            created_by=self.user,
        )
        DatabaseMembership.objects.create(database=database, user=self.user, role=DatabaseMembership.Role.ADMIN)
        CustomField.objects.create(
            database=database,
            label="Nombre",
            key="nombre",
            field_type=CustomField.FieldType.TEXT,
            required=True,
            position=1,
            is_primary=True,
        )
        lines = ["Nombre,Prioridad"]
        for index in range(60):
            lines.append(f"Producto {index},normal")
        csv_file = SimpleUploadedFile(
            "productos_masivos.csv",
            "\n".join(lines).encode("utf-8"),
            content_type="text/csv",
        )
        response = self.client.post(
            reverse("records_import", args=[database.slug]),
            {"csv_file": csv_file, "has_header": "on"},
        )
        self.assertEqual(response.status_code, 302)
        mapping_response = self.client.post(
            reverse("records_import_map", args=[database.slug]),
            {
                "map_Nombre": "nombre",
                "map_Prioridad": "priority",
            },
        )
        self.assertEqual(mapping_response.status_code, 302)
        self.assertEqual(database.records.count(), 60)

    def test_creation_wizard_can_add_manual_fields_in_step_three(self):
        self.client.login(username="admin", password="secret123")
        self.client.post(
            reverse("database_create"),
            {"step": "1", "starter_template": "inventory"},
        )
        self.client.post(
            reverse("database_create"),
            {
                "step": "2",
                "starter_template": "inventory",
                "use_case": "inventory",
                "name": "Base con manuales",
                "description": "Prueba",
            },
        )
        response = self.client.post(
            reverse("database_create"),
            {
                "step": "3",
                "starter_template": "inventory",
                "use_case": "inventory",
                "name": "Base con manuales",
                "description": "Prueba",
                "selected_fields": "inventory_nombre",
                "custom_fields_json": json.dumps(
                    [
                        {"label": "Proveedor alternativo", "field_type": CustomField.FieldType.TEXT, "options_text": ""},
                        {"label": "Estado interno", "field_type": CustomField.FieldType.SELECT, "options_text": "Pendiente\nActivo"},
                    ]
                ),
            },
        )
        self.assertEqual(response.status_code, 200)
        confirm_response = self.client.post(
            reverse("database_create"),
            {
                "step": "4",
                "starter_template": "inventory",
                "use_case": "inventory",
                "name": "Base con manuales",
                "description": "Prueba",
                "selected_fields": "inventory_nombre",
                "custom_fields_json": json.dumps(
                    [
                        {"label": "Proveedor alternativo", "field_type": CustomField.FieldType.TEXT, "options_text": ""},
                        {"label": "Estado interno", "field_type": CustomField.FieldType.SELECT, "options_text": "Pendiente\nActivo"},
                    ]
                ),
            },
        )
        self.assertEqual(confirm_response.status_code, 302)
        database = AppDatabase.objects.get(name="Base con manuales")
        self.assertTrue(database.fields.filter(label="Proveedor alternativo", field_type=CustomField.FieldType.TEXT).exists())
        self.assertTrue(database.fields.filter(label="Estado interno", field_type=CustomField.FieldType.SELECT).exists())

    def test_relation_database_queryset_is_limited_to_accessible_bases(self):
        owner = User.objects.create_user(username="owner", password="secret123")
        visible_db = AppDatabase.objects.create(name="Visible", slug="visible-db", created_by=owner)
        hidden_db = AppDatabase.objects.create(name="Oculta", slug="oculta-db", created_by=owner)
        current_db = AppDatabase.objects.create(name="Actual", slug="actual-db", created_by=self.user)
        DatabaseMembership.objects.create(database=current_db, user=self.user, role=DatabaseMembership.Role.ADMIN)
        DatabaseMembership.objects.create(database=visible_db, user=self.user, role=DatabaseMembership.Role.ADMIN)
        DatabaseMembership.objects.create(database=visible_db, user=owner, role=DatabaseMembership.Role.ADMIN)
        DatabaseMembership.objects.create(database=hidden_db, user=owner, role=DatabaseMembership.Role.ADMIN)

        form = CustomFieldForm(current_db, actor=self.user)

        self.assertIn(visible_db, form.fields["relation_database"].queryset)
        self.assertNotIn(hidden_db, form.fields["relation_database"].queryset)

    def test_cannot_change_relation_database_when_field_already_has_data(self):
        self.client.login(username="admin", password="secret123")
        customers_db = AppDatabase.objects.create(name="Clientes", slug="clientes-a", created_by=self.user)
        suppliers_db = AppDatabase.objects.create(name="Proveedores", slug="proveedores-a", created_by=self.user)
        orders_db = AppDatabase.objects.create(name="Pedidos", slug="pedidos-a", created_by=self.user)
        DatabaseMembership.objects.create(database=customers_db, user=self.user, role=DatabaseMembership.Role.ADMIN)
        DatabaseMembership.objects.create(database=suppliers_db, user=self.user, role=DatabaseMembership.Role.ADMIN)
        DatabaseMembership.objects.create(database=orders_db, user=self.user, role=DatabaseMembership.Role.ADMIN)

        relation_field = CustomField.objects.create(
            database=orders_db,
            label="Cliente",
            key="cliente",
            field_type=CustomField.FieldType.RELATION,
            relation_database=customers_db,
            required=False,
            position=1,
        )
        Record.objects.create(
            database=orders_db,
            title="Pedido 1",
            data={"cliente": "7"},
            created_by=self.user,
            updated_by=self.user,
        )

        response = self.client.post(
            reverse("field_update", args=[orders_db.slug, relation_field.pk]),
            {
                "label": "Cliente",
                "field_type": CustomField.FieldType.RELATION,
                "help_text": "",
                "options_text": "",
                "relation_database": str(suppliers_db.pk),
                "show_in_table": "on",
            },
        )

        self.assertEqual(response.status_code, 302)
        relation_field.refresh_from_db()
        self.assertEqual(relation_field.relation_database, customers_db)

    def test_import_csv_relation_requires_unique_match_or_id(self):
        self.client.login(username="admin", password="secret123")
        clients_db = AppDatabase.objects.create(name="Clientes", slug="clientes-dup", created_by=self.user)
        tasks_db = AppDatabase.objects.create(name="Tareas", slug="tareas-dup", created_by=self.user)
        DatabaseMembership.objects.create(database=clients_db, user=self.user, role=DatabaseMembership.Role.ADMIN)
        DatabaseMembership.objects.create(database=tasks_db, user=self.user, role=DatabaseMembership.Role.ADMIN)
        Record.objects.create(database=clients_db, title="Globex", data={}, created_by=self.user, updated_by=self.user)
        Record.objects.create(database=clients_db, title="Globex", data={}, created_by=self.user, updated_by=self.user)
        CustomField.objects.create(
            database=tasks_db,
            label="Tarea",
            key="tarea",
            field_type=CustomField.FieldType.TEXT,
            required=True,
            position=1,
            is_primary=True,
        )
        CustomField.objects.create(
            database=tasks_db,
            label="Cliente",
            key="cliente",
            field_type=CustomField.FieldType.RELATION,
            relation_database=clients_db,
            required=False,
            position=2,
        )
        csv_file = SimpleUploadedFile(
            "tareas_duplicadas.csv",
            b"Tarea,Cliente\nLlamar,Globex\n",
            content_type="text/csv",
        )

        start_response = self.client.post(
            reverse("records_import", args=[tasks_db.slug]),
            {"csv_file": csv_file, "has_header": "on"},
        )
        self.assertEqual(start_response.status_code, 302)

        mapping_response = self.client.post(
            reverse("records_import_map", args=[tasks_db.slug]),
            {
                "map_Tarea": "tarea",
                "map_Cliente": "cliente",
            },
            follow=True,
        )

        self.assertEqual(tasks_db.records.count(), 0)
        self.assertContains(mapping_response, "Importa usando el ID del registro relacionado")

    def test_structure_tab_shows_accessible_related_databases_in_field_form(self):
        self.client.login(username="admin", password="secret123")
        related_db = AppDatabase.objects.create(name="Clientes", slug="clientes-rel", created_by=self.user)
        current_db = AppDatabase.objects.create(name="Pedidos", slug="pedidos-rel", created_by=self.user)
        DatabaseMembership.objects.create(database=related_db, user=self.user, role=DatabaseMembership.Role.ADMIN)
        DatabaseMembership.objects.create(database=current_db, user=self.user, role=DatabaseMembership.Role.ADMIN)

        response = self.client.get(reverse("database_detail", args=[current_db.slug]), {"tab": "structure"})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Base relacionada")
        self.assertContains(response, "Clientes")

    def test_user_cannot_link_record_to_unaccessible_relation_database(self):
        other_user = User.objects.create_user(username="otro", password="secret123")
        database = AppDatabase.objects.create(name="Pedidos", slug="pedidos-test", has_priority=True, created_by=self.user)
        hidden_db = AppDatabase.objects.create(name="Privada", slug="privada-test", created_by=other_user)
        DatabaseMembership.objects.create(database=database, user=self.user, role=DatabaseMembership.Role.ADMIN)
        DatabaseMembership.objects.create(database=hidden_db, user=other_user, role=DatabaseMembership.Role.ADMIN)
        hidden_record = Record.objects.create(
            database=hidden_db,
            title="Cliente secreto",
            priority=Record.Priority.NORMAL,
            data={},
            created_by=other_user,
            updated_by=other_user,
        )
        CustomField.objects.create(
            database=database,
            label="Pedido",
            key="pedido",
            field_type=CustomField.FieldType.TEXT,
            required=True,
            position=1,
            is_primary=True,
        )
        CustomField.objects.create(
            database=database,
            label="Cliente",
            key="cliente",
            field_type=CustomField.FieldType.RELATION,
            relation_database=hidden_db,
            required=False,
            position=2,
        )

        self.client.login(username="admin", password="secret123")
        response = self.client.post(
            reverse("record_create", args=[database.slug]),
            {
                "pedido": "Pedido restringido",
                "priority": Record.Priority.NORMAL,
                "cliente": str(hidden_record.pk),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Seleccione una opción válida")
        self.assertEqual(database.records.count(), 0)

    def test_cannot_delete_field_with_existing_data(self):
        self.client.login(username="admin", password="secret123")
        database = AppDatabase.objects.create(name="Catalogo seguro", slug="catalogo-seguro", created_by=self.user)
        DatabaseMembership.objects.create(database=database, user=self.user, role=DatabaseMembership.Role.ADMIN)
        field = CustomField.objects.create(
            database=database,
            label="Codigo",
            key="codigo",
            field_type=CustomField.FieldType.TEXT,
            required=False,
            position=1,
        )
        Record.objects.create(
            database=database,
            title="Item 1",
            priority=Record.Priority.NORMAL,
            data={"codigo": "A-100"},
            created_by=self.user,
            updated_by=self.user,
        )

        response = self.client.post(reverse("field_delete", args=[database.slug, field.pk]))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(database.fields.filter(pk=field.pk).exists())

    def test_admin_can_delete_database_with_explicit_confirmation(self):
        self.client.login(username="admin", password="secret123")
        database = AppDatabase.objects.create(name="Base critica", slug="base-critica", created_by=self.user)
        DatabaseMembership.objects.create(database=database, user=self.user, role=DatabaseMembership.Role.ADMIN)

        response = self.client.post(
            reverse("database_delete", args=[database.slug]),
            {
                "confirmation_name": "Base critica",
                "confirmation_phrase": "ELIMINAR",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertFalse(AppDatabase.objects.filter(pk=database.pk).exists())

    def test_database_delete_requires_exact_confirmation(self):
        self.client.login(username="admin", password="secret123")
        database = AppDatabase.objects.create(name="Base sensible", slug="base-sensible", created_by=self.user)
        DatabaseMembership.objects.create(database=database, user=self.user, role=DatabaseMembership.Role.ADMIN)

        response = self.client.post(
            reverse("database_delete", args=[database.slug]),
            {
                "confirmation_name": "Base",
                "confirmation_phrase": "ELIMINAR",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(AppDatabase.objects.filter(pk=database.pk).exists())
