from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CustomerSegmentViewSet,
    CustomerAnalyticsViewSet,
    CustomerBehaviorEventViewSet,
    CustomerCohortViewSet,
    CustomerLifecycleStageViewSet,
    CustomerRecommendationViewSet,
    CustomerSatisfactionSurveyViewSet
)

router = DefaultRouter()
router.register(r'segments', CustomerSegmentViewSet)
router.register(r'analytics', CustomerAnalyticsViewSet)
router.register(r'behavior-events', CustomerBehaviorEventViewSet)
router.register(r'cohorts', CustomerCohortViewSet)
router.register(r'lifecycle-stages', CustomerLifecycleStageViewSet)
router.register(r'recommendations', CustomerRecommendationViewSet)
router.register(r'satisfaction-surveys', CustomerSatisfactionSurveyViewSet)

urlpatterns = [
    path('', include(router.urls)),
]