from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q, Count, Sum
from decimal import Decimal
import json
from datetime import datetime, timedelta

from .models import (
    Language, Currency, Timezone, Translation, LocalizedContent,
    RegionalCompliance, CurrencyExchangeRate, UserLocalization,
    InternationalPaymentGateway, InternationalShipping, InternationalTaxRule
)
from .serializers import (
    LanguageSerializer, CurrencySerializer, TimezoneSerializer,
    TranslationSerializer, LocalizedContentSerializer, RegionalComplianceSerializer,
    CurrencyExchangeRateSerializer, UserLocalizationSerializer,
    InternationalPaymentGatewaySerializer, InternationalShippingSerializer,
    InternationalTaxRuleSerializer, CurrencyConversionSerializer,
    TranslationBulkSerializer, LocalizationPreferencesSerializer,
    TaxCalculationSerializer, ComplianceCheckSerializer,
    LocalizedContentBulkSerializer, ExchangeRateUpdateSerializer,
    InternationalAnalyticsSerializer, InternationalReportSerializer,
    MultiLanguageContentSerializer, InternationalSettingsSerializer
)
from .services import LocalizationService


class LanguageViewSet(viewsets.ModelViewSet):
    """ViewSet for managing languages"""
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.query_params.get('active_only') == 'true':
            queryset = queryset.filter(is_active=True)
        return queryset.order_by('name')
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get only active languages"""
        languages = Language.objects.filter(is_active=True).order_by('name')
        serializer = self.get_serializer(languages, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def default(self, request):
        """Get default language"""
        try:
            language = Language.objects.get(is_default=True)
            serializer = self.get_serializer(language)
            return Response(serializer.data)
        except Language.DoesNotExist:
            return Response({'error': 'No default language set'}, status=status.HTTP_404_NOT_FOUND)


class CurrencyViewSet(viewsets.ModelViewSet):
    """ViewSet for managing currencies"""
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.query_params.get('active_only') == 'true':
            queryset = queryset.filter(is_active=True)
        return queryset.order_by('name')
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get only active currencies"""
        currencies = Currency.objects.filter(is_active=True).order_by('name')
        serializer = self.get_serializer(currencies, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def default(self, request):
        """Get default currency"""
        try:
            currency = Currency.objects.get(is_default=True)
            serializer = self.get_serializer(currency)
            return Response(serializer.data)
        except Currency.DoesNotExist:
            return Response({'error': 'No default currency set'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=False, methods=['post'])
    def convert(self, request):
        """Convert amount between currencies"""
        serializer = CurrencyConversionSerializer(data=request.data)
        if serializer.is_valid():
            localization_service = LocalizationService()
            
            amount = serializer.validated_data['amount']
            from_currency = serializer.validated_data['from_currency']
            to_currency = serializer.validated_data['to_currency']
            
            converted_amount = localization_service.currency_service.convert_amount(
                amount, from_currency, to_currency
            )
            
            exchange_rate = localization_service.currency_service.get_exchange_rate(
                from_currency, to_currency
            )
            
            return Response({
                'original_amount': amount,
                'converted_amount': converted_amount,
                'from_currency': from_currency,
                'to_currency': to_currency,
                'exchange_rate': exchange_rate,
                'conversion_date': timezone.now().isoformat()
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TimezoneViewSet(viewsets.ModelViewSet):
    """ViewSet for managing timezones"""
    queryset = Timezone.objects.all()
    serializer_class = TimezoneSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.query_params.get('active_only') == 'true':
            queryset = queryset.filter(is_active=True)
        if self.request.query_params.get('country'):
            queryset = queryset.filter(country_code=self.request.query_params.get('country'))
        return queryset.order_by('display_name')
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get only active timezones"""
        timezones = Timezone.objects.filter(is_active=True).order_by('display_name')
        serializer = self.get_serializer(timezones, many=True)
        return Response(serializer.data)


class TranslationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing translations"""
    queryset = Translation.objects.all()
    serializer_class = TranslationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.query_params.get('language'):
            queryset = queryset.filter(language__code=self.request.query_params.get('language'))
        if self.request.query_params.get('key'):
            queryset = queryset.filter(key__icontains=self.request.query_params.get('key'))
        if self.request.query_params.get('approved_only') == 'true':
            queryset = queryset.filter(is_approved=True)
        return queryset.order_by('key', 'language__name')
    
    @action(detail=False, methods=['post'])
    def bulk_get(self, request):
        """Get multiple translations at once"""
        serializer = TranslationBulkSerializer(data=request.data)
        if serializer.is_valid():
            localization_service = LocalizationService()
            
            keys = serializer.validated_data['keys']
            language_code = serializer.validated_data['language_code']
            context = serializer.validated_data.get('context', '')
            
            translations = localization_service.translation_service.get_translations_bulk(
                keys, language_code, context
            )
            
            return Response({'translations': translations})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def bulk_set(self, request):
        """Set multiple translations at once"""
        translations_data = request.data.get('translations', {})
        language_code = request.data.get('language_code')
        context = request.data.get('context', '')
        
        if not translations_data or not language_code:
            return Response(
                {'error': 'translations and language_code are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        localization_service = LocalizationService()
        results = []
        
        for key, value in translations_data.items():
            success = localization_service.translation_service.set_translation(
                key, language_code, value, context, request.user
            )
            results.append({'key': key, 'success': success})
        
        return Response({'results': results})


class LocalizedContentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing localized content"""
    queryset = LocalizedContent.objects.all()
    serializer_class = LocalizedContentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.query_params.get('content_type'):
            queryset = queryset.filter(content_type=self.request.query_params.get('content_type'))
        if self.request.query_params.get('content_id'):
            queryset = queryset.filter(content_id=self.request.query_params.get('content_id'))
        if self.request.query_params.get('language'):
            queryset = queryset.filter(language__code=self.request.query_params.get('language'))
        return queryset.order_by('content_type', 'content_id', 'field_name')
    
    @action(detail=False, methods=['post'])
    def bulk_get(self, request):
        """Get multiple localized content at once"""
        serializer = LocalizedContentBulkSerializer(data=request.data)
        if serializer.is_valid():
            localization_service = LocalizationService()
            
            content_type = serializer.validated_data['content_type']
            content_ids = serializer.validated_data['content_ids']
            field_names = serializer.validated_data['field_names']
            language_code = serializer.validated_data['language_code']
            
            results = {}
            for content_id in content_ids:
                results[content_id] = {}
                for field_name in field_names:
                    content = localization_service.translation_service.get_localized_content(
                        content_type, content_id, field_name, language_code
                    )
                    results[content_id][field_name] = content
            
            return Response({'localized_content': results})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserLocalizationViewSet(viewsets.ModelViewSet):
    """ViewSet for managing user localization preferences"""
    queryset = UserLocalization.objects.all()
    serializer_class = UserLocalizationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_superuser:
            return super().get_queryset()
        return super().get_queryset().filter(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def my_preferences(self, request):
        """Get current user's localization preferences"""
        localization_service = LocalizationService()
        preferences = localization_service.get_user_localization(request.user)
        return Response(preferences)
    
    @action(detail=False, methods=['post'])
    def set_preferences(self, request):
        """Set current user's localization preferences"""
        serializer = LocalizationPreferencesSerializer(data=request.data)
        if serializer.is_valid():
            localization_service = LocalizationService()
            success = localization_service.set_user_localization(
                request.user, **serializer.validated_data
            )
            
            if success:
                preferences = localization_service.get_user_localization(request.user)
                return Response({'success': True, 'preferences': preferences})
            else:
                return Response(
                    {'error': 'Failed to update preferences'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InternationalPaymentGatewayViewSet(viewsets.ModelViewSet):
    """ViewSet for managing international payment gateways"""
    queryset = InternationalPaymentGateway.objects.all()
    serializer_class = InternationalPaymentGatewaySerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def by_country(self, request):
        """Get payment gateways available for a specific country"""
        country_code = request.query_params.get('country')
        if not country_code:
            return Response(
                {'error': 'country parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        gateways = self.queryset.filter(
            is_active=True,
            supported_countries__contains=[country_code]
        )
        serializer = self.get_serializer(gateways, many=True)
        return Response(serializer.data)


class InternationalShippingViewSet(viewsets.ModelViewSet):
    """ViewSet for managing international shipping"""
    queryset = InternationalShipping.objects.all()
    serializer_class = InternationalShippingSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def by_country(self, request):
        """Get shipping options available for a specific country"""
        country_code = request.query_params.get('country')
        if not country_code:
            return Response(
                {'error': 'country parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        shipping_options = self.queryset.filter(
            is_active=True,
            supported_countries__contains=[country_code]
        )
        serializer = self.get_serializer(shipping_options, many=True)
        return Response(serializer.data)


class InternationalTaxRuleViewSet(viewsets.ModelViewSet):
    """ViewSet for managing international tax rules"""
    queryset = InternationalTaxRule.objects.all()
    serializer_class = InternationalTaxRuleSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def calculate(self, request):
        """Calculate tax for a specific amount and country"""
        serializer = TaxCalculationSerializer(data=request.data)
        if serializer.is_valid():
            localization_service = LocalizationService()
            
            amount = serializer.validated_data['amount']
            country_code = serializer.validated_data['country_code']
            product_category = serializer.validated_data.get('product_category')
            
            tax_info = localization_service.tax_service.calculate_tax(
                amount, country_code, product_category
            )
            
            return Response(tax_info)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RegionalComplianceViewSet(viewsets.ModelViewSet):
    """ViewSet for managing regional compliance"""
    queryset = RegionalCompliance.objects.all()
    serializer_class = RegionalComplianceSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def check(self, request):
        """Check compliance for specific data and region"""
        serializer = ComplianceCheckSerializer(data=request.data)
        if serializer.is_valid():
            localization_service = LocalizationService()
            
            region_code = serializer.validated_data['region_code']
            data = serializer.validated_data['data']
            
            compliance_result = localization_service.compliance_service.check_compliance(
                region_code, data
            )
            
            return Response(compliance_result)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CurrencyExchangeRateViewSet(viewsets.ModelViewSet):
    """ViewSet for managing currency exchange rates"""
    queryset = CurrencyExchangeRate.objects.all()
    serializer_class = CurrencyExchangeRateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.query_params.get('from_currency'):
            queryset = queryset.filter(from_currency__code=self.request.query_params.get('from_currency'))
        if self.request.query_params.get('to_currency'):
            queryset = queryset.filter(to_currency__code=self.request.query_params.get('to_currency'))
        if self.request.query_params.get('date'):
            queryset = queryset.filter(date=self.request.query_params.get('date'))
        return queryset.order_by('-date', 'from_currency__code', 'to_currency__code')
    
    @action(detail=False, methods=['post'])
    def update_rates(self, request):
        """Update exchange rates from external API"""
        serializer = ExchangeRateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            localization_service = LocalizationService()
            
            success = localization_service.currency_service.update_exchange_rates()
            
            if success:
                return Response({'success': True, 'message': 'Exchange rates updated successfully'})
            else:
                return Response(
                    {'success': False, 'message': 'Failed to update exchange rates'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InternationalizationAnalyticsViewSet(viewsets.ViewSet):
    """ViewSet for internationalization analytics"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def analytics(self, request):
        """Get international analytics data"""
        serializer = InternationalAnalyticsSerializer(data=request.data)
        if serializer.is_valid():
            date_from = serializer.validated_data['date_from']
            date_to = serializer.validated_data['date_to']
            group_by = serializer.validated_data['group_by']
            metrics = serializer.validated_data['metrics']
            
            # This would integrate with your existing analytics system
            # For now, return sample data structure
            analytics_data = {
                'date_range': {
                    'from': date_from.isoformat(),
                    'to': date_to.isoformat()
                },
                'group_by': group_by,
                'metrics': metrics,
                'data': [
                    # Sample data structure
                    {
                        'group': 'US',
                        'revenue': 10000.00,
                        'orders': 150,
                        'customers': 120,
                        'conversion': 2.5
                    }
                ]
            }
            
            return Response(analytics_data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def reports(self, request):
        """Generate international reports"""
        serializer = InternationalReportSerializer(data=request.data)
        if serializer.is_valid():
            report_type = serializer.validated_data['report_type']
            date_from = serializer.validated_data['date_from']
            date_to = serializer.validated_data['date_to']
            filters = serializer.validated_data.get('filters', {})
            format_type = serializer.validated_data['format']
            
            # Generate report based on type
            report_data = self._generate_report(report_type, date_from, date_to, filters)
            
            if format_type == 'json':
                return Response(report_data)
            elif format_type == 'csv':
                # Convert to CSV and return as file
                pass
            elif format_type == 'excel':
                # Convert to Excel and return as file
                pass
            
            return Response(report_data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def _generate_report(self, report_type, date_from, date_to, filters):
        """Generate specific report based on type"""
        if report_type == 'localization_usage':
            return {
                'report_type': 'localization_usage',
                'summary': {
                    'total_users': 1000,
                    'localized_users': 750,
                    'localization_rate': 75.0
                },
                'by_language': [
                    {'language': 'English', 'users': 600, 'percentage': 60.0},
                    {'language': 'Spanish', 'users': 200, 'percentage': 20.0},
                    {'language': 'French', 'users': 100, 'percentage': 10.0}
                ]
            }
        elif report_type == 'currency_performance':
            return {
                'report_type': 'currency_performance',
                'summary': {
                    'total_revenue': 100000.00,
                    'currencies_used': 5
                },
                'by_currency': [
                    {'currency': 'USD', 'revenue': 60000.00, 'percentage': 60.0},
                    {'currency': 'EUR', 'revenue': 25000.00, 'percentage': 25.0},
                    {'currency': 'GBP', 'revenue': 15000.00, 'percentage': 15.0}
                ]
            }
        # Add more report types as needed
        
        return {'error': 'Unknown report type'}