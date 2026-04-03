from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0004_appdatabase_has_priority_customfield_is_primary"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="DatabaseActivity",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("action", models.CharField(max_length=80)),
                ("detail", models.CharField(max_length=220)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="database_activities", to=settings.AUTH_USER_MODEL)),
                ("database", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="activities", to="app.appdatabase")),
            ],
            options={
                "ordering": ["-created_at", "-id"],
            },
        ),
    ]
