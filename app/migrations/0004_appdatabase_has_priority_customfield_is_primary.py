from django.db import migrations, models


def seed_existing_database_flags(apps, schema_editor):
    AppDatabase = apps.get_model("app", "AppDatabase")
    CustomField = apps.get_model("app", "CustomField")

    AppDatabase.objects.all().update(has_priority=True)

    for database in AppDatabase.objects.all():
        if CustomField.objects.filter(database=database, is_primary=True).exists():
            continue
        first_field = CustomField.objects.filter(database=database).order_by("position", "id").first()
        if first_field:
            first_field.is_primary = True
            first_field.save(update_fields=["is_primary"])


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0003_savedview"),
    ]

    operations = [
        migrations.AddField(
            model_name="appdatabase",
            name="has_priority",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="customfield",
            name="is_primary",
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(seed_existing_database_flags, migrations.RunPython.noop),
    ]
