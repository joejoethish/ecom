from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SupplierCategoryViewSet, SupplierViewSet, SupplierDocumentViewSet,
    SupplierContactViewSet, PurchaseOrderViewSet, SupplierAuditViewSet,
    SupplierCommunicationViewSet, SupplierContractViewSet
)

router = DefaultRouter()
router.register(r'categories', SupplierCategoryViewSet)
router.register(r'suppliers', SupplierViewSet)
router.register(r'documents', SupplierDocumentViewSet)
router.register(r'contacts', SupplierContactViewSet)
router.register(r'purchase-orders', PurchaseOrderViewSet)
router.register(r'audits', SupplierAuditViewSet)
router.register(r'communications', SupplierCommunicationViewSet)
router.register(r'contracts', SupplierContractViewSet)

urlpatterns = [
    path('api/suppliers/', include(router.urls)),
]