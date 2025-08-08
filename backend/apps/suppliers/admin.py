from django.contrib import admin
from .models import (
    SupplierCategory, Supplier, SupplierDocument, SupplierContact,
    SupplierPerformanceMetric, PurchaseOrder, PurchaseOrderItem,
    SupplierAudit, SupplierCommunication, SupplierContract
)


@admin.register(SupplierCategory)
class SupplierCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name']


class SupplierDocumentInline(admin.TabularInline):
    model = SupplierDocument
    extra = 0


class SupplierContactInline(admin.TabularInline):
    model = SupplierContact
    extra = 0


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = [
        'supplier_code', 'company_name', 'supplier_type', 'status',
        'performance_score', 'risk_level', 'created_at'
    ]
    list_filter = [
        'status', 'supplier_type', 'risk_level', 'category',
        'is_minority_owned', 'is_women_owned', 'esg_compliance'
    ]
    search_fields = ['supplier_code', 'company_name', 'legal_name']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [SupplierDocumentInline, SupplierContactInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('supplier_code', 'company_name', 'legal_name', 'supplier_type', 'category', 'status')
        }),
        ('Contact Information', {
            'fields': (
                'primary_contact_name', 'primary_contact_email', 'primary_contact_phone',
                'secondary_contact_name', 'secondary_contact_email', 'secondary_contact_phone'
            )
        }),
        ('Address', {
            'fields': ('address_line1', 'address_line2', 'city', 'state', 'postal_code', 'country')
        }),
        ('Business Information', {
            'fields': ('tax_id', 'business_license', 'website', 'established_year', 'employee_count', 'annual_revenue')
        }),
        ('Performance Metrics', {
            'fields': ('performance_score', 'quality_score', 'delivery_score', 'reliability_score')
        }),
        ('Risk Assessment', {
            'fields': ('risk_level', 'financial_stability_score', 'compliance_score')
        }),
        ('Payment Terms', {
            'fields': ('payment_terms_days', 'credit_limit', 'currency')
        }),
        ('Diversity Information', {
            'fields': ('is_minority_owned', 'is_women_owned', 'is_veteran_owned', 'is_small_business')
        }),
        ('Sustainability', {
            'fields': ('sustainability_score', 'esg_compliance')
        }),
        ('Audit Information', {
            'fields': ('last_audit_date', 'next_audit_date')
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(SupplierDocument)
class SupplierDocumentAdmin(admin.ModelAdmin):
    list_display = ['supplier', 'document_type', 'title', 'expiry_date', 'is_verified', 'uploaded_at']
    list_filter = ['document_type', 'is_verified', 'expiry_date']
    search_fields = ['supplier__company_name', 'title']


@admin.register(SupplierPerformanceMetric)
class SupplierPerformanceMetricAdmin(admin.ModelAdmin):
    list_display = [
        'supplier', 'metric_date', 'on_time_delivery_rate',
        'defect_rate', 'total_orders', 'total_value'
    ]
    list_filter = ['metric_date', 'supplier']
    search_fields = ['supplier__company_name']


class PurchaseOrderItemInline(admin.TabularInline):
    model = PurchaseOrderItem
    extra = 0


@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = [
        'po_number', 'supplier', 'status', 'priority',
        'total_amount', 'order_date', 'required_date'
    ]
    list_filter = ['status', 'priority', 'order_date']
    search_fields = ['po_number', 'supplier__company_name']
    inlines = [PurchaseOrderItemInline]


@admin.register(SupplierAudit)
class SupplierAuditAdmin(admin.ModelAdmin):
    list_display = [
        'supplier', 'audit_type', 'status', 'scheduled_date',
        'completed_date', 'overall_score', 'auditor'
    ]
    list_filter = ['audit_type', 'status', 'scheduled_date']
    search_fields = ['supplier__company_name']


@admin.register(SupplierCommunication)
class SupplierCommunicationAdmin(admin.ModelAdmin):
    list_display = [
        'supplier', 'communication_type', 'subject',
        'internal_contact', 'requires_follow_up', 'created_at'
    ]
    list_filter = ['communication_type', 'requires_follow_up', 'is_resolved']
    search_fields = ['supplier__company_name', 'subject']


@admin.register(SupplierContract)
class SupplierContractAdmin(admin.ModelAdmin):
    list_display = [
        'supplier', 'contract_type', 'contract_number',
        'status', 'start_date', 'end_date', 'contract_value'
    ]
    list_filter = ['contract_type', 'status', 'start_date', 'end_date']
    search_fields = ['supplier__company_name', 'contract_number', 'title']