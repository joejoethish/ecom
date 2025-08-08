"""
Simple indexes and basic setup for admin panel.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('admin_panel', '0001_initial'),
    ]

    operations = [
        # Skip additional indexes and views for now - Django creates the basic ones automatically
        # Views will be created later when all dependent tables exist
    ]