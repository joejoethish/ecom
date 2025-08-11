# Generated manually for BI models

from django.db import migrations, models
import django.db.models.deletion
import uuid
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('analytics', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='BIDashboard',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('dashboard_type', models.CharField(choices=[('executive', 'Executive Summary'), ('sales', 'Sales Analytics'), ('financial', 'Financial Analytics'), ('operational', 'Operational Analytics'), ('customer', 'Customer Analytics'), ('product', 'Product Analytics'), ('custom', 'Custom Dashboard')], max_length=50)),
                ('layout_config', models.JSONField(default=dict)),
                ('filters_config', models.JSONField(default=dict)),
                ('refresh_interval', models.IntegerField(default=300)),
                ('is_public', models.BooleanField(default=False)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.user')),
                ('shared_with', models.ManyToManyField(blank=True, related_name='shared_dashboards', to='auth.user')),
            ],
            options={
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='BIDataSource',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('source_type', models.CharField(choices=[('database', 'Database Query'), ('api', 'API Endpoint'), ('file', 'File Upload'), ('external', 'External Service'), ('realtime', 'Real-time Stream')], max_length=50)),
                ('connection_config', models.JSONField(default=dict)),
                ('query_template', models.TextField(blank=True)),
                ('schema_definition', models.JSONField(default=dict)),
                ('refresh_schedule', models.CharField(choices=[('realtime', 'Real-time'), ('1min', 'Every Minute'), ('5min', 'Every 5 Minutes'), ('15min', 'Every 15 Minutes'), ('hourly', 'Hourly'), ('daily', 'Daily'), ('weekly', 'Weekly'), ('manual', 'Manual Only')], default='hourly', max_length=50)),
                ('last_refresh', models.DateTimeField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.user')),
            ],
        ),
        migrations.CreateModel(
            name='BIWidget',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200)),
                ('widget_type', models.CharField(choices=[('metric', 'Key Metric'), ('chart', 'Chart'), ('table', 'Data Table'), ('gauge', 'Gauge'), ('map', 'Geographic Map'), ('funnel', 'Funnel Chart'), ('heatmap', 'Heat Map'), ('treemap', 'Tree Map'), ('scatter', 'Scatter Plot'), ('timeline', 'Timeline'), ('custom', 'Custom Widget')], max_length=50)),
                ('data_source', models.CharField(max_length=100)),
                ('query_config', models.JSONField(default=dict)),
                ('visualization_config', models.JSONField(default=dict)),
                ('position_x', models.IntegerField(default=0)),
                ('position_y', models.IntegerField(default=0)),
                ('width', models.IntegerField(default=4)),
                ('height', models.IntegerField(default=3)),
                ('refresh_interval', models.IntegerField(default=300)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('dashboard', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='widgets', to='analytics.bidashboard')),
            ],
            options={
                'ordering': ['position_y', 'position_x'],
            },
        ),
        migrations.CreateModel(
            name='BIInsight',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('insight_type', models.CharField(choices=[('anomaly', 'Anomaly Detection'), ('trend', 'Trend Analysis'), ('correlation', 'Correlation Discovery'), ('forecast', 'Forecast Alert'), ('threshold', 'Threshold Breach'), ('pattern', 'Pattern Recognition'), ('recommendation', 'Recommendation'), ('alert', 'Business Alert')], max_length=50)),
                ('severity', models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], max_length=20)),
                ('metric_name', models.CharField(max_length=100)),
                ('current_value', models.DecimalField(blank=True, decimal_places=4, max_digits=15, null=True)),
                ('expected_value', models.DecimalField(blank=True, decimal_places=4, max_digits=15, null=True)),
                ('deviation_percentage', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('confidence_score', models.DecimalField(decimal_places=2, max_digits=5, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)])),
                ('metadata', models.JSONField(default=dict)),
                ('action_items', models.JSONField(default=list)),
                ('is_acknowledged', models.BooleanField(default=False)),
                ('acknowledged_at', models.DateTimeField(blank=True, null=True)),
                ('is_resolved', models.BooleanField(default=False)),
                ('resolution_notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('acknowledged_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='acknowledged_insights', to='auth.user')),
                ('data_source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='analytics.bidatasource')),
            ],
            options={
                'ordering': ['-created_at', '-severity'],
            },
        ),
        migrations.CreateModel(
            name='BIMLModel',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('model_type', models.CharField(choices=[('forecasting', 'Sales Forecasting'), ('classification', 'Customer Classification'), ('clustering', 'Customer Segmentation'), ('anomaly_detection', 'Anomaly Detection'), ('recommendation', 'Recommendation Engine'), ('churn_prediction', 'Churn Prediction'), ('price_optimization', 'Price Optimization'), ('demand_planning', 'Demand Planning')], max_length=50)),
                ('algorithm', models.CharField(max_length=100)),
                ('feature_config', models.JSONField(default=dict)),
                ('hyperparameters', models.JSONField(default=dict)),
                ('performance_metrics', models.JSONField(default=dict)),
                ('model_file_path', models.CharField(blank=True, max_length=500)),
                ('version', models.CharField(default='1.0', max_length=50)),
                ('is_deployed', models.BooleanField(default=False)),
                ('deployment_config', models.JSONField(default=dict)),
                ('last_trained', models.DateTimeField(blank=True, null=True)),
                ('last_prediction', models.DateTimeField(blank=True, null=True)),
                ('training_schedule', models.CharField(choices=[('manual', 'Manual'), ('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')], default='manual', max_length=50)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.user')),
                ('training_data_source', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ml_models', to='analytics.bidatasource')),
            ],
            options={
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='BIAnalyticsSession',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('query_history', models.JSONField(default=list)),
                ('visualizations', models.JSONField(default=list)),
                ('insights_discovered', models.JSONField(default=list)),
                ('bookmarks', models.JSONField(default=list)),
                ('collaboration_notes', models.TextField(blank=True)),
                ('is_public', models.BooleanField(default=False)),
                ('last_accessed', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('data_sources', models.ManyToManyField(related_name='analytics_sessions', to='analytics.bidatasource')),
                ('shared_with', models.ManyToManyField(blank=True, related_name='shared_analytics_sessions', to='auth.user')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='auth.user')),
            ],
            options={
                'ordering': ['-last_accessed'],
            },
        ),
    ]