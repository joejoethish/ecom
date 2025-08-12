from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()
from django.utils import timezone
from decimal import Decimal
import json


class Language(models.Model):
    """Language configuration model"""
    code = models.CharField(max_length=10, unique=True)  # e.g., 'en', 'es', 'fr'
    name = models.CharField(max_length=100)  # e.g., 'English', 'Spanish'
    native_name = models.CharField(max_length=100)  # e.g., 'English', 'Español'
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    is_rtl = models.BooleanField(default=False)  # Right-to-left languages
    flag_icon = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.code})"


class Currency(models.Model):
    """Currency configuration model"""
    code = models.CharField(max_length=3, unique=True)  # ISO 4217 code
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=10)
    decimal_places = models.IntegerField(default=2)
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    exchange_rate = models.DecimalField(max_digits=15, decimal_places=6, default=1.0)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Currencies'

    def __str__(self):
        return f"{self.name} ({self.code})"


class Timezone(models.Model):
    """Timezone configuration model"""
    name = models.CharField(max_length=100, unique=True)  # e.g., 'America/New_York'
    display_name = models.CharField(max_length=100)  # e.g., 'Eastern Time'
    offset = models.CharField(max_length=10)  # e.g., '-05:00'
    is_active = models.BooleanField(default=True)
    country_code = models.CharField(max_length=2, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['display_name']

    def __str__(self):
        return f"{self.display_name} ({self.name})"


class Translation(models.Model):
    """Translation storage model"""
    key = models.CharField(max_length=255, db_index=True)
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    value = models.TextField()
    context = models.CharField(max_length=100, blank=True)  # Context for translators
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        unique_together = ['key', 'language', 'context']
        indexes = [
            models.Index(fields=['key', 'language']),
            models.Index(fields=['language', 'is_approved']),
        ]

    def __str__(self):
        return f"{self.key} ({self.language.code})"


class LocalizedContent(models.Model):
    """Localized content for dynamic content"""
    content_type = models.CharField(max_length=50)  # 'product', 'category', 'page', etc.
    content_id = models.CharField(max_length=100)
    field_name = models.CharField(max_length=100)  # 'name', 'description', etc.
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    value = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['content_type', 'content_id', 'field_name', 'language']
        indexes = [
            models.Index(fields=['content_type', 'content_id', 'language']),
            models.Index(fields=['language', 'is_approved']),
        ]

    def __str__(self):
        return f"{self.content_type}:{self.content_id}.{self.field_name} ({self.language.code})"


class RegionalCompliance(models.Model):
    """Regional compliance and regulatory requirements"""
    region_code = models.CharField(max_length=10)  # 'US', 'EU', 'GDPR', etc.
    region_name = models.CharField(max_length=100)
    compliance_type = models.CharField(max_length=50)  # 'privacy', 'tax', 'shipping', etc.
    requirements = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    effective_date = models.DateTimeField()
    expiry_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['region_code', 'compliance_type']

    def __str__(self):
        return f"{self.region_name} - {self.compliance_type}"


class CurrencyExchangeRate(models.Model):
    """Historical exchange rates"""
    from_currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='from_rates')
    to_currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='to_rates')
    rate = models.DecimalField(max_digits=15, decimal_places=6)
    date = models.DateField()
    source = models.CharField(max_length=50, default='manual')  # 'api', 'manual', etc.
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['from_currency', 'to_currency', 'date']
        indexes = [
            models.Index(fields=['from_currency', 'to_currency', 'date']),
        ]

    def __str__(self):
        return f"{self.from_currency.code} to {self.to_currency.code}: {self.rate}"


class UserLocalization(models.Model):
    """User-specific localization preferences"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    language = models.ForeignKey(Language, on_delete=models.SET_NULL, null=True, blank=True)
    currency = models.ForeignKey(Currency, on_delete=models.SET_NULL, null=True, blank=True)
    timezone = models.ForeignKey(Timezone, on_delete=models.SET_NULL, null=True, blank=True)
    date_format = models.CharField(max_length=20, default='YYYY-MM-DD')
    time_format = models.CharField(max_length=20, default='HH:mm:ss')
    number_format = models.CharField(max_length=20, default='1,234.56')
    auto_detect_location = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} localization"


class InternationalPaymentGateway(models.Model):
    """International payment gateway configurations"""
    name = models.CharField(max_length=100)
    provider = models.CharField(max_length=50)  # 'stripe', 'paypal', 'adyen', etc.
    supported_countries = models.JSONField(default=list)
    supported_currencies = models.ManyToManyField(Currency)
    configuration = models.JSONField(default=dict)
    is_active = models.BooleanField(default=True)
    is_sandbox = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.provider})"


class InternationalShipping(models.Model):
    """International shipping configurations"""
    carrier = models.CharField(max_length=100)
    service_name = models.CharField(max_length=100)
    supported_countries = models.JSONField(default=list)
    restrictions = models.JSONField(default=dict)
    pricing_rules = models.JSONField(default=dict)
    delivery_time = models.CharField(max_length=100)
    tracking_supported = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['carrier', 'service_name']

    def __str__(self):
        return f"{self.carrier} - {self.service_name}"


class InternationalTaxRule(models.Model):
    """International tax calculation rules"""
    country_code = models.CharField(max_length=2)
    region = models.CharField(max_length=100, blank=True)
    tax_type = models.CharField(max_length=50)  # 'VAT', 'GST', 'Sales Tax', etc.
    rate = models.DecimalField(max_digits=5, decimal_places=4)
    applies_to = models.JSONField(default=dict)  # Product categories, customer types, etc.
    effective_date = models.DateTimeField()
    expiry_date = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['country_code', 'is_active']),
            models.Index(fields=['effective_date', 'expiry_date']),
        ]

    def __str__(self):
        return f"{self.country_code} - {self.tax_type}: {self.rate}%"