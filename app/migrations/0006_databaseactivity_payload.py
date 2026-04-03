from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0005_databaseactivity"),
    ]

    operations = [
        migrations.AddField(
            model_name="databaseactivity",
            name="payload",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
