from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from decimal import Decimal, ROUND_HALF_UP
import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pytz
from .models import (
    Language, Currency, Timezone, Translation, LocalizedContent,
    CurrencyExchangeRate, UserLocalization, RegionalCompliance,
    InternationalTaxRule
)


class TranslationService:
    """Service for managing translations"""
    
    def __init__(self):
        self.cache_timeout = 3600  # 1 hour
    
    def get_translation(self, key: str, language_code: str, context: str = '', default: str = None) -> str:
        """Get translation for a key in specified language"""
        cache_key = f"translation:{language_code}:{key}:{context}"
        translation = cache.get(cache_key)
        
        if translation is None:
            try:
                language = Language.objects.get(code=language_code, is_active=True)
                translation_obj = Translation.objects.get(
                    key=key,
                    language=language,
                    context=context,
                    is_approved=True
                )
                translation = translation_obj.value
                cache.set(cache_key, translation, self.cache_timeout)
            except (Language.DoesNotExist, Translation.DoesNotExist):
                # Fallback to default language
                try:
                    default_language = Language.objects.get(is_default=True)
                    translation_obj = Translation.objects.get(
                        key=key,
                        language=default_language,
                        context=context,
                        is_approved=True
                    )
                    translation = translation_obj.value
                    cache.set(cache_key, translation, self.cache_timeout)
                except (Language.DoesNotExist, Translation.DoesNotExist):
                    translation = default or key
        
        return translation
    
    def get_translations_bulk(self, keys: List[str], language_code: str, context: str = '') -> Dict[str, str]:
        """Get multiple translations at once"""
        translations = {}
        cache_keys = [f"translation:{language_code}:{key}:{context}" for key in keys]
        cached_translations = cache.get_many(cache_keys)
        
        # Get cached translations
        for i, key in enumerate(keys):
            cache_key = cache_keys[i]
            if cache_key in cached_translations:
                translations[key] = cached_translations[cache_key]
        
        # Get missing translations from database
        missing_keys = [key for key in keys if key not in translations]
        if missing_keys:
            try:
                language = Language.objects.get(code=language_code, is_active=True)
                translation_objs = Translation.objects.filter(
                    key__in=missing_keys,
                    language=language,
                    context=context,
                    is_approved=True
                )
                
                db_translations = {t.key: t.value for t in translation_objs}
                
                # Cache the found translations
                cache_data = {}
                for key in missing_keys:
                    if key in db_translations:
                        translations[key] = db_translations[key]
                        cache_key = f"translation:{language_code}:{key}:{context}"
                        cache_data[cache_key] = db_translations[key]
                    else:
                        translations[key] = key  # Fallback to key
                
                if cache_data:
                    cache.set_many(cache_data, self.cache_timeout)
                    
            except Language.DoesNotExist:
                # Fallback to keys
                for key in missing_keys:
                    translations[key] = key
        
        return translations
    
    def set_translation(self, key: str, language_code: str, value: str, context: str = '', user=None) -> bool:
        """Set or update a translation"""
        try:
            language = Language.objects.get(code=language_code, is_active=True)
            translation, created = Translation.objects.update_or_create(
                key=key,
                language=language,
                context=context,
                defaults={
                    'value': value,
                    'created_by': user,
                    'is_approved': True  # Auto-approve for now
                }
            )
            
            # Clear cache
            cache_key = f"translation:{language_code}:{key}:{context}"
            cache.delete(cache_key)
            
            return True
        except Language.DoesNotExist:
            return False
    
    def get_localized_content(self, content_type: str, content_id: str, field_name: str, language_code: str) -> Optional[str]:
        """Get localized content for dynamic content"""
        cache_key = f"localized_content:{content_type}:{content_id}:{field_name}:{language_code}"
        content = cache.get(cache_key)
        
        if content is None:
            try:
                language = Language.objects.get(code=language_code, is_active=True)
                localized_obj = LocalizedContent.objects.get(
                    content_type=content_type,
                    content_id=content_id,
                    field_name=field_name,
                    language=language,
                    is_approved=True
                )
                content = localized_obj.value
                cache.set(cache_key, content, self.cache_timeout)
            except (Language.DoesNotExist, LocalizedContent.DoesNotExist):
                content = None
        
        return content


