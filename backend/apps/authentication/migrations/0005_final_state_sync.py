# Generated manually to sync final state

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("authentication", "0004_uuid_field_state"),
    ]

    operations = [
        # This migration marks the database as being in the correct state
        # without actually performing any operations
        migrations.RunSQL(
            sql="SELECT 1;",  # No-op SQL
            reverse_sql="SELECT 1;"
        ),
    ]