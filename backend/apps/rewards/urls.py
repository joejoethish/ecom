"""
Rewards URL configuration.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomerRewardsViewSet

router = DefaultRouter()
router.register(r'', CustomerRewardsViewSet, basename='rewards')

urlpatterns = [
    path('', include(router.urls)),
]