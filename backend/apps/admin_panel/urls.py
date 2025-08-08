"""
URL configuration for the comprehensive admin panel.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .product_views import (
    ComprehensiveProductViewSet, ProductVariantViewSet, ProductAttributeViewSet,
    ProductBundleViewSet, ProductTemplateViewSet, ProductAnalyticsViewSet
)
from .customer_views import (
    ComprehensiveCustomerViewSet, CustomerSegmentViewSet, CustomerSupportTicketViewSet,
    CustomerSocialMediaIntegrationViewSet, CustomerWinBackCampaignViewSet,
    CustomerAccountHealthScoreViewSet, CustomerPreferenceCenterViewSet,
    CustomerComplaintManagementViewSet, CustomerServiceLevelAgreementViewSet,
    CustomerChurnPredictionViewSet
)
from .order_views import (
    AdminOrderViewSet, OrderSearchFilterViewSet, OrderWorkflowViewSet,
    OrderFraudScoreViewSet, OrderNoteViewSet, OrderEscalationViewSet,
    OrderSLAViewSet, OrderAllocationViewSet, OrderProfitabilityViewSet,
    OrderDocumentViewSet, OrderQualityControlViewSet, OrderSubscriptionViewSet
)
from .inventory_views import (
    InventoryLocationViewSet, InventoryItemViewSet, InventoryValuationViewSet,
    InventoryAdjustmentViewSet, InventoryTransferViewSet, InventoryReservationViewSet,
    InventoryAlertViewSet, InventoryAuditViewSet, InventoryOptimizationViewSet,
    InventoryDashboardViewSet, InventoryImportExportViewSet
)
from .supplier_views import (
    SupplierCategoryViewSet, SupplierViewSet, SupplierContactViewSet,
    SupplierDocumentViewSet, PurchaseOrderViewSet, SupplierPerformanceMetricViewSet,
    SupplierCommunicationViewSet, SupplierContractViewSet, SupplierAuditViewSet,
    SupplierRiskAssessmentViewSet, SupplierQualificationViewSet, SupplierPaymentViewSet
)

# Create router for API endpoints
router = DefaultRouter()

# Product management endpoints
router.register(r'products', ComprehensiveProductViewSet, basename='admin-products')
router.register(r'product-variants', ProductVariantViewSet, basename='admin-product-variants')
router.register(r'product-attributes', ProductAttributeViewSet, basename='admin-product-attributes')
router.register(r'product-bundles', ProductBundleViewSet, basename='admin-product-bundles')
router.register(r'product-templates', ProductTemplateViewSet, basename='admin-product-templates')
router.register(r'product-analytics', ProductAnalyticsViewSet, basename='admin-product-analytics')

# Customer management endpoints
router.register(r'customers', ComprehensiveCustomerViewSet, basename='admin-customers')
router.register(r'customer-segments', CustomerSegmentViewSet, basename='admin-customer-segments')
router.register(r'support-tickets', CustomerSupportTicketViewSet, basename='admin-support-tickets')
router.register(r'social-media', CustomerSocialMediaIntegrationViewSet, basename='admin-social-media')
router.register(r'winback-campaigns', CustomerWinBackCampaignViewSet, basename='admin-winback-campaigns')
router.register(r'health-scores', CustomerAccountHealthScoreViewSet, basename='admin-health-scores')
router.register(r'preferences', CustomerPreferenceCenterViewSet, basename='admin-preferences')
router.register(r'complaints', CustomerComplaintManagementViewSet, basename='admin-complaints')
router.register(r'sla-tracking', CustomerServiceLevelAgreementViewSet, basename='admin-sla-tracking')
router.register(r'churn-predictions', CustomerChurnPredictionViewSet, basename='admin-churn-predictions')

# Order management endpoints
router.register(r'orders', AdminOrderViewSet, basename='admin-orders')
router.register(r'order-filters', OrderSearchFilterViewSet, basename='admin-order-filters')
router.register(r'order-workflows', OrderWorkflowViewSet, basename='admin-order-workflows')
router.register(r'order-fraud-scores', OrderFraudScoreViewSet, basename='admin-order-fraud-scores')
router.register(r'order-notes', OrderNoteViewSet, basename='admin-order-notes')
router.register(r'order-escalations', OrderEscalationViewSet, basename='admin-order-escalations')
router.register(r'order-sla', OrderSLAViewSet, basename='admin-order-sla')
router.register(r'order-allocations', OrderAllocationViewSet, basename='admin-order-allocations')
router.register(r'order-profitability', OrderProfitabilityViewSet, basename='admin-order-profitability')
router.register(r'order-documents', OrderDocumentViewSet, basename='admin-order-documents')
router.register(r'order-quality-control', OrderQualityControlViewSet, basename='admin-order-quality-control')
router.register(r'order-subscriptions', OrderSubscriptionViewSet, basename='admin-order-subscriptions')

# Inventory management endpoints
router.register(r'inventory-locations', InventoryLocationViewSet, basename='admin-inventory-locations')
router.register(r'inventory-items', InventoryItemViewSet, basename='admin-inventory-items')
router.register(r'inventory-valuations', InventoryValuationViewSet, basename='admin-inventory-valuations')
router.register(r'inventory-adjustments', InventoryAdjustmentViewSet, basename='admin-inventory-adjustments')
router.register(r'inventory-transfers', InventoryTransferViewSet, basename='admin-inventory-transfers')
router.register(r'inventory-reservations', InventoryReservationViewSet, basename='admin-inventory-reservations')
router.register(r'inventory-alerts', InventoryAlertViewSet, basename='admin-inventory-alerts')
router.register(r'inventory-audits', InventoryAuditViewSet, basename='admin-inventory-audits')
router.register(r'inventory-optimizations', InventoryOptimizationViewSet, basename='admin-inventory-optimizations')
router.register(r'inventory-dashboard', InventoryDashboardViewSet, basename='admin-inventory-dashboard')
router.register(r'inventory-import-export', InventoryImportExportViewSet, basename='admin-inventory-import-export')

# Supplier and vendor management endpoints
router.register(r'supplier-categories', SupplierCategoryViewSet, basename='admin-supplier-categories')
router.register(r'suppliers', SupplierViewSet, basename='admin-suppliers')
router.register(r'supplier-contacts', SupplierContactViewSet, basename='admin-supplier-contacts')
router.register(r'supplier-documents', SupplierDocumentViewSet, basename='admin-supplier-documents')
router.register(r'purchase-orders', PurchaseOrderViewSet, basename='admin-purchase-orders')
router.register(r'supplier-performance', SupplierPerformanceMetricViewSet, basename='admin-supplier-performance')
router.register(r'supplier-communications', SupplierCommunicationViewSet, basename='admin-supplier-communications')
router.register(r'supplier-contracts', SupplierContractViewSet, basename='admin-supplier-contracts')
router.register(r'supplier-audits', SupplierAuditViewSet, basename='admin-supplier-audits')
router.register(r'supplier-risk-assessments', SupplierRiskAssessmentViewSet, basename='admin-supplier-risk-assessments')
router.register(r'supplier-qualifications', SupplierQualificationViewSet, basename='admin-supplier-qualifications')
router.register(r'supplier-payments', SupplierPaymentViewSet, basename='admin-supplier-payments')

app_name = 'admin_panel'

urlpatterns = [
    # API endpoints
    path('api/', include(router.urls)),
    
    # Additional custom endpoints can be added here
]