class CurrencyService:
    """Service for currency conversion and management"""
    
    def __init__(self):
        self.cache_timeout = 1800  # 30 minutes
        self.api_key = getattr(settings, 'EXCHANGE_RATE_API_KEY', None)
    
    def get_exchange_rate(self, from_currency: str, to_currency: str) -> Decimal:
        """Get current exchange rate between two currencies"""
        if from_currency == to_currency:
            return Decimal('1.0')
        
        cache_key = f"exchange_rate:{from_currency}:{to_currency}"
        rate = cache.get(cache_key)
        
        if rate is None:
            try:
                # Try to get from database first
                from_curr = Currency.objects.get(code=from_currency, is_active=True)
                to_curr = Currency.objects.get(code=to_currency, is_active=True)
                
                # Check if we have a direct rate
                try:
                    rate_obj = CurrencyExchangeRate.objects.filter(
                        from_currency=from_curr,
                        to_currency=to_curr,
                        date=timezone.now().date()
                    ).first()
                    
                    if rate_obj:
                        rate = rate_obj.rate
                    else:
                        # Calculate via base currency (usually USD)
                        base_currency = Currency.objects.get(is_default=True)
                        if from_curr == base_currency:
                            rate = to_curr.exchange_rate
                        elif to_curr == base_currency:
                            rate = Decimal('1.0') / from_curr.exchange_rate
                        else:
                            rate = to_curr.exchange_rate / from_curr.exchange_rate
                    
                    cache.set(cache_key, rate, self.cache_timeout)
                    
                except CurrencyExchangeRate.DoesNotExist:
                    rate = Decimal('1.0')
                    
            except Currency.DoesNotExist:
                rate = Decimal('1.0')
        
        return rate
    
    def convert_amount(self, amount: Decimal, from_currency: str, to_currency: str) -> Decimal:
        """Convert amount from one currency to another"""
        rate = self.get_exchange_rate(from_currency, to_currency)
        converted = amount * rate
        
        # Round to appropriate decimal places
        try:
            to_curr = Currency.objects.get(code=to_currency)
            decimal_places = to_curr.decimal_places
            return converted.quantize(Decimal('0.1') ** decimal_places, rounding=ROUND_HALF_UP)
        except Currency.DoesNotExist:
            return converted.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def format_currency(self, amount: Decimal, currency_code: str, language_code: str = 'en') -> str:
        """Format currency amount according to locale"""
        try:
            currency = Currency.objects.get(code=currency_code)
            
            # Basic formatting - can be enhanced with locale-specific formatting
            if language_code in ['en', 'en-US']:
                return f"{currency.symbol}{amount:,.{currency.decimal_places}f}"
            elif language_code in ['de', 'de-DE']:
                return f"{amount:,.{currency.decimal_places}f} {currency.symbol}".replace(',', 'X').replace('.', ',').replace('X', '.')
            elif language_code in ['fr', 'fr-FR']:
                return f"{amount:,.{currency.decimal_places}f} {currency.symbol}".replace(',', ' ')
            else:
                return f"{currency.symbol}{amount:,.{currency.decimal_places}f}"
                
        except Currency.DoesNotExist:
            return str(amount)
    
    def update_exchange_rates(self) -> bool:
        """Update exchange rates from external API"""
        if not self.api_key:
            return False
        
        try:
            base_currency = Currency.objects.get(is_default=True)
            active_currencies = Currency.objects.filter(is_active=True).exclude(id=base_currency.id)
            
            # Example API call (replace with actual API)
            url = f"https://api.exchangerate-api.com/v4/latest/{base_currency.code}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                rates = data.get('rates', {})
                
                for currency in active_currencies:
                    if currency.code in rates:
                        rate = Decimal(str(rates[currency.code]))
                        
                        # Update currency exchange rate
                        currency.exchange_rate = rate
                        currency.save()
                        
                        # Store historical rate
                        CurrencyExchangeRate.objects.update_or_create(
                            from_currency=base_currency,
                            to_currency=currency,
                            date=timezone.now().date(),
                            defaults={
                                'rate': rate,
                                'source': 'api'
                            }
                        )
                
                return True
        except Exception as e:
            print(f"Error updating exchange rates: {e}")
            return False
        
        return False


