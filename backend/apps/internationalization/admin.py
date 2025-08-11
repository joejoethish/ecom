from django.contrib import admin
from .models import (
    Language, Currency, Timezone, Translation, LocalizedContent,
    RegionalCompliance, CurrencyExchangeRate, UserLocalization,
    InternationalPaymentGateway, InternationalShipping, InternationalTaxRule
)


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'native_name', 'is_active', 'is_default', 'is_rtl']
    list_filter = ['is_active', 'is_default', 'is_rtl']
    search_fields = ['name', 'code', 'native_name']
    ordering = ['name']


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'symbol', 'is_active', 'is_default', 'exchange_rate', 'last_updated']
    list_filter = ['is_active', 'is_default']
    search_fields = ['name', 'code']
    ordering = ['name']
    readonly_fields = ['last_updated']


@admin.register(Timezone)
class TimezoneAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'name', 'offset', 'country_code', 'is_active']
    list_filter = ['is_active', 'country_code']
    search_fields = ['display_name', 'name', 'country_code']
    ordering = ['display_name']


@admin.register(Translation)
class TranslationAdmin(admin.ModelAdmin):
    list_display = ['key', 'language', 'value', 'context', 'is_approved', 'created_by', 'updated_at']
    list_filter = ['language', 'is_approved', 'context']
    search_fields = ['key', 'value', 'context']
    ordering = ['key', 'language']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('language', 'created_by')


@admin.register(LocalizedContent)
class LocalizedContentAdmin(admin.ModelAdmin):
    list_display = ['content_type', 'content_id', 'field_name', 'language', 'is_approved', 'updated_at']
    list_filter = ['content_type', 'language', 'is_approved']
    search_fields = ['content_type', 'content_id', 'field_name', 'value']
    ordering = ['content_type', 'content_id', 'field_name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(RegionalCompliance)
class RegionalComplianceAdmin(admin.ModelAdmin):
    list_display = ['region_name', 'region_code', 'compliance_type', 'is_active', 'effective_date', 'expiry_date']
    list_filter = ['compliance_type', 'is_active', 'region_code']
    search_fields = ['region_name', 'region_code', 'compliance_type']
    ordering = ['region_name', 'compliance_type']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(CurrencyExchangeRate)
class CurrencyExchangeRateAdmin(admin.ModelAdmin):
    list_display = ['from_currency', 'to_currency', 'rate', 'date', 'source']
    list_filter = ['source', 'date', 'from_currency', 'to_currency']
    search_fields = ['from_currency__code', 'to_currency__code']
    ordering = ['-date', 'from_currency', 'to_currency']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('from_currency', 'to_currency')


@admin.register(UserLocalization)
class UserLocalizationAdmin(admin.ModelAdmin):
    list_display = ['user', 'language', 'currency', 'timezone', 'auto_detect_location', 'updated_at']
    list_filter = ['language', 'currency', 'timezone', 'auto_detect_location']
    search_fields = ['user__username', 'user__email']
    ordering = ['user__username']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'language', 'currency', 'timezone')


@admin.register(InternationalPaymentGateway)
class InternationalPaymentGatewayAdmin(admin.ModelAdmin):
    list_display = ['name', 'provider', 'is_active', 'is_sandbox', 'updated_at']
    list_filter = ['provider', 'is_active', 'is_sandbox']
    search_fields = ['name', 'provider']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['supported_currencies']


@admin.register(InternationalShipping)
class InternationalShippingAdmin(admin.ModelAdmin):
    list_display = ['carrier', 'service_name', 'delivery_time', 'tracking_supported', 'is_active']
    list_filter = ['carrier', 'tracking_supported', 'is_active']
    search_fields = ['carrier', 'service_name']
    ordering = ['carrier', 'service_name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(InternationalTaxRule)
class InternationalTaxRuleAdmin(admin.ModelAdmin):
    list_display = ['country_code', 'region', 'tax_type', 'rate', 'effective_date', 'expiry_date', 'is_active']
    list_filter = ['country_code', 'tax_type', 'is_active']
    search_fields = ['country_code', 'region', 'tax_type']
    ordering = ['country_code', 'tax_type']
    readonly_fields = ['created_at', 'updated_at']