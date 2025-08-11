from django.contrib import admin
from .models import (
    FormTemplate, Form, FormField, FormSubmission, FormVersion,
    FormAnalytics, FormApprovalWorkflow, FormIntegration, FormABTest
)

@admin.register(FormTemplate)
class FormTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'form_type', 'is_active', 'version', 'created_by', 'created_at']
    list_filter = ['form_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']

class FormFieldInline(admin.TabularInline):
    model = FormField
    extra = 0
    fields = ['name', 'label', 'field_type', 'is_required', 'order']
    ordering = ['order']

@admin.register(Form)
class FormAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'is_multi_step', 'created_by', 'created_at', 'published_at']
    list_filter = ['status', 'is_multi_step', 'created_at']
    search_fields = ['name', 'description', 'slug']
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [FormFieldInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')

@admin.register(FormField)
class FormFieldAdmin(admin.ModelAdmin):
    list_display = ['form', 'name', 'label', 'field_type', 'is_required', 'order']
    list_filter = ['field_type', 'is_required', 'form']
    search_fields = ['name', 'label', 'form__name']
    readonly_fields = ['id', 'created_at', 'updated_at']

@admin.register(FormSubmission)
class FormSubmissionAdmin(admin.ModelAdmin):
    list_display = ['form', 'status', 'is_spam', 'submitted_at', 'ip_address']
    list_filter = ['status', 'is_spam', 'submitted_at', 'form']
    search_fields = ['form__name', 'ip_address']
    readonly_fields = ['id', 'submitted_at', 'processed_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('form')

@admin.register(FormVersion)
class FormVersionAdmin(admin.ModelAdmin):
    list_display = ['form', 'version_number', 'is_current', 'created_by', 'created_at']
    list_filter = ['is_current', 'created_at']
    search_fields = ['form__name', 'version_number']
    readonly_fields = ['id', 'created_at']

@admin.register(FormAnalytics)
class FormAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['form', 'date', 'views', 'completions', 'conversion_rate']
    list_filter = ['date', 'form']
    search_fields = ['form__name']
    readonly_fields = ['id', 'created_at', 'updated_at']

@admin.register(FormApprovalWorkflow)
class FormApprovalWorkflowAdmin(admin.ModelAdmin):
    list_display = ['submission', 'approver', 'status', 'step', 'created_at']
    list_filter = ['status', 'step', 'created_at']
    search_fields = ['submission__form__name', 'approver__username']
    readonly_fields = ['id', 'created_at', 'processed_at']

@admin.register(FormIntegration)
class FormIntegrationAdmin(admin.ModelAdmin):
    list_display = ['form', 'name', 'integration_type', 'is_active', 'created_at']
    list_filter = ['integration_type', 'is_active', 'created_at']
    search_fields = ['form__name', 'name']
    readonly_fields = ['id', 'created_at', 'updated_at']

@admin.register(FormABTest)
class FormABTestAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'traffic_split', 'start_date', 'end_date']
    list_filter = ['status', 'start_date', 'end_date']
    search_fields = ['name', 'original_form__name', 'variant_form__name']
    readonly_fields = ['id', 'created_at', 'updated_at']