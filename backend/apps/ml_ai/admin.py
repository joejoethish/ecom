from django.contrib import admin
from .models import *


@admin.register(MLModel)
class MLModelAdmin(admin.ModelAdmin):
    list_display = ['name', 'model_type', 'version', 'status', 'accuracy', 'created_at', 'last_trained']
    list_filter = ['model_type', 'status', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'model_type', 'version', 'status', 'description')
        }),
        ('Performance Metrics', {
            'fields': ('accuracy', 'precision', 'recall', 'f1_score')
        }),
        ('Configuration', {
            'fields': ('parameters', 'hyperparameters')
        }),
        ('File Paths', {
            'fields': ('model_file_path', 'training_data_path')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at', 'last_trained'),
            'classes': ('collapse',)
        })
    )


@admin.register(MLPrediction)
class MLPredictionAdmin(admin.ModelAdmin):
    list_display = ['model', 'content_type', 'object_id', 'confidence_score', 'created_at']
    list_filter = ['model__model_type', 'content_type', 'created_at']
    readonly_fields = ['id', 'created_at']


@admin.register(DemandForecast)
class DemandForecastAdmin(admin.ModelAdmin):
    list_display = ['product_id', 'forecast_date', 'predicted_demand', 'actual_demand', 'model', 'created_at']
    list_filter = ['forecast_date', 'model', 'created_at']
    search_fields = ['product_id']
    readonly_fields = ['id', 'created_at']


@admin.register(CustomerSegment)
class CustomerSegmentAdmin(admin.ModelAdmin):
    list_display = ['customer_id', 'segment_type', 'segment_score', 'model', 'created_at']
    list_filter = ['segment_type', 'model', 'created_at']
    search_fields = ['customer_id']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(FraudDetection)
class FraudDetectionAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'risk_level', 'risk_score', 'is_confirmed_fraud', 'model', 'created_at']
    list_filter = ['risk_level', 'is_confirmed_fraud', 'model', 'created_at']
    search_fields = ['transaction_id']
    readonly_fields = ['id', 'created_at']
    
    actions = ['mark_as_fraud', 'mark_as_legitimate']
    
    def mark_as_fraud(self, request, queryset):
        queryset.update(is_confirmed_fraud=True)
        self.message_user(request, f"{queryset.count()} transactions marked as fraud.")
    mark_as_fraud.short_description = "Mark selected as confirmed fraud"
    
    def mark_as_legitimate(self, request, queryset):
        queryset.update(is_confirmed_fraud=False)
        self.message_user(request, f"{queryset.count()} transactions marked as legitimate.")
    mark_as_legitimate.short_description = "Mark selected as legitimate"


@admin.register(ProductRecommendation)
class ProductRecommendationAdmin(admin.ModelAdmin):
    list_display = ['customer_id', 'product_id', 'recommendation_type', 'score', 'rank', 'model', 'created_at']
    list_filter = ['recommendation_type', 'model', 'created_at']
    search_fields = ['customer_id', 'product_id']
    readonly_fields = ['id', 'created_at']


@admin.register(PricingOptimization)
class PricingOptimizationAdmin(admin.ModelAdmin):
    list_display = ['product_id', 'current_price', 'optimized_price', 'expected_revenue', 'applied_at', 'created_at']
    list_filter = ['applied_at', 'model', 'created_at']
    search_fields = ['product_id']
    readonly_fields = ['id', 'created_at']
    
    actions = ['apply_pricing']
    
    def apply_pricing(self, request, queryset):
        from django.utils import timezone
        queryset.update(applied_at=timezone.now())
        self.message_user(request, f"Applied pricing for {queryset.count()} products.")
    apply_pricing.short_description = "Apply optimized pricing"


@admin.register(ChurnPrediction)
class ChurnPredictionAdmin(admin.ModelAdmin):
    list_display = ['customer_id', 'churn_probability', 'risk_level', 'model', 'created_at']
    list_filter = ['risk_level', 'model', 'created_at']
    search_fields = ['customer_id']
    readonly_fields = ['id', 'created_at']


@admin.register(SentimentAnalysis)
class SentimentAnalysisAdmin(admin.ModelAdmin):
    list_display = ['sentiment', 'confidence_score', 'source_type', 'source_id', 'model', 'created_at']
    list_filter = ['sentiment', 'source_type', 'model', 'created_at']
    search_fields = ['text_content', 'source_id']
    readonly_fields = ['id', 'created_at']


@admin.register(AnomalyDetection)
class AnomalyDetectionAdmin(admin.ModelAdmin):
    list_display = ['anomaly_type', 'anomaly_score', 'threshold', 'is_investigated', 'model', 'created_at']
    list_filter = ['anomaly_type', 'is_investigated', 'model', 'created_at']
    readonly_fields = ['id', 'created_at']
    
    actions = ['mark_investigated']
    
    def mark_investigated(self, request, queryset):
        queryset.update(is_investigated=True)
        self.message_user(request, f"Marked {queryset.count()} anomalies as investigated.")
    mark_investigated.short_description = "Mark as investigated"


@admin.register(MLTrainingJob)
class MLTrainingJobAdmin(admin.ModelAdmin):
    list_display = ['model', 'status', 'progress_percentage', 'started_at', 'completed_at']
    list_filter = ['status', 'started_at', 'completed_at']
    readonly_fields = ['id', 'created_at']


@admin.register(AIInsight)
class AIInsightAdmin(admin.ModelAdmin):
    list_display = ['title', 'insight_type', 'priority', 'confidence_level', 'is_reviewed', 'is_implemented', 'created_at']
    list_filter = ['insight_type', 'priority', 'is_reviewed', 'is_implemented', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['id', 'created_at']
    
    actions = ['mark_reviewed', 'mark_implemented']
    
    def mark_reviewed(self, request, queryset):
        from django.utils import timezone
        queryset.update(is_reviewed=True, reviewed_at=timezone.now())
        self.message_user(request, f"Marked {queryset.count()} insights as reviewed.")
    mark_reviewed.short_description = "Mark as reviewed"
    
    def mark_implemented(self, request, queryset):
        queryset.update(is_implemented=True)
        self.message_user(request, f"Marked {queryset.count()} insights as implemented.")
    mark_implemented.short_description = "Mark as implemented"