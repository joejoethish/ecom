from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'partners', views.ShippingPartnerViewSet)
router.register(r'areas', views.ServiceableAreaViewSet)
router.register(r'slots', views.DeliverySlotViewSet)
router.register(r'shipments', views.ShipmentViewSet)
router.register(r'rates', views.ShippingRateViewSet)

urlpatterns = [
    path('', include(router.urls)),
    # Tracking endpoint with a more user-friendly URL
    path('track/<str:tracking_number>/', views.ShipmentViewSet.as_view({'get': 'track'}), name='shipment-tracking'),
    # Webhook endpoint
    path('webhook/', views.ShipmentViewSet.as_view({'post': 'webhook'}), name='shipment-webhook'),
]