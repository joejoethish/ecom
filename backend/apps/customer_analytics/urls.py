from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CustomerSegmentViewSet,
    CustomerAnalyticsViewSet,
    CustomerBehaviorEventViewSet,
    CustomerCohortViewSet,
    CustomerLifecycleStageViewSet,
    CustomerRecommendationViewSet,
    CustomerSatisfactionSurveyViewSet,
    AdvancedCustomerAnalyticsViewSet,
    MLCustomerAnalyticsViewSet
)

router = DefaultRouter()
router.register(r'segments', CustomerSegmentViewSet)
router.register(r'analytics', CustomerAnalyticsViewSet)
router.register(r'behavior-events', CustomerBehaviorEventViewSet)
router.register(r'cohorts', CustomerCohortViewSet)
router.register(r'lifecycle-stages', CustomerLifecycleStageViewSet)
router.register(r'recommendations', CustomerRecommendationViewSet)
router.register(r'satisfaction-surveys', CustomerSatisfactionSurveyViewSet)
router.register(r'advanced', AdvancedCustomerAnalyticsViewSet, basename='advanced-analytics')
router.register(r'ml', MLCustomerAnalyticsViewSet, basename='ml-analytics')

urlpatterns = [
    path('', include(router.urls)),
]