from rest_framework import serializers
from .models import (
    FormTemplate, Form, FormField, FormSubmission, FormVersion,
    FormAnalytics, FormApprovalWorkflow, FormIntegration, FormABTest
)
from django.contrib.auth import get_user_model

User = get_user_model()

class FormFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = FormField
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')

class FormTemplateSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = FormTemplate
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by')

class FormSerializer(serializers.ModelSerializer):
    fields = FormFieldSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    submission_count = serializers.SerializerMethodField()
    conversion_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = Form
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by')
    
    def get_submission_count(self, obj):
        return obj.submissions.count()
    
    def get_conversion_rate(self, obj):
        # Calculate conversion rate based on analytics
        latest_analytics = obj.analytics.first()
        if latest_analytics and latest_analytics.views > 0:
            return (latest_analytics.completions / latest_analytics.views) * 100
        return 0

class FormSubmissionSerializer(serializers.ModelSerializer):
    form_name = serializers.CharField(source='form.name', read_only=True)
    submitted_by_name = serializers.CharField(source='submitted_by.get_full_name', read_only=True)
    
    class Meta:
        model = FormSubmission
        fields = '__all__'
        read_only_fields = ('id', 'submitted_at', 'processed_at')

class FormVersionSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = FormVersion
        fields = '__all__'
        read_only_fields = ('id', 'created_at')

class FormAnalyticsSerializer(serializers.ModelSerializer):
    form_name = serializers.CharField(source='form.name', read_only=True)
    
    class Meta:
        model = FormAnalytics
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')

class FormApprovalWorkflowSerializer(serializers.ModelSerializer):
    approver_name = serializers.CharField(source='approver.get_full_name', read_only=True)
    submission_data = FormSubmissionSerializer(source='submission', read_only=True)
    
    class Meta:
        model = FormApprovalWorkflow
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'processed_at')

class FormIntegrationSerializer(serializers.ModelSerializer):
    form_name = serializers.CharField(source='form.name', read_only=True)
    
    class Meta:
        model = FormIntegration
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at')

class FormABTestSerializer(serializers.ModelSerializer):
    original_form_name = serializers.CharField(source='original_form.name', read_only=True)
    variant_form_name = serializers.CharField(source='variant_form.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = FormABTest
        fields = '__all__'
        read_only_fields = ('id', 'created_at', 'updated_at', 'created_by')

# Specialized serializers for form builder
class FormBuilderFieldSerializer(serializers.ModelSerializer):
    """Serializer for form builder interface"""
    
    class Meta:
        model = FormField
        fields = [
            'id', 'name', 'label', 'field_type', 'placeholder', 'help_text',
            'default_value', 'options', 'validation_rules', 'conditional_logic',
            'is_required', 'is_readonly', 'is_hidden', 'order', 'step',
            'css_classes', 'attributes'
        ]

class FormBuilderSerializer(serializers.ModelSerializer):
    """Serializer for form builder interface"""
    fields = FormBuilderFieldSerializer(many=True)
    
    class Meta:
        model = Form
        fields = [
            'id', 'name', 'slug', 'description', 'schema', 'validation_rules',
            'conditional_logic', 'settings', 'status', 'is_multi_step',
            'steps_config', 'auto_save_enabled', 'requires_approval',
            'approval_workflow', 'encryption_enabled', 'spam_protection_enabled',
            'analytics_enabled', 'fields'
        ]
    
    def create(self, validated_data):
        fields_data = validated_data.pop('fields', [])
        form = Form.objects.create(**validated_data)
        
        for field_data in fields_data:
            FormField.objects.create(form=form, **field_data)
        
        return form
    
    def update(self, instance, validated_data):
        fields_data = validated_data.pop('fields', [])
        
        # Update form instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update fields
        if fields_data:
            # Delete existing fields
            instance.fields.all().delete()
            
            # Create new fields
            for field_data in fields_data:
                FormField.objects.create(form=instance, **field_data)
        
        return instance

class FormSubmissionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating form submissions"""
    
    class Meta:
        model = FormSubmission
        fields = ['form', 'data', 'files', 'ip_address', 'user_agent', 'referrer', 'session_id']
    
    def validate_data(self, value):
        """Validate form data against form schema"""
        form = self.initial_data.get('form')
        if form:
            # Get form instance and validate against its schema
            try:
                form_instance = Form.objects.get(id=form)
                # Implement validation logic here
                # This would validate against the form's validation_rules
                return value
            except Form.DoesNotExist:
                raise serializers.ValidationError("Invalid form ID")
        return value

class FormAnalyticsReportSerializer(serializers.Serializer):
    """Serializer for form analytics reports"""
    form_id = serializers.UUIDField()
    date_range = serializers.CharField()
    metrics = serializers.ListField(child=serializers.CharField())
    
    def validate_date_range(self, value):
        valid_ranges = ['today', 'yesterday', 'last_7_days', 'last_30_days', 'last_90_days', 'custom']
        if value not in valid_ranges:
            raise serializers.ValidationError(f"Invalid date range. Must be one of: {valid_ranges}")
        return value