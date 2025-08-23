# Generated manually to mark UUID field state

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0003_fix_authentication_models"),
    ]

    operations = [
        # This migration just marks the UUID field as added in Django's migration state
        # The field already exists in the database
        migrations.AddField(
            model_name='user',
            name='uuid',
            field=models.CharField(max_length=32, unique=True, blank=True),
        ),
    ]