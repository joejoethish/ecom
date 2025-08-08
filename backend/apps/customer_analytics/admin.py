from django.contrib import admin
from .models import (
    CustomerSegment,
    CustomerAnalytics,
    CustomerBehaviorEvent,
    CustomerCohort,
    CustomerLifecycleStage,
    CustomerRecommendation,
    CustomerSatisfactionSurvey
)


@admin.register(CustomerSegment)
class CustomerSegmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'segment_type', 'is_active', 'created_at']
    list_filter = ['segment_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(CustomerAnalytics)
class CustomerAnalyticsAdmin(admin.ModelAdmin):
    list_display = ['customer', 'segment', 'total_orders', 'total_spent', 'churn_risk_score', 'last_calculated']
    list_filter = ['segment', 'last_calculated']
    search_fields = ['customer__username', 'customer__email']
    readonly_fields = ['created_at', 'updated_at', 'last_calculated']
    raw_id_fields = ['customer']


@admin.register(CustomerBehaviorEvent)
class CustomerBehaviorEventAdmin(admin.ModelAdmin):
    list_display = ['customer', 'event_type', 'timestamp', 'session_id']
    list_filter = ['event_type', 'timestamp']
    search_fields = ['customer__username', 'session_id']
    readonly_fields = ['timestamp']
    raw_id_fields = ['customer']
    date_hierarchy = 'timestamp'


@admin.register(CustomerCohort)
class CustomerCohortAdmin(admin.ModelAdmin):
    list_display = ['name', 'cohort_date', 'initial_customers', 'current_active_customers', 'retention_rate']
    list_filter = ['cohort_date']
    search_fields = ['name']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'cohort_date'


@admin.register(CustomerLifecycleStage)
class CustomerLifecycleStageAdmin(admin.ModelAdmin):
    list_display = ['customer', 'stage', 'stage_date', 'stage_duration']
    list_filter = ['stage', 'stage_date']
    search_fields = ['customer__username']
    readonly_fields = ['stage_date']
    raw_id_fields = ['customer']
    date_hierarchy = 'stage_date'


@admin.register(CustomerRecommendation)
class CustomerRecommendationAdmin(admin.ModelAdmin):
    list_display = ['customer', 'recommendation_type', 'confidence_score', 'is_active', 'click_through_rate']
    list_filter = ['recommendation_type', 'is_active', 'created_at']
    search_fields = ['customer__username']
    readonly_fields = ['created_at', 'click_through_rate', 'conversion_rate']
    raw_id_fields = ['customer']


@admin.register(CustomerSatisfactionSurvey)
class CustomerSatisfactionSurveyAdmin(admin.ModelAdmin):
    list_display = ['customer', 'survey_type', 'score', 'max_score', 'normalized_score', 'survey_date']
    list_filter = ['survey_type', 'score', 'survey_date']
    search_fields = ['customer__username', 'feedback_text']
    readonly_fields = ['survey_date', 'normalized_score']
    raw_id_fields = ['customer']
    date_hierarchy = 'survey_date'