# Generated migration for chart models

from django.db import migrations, models
import django.db.models.deletion
import uuid
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('admin_panel', '0002_simple_indexes'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ChartTemplate',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('chart_type', models.CharField(choices=[('line', 'Line Chart'), ('bar', 'Bar Chart'), ('pie', 'Pie Chart'), ('area', 'Area Chart'), ('scatter', 'Scatter Plot'), ('heatmap', 'Heatmap'), ('gauge', 'Gauge Chart'), ('funnel', 'Funnel Chart'), ('treemap', 'Treemap'), ('radar', 'Radar Chart')], max_length=50)),
                ('category', models.CharField(max_length=100)),
                ('config', models.JSONField(default=dict)),
                ('data_source', models.CharField(max_length=200)),
                ('is_public', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'admin_chart_templates',
                'ordering': ['category', 'name'],
            },
        ),
        migrations.CreateModel(
            name='Chart',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('chart_type', models.CharField(choices=[('line', 'Line Chart'), ('bar', 'Bar Chart'), ('pie', 'Pie Chart'), ('area', 'Area Chart'), ('scatter', 'Scatter Plot'), ('heatmap', 'Heatmap'), ('gauge', 'Gauge Chart'), ('funnel', 'Funnel Chart'), ('treemap', 'Treemap'), ('radar', 'Radar Chart')], max_length=50)),
                ('config', models.JSONField(default=dict)),
                ('data_source', models.CharField(max_length=200)),
                ('refresh_interval', models.IntegerField(default=300)),
                ('theme', models.CharField(default='default', max_length=50)),
                ('colors', models.JSONField(default=list)),
                ('custom_css', models.TextField(blank=True)),
                ('is_public', models.BooleanField(default=False)),
                ('allowed_roles', models.JSONField(default=list)),
                ('status', models.CharField(choices=[('active', 'Active'), ('draft', 'Draft'), ('archived', 'Archived')], default='active', max_length=20)),
                ('is_real_time', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('last_accessed', models.DateTimeField(blank=True, null=True)),
                ('access_count', models.IntegerField(default=0)),
                ('allowed_users', models.ManyToManyField(blank=True, to=settings.AUTH_USER_MODEL)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_charts', to=settings.AUTH_USER_MODEL)),
                ('template', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='admin_panel.charttemplate')),
            ],
            options={
                'db_table': 'admin_charts',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ChartVersion',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('version_number', models.IntegerField()),
                ('title', models.CharField(max_length=200)),
                ('config', models.JSONField()),
                ('changes_summary', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('chart', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='versions', to='admin_panel.chart')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'admin_chart_versions',
                'ordering': ['-version_number'],
            },
        ),
        migrations.CreateModel(
            name='ChartAnnotation',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('annotation_type', models.CharField(choices=[('note', 'Note'), ('highlight', 'Highlight'), ('trend_line', 'Trend Line'), ('threshold', 'Threshold'), ('event', 'Event Marker')], max_length=50)),
                ('title', models.CharField(max_length=200)),
                ('content', models.TextField()),
                ('position', models.JSONField()),
                ('style', models.JSONField(default=dict)),
                ('is_visible', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('chart', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='annotations', to='admin_panel.chart')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'admin_chart_annotations',
            },
        ),
        migrations.CreateModel(
            name='ChartComment',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('content', models.TextField()),
                ('position', models.JSONField(blank=True, null=True)),
                ('is_resolved', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('chart', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to='admin_panel.chart')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='admin_panel.chartcomment')),
            ],
            options={
                'db_table': 'admin_chart_comments',
                'ordering': ['created_at'],
            },
        ),
        migrations.CreateModel(
            name='ChartShare',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('share_type', models.CharField(choices=[('public_link', 'Public Link'), ('embed_code', 'Embed Code'), ('api_access', 'API Access'), ('email', 'Email Share')], max_length=50)),
                ('share_token', models.CharField(max_length=100, unique=True)),
                ('expires_at', models.DateTimeField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('access_count', models.IntegerField(default=0)),
                ('settings', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('chart', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='shares', to='admin_panel.chart')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'admin_chart_shares',
            },
        ),
        migrations.CreateModel(
            name='ChartPerformanceMetric',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('load_time', models.FloatField()),
                ('data_size', models.IntegerField()),
                ('render_time', models.FloatField()),
                ('user_agent', models.TextField()),
                ('ip_address', models.GenericIPAddressField()),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('chart', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='performance_metrics', to='admin_panel.chart')),
            ],
            options={
                'db_table': 'admin_chart_performance',
            },
        ),
        migrations.CreateModel(
            name='ChartDataCache',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('cache_key', models.CharField(max_length=200, unique=True)),
                ('data', models.JSONField()),
                ('expires_at', models.DateTimeField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('chart', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='data_cache', to='admin_panel.chart')),
            ],
            options={
                'db_table': 'admin_chart_data_cache',
            },
        ),
        migrations.CreateModel(
            name='ChartExport',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('export_format', models.CharField(choices=[('png', 'PNG Image'), ('pdf', 'PDF Document'), ('svg', 'SVG Vector'), ('excel', 'Excel Spreadsheet'), ('csv', 'CSV Data'), ('json', 'JSON Data')], max_length=20)),
                ('file_path', models.CharField(max_length=500)),
                ('file_size', models.IntegerField()),
                ('export_settings', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('chart', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='exports', to='admin_panel.chart')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'admin_chart_exports',
            },
        ),
        migrations.AddIndex(
            model_name='chartperformancemetric',
            index=models.Index(fields=['chart', 'timestamp'], name='admin_chart_chart_i_b8c8a5_idx'),
        ),
        migrations.AddIndex(
            model_name='chartdatacache',
            index=models.Index(fields=['cache_key', 'expires_at'], name='admin_chart_cache_k_4f8b2a_idx'),
        ),
        migrations.AlterUniqueTogether(
            name='chartversion',
            unique_together={('chart', 'version_number')},
        ),
    ]