class TimezoneService:
    """Service for timezone management"""
    
    def convert_timezone(self, dt: datetime, from_tz: str, to_tz: str) -> datetime:
        """Convert datetime from one timezone to another"""
        try:
            from_timezone = pytz.timezone(from_tz)
            to_timezone = pytz.timezone(to_tz)
            
            # Localize the datetime if it's naive
            if dt.tzinfo is None:
                dt = from_timezone.localize(dt)
            
            # Convert to target timezone
            return dt.astimezone(to_timezone)
        except Exception:
            return dt
    
    def get_user_timezone(self, user) -> str:
        """Get user's preferred timezone"""
        try:
            user_localization = UserLocalization.objects.get(user=user)
            if user_localization.timezone:
                return user_localization.timezone.name
        except UserLocalization.DoesNotExist:
            pass
        
        return settings.TIME_ZONE
    
    def format_datetime(self, dt: datetime, timezone_name: str, language_code: str = 'en') -> str:
        """Format datetime according to user's timezone and locale"""
        try:
            user_tz = pytz.timezone(timezone_name)
            localized_dt = dt.astimezone(user_tz)
            
            # Basic formatting - can be enhanced with locale-specific formatting
            if language_code in ['en', 'en-US']:
                return localized_dt.strftime('%Y-%m-%d %H:%M:%S %Z')
            elif language_code in ['de', 'de-DE']:
                return localized_dt.strftime('%d.%m.%Y %H:%M:%S %Z')
            elif language_code in ['fr', 'fr-FR']:
                return localized_dt.strftime('%d/%m/%Y %H:%M:%S %Z')
            else:
                return localized_dt.strftime('%Y-%m-%d %H:%M:%S %Z')
                
        except Exception:
            return dt.strftime('%Y-%m-%d %H:%M:%S')


