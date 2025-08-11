# Generated migration for tenant models

from django.db import migrations, models
import django.contrib.auth.models
import django.contrib.auth.validators
import django.core.validators
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='Tenant',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200)),
                ('slug', models.SlugField(max_length=100, unique=True)),
                ('domain', models.CharField(blank=True, max_length=255, null=True, unique=True)),
                ('subdomain', models.CharField(max_length=100, unique=True)),
                ('logo', models.ImageField(blank=True, null=True, upload_to='tenant_logos/')),
                ('primary_color', models.CharField(default='#007bff', max_length=7)),
                ('secondary_color', models.CharField(default='#6c757d', max_length=7)),
                ('favicon', models.ImageField(blank=True, null=True, upload_to='tenant_favicons/')),
                ('plan', models.CharField(choices=[('starter', 'Starter'), ('professional', 'Professional'), ('enterprise', 'Enterprise'), ('custom', 'Custom')], default='starter', max_length=20)),
                ('status', models.CharField(choices=[('active', 'Active'), ('suspended', 'Suspended'), ('trial', 'Trial'), ('expired', 'Expired'), ('cancelled', 'Cancelled')], default='trial', max_length=20)),
                ('trial_ends_at', models.DateTimeField(blank=True, null=True)),
                ('subscription_starts_at', models.DateTimeField(blank=True, null=True)),
                ('subscription_ends_at', models.DateTimeField(blank=True, null=True)),
                ('max_users', models.IntegerField(default=5)),
                ('max_products', models.IntegerField(default=100)),
                ('max_orders', models.IntegerField(default=1000)),
                ('max_storage_gb', models.IntegerField(default=1)),
                ('contact_name', models.CharField(max_length=200)),
                ('contact_email', models.EmailField(max_length=254)),
                ('contact_phone', models.CharField(blank=True, max_length=20, null=True)),
                ('address_line1', models.CharField(blank=True, max_length=255, null=True)),
                ('address_line2', models.CharField(blank=True, max_length=255, null=True)),
                ('city', models.CharField(blank=True, max_length=100, null=True)),
                ('state', models.CharField(blank=True, max_length=100, null=True)),
                ('postal_code', models.CharField(blank=True, max_length=20, null=True)),
                ('country', models.CharField(blank=True, max_length=100, null=True)),
                ('timezone', models.CharField(default='UTC', max_length=50)),
                ('currency', models.CharField(default='USD', max_length=3)),
                ('language', models.CharField(default='en', max_length=10)),
                ('features', models.JSONField(default=dict)),
                ('custom_settings', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'tenants',
                'ordering': ['name'],
            },
        ),
    ]