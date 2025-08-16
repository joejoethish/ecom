# Generated migration for internationalization app

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Language',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=10, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('native_name', models.CharField(max_length=100)),
                ('is_active', models.BooleanField(default=True)),
                ('is_default', models.BooleanField(default=False)),
                ('is_rtl', models.BooleanField(default=False)),
                ('flag_icon', models.CharField(blank=True, max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Currency',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=3, unique=True)),
                ('name', models.CharField(max_length=100)),
                ('symbol', models.CharField(max_length=10)),
                ('decimal_places', models.IntegerField(default=2)),
                ('is_active', models.BooleanField(default=True)),
                ('is_default', models.BooleanField(default=False)),
                ('exchange_rate', models.DecimalField(decimal_places=6, default=1.0, max_digits=15)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name_plural': 'Currencies',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='Timezone',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
                ('display_name', models.CharField(max_length=100)),
                ('offset', models.CharField(max_length=10)),
                ('is_active', models.BooleanField(default=True)),
                ('country_code', models.CharField(blank=True, max_length=2)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['display_name'],
            },
        ),
        migrations.CreateModel(
            name='RegionalCompliance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('region_code', models.CharField(max_length=10)),
                ('region_name', models.CharField(max_length=100)),
                ('compliance_type', models.CharField(max_length=50)),
                ('requirements', models.JSONField(default=dict)),
                ('is_active', models.BooleanField(default=True)),
                ('effective_date', models.DateTimeField()),
                ('expiry_date', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='InternationalPaymentGateway',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('provider', models.CharField(max_length=50)),
                ('supported_countries', models.JSONField(default=list)),
                ('configuration', models.JSONField(default=dict)),
                ('is_active', models.BooleanField(default=True)),
                ('is_sandbox', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('supported_currencies', models.ManyToManyField(to='internationalization.Currency')),
            ],
        ),
        migrations.CreateModel(
            name='InternationalShipping',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('carrier', models.CharField(max_length=100)),
                ('service_name', models.CharField(max_length=100)),
                ('supported_countries', models.JSONField(default=list)),
                ('restrictions', models.JSONField(default=dict)),
                ('pricing_rules', models.JSONField(default=dict)),
                ('delivery_time', models.CharField(max_length=100)),
                ('tracking_supported', models.BooleanField(default=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='InternationalTaxRule',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('country_code', models.CharField(max_length=2)),
                ('region', models.CharField(blank=True, max_length=100)),
                ('tax_type', models.CharField(max_length=50)),
                ('rate', models.DecimalField(decimal_places=4, max_digits=5)),
                ('applies_to', models.JSONField(default=dict)),
                ('effective_date', models.DateTimeField()),
                ('expiry_date', models.DateTimeField(blank=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='UserLocalization',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_format', models.CharField(default='YYYY-MM-DD', max_length=20)),
                ('time_format', models.CharField(default='HH:mm:ss', max_length=20)),
                ('number_format', models.CharField(default='1,234.56', max_length=20)),
                ('auto_detect_location', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('currency', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='internationalization.currency')),
                ('language', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='internationalization.language')),
                ('timezone', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='internationalization.timezone')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Translation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(db_index=True, max_length=255)),
                ('value', models.TextField()),
                ('context', models.CharField(blank=True, max_length=100)),
                ('is_approved', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('language', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='internationalization.language')),
            ],
        ),
        migrations.CreateModel(
            name='LocalizedContent',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content_type', models.CharField(max_length=50)),
                ('content_id', models.CharField(max_length=100)),
                ('field_name', models.CharField(max_length=100)),
                ('value', models.TextField()),
                ('is_approved', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('language', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='internationalization.language')),
            ],
        ),
        migrations.CreateModel(
            name='CurrencyExchangeRate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('rate', models.DecimalField(decimal_places=6, max_digits=15)),
                ('date', models.DateField()),
                ('source', models.CharField(default='manual', max_length=50)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('from_currency', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='from_rates', to='internationalization.currency')),
                ('to_currency', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='to_rates', to='internationalization.currency')),
            ],
        ),
        migrations.AddConstraint(
            model_name='regionalcompliance',
            constraint=models.UniqueConstraint(fields=('region_code', 'compliance_type'), name='unique_region_compliance'),
        ),
        migrations.AddConstraint(
            model_name='internationalshipping',
            constraint=models.UniqueConstraint(fields=('carrier', 'service_name'), name='unique_shipping_service'),
        ),
        migrations.AddConstraint(
            model_name='translation',
            constraint=models.UniqueConstraint(fields=('key', 'language', 'context'), name='unique_translation'),
        ),
        migrations.AddConstraint(
            model_name='localizedcontent',
            constraint=models.UniqueConstraint(fields=('content_type', 'content_id', 'field_name', 'language'), name='unique_localized_content'),
        ),
        migrations.AddConstraint(
            model_name='currencyexchangerate',
            constraint=models.UniqueConstraint(fields=('from_currency', 'to_currency', 'date'), name='unique_exchange_rate'),
        ),
        migrations.AddIndex(
            model_name='translation',
            index=models.Index(fields=['key', 'language'], name='internationa_key_b8e123_idx'),
        ),
        migrations.AddIndex(
            model_name='translation',
            index=models.Index(fields=['language', 'is_approved'], name='internationa_languag_c4f567_idx'),
        ),
        migrations.AddIndex(
            model_name='localizedcontent',
            index=models.Index(fields=['content_type', 'content_id', 'language'], name='internationa_content_a1b234_idx'),
        ),
        migrations.AddIndex(
            model_name='localizedcontent',
            index=models.Index(fields=['language', 'is_approved'], name='internationa_languag_d5e678_idx'),
        ),
        migrations.AddIndex(
            model_name='internationalTaxRule',
            index=models.Index(fields=['country_code', 'is_active'], name='internationa_country_f9g012_idx'),
        ),
        migrations.AddIndex(
            model_name='internationalTaxRule',
            index=models.Index(fields=['effective_date', 'expiry_date'], name='internationa_effecti_h3i456_idx'),
        ),
        migrations.AddIndex(
            model_name='currencyexchangerate',
            index=models.Index(fields=['from_currency', 'to_currency', 'date'], name='internationa_from_cu_j7k890_idx'),
        ),
    ]