class ComplianceService:
    """Service for regional compliance management"""
    
    def get_compliance_requirements(self, region_code: str, compliance_type: str) -> Dict[str, Any]:
        """Get compliance requirements for a region"""
        try:
            compliance = RegionalCompliance.objects.get(
                region_code=region_code,
                compliance_type=compliance_type,
                is_active=True,
                effective_date__lte=timezone.now()
            )
            return compliance.requirements
        except RegionalCompliance.DoesNotExist:
            return {}
    
    def check_compliance(self, region_code: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Check if data meets compliance requirements"""
        compliance_results = {
            'compliant': True,
            'violations': [],
            'warnings': []
        }
        
        # Get all compliance requirements for the region
        compliances = RegionalCompliance.objects.filter(
            region_code=region_code,
            is_active=True,
            effective_date__lte=timezone.now()
        )
        
        for compliance in compliances:
            requirements = compliance.requirements
            
            # Example compliance checks (customize based on requirements)
            if compliance.compliance_type == 'privacy':
                if 'consent' in requirements and not data.get('user_consent'):
                    compliance_results['compliant'] = False
                    compliance_results['violations'].append('User consent required')
            
            elif compliance.compliance_type == 'tax':
                if 'vat_required' in requirements and not data.get('vat_number'):
                    compliance_results['warnings'].append('VAT number recommended')
        
        return compliance_results


class TaxCalculationService:
    """Service for international tax calculations"""
    
    def calculate_tax(self, amount: Decimal, country_code: str, product_category: str = None) -> Dict[str, Any]:
        """Calculate tax for an amount in a specific country"""
        tax_info = {
            'tax_amount': Decimal('0.00'),
            'tax_rate': Decimal('0.00'),
            'tax_type': '',
            'breakdown': []
        }
        
        try:
            # Get applicable tax rules
            tax_rules = InternationalTaxRule.objects.filter(
                country_code=country_code,
                is_active=True,
                effective_date__lte=timezone.now()
            ).filter(
                models.Q(expiry_date__isnull=True) | models.Q(expiry_date__gt=timezone.now())
            )
            
            total_tax = Decimal('0.00')
            
            for rule in tax_rules:
                # Check if rule applies to this product category
                applies_to = rule.applies_to
                if product_category and 'categories' in applies_to:
                    if product_category not in applies_to['categories']:
                        continue
                
                # Calculate tax for this rule
                rule_tax = amount * (rule.rate / 100)
                total_tax += rule_tax
                
                tax_info['breakdown'].append({
                    'tax_type': rule.tax_type,
                    'rate': rule.rate,
                    'amount': rule_tax
                })
            
            tax_info['tax_amount'] = total_tax
            tax_info['tax_rate'] = (total_tax / amount * 100) if amount > 0 else Decimal('0.00')
            
            if tax_info['breakdown']:
                tax_info['tax_type'] = ', '.join([b['tax_type'] for b in tax_info['breakdown']])
        
        except Exception as e:
            print(f"Error calculating tax: {e}")
        
        return tax_info


class LocalizationService:
    """Main service that combines all internationalization services"""
    
    def __init__(self):
        self.translation_service = TranslationService()
        self.currency_service = CurrencyService()
        self.timezone_service = TimezoneService()
        self.compliance_service = ComplianceService()
        self.tax_service = TaxCalculationService()
    
    def get_user_localization(self, user) -> Dict[str, Any]:
        """Get complete localization settings for a user"""
        try:
            user_loc = UserLocalization.objects.get(user=user)
            return {
                'language': user_loc.language.code if user_loc.language else 'en',
                'currency': user_loc.currency.code if user_loc.currency else 'USD',
                'timezone': user_loc.timezone.name if user_loc.timezone else settings.TIME_ZONE,
                'date_format': user_loc.date_format,
                'time_format': user_loc.time_format,
                'number_format': user_loc.number_format
            }
        except UserLocalization.DoesNotExist:
            # Return defaults
            return {
                'language': 'en',
                'currency': 'USD',
                'timezone': settings.TIME_ZONE,
                'date_format': 'YYYY-MM-DD',
                'time_format': 'HH:mm:ss',
                'number_format': '1,234.56'
            }
    
    def set_user_localization(self, user, **kwargs) -> bool:
        """Set user localization preferences"""
        try:
            user_loc, created = UserLocalization.objects.get_or_create(user=user)
            
            if 'language' in kwargs:
                try:
                    language = Language.objects.get(code=kwargs['language'], is_active=True)
                    user_loc.language = language
                except Language.DoesNotExist:
                    pass
            
            if 'currency' in kwargs:
                try:
                    currency = Currency.objects.get(code=kwargs['currency'], is_active=True)
                    user_loc.currency = currency
                except Currency.DoesNotExist:
                    pass
            
            if 'timezone' in kwargs:
                try:
                    timezone_obj = Timezone.objects.get(name=kwargs['timezone'], is_active=True)
                    user_loc.timezone = timezone_obj
                except Timezone.DoesNotExist:
                    pass
            
            for field in ['date_format', 'time_format', 'number_format', 'auto_detect_location']:
                if field in kwargs:
                    setattr(user_loc, field, kwargs[field])
            
            user_loc.save()
            return True
        except Exception as e:
            print(f"Error setting user localization: {e}")
            return False