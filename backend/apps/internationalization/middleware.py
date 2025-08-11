from django.utils import translation, timezone
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
import pytz
from .models import UserLocalization, Language, Currency, Timezone
from .services import LocalizationService


class InternationalizationMiddleware(MiddlewareMixin):
    """Middleware to handle user-specific internationalization settings"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.localization_service = LocalizationService()
        super().__init__(get_response)
    
    def process_request(self, request):
        """Process incoming request to set user's localization preferences"""
        
        # Set default values
        language_code = settings.LANGUAGE_CODE
        currency_code = getattr(settings, 'DEFAULT_CURRENCY', 'USD')
        timezone_name = settings.TIME_ZONE
        
        # Try to get user preferences if authenticated
        if hasattr(request, 'user') and request.user.is_authenticated:
            try:
                user_localization = UserLocalization.objects.select_related(
                    'language', 'currency', 'timezone'
                ).get(user=request.user)
                
                if user_localization.language:
                    language_code = user_localization.language.code
                if user_localization.currency:
                    currency_code = user_localization.currency.code
                if user_localization.timezone:
                    timezone_name = user_localization.timezone.name
                    
            except UserLocalization.DoesNotExist:
                # Auto-detect from headers if enabled
                if getattr(settings, 'AUTO_DETECT_USER_LOCATION', True):
                    detected_settings = self._detect_user_settings(request)
                    language_code = detected_settings.get('language', language_code)
                    timezone_name = detected_settings.get('timezone', timezone_name)
        
        # Try to get from session or headers for anonymous users
        else:
            # Check session first
            language_code = request.session.get('language', language_code)
            currency_code = request.session.get('currency', currency_code)
            timezone_name = request.session.get('timezone', timezone_name)
            
            # Auto-detect if not in session
            if language_code == settings.LANGUAGE_CODE:
                detected_settings = self._detect_user_settings(request)
                language_code = detected_settings.get('language', language_code)
                timezone_name = detected_settings.get('timezone', timezone_name)
        
        # Set language
        translation.activate(language_code)
        request.LANGUAGE_CODE = language_code
        
        # Set timezone
        try:
            user_timezone = pytz.timezone(timezone_name)
            timezone.activate(user_timezone)
            request.timezone = user_timezone
        except pytz.exceptions.UnknownTimeZoneError:
            request.timezone = pytz.timezone(settings.TIME_ZONE)
        
        # Set currency
        request.CURRENCY_CODE = currency_code
        
        # Store in request for easy access
        request.localization = {
            'language': language_code,
            'currency': currency_code,
            'timezone': timezone_name
        }
    
    def process_response(self, request, response):
        """Process response to handle language and timezone"""
        
        # Deactivate timezone to prevent memory leaks
        timezone.deactivate()
        
        # Set language cookie if changed
        if hasattr(request, 'LANGUAGE_CODE'):
            current_language = translation.get_language()
            if current_language != settings.LANGUAGE_CODE:
                response.set_cookie(
                    'django_language',
                    current_language,
                    max_age=settings.LANGUAGE_COOKIE_AGE,
                    path=settings.LANGUAGE_COOKIE_PATH,
                    domain=settings.LANGUAGE_COOKIE_DOMAIN,
                    secure=settings.LANGUAGE_COOKIE_SECURE,
                    httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
                    samesite=settings.LANGUAGE_COOKIE_SAMESITE,
                )
        
        return response
    
    def _detect_user_settings(self, request):
        """Auto-detect user settings from request headers"""
        detected = {}
        
        # Detect language from Accept-Language header
        accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        if accept_language:
            # Parse Accept-Language header
            languages = []
            for lang_range in accept_language.split(','):
                lang_range = lang_range.strip()
                if ';' in lang_range:
                    lang, quality = lang_range.split(';', 1)
                    try:
                        quality = float(quality.split('=')[1])
                    except (ValueError, IndexError):
                        quality = 1.0
                else:
                    lang, quality = lang_range, 1.0
                
                lang = lang.strip().lower()
                languages.append((quality, lang))
            
            # Sort by quality and find supported language
            languages.sort(reverse=True)
            for quality, lang in languages:
                # Try exact match first
                if Language.objects.filter(code=lang, is_active=True).exists():
                    detected['language'] = lang
                    break
                
                # Try language without country code
                if '-' in lang:
                    base_lang = lang.split('-')[0]
                    if Language.objects.filter(code=base_lang, is_active=True).exists():
                        detected['language'] = base_lang
                        break
        
        # Detect timezone from IP or other methods
        # This is a simplified version - in production, you might use GeoIP
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        if 'Mobile' in user_agent:
            # Mobile users might have different timezone preferences
            pass
        
        # You could integrate with GeoIP services here
        # For now, we'll use a simple mapping based on common patterns
        
        return detected


class LocalizationContextMiddleware(MiddlewareMixin):
    """Middleware to add localization context to all requests"""
    
    def process_request(self, request):
        """Add localization services to request"""
        request.localization_service = LocalizationService()
        
        # Add helper methods to request
        request.translate = lambda key, context='', default=None: (
            request.localization_service.translation_service.get_translation(
                key, request.LANGUAGE_CODE, context, default
            )
        )
        
        request.format_currency = lambda amount, currency_code=None: (
            request.localization_service.currency_service.format_currency(
                amount, 
                currency_code or request.CURRENCY_CODE,
                request.LANGUAGE_CODE
            )
        )
        
        request.convert_currency = lambda amount, from_currency, to_currency=None: (
            request.localization_service.currency_service.convert_amount(
                amount, 
                from_currency, 
                to_currency or request.CURRENCY_CODE
            )
        )
        
        request.format_datetime = lambda dt, timezone_name=None: (
            request.localization_service.timezone_service.format_datetime(
                dt,
                timezone_name or request.localization['timezone'],
                request.LANGUAGE_CODE
            )
        )


class APILocalizationMiddleware(MiddlewareMixin):
    """Middleware specifically for API requests to handle localization headers"""
    
    def process_request(self, request):
        """Process API localization headers"""
        
        # Skip if not an API request
        if not request.path.startswith('/api/'):
            return
        
        # Get localization from headers
        language = request.META.get('HTTP_ACCEPT_LANGUAGE_CODE')
        currency = request.META.get('HTTP_ACCEPT_CURRENCY')
        timezone_header = request.META.get('HTTP_ACCEPT_TIMEZONE')
        
        # Override request localization if headers are present
        if language:
            try:
                if Language.objects.filter(code=language, is_active=True).exists():
                    translation.activate(language)
                    request.LANGUAGE_CODE = language
                    request.localization['language'] = language
            except:
                pass
        
        if currency:
            try:
                if Currency.objects.filter(code=currency, is_active=True).exists():
                    request.CURRENCY_CODE = currency
                    request.localization['currency'] = currency
            except:
                pass
        
        if timezone_header:
            try:
                user_timezone = pytz.timezone(timezone_header)
                timezone.activate(user_timezone)
                request.timezone = user_timezone
                request.localization['timezone'] = timezone_header
            except pytz.exceptions.UnknownTimeZoneError:
                pass
    
    def process_response(self, request, response):
        """Add localization headers to API responses"""
        
        # Skip if not an API request
        if not request.path.startswith('/api/'):
            return response
        
        # Add current localization to response headers
        if hasattr(request, 'localization'):
            response['X-Current-Language'] = request.localization.get('language', 'en')
            response['X-Current-Currency'] = request.localization.get('currency', 'USD')
            response['X-Current-Timezone'] = request.localization.get('timezone', 'UTC')
        
        return response