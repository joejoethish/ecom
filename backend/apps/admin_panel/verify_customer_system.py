"""
Simple verification script for the customer management system.
"""
from django.urls import reverse
from rest_framework.test import APIClient
from apps.admin_panel.models import AdminUser
from apps.admin_panel.customer_models import (
    CustomerSegment, CustomerLifecycleStage, CustomerCommunicationHistory,
    CustomerSupportTicket, CustomerAnalytics, CustomerLoyaltyProgram,
    CustomerRiskAssessment, CustomerGDPRCompliance, CustomerSocialMediaIntegration,
    CustomerWinBackCampaign, CustomerAccountHealthScore, CustomerPreferenceCenter,
    CustomerComplaintManagement, CustomerChurnPrediction
)

def verify_customer_system():
    """Verify the customer management system components."""
    print("🔍 Verifying Customer Management System...")
    
    # Check models
    models_to_check = [
        CustomerSegment,
        CustomerLifecycleStage,
        CustomerCommunicationHistory,
        CustomerSupportTicket,
        CustomerAnalytics,
        CustomerLoyaltyProgram,
        CustomerRiskAssessment,
        CustomerGDPRCompliance,
        CustomerSocialMediaIntegration,
        CustomerWinBackCampaign,
        CustomerAccountHealthScore,
        CustomerPreferenceCenter,
        CustomerComplaintManagement,
        CustomerChurnPrediction,
    ]
    
    print("\n📊 Model Verification:")
    for model in models_to_check:
        try:
            table_name = model._meta.db_table
            model_name = model.__name__
            print(f"✓ {model_name} -> {table_name}")
        except Exception as e:
            print(f"❌ {model.__name__}: {str(e)}")
    
    # Check URL patterns
    print("\n🌐 URL Pattern Verification:")
    url_patterns = [
        'admin_panel:admin-customers-list',
        'admin_panel:admin-customer-segments-list',
        'admin_panel:admin-support-tickets-list',
        'admin_panel:admin-social-media-list',
        'admin_panel:admin-winback-campaigns-list',
        'admin_panel:admin-health-scores-list',
        'admin_panel:admin-preferences-list',
        'admin_panel:admin-complaints-list',
        'admin_panel:admin-sla-tracking-list',
        'admin_panel:admin-churn-predictions-list',
    ]
    
    for pattern in url_patterns:
        try:
            url = reverse(pattern)
            print(f"✓ {pattern} -> {url}")
        except Exception as e:
            print(f"❌ {pattern}: {str(e)}")
    
    print("\n✅ Customer Management System verification completed!")
    return True

if __name__ == "__main__":
    verify_customer_system()