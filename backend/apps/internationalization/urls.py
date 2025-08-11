from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    LanguageViewSet, CurrencyViewSet, TimezoneViewSet, TranslationViewSet,
    LocalizedContentViewSet, UserLocalizationViewSet, InternationalPaymentGatewayViewSet,
    InternationalShippingViewSet, InternationalTaxRuleViewSet, RegionalComplianceViewSet,
    CurrencyExchangeRateViewSet, InternationalizationAnalyticsViewSet
)

router = DefaultRouter()
router.register(r'languages', LanguageViewSet)
router.register(r'currencies', CurrencyViewSet)
router.register(r'timezones', TimezoneViewSet)
router.register(r'translations', TranslationViewSet)
router.register(r'localized-content', LocalizedContentViewSet)
router.register(r'user-localization', UserLocalizationViewSet)
router.register(r'payment-gateways', InternationalPaymentGatewayViewSet)
router.register(r'shipping', InternationalShippingViewSet)
router.register(r'tax-rules', InternationalTaxRuleViewSet)
router.register(r'compliance', RegionalComplianceViewSet)
router.register(r'exchange-rates', CurrencyExchangeRateViewSet)
router.register(r'analytics', InternationalizationAnalyticsViewSet, basename='internationalization-analytics')

urlpatterns = [
    path('api/internationalization/', include(router.urls)),
]