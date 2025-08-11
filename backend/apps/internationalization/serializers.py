from rest_framework import serializers
from .models import (
    Language, Currency, Timezone, Translation, LocalizedContent,
    RegionalCompliance, CurrencyExchangeRate, UserLocalization,
    InternationalPaymentGateway, InternationalShipping, InternationalTaxRule
)


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = '__all__'


class CurrencySerializer(serializers.ModelSerializer):
    formatted_symbol = serializers.SerializerMethodField()
    
    class Meta:
        model = Currency
        fields = '__all__'
    
    def get_formatted_symbol(self, obj):
        return f"{obj.symbol} ({obj.code})"


class TimezoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Timezone
        fields = '__all__'


class TranslationSerializer(serializers.ModelSerializer):
    language_name = serializers.CharField(source='language.name', read_only=True)
    language_code = serializers.CharField(source='language.code', read_only=True)
    
    class Meta:
        model = Translation
        fields = '__all__'


class LocalizedContentSerializer(serializers.ModelSerializer):
    language_name = serializers.CharField(source='language.name', read_only=True)
    language_code = serializers.CharField(source='language.code', read_only=True)
    
    class Meta:
        model = LocalizedContent
        fields = '__all__'


class RegionalComplianceSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegionalCompliance
        fields = '__all__'


class CurrencyExchangeRateSerializer(serializers.ModelSerializer):
    from_currency_code = serializers.CharField(source='from_currency.code', read_only=True)
    to_currency_code = serializers.CharField(source='to_currency.code', read_only=True)
    from_currency_name = serializers.CharField(source='from_currency.name', read_only=True)
    to_currency_name = serializers.CharField(source='to_currency.name', read_only=True)
    
    class Meta:
        model = CurrencyExchangeRate
        fields = '__all__'


class UserLocalizationSerializer(serializers.ModelSerializer):
    language_name = serializers.CharField(source='language.name', read_only=True)
    language_code = serializers.CharField(source='language.code', read_only=True)
    currency_name = serializers.CharField(source='currency.name', read_only=True)
    currency_code = serializers.CharField(source='currency.code', read_only=True)
    currency_symbol = serializers.CharField(source='currency.symbol', read_only=True)
    timezone_name = serializers.CharField(source='timezone.name', read_only=True)
    timezone_display = serializers.CharField(source='timezone.display_name', read_only=True)
    
    class Meta:
        model = UserLocalization
        fields = '__all__'


class InternationalPaymentGatewaySerializer(serializers.ModelSerializer):
    supported_currencies_data = CurrencySerializer(source='supported_currencies', many=True, read_only=True)
    
    class Meta:
        model = InternationalPaymentGateway
        fields = '__all__'


class InternationalShippingSerializer(serializers.ModelSerializer):
    class Meta:
        model = InternationalShipping
        fields = '__all__'


class InternationalTaxRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = InternationalTaxRule
        fields = '__all__'


class CurrencyConversionSerializer(serializers.Serializer):
    """Serializer for currency conversion requests"""
    amount = serializers.DecimalField(max_digits=15, decimal_places=6)
    from_currency = serializers.CharField(max_length=3)
    to_currency = serializers.CharField(max_length=3)


class TranslationBulkSerializer(serializers.Serializer):
    """Serializer for bulk translation requests"""
    keys = serializers.ListField(child=serializers.CharField(max_length=255))
    language_code = serializers.CharField(max_length=10)
    context = serializers.CharField(max_length=100, required=False, default='')


class LocalizationPreferencesSerializer(serializers.Serializer):
    """Serializer for user localization preferences"""
    language = serializers.CharField(max_length=10, required=False)
    currency = serializers.CharField(max_length=3, required=False)
    timezone = serializers.CharField(max_length=100, required=False)
    date_format = serializers.CharField(max_length=20, required=False)
    time_format = serializers.CharField(max_length=20, required=False)
    number_format = serializers.CharField(max_length=20, required=False)
    auto_detect_location = serializers.BooleanField(required=False)


class TaxCalculationSerializer(serializers.Serializer):
    """Serializer for tax calculation requests"""
    amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    country_code = serializers.CharField(max_length=2)
    product_category = serializers.CharField(max_length=100, required=False)


class ComplianceCheckSerializer(serializers.Serializer):
    """Serializer for compliance check requests"""
    region_code = serializers.CharField(max_length=10)
    data = serializers.JSONField()


class LocalizedContentBulkSerializer(serializers.Serializer):
    """Serializer for bulk localized content requests"""
    content_type = serializers.CharField(max_length=50)
    content_ids = serializers.ListField(child=serializers.CharField(max_length=100))
    field_names = serializers.ListField(child=serializers.CharField(max_length=100))
    language_code = serializers.CharField(max_length=10)


class ExchangeRateUpdateSerializer(serializers.Serializer):
    """Serializer for exchange rate update requests"""
    force_update = serializers.BooleanField(default=False)


class InternationalAnalyticsSerializer(serializers.Serializer):
    """Serializer for international analytics data"""
    date_from = serializers.DateField()
    date_to = serializers.DateField()
    group_by = serializers.ChoiceField(choices=['country', 'language', 'currency', 'region'])
    metrics = serializers.ListField(
        child=serializers.ChoiceField(choices=['revenue', 'orders', 'customers', 'conversion'])
    )


class InternationalReportSerializer(serializers.Serializer):
    """Serializer for international reports"""
    report_type = serializers.ChoiceField(choices=[
        'localization_usage', 'currency_performance', 'regional_compliance',
        'translation_coverage', 'international_sales'
    ])
    date_from = serializers.DateField()
    date_to = serializers.DateField()
    filters = serializers.JSONField(required=False, default=dict)
    format = serializers.ChoiceField(choices=['json', 'csv', 'excel'], default='json')


class MultiLanguageContentSerializer(serializers.Serializer):
    """Serializer for multi-language content management"""
    content_type = serializers.CharField(max_length=50)
    content_id = serializers.CharField(max_length=100)
    translations = serializers.DictField(
        child=serializers.DictField(child=serializers.CharField())
    )  # {language_code: {field_name: value}}


class InternationalSettingsSerializer(serializers.Serializer):
    """Serializer for international system settings"""
    default_language = serializers.CharField(max_length=10)
    default_currency = serializers.CharField(max_length=3)
    default_timezone = serializers.CharField(max_length=100)
    auto_detect_user_location = serializers.BooleanField(default=True)
    enable_currency_conversion = serializers.BooleanField(default=True)
    enable_automatic_translation = serializers.BooleanField(default=False)
    supported_languages = serializers.ListField(child=serializers.CharField(max_length=10))
    supported_currencies = serializers.ListField(child=serializers.CharField(max_length=3))
    supported_timezones = serializers.ListField(child=serializers.CharField(max_length=100))
    exchange_rate_update_frequency = serializers.IntegerField(default=3600)  # seconds
    translation_cache_timeout = serializers.IntegerField(default=3600)  # seconds