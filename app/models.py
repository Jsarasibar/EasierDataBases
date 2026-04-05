from django.conf import settings
from django.db import models
from django.utils.text import slugify


class AppDatabase(models.Model):
    class UseCase(models.TextChoices):
        INVENTORY = "inventory", "Inventario / Productos"
        STUDENTS = "students", "Alumnos"
        CLIENTS = "clients", "Clientes"
        GENERIC = "generic", "General"

    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True)
    description = models.TextField(blank=True)
    has_priority = models.BooleanField(default=False)
    use_case = models.CharField(
        max_length=20,
        choices=UseCase.choices,
        default=UseCase.INVENTORY,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_databases",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_primary_field(self):
        return self.fields.filter(is_primary=True).order_by("position", "id").first() or self.fields.order_by("position", "id").first()

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or "base"
            slug = base_slug
            counter = 2
            while AppDatabase.objects.exclude(pk=self.pk).filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)


class DatabaseMembership(models.Model):
    class Role(models.TextChoices):
        ADMIN = "admin", "Administrador"
        EDITOR = "editor", "Editor"

    database = models.ForeignKey(
        AppDatabase,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="database_memberships",
    )
    role = models.CharField(max_length=12, choices=Role.choices, default=Role.EDITOR)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("database", "user")
        ordering = ["database", "user__username"]

    def __str__(self):
        return f"{self.user} -> {self.database} ({self.get_role_display()})"


class CustomField(models.Model):
    class FieldType(models.TextChoices):
        TEXT = "text", "Texto"
        DESCRIPTION = "description", "Descripcion"
        NUMBER = "number", "Numero"
        CURRENCY = "currency", "Moneda"
        BOOLEAN = "boolean", "Si / No"
        DATE = "date", "Fecha"
        EMAIL = "email", "Email"
        PHONE = "phone", "Telefono"
        SELECT = "select", "Seleccion"
        RELATION = "relation", "Relacion con otra base"

    database = models.ForeignKey(
        AppDatabase,
        on_delete=models.CASCADE,
        related_name="fields",
    )
    label = models.CharField(max_length=80)
    key = models.SlugField(max_length=80)
    field_type = models.CharField(max_length=12, choices=FieldType.choices)
    help_text = models.CharField(max_length=180, blank=True)
    options_text = models.TextField(blank=True)
    relation_database = models.ForeignKey(
        AppDatabase,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="incoming_relation_fields",
    )
    required = models.BooleanField(default=False)
    show_in_table = models.BooleanField(default=True)
    is_primary = models.BooleanField(default=False)
    position = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("database", "key")
        ordering = ["position", "id"]

    def __str__(self):
        return f"{self.database.name}: {self.label}"

    def get_options(self):
        return [option.strip() for option in self.options_text.splitlines() if option.strip()]

    def save(self, *args, **kwargs):
        if not self.key:
            base_key = slugify(self.label).replace("-", "_") or "campo"
            key = base_key
            counter = 2
            while CustomField.objects.exclude(pk=self.pk).filter(
                database=self.database,
                key=key,
            ).exists():
                key = f"{base_key}_{counter}"
                counter += 1
            self.key = key
        if not self.pk and not self.database.fields.filter(is_primary=True).exists():
            self.is_primary = True
        super().save(*args, **kwargs)
        if self.is_primary:
            CustomField.objects.filter(database=self.database).exclude(pk=self.pk).update(is_primary=False)


class Record(models.Model):
    class Priority(models.TextChoices):
        NORMAL = "normal", "Normal"
        HIGH = "high", "Alta"
        URGENT = "urgent", "Urgente"

    database = models.ForeignKey(
        AppDatabase,
        on_delete=models.CASCADE,
        related_name="records",
    )
    title = models.CharField(max_length=160)
    priority = models.CharField(
        max_length=12,
        choices=Priority.choices,
        default=Priority.NORMAL,
    )
    data = models.JSONField(default=dict, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_records",
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="updated_records",
    )
    archived_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="archived_records",
    )
    archived_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at", "-id"]

    def __str__(self):
        return self.title

    @property
    def is_archived(self):
        return self.archived_at is not None

    def get_value(self, field):
        return self.data.get(field.key, "")

    def get_display_value(self, field):
        value = self.get_value(field)
        if value in ("", None):
            return ""
        if field.field_type == CustomField.FieldType.BOOLEAN:
            return "Si" if value else "No"
        if field.field_type == CustomField.FieldType.RELATION and field.relation_database:
            try:
                related_record = field.relation_database.records.get(pk=int(value))
                return related_record.title
            except (ValueError, TypeError, Record.DoesNotExist):
                return f"Registro relacionado no disponible (ID {value})"
        return value


class SavedView(models.Model):
    database = models.ForeignKey(
        AppDatabase,
        on_delete=models.CASCADE,
        related_name="saved_views",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_views",
    )
    name = models.CharField(max_length=80)
    query = models.CharField(max_length=120, blank=True)
    priority = models.CharField(max_length=12, blank=True)
    sort = models.CharField(max_length=20, default="updated")
    view_mode = models.CharField(max_length=12, default="table")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("database", "user", "name")
        ordering = ["name"]

    def __str__(self):
        return f"{self.database.name}: {self.name}"


class SavedStatistic(models.Model):
    class ChartType(models.TextChoices):
        AUTO = "auto", "Automatico"
        BARS = "bars", "Barras"
        DONUT = "donut", "Dona"
        TABLE = "table", "Tabla"
        METRICS = "metrics", "Metricas"

    database = models.ForeignKey(
        AppDatabase,
        on_delete=models.CASCADE,
        related_name="saved_statistics",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_statistics",
    )
    name = models.CharField(max_length=80)
    field_key = models.CharField(max_length=80, default="__created_at__")
    chart_type = models.CharField(max_length=16, choices=ChartType.choices, default=ChartType.AUTO)
    query = models.CharField(max_length=120, blank=True)
    priority = models.CharField(max_length=12, blank=True)
    date_from = models.DateField(null=True, blank=True)
    date_to = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("database", "user", "name")
        ordering = ["name"]

    def __str__(self):
        return f"{self.database.name}: {self.name}"


class DatabaseActivity(models.Model):
    database = models.ForeignKey(
        AppDatabase,
        on_delete=models.CASCADE,
        related_name="activities",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="database_activities",
    )
    action = models.CharField(max_length=80)
    detail = models.CharField(max_length=220)
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"{self.database.name}: {self.action}"
