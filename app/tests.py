from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .forms import CustomFieldForm
from .models import AppDatabase, CustomField, DatabaseMembership, Record


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
        suggested_fields=None,
        load_demo_data=False,
        preferred_mode="basic",
    ):
        suggested_fields = suggested_fields or []
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
            "preferred_mode": preferred_mode,
        }
        for field in suggested_fields:
            payload.setdefault("suggested_fields", [])
            payload["suggested_fields"].append(field)
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
            "preferred_mode": preferred_mode,
        }
        for field in suggested_fields:
            confirm_payload.setdefault("suggested_fields", [])
            confirm_payload["suggested_fields"].append(field)
        if load_demo_data:
            confirm_payload["load_demo_data"] = "on"
        return self.client.post(reverse("database_create"), confirm_payload)

    def test_create_database_with_template(self):
        self.client.login(username="admin", password="secret123")
        response = self.complete_creation_wizard()
        self.assertEqual(response.status_code, 302)
        database = AppDatabase.objects.get(name="Inventario central")
        self.assertTrue(database.fields.filter(label="Precio").exists())
        self.assertTrue(
            DatabaseMembership.objects.filter(
                database=database,
                user=self.user,
                role=DatabaseMembership.Role.ADMIN,
            ).exists()
        )

    def test_create_record(self):
        self.client.login(username="admin", password="secret123")
        database = AppDatabase.objects.create(
            name="Productos",
            slug="productos",
            created_by=self.user,
        )
        DatabaseMembership.objects.create(
            database=database,
            user=self.user,
            role=DatabaseMembership.Role.ADMIN,
        )
        CustomField.objects.create(
            database=database,
            label="Precio",
            key="precio",
            field_type=CustomField.FieldType.CURRENCY,
            required=True,
            position=1,
        )
        response = self.client.post(
            reverse("record_create", args=[database.slug]),
            {
                "title": "Cafe molido",
                "priority": Record.Priority.URGENT,
                "precio": "1500",
            },
        )
        self.assertEqual(response.status_code, 302)
        record = database.records.get()
        self.assertEqual(record.data["precio"], "1500")

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
            created_by=self.user,
        )
        DatabaseMembership.objects.create(
            database=database,
            user=self.user,
            role=DatabaseMembership.Role.ADMIN,
        )
        CustomField.objects.create(
            database=database,
            label="Precio",
            key="precio",
            field_type=CustomField.FieldType.CURRENCY,
            required=False,
            position=1,
        )
        csv_file = SimpleUploadedFile(
            "productos.csv",
            b"title,priority,Precio\nCafe,urgent,1200\nTe,high,900\n",
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
                "map_title": "title",
                "map_priority": "priority",
                "map_Precio": "precio",
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
            created_by=self.user,
        )
        DatabaseMembership.objects.create(
            database=database,
            user=self.user,
            role=DatabaseMembership.Role.ADMIN,
        )
        field = CustomField.objects.create(
            database=database,
            label="Empresa",
            key="empresa",
            field_type=CustomField.FieldType.TEXT,
            required=False,
            position=1,
        )
        Record.objects.create(
            database=database,
            title="Acme",
            priority=Record.Priority.HIGH,
            data={field.key: "Acme SA"},
            created_by=self.user,
            updated_by=self.user,
        )
        response = self.client.get(reverse("records_export", args=[database.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertIn("title,priority,Empresa", response.content.decode("utf-8-sig"))
        self.assertIn("Acme,high,Acme SA", response.content.decode("utf-8-sig"))

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
            label="Cliente",
            key="cliente",
            field_type=CustomField.FieldType.RELATION,
            relation_database=clients_db,
            required=True,
            position=1,
        )
        CustomField.objects.create(
            database=orders_db,
            label="Estado",
            key="estado",
            field_type=CustomField.FieldType.SELECT,
            options_text="Pendiente\nEntregado",
            required=True,
            position=2,
        )
        response = self.client.post(
            reverse("record_create", args=[orders_db.slug]),
            {
                "title": "Pedido 001",
                "priority": Record.Priority.HIGH,
                "cliente": str(client_record.pk),
                "estado": "Pendiente",
            },
        )
        self.assertEqual(response.status_code, 302)
        record = orders_db.records.get()
        self.assertEqual(record.data["cliente"], str(client_record.pk))
        self.assertEqual(record.get_display_value(orders_db.fields.get(key="cliente")), "Acme SA")

    def test_import_csv_with_relation_by_title(self):
        self.client.login(username="admin", password="secret123")
        clients_db = AppDatabase.objects.create(name="Clientes", slug="clientes", created_by=self.user)
        tasks_db = AppDatabase.objects.create(name="Tareas", slug="tareas", created_by=self.user)
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
            label="Cliente",
            key="cliente",
            field_type=CustomField.FieldType.RELATION,
            relation_database=clients_db,
            required=False,
            position=1,
        )
        csv_file = SimpleUploadedFile(
            "tareas.csv",
            b"title,priority,Cliente\nLlamar a cliente,high,Globex\n",
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
                "map_title": "title",
                "map_priority": "priority",
                "map_Cliente": "cliente",
            },
        )
        self.assertEqual(mapping_response.status_code, 302)
        imported = tasks_db.records.get()
        self.assertEqual(imported.get_display_value(tasks_db.fields.get(key="cliente")), "Globex")

    def test_record_detail_shows_bidirectional_relations(self):
        self.client.login(username="admin", password="secret123")
        clients_db = AppDatabase.objects.create(name="Clientes", slug="clientes", created_by=self.user)
        orders_db = AppDatabase.objects.create(name="Pedidos", slug="pedidos", created_by=self.user)
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
        relation_field = CustomField.objects.create(
            database=orders_db,
            label="Cliente",
            key="cliente",
            field_type=CustomField.FieldType.RELATION,
            relation_database=clients_db,
            required=False,
            position=1,
        )
        order = Record.objects.create(
            database=orders_db,
            title="Pedido 900",
            priority=Record.Priority.HIGH,
            data={relation_field.key: str(client.pk)},
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

    def test_database_tabs_render_specific_sections(self):
        self.client.login(username="admin", password="secret123")
        database = AppDatabase.objects.create(name="Operaciones", slug="operaciones", created_by=self.user)
        DatabaseMembership.objects.create(database=database, user=self.user, role=DatabaseMembership.Role.ADMIN)

        records_response = self.client.get(reverse("database_detail", args=[database.slug]), {"tab": "records"})
        self.assertEqual(records_response.status_code, 200)
        self.assertContains(records_response, "Buscar y operar elementos")
        self.assertContains(records_response, "Agregar registro")

        structure_response = self.client.get(reverse("database_detail", args=[database.slug]), {"tab": "structure"})
        self.assertEqual(structure_response.status_code, 200)
        self.assertContains(structure_response, "Mapa visual de la base")
        self.assertContains(structure_response, "Agregar campo o relacion")

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
            created_by=self.user,
        )
        DatabaseMembership.objects.create(database=database, user=self.user, role=DatabaseMembership.Role.ADMIN)
        lines = ["title,priority"]
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
                "map_title": "title",
                "map_priority": "priority",
            },
        )
        self.assertEqual(mapping_response.status_code, 302)
        self.assertEqual(database.records.count(), 60)

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

    def test_user_cannot_link_record_to_unaccessible_relation_database(self):
        other_user = User.objects.create_user(username="otro", password="secret123")
        database = AppDatabase.objects.create(name="Pedidos", slug="pedidos-test", created_by=self.user)
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
            label="Cliente",
            key="cliente",
            field_type=CustomField.FieldType.RELATION,
            relation_database=hidden_db,
            required=False,
            position=1,
        )

        self.client.login(username="admin", password="secret123")
        response = self.client.post(
            reverse("record_create", args=[database.slug]),
            {
                "title": "Pedido restringido",
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
