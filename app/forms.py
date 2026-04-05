import csv
import io
import json
import uuid
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.db.models import Max
from django.urls import reverse
from django.utils.text import slugify

from django.conf import settings

from .models import AppDatabase, CustomField, DatabaseMembership, Record, SavedStatistic, SavedView


User = get_user_model()


class RelationRecordChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"#{obj.pk} - {obj.title}"


class LoginForm(AuthenticationForm):
    username = forms.CharField(label="Usuario")


class RegisterForm(UserCreationForm):
    email = forms.EmailField(label="Email")
    first_name = forms.CharField(label="Nombre", max_length=30, required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "first_name", "email")


class WizardTemplateForm(forms.Form):
    starter_template = forms.ChoiceField(
        label="Plantilla inicial",
        initial="inventory",
        choices=(
            ("inventory", "Productos / Inventario"),
            ("students", "Alumnos / Cursos"),
            ("clients", "Clientes / Contactos"),
            ("generic", "Otra / General"),
            ("blank", "Empezar desde cero"),
        ),
    )


class WizardSetupForm(forms.Form):
    name = forms.CharField(label="Nombre de tu base", max_length=120)
    description = forms.CharField(
        label="Para que la vas a usar",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )


class WizardOptionsForm(forms.Form):
    selected_fields = forms.MultipleChoiceField(
        label="Campos iniciales",
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    load_demo_data = forms.BooleanField(
        label="Cargar ejemplos para entender la base",
        required=False,
        initial=True,
    )
    custom_fields_json = forms.CharField(widget=forms.HiddenInput(), required=False)

    def __init__(self, *args, **kwargs):
        field_choices = kwargs.pop("field_choices", ())
        super().__init__(*args, **kwargs)
        self.fields["selected_fields"].choices = field_choices

    def clean(self):
        cleaned_data = super().clean()
        selected_fields = cleaned_data.get("selected_fields") or []
        custom_fields = []
        raw_custom_fields = cleaned_data.get("custom_fields_json") or "[]"
        try:
            parsed_custom_fields = json.loads(raw_custom_fields)
        except json.JSONDecodeError as exc:
            raise ValidationError("No se pudieron leer los campos personalizados agregados en este paso.") from exc

        if not isinstance(parsed_custom_fields, list):
            raise ValidationError("El formato de los campos personalizados no es valido.")

        for item in parsed_custom_fields:
            if not isinstance(item, dict):
                raise ValidationError("Cada campo personalizado debe tener un formato valido.")
            label = str(item.get("label", "")).strip()
            field_type = str(item.get("field_type", "")).strip()
            options_text = str(item.get("options_text", "")).strip()
            if not label and not field_type and not options_text:
                continue
            if label and not field_type:
                raise ValidationError("Todos los campos personalizados necesitan un tipo.")
            if field_type and not label:
                raise ValidationError("Todos los campos personalizados necesitan un nombre.")
            if field_type == CustomField.FieldType.SELECT and not options_text:
                raise ValidationError("Los campos personalizados de seleccion necesitan opciones.")
            if field_type != CustomField.FieldType.SELECT:
                options_text = ""
            custom_fields.append(
                {
                    "label": label,
                    "field_type": field_type,
                    "options_text": options_text,
                }
            )
        selected_non_system_fields = [value for value in selected_fields if value != "__priority__"]
        if not selected_non_system_fields and not custom_fields:
            raise ValidationError("Selecciona al menos un campo para identificar tus registros o agrega uno propio.")
        cleaned_data["custom_fields"] = custom_fields
        return cleaned_data


class SaveViewForm(forms.ModelForm):
    class Meta:
        model = SavedView
        fields = ("name",)
        labels = {"name": "Nombre de la vista"}


class SavedStatisticForm(forms.ModelForm):
    class Meta:
        model = SavedStatistic
        fields = ("name",)
        labels = {"name": "Nombre de la estadistica"}


class CSVMappingForm(forms.Form):
    def __init__(self, database, headers, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = [("__ignore__", "Ignorar")]
        choices += [(field.key, field.label) for field in database.fields.all()]
        if database.has_priority:
            choices.append(("priority", "Prioridad"))
        for header in headers:
            self.fields[f"map_{header}"] = forms.ChoiceField(
                label=header,
                choices=choices,
            )


class CSVImportForm(forms.Form):
    csv_file = forms.FileField(label="Archivo CSV")
    has_header = forms.BooleanField(
        label="El archivo tiene encabezados",
        required=False,
        initial=True,
    )

    def __init__(self, database, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.database = database

    def clean_csv_file(self):
        csv_file = self.cleaned_data["csv_file"]
        if not csv_file.name.lower().endswith(".csv"):
            raise ValidationError("Sube un archivo con extension .csv.")
        return csv_file

    def save_temporary_upload(self):
        csv_file = self.cleaned_data["csv_file"]
        import_dir = Path(settings.BASE_DIR) / "tmp" / "imports"
        import_dir.mkdir(parents=True, exist_ok=True)
        suffix = Path(csv_file.name).suffix or ".csv"
        temp_name = f"{uuid.uuid4().hex}{suffix}"
        temp_path = import_dir / temp_name
        with temp_path.open("wb") as destination:
            for chunk in csv_file.chunks():
                destination.write(chunk)
        return str(temp_path)

    def inspect_file(self, file_path, preview_limit=5):
        rows = list(self.iter_rows(file_path))
        headers = list(rows[0].keys()) if rows else []
        return {
            "headers": headers,
            "preview_rows": rows[:preview_limit],
            "total_rows": len(rows),
        }

    def iter_rows(self, file_path):
        with Path(file_path).open("r", encoding="utf-8-sig", newline="") as csv_handle:
            content = csv_handle.read()
        buffer = io.StringIO(content)
        sample = content[:2048]
        try:
            fallback_sample = ",".join([field.key for field in self.database.fields.all()[:2]]) or "nombre"
            dialect = csv.Sniffer().sniff(sample or fallback_sample)
        except csv.Error:
            dialect = csv.excel

        if self.cleaned_data.get("has_header", True):
            reader = csv.DictReader(buffer, dialect=dialect)
            if not reader.fieldnames:
                raise ValidationError("No se encontraron encabezados en el CSV.")
            for row in reader:
                yield row
            return

        reader = csv.reader(buffer, dialect=dialect)
        fields = [field.key for field in self.database.fields.all()]
        if self.database.has_priority:
            fields.append("priority")
        for row in reader:
            mapped = {}
            for index, key in enumerate(fields):
                mapped[key] = row[index] if index < len(row) else ""
            yield mapped


class CustomFieldForm(forms.ModelForm):
    class Meta:
        model = CustomField
        fields = (
            "label",
            "field_type",
            "help_text",
            "options_text",
            "relation_database",
            "required",
            "show_in_table",
        )
        labels = {
            "label": "Nombre del campo",
            "field_type": "Tipo",
            "help_text": "Ayuda",
            "options_text": "Opciones",
            "relation_database": "Base relacionada",
            "required": "Obligatorio",
            "show_in_table": "Mostrar en la tabla principal",
        }
        widgets = {
            "options_text": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Una opcion por linea\nPendiente\nEn progreso\nCompletado",
                }
            ),
        }

    def __init__(self, database, *args, **kwargs):
        self.actor = kwargs.pop("actor", None)
        super().__init__(*args, **kwargs)
        self.database = database
        relation_queryset = AppDatabase.objects.exclude(pk=database.pk).order_by("name")
        if self.actor:
            relation_queryset = relation_queryset.filter(memberships__user=self.actor).distinct()
        self.fields["relation_database"].queryset = relation_queryset
        self.fields["field_type"].widget.attrs["data-field-type-control"] = "true"
        self.fields["options_text"].widget.attrs["data-options-input"] = "true"
        self.fields["relation_database"].widget.attrs["data-relation-input"] = "true"
        self.fields["options_text"].help_text = "Solo para campos de seleccion. Una opcion por linea."
        if relation_queryset.exists():
            self.fields["relation_database"].help_text = "Solo para campos de relacion. Elige una de tus otras bases para vincular registros."
        else:
            self.fields["relation_database"].help_text = "Todavia no tienes otra base disponible para relacionar. Crea otra base primero y luego vuelve a este campo."

    def _field_has_existing_data(self):
        if not self.instance.pk:
            return False
        field_key = self.instance.key
        for record in self.database.records.only("data"):
            if field_key in (record.data or {}) and record.data.get(field_key) not in ("", None):
                return True
        return False

    def clean(self):
        cleaned_data = super().clean()
        field_type = cleaned_data.get("field_type")
        options_text = (cleaned_data.get("options_text") or "").strip()
        relation_database = cleaned_data.get("relation_database")
        previous_type = self.instance.field_type if self.instance.pk else None
        previous_relation_database_id = self.instance.relation_database_id if self.instance.pk else None

        if field_type == CustomField.FieldType.SELECT and not options_text:
            self.add_error("options_text", "Define al menos una opcion para este campo.")
        if field_type == CustomField.FieldType.RELATION and not relation_database:
            self.add_error("relation_database", "Elegi una base relacionada.")
        if (
            self.instance.pk
            and previous_type
            and field_type
            and previous_type != field_type
            and self._field_has_existing_data()
        ):
            self.add_error(
                "field_type",
                "No puedes cambiar el tipo de un campo que ya tiene datos. Crea uno nuevo o vacia los registros primero.",
            )
        if (
            self.instance.pk
            and previous_type == CustomField.FieldType.RELATION
            and field_type == CustomField.FieldType.RELATION
            and previous_relation_database_id != getattr(relation_database, "pk", None)
            and self._field_has_existing_data()
        ):
            self.add_error(
                "relation_database",
                "No puedes cambiar la base relacionada de un campo que ya tiene datos. Crea uno nuevo o limpia esos registros primero.",
            )
        if field_type != CustomField.FieldType.SELECT:
            cleaned_data["options_text"] = ""
        if field_type != CustomField.FieldType.RELATION:
            cleaned_data["relation_database"] = None
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.database = self.database
        if not instance.pk:
            instance.key = slugify(instance.label).replace("-", "_")
            max_position = self.database.fields.aggregate(Max("position"))["position__max"] or 0
            instance.position = max_position + 1
        if commit:
            instance.save()
        return instance


class MembershipForm(forms.Form):
    username = forms.CharField(label="Usuario")
    role = forms.ChoiceField(label="Rol", choices=DatabaseMembership.Role.choices)

    def __init__(self, database, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.database = database

    def clean_username(self):
        username = self.cleaned_data["username"]
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist as exc:
            raise ValidationError("No existe un usuario con ese nombre.") from exc

    def save(self):
        user = self.cleaned_data["username"]
        membership, _ = DatabaseMembership.objects.update_or_create(
            database=self.database,
            user=user,
            defaults={"role": self.cleaned_data["role"]},
        )
        return membership


class RecordForm(forms.Form):
    def __init__(self, database, *args, record=None, actor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.database = database
        self.record = record
        self.actor = actor
        self.primary_field = database.get_primary_field()

        if database.has_priority:
            self.fields["priority"] = forms.ChoiceField(label="Prioridad", choices=Record.Priority.choices)
            if record:
                self.fields["priority"].initial = record.priority

        for field in database.fields.all():
            self.fields[field.key] = self._build_form_field(field)
            if record:
                self.fields[field.key].initial = record.data.get(field.key)

    def _build_form_field(self, custom_field):
        common = {
            "label": custom_field.label,
            "required": custom_field.required,
            "help_text": custom_field.help_text,
        }
        if custom_field.field_type == CustomField.FieldType.NUMBER:
            return forms.DecimalField(decimal_places=2, **common)
        if custom_field.field_type == CustomField.FieldType.CURRENCY:
            return forms.DecimalField(decimal_places=2, **common)
        if custom_field.field_type == CustomField.FieldType.BOOLEAN:
            return forms.BooleanField(
                required=False,
                label=custom_field.label,
                help_text=custom_field.help_text,
            )
        if custom_field.field_type == CustomField.FieldType.DATE:
            return forms.DateField(widget=forms.DateInput(attrs={"type": "date"}), **common)
        if custom_field.field_type == CustomField.FieldType.EMAIL:
            return forms.EmailField(**common)
        if custom_field.field_type == CustomField.FieldType.PHONE:
            return forms.CharField(**common)
        if custom_field.field_type == CustomField.FieldType.SELECT:
            options = [(option, option) for option in custom_field.get_options()]
            return forms.ChoiceField(choices=options, **common)
        if custom_field.field_type == CustomField.FieldType.RELATION:
            queryset = Record.objects.none()
            if (
                custom_field.relation_database
                and self.actor
                and custom_field.relation_database.memberships.filter(user=self.actor).exists()
            ):
                queryset = custom_field.relation_database.records.order_by("title", "pk")
            relation_common = common.copy()
            relation_common["help_text"] = (
                f"{custom_field.help_text} Elige un registro de {custom_field.relation_database.name}."
                if custom_field.help_text and custom_field.relation_database
                else f"Elige un registro de {custom_field.relation_database.name}."
                if custom_field.relation_database
                else custom_field.help_text
            )
            field = RelationRecordChoiceField(
                queryset=queryset,
                empty_label="Selecciona un registro",
                **relation_common,
            )
            if custom_field.relation_database:
                field.widget.attrs["data-relation-field-key"] = custom_field.key
                field.widget.attrs["data-relation-field-id"] = str(custom_field.pk)
                field.widget.attrs["data-relation-create-url"] = reverse(
                    "record_create",
                    args=[custom_field.relation_database.slug],
                )
                field.widget.attrs["data-relation-search-url"] = reverse(
                    "relation_record_search",
                    args=[self.database.slug, custom_field.pk],
                )
                field.widget.attrs["data-relation-create-label"] = f"+ Agregar nuevo en {custom_field.relation_database.name}"
                field.widget.attrs["data-relation-searchable"] = "true"
            return field
        return forms.CharField(**common)

    def clean(self):
        cleaned_data = super().clean()
        data = {}
        for field in self.database.fields.all():
            value = cleaned_data.get(field.key)
            if value in ("", None):
                data[field.key] = False if field.field_type == CustomField.FieldType.BOOLEAN else ""
                continue
            if field.field_type in {CustomField.FieldType.NUMBER, CustomField.FieldType.CURRENCY}:
                try:
                    data[field.key] = str(Decimal(value))
                except (InvalidOperation, TypeError) as exc:
                    raise ValidationError(f"El campo {field.label} debe ser numerico.") from exc
            elif field.field_type == CustomField.FieldType.DATE:
                data[field.key] = value.isoformat()
            elif field.field_type == CustomField.FieldType.RELATION:
                data[field.key] = str(value.pk)
            else:
                data[field.key] = value
        if not self.primary_field:
            raise ValidationError("Esta base no tiene un campo principal definido. Agrega al menos un campo antes de cargar registros.")
        title_value = cleaned_data.get(self.primary_field.key)
        if title_value in ("", None):
            self.add_error(self.primary_field.key, "Este campo se usa como nombre visible del registro.")
        cleaned_data["record_title"] = self._format_title_value(self.primary_field, title_value)
        cleaned_data["record_data"] = data
        return cleaned_data

    def _format_title_value(self, field, value):
        if value in ("", None):
            return ""
        if field.field_type == CustomField.FieldType.BOOLEAN:
            return "Si" if value else "No"
        if field.field_type == CustomField.FieldType.DATE:
            return value.isoformat()
        if field.field_type == CustomField.FieldType.RELATION:
            return value.title
        return str(value).strip()

    def save(self, user):
        record = self.record or Record(database=self.database, created_by=user)
        record.title = self.cleaned_data["record_title"]
        record.priority = self.cleaned_data.get("priority") or Record.Priority.NORMAL
        record.data = self.cleaned_data["record_data"]
        record.updated_by = user
        record.save()
        return record
