# Generated migration for forms app

from django.db import migrations, models
import django.db.models.deletion
import uuid
from django.conf import settings

class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='FormTemplate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('form_type', models.CharField(choices=[('contact', 'Contact Form'), ('survey', 'Survey Form'), ('registration', 'Registration Form'), ('feedback', 'Feedback Form'), ('application', 'Application Form'), ('custom', 'Custom Form')], default='custom', max_length=50)),
                ('schema', models.JSONField(default=dict)),
                ('settings', models.JSONField(default=dict)),
                ('is_active', models.BooleanField(default=True)),
                ('is_template', models.BooleanField(default=True)),
                ('version', models.CharField(default='1.0', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='form_templates', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'form_templates',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Form',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200)),
                ('slug', models.SlugField(unique=True)),
                ('description', models.TextField(blank=True)),
                ('schema', models.JSONField(default=dict)),
                ('validation_rules', models.JSONField(default=dict)),
                ('conditional_logic', models.JSONField(default=dict)),
                ('settings', models.JSONField(default=dict)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('active', 'Active'), ('inactive', 'Inactive'), ('archived', 'Archived')], default='draft', max_length=20)),
                ('is_multi_step', models.BooleanField(default=False)),
                ('steps_config', models.JSONField(default=dict)),
                ('auto_save_enabled', models.BooleanField(default=True)),
                ('requires_approval', models.BooleanField(default=False)),
                ('approval_workflow', models.JSONField(default=dict)),
                ('encryption_enabled', models.BooleanField(default=False)),
                ('spam_protection_enabled', models.BooleanField(default=True)),
                ('analytics_enabled', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('published_at', models.DateTimeField(blank=True, null=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='forms', to=settings.AUTH_USER_MODEL)),
                ('template', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='forms.formtemplate')),
            ],
            options={
                'db_table': 'forms',
                'ordering': ['-created_at'],
            },
        ),
    ]