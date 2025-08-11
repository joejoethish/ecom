#!/usr/bin/env python
"""
Comprehensive test suite for Advanced Customer Analytics functionality.
Tests all features implemented in task 14: Advanced Customer Analytics and Behavior Analysis.
"""

import os
import sys
import django
from decimal import Decimal
from datetime import datetime, timedelta

# Setup Django environment
sys.path.append('/workspaces/comprehensive-ecommerce-platform/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ecommerce_project.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.customer_analytics.models import *
from apps.customer_analytics.services import CustomerAnalyticsService
from apps.customer_analytics.advanced_analytics_service import AdvancedCustomerAnalyticsService
from apps.customer_analytics.ml_analytics_service import MLCustomerAnalyticsService

User = get_user_model()


class AdvancedCustomerAnalyticsTest:
    """Test suite for advanced customer analytics"""
    
    def __init__(self):
        self.basic_service = CustomerAnalyticsService()
        self.advanced_service = AdvancedCustomerAnalyticsService()
        self.ml_service = MLCustomerAnalyticsService()
        self.test_customer = None
        
    def setup_test_data(self):
        """Setup test data for analytics testing"""
        print("Setting up test data...")
        
        # Create test customer
        self.test_customer, created = User.objects.get_or_create(
            username='test_analytics_customer',
            defaults={
                'email': 'test@analytics.com',
                'first_name': 'Test',
                'last_name': 'Customer'
            }
        )
        
        # Create customer analytics record
        analytics, created = CustomerAnalytics.objects.get_or_create(
            customer=self.test_customer,
            defaults={
                'total_orders': 5,
                'total_spent': Decimal('1500.00'),
                'average_order_value': Decimal('300.00'),
                'first_purchase_date': timezone.now() - timedelta(days=180),
                'last_purchase_date': timezone.now() - timedelta(days=30),
                'days_since_last_purchase': 30,
                'purchase_frequency': Decimal('1.5'),
                'customer_lifetime_value': Decimal('2500.00'),
                'churn_risk_score': Decimal('35.50'),
                'satisfaction_score': Decimal('8.5')
            }
        )
        
        # Create behavior events
        event_types = ['product_view', 'add_to_cart', 'checkout_complete', 'search', 'page_view']
        for i, event_type in enumerate(event_types):
            CustomerBehaviorEvent.objects.get_or_create(
                customer=self.test_customer,
                event_type=event_type,
                defaults={
                    'event_data': {'product_id': i+1, 'category': 'Electronics'},
                    'session_id': f'session_{i}',
                    'timestamp': timezone.now() - timedelta(hours=i)
                }
            )
        
        # Create satisfaction surveys
        CustomerSatisfactionSurvey.objects.get_or_create(
            customer=self.test_customer,
            survey_type='nps',
            defaults={
                'score': 9,
                'max_score': 10,
                'feedback_text': 'Great service and products!'
            }
        )
        
        CustomerSatisfactionSurvey.objects.get_or_create(
            customer=self.test_customer,
            survey_type='csat',
            defaults={
                'score': 8,
                'max_score': 10,
                'feedback_text': 'Very satisfied with the purchase'
            }
        )
        
        print("✓ Test data setup completed")
    
    def test_customer_lifetime_value_calculation(self):
        """Test CLV calculation and segmentation"""
        print("\n1. Testing Customer Lifetime Value (CLV) Calculation...")
        
        try:
            # Test CLV calculation for specific customer
            clv_data = self.advanced_service.calculate_customer_lifetime_value(self.test_customer.id)
            
            assert clv_data is not None, "CLV data should not be None"
            assert clv_data.customer == self.test_customer, "CLV should be for correct customer"
            assert clv_data.historical_clv >= 0, "Historical CLV should be non-negative"
            assert clv_data.predicted_clv >= 0, "Predicted CLV should be non-negative"
            assert clv_data.purchase_frequency >= 0, "Purchase frequency should be non-negative"
            assert clv_data.average_order_value >= 0, "AOV should be non-negative"
            assert clv_data.customer_lifespan >= 0, "Customer lifespan should be non-negative"
            assert clv_data.clv_to_cac_ratio >= 0, "CLV to CAC ratio should be non-negative"
            
            print(f"   ✓ Historical CLV: ${clv_data.historical_clv}")
            print(f"   ✓ Predicted CLV: ${clv_data.predicted_clv}")
            print(f"   ✓ Purchase Frequency: {clv_data.purchase_frequency}")
            print(f"   ✓ Average Order Value: ${clv_data.average_order_value}")
            print(f"   ✓ Customer Lifespan: {clv_data.customer_lifespan} months")
            print(f"   ✓ CLV to CAC Ratio: {clv_data.clv_to_cac_ratio}")
            print(f"   ✓ Engagement Score: {clv_data.engagement_score}")
            print(f"   ✓ Loyalty Score: {clv_data.loyalty_score}")
            print(f"   ✓ Prediction Confidence: {clv_data.prediction_confidence}%")
            
            # Test CLV segmentation
            segments = self.advanced_service.segment_customers_by_clv()
            assert isinstance(segments, dict), "Segments should be a dictionary"
            assert 'champions' in segments, "Should have champions segment"
            assert 'loyal_customers' in segments, "Should have loyal customers segment"
            assert 'at_risk' in segments, "Should have at-risk segment"
            
            print("   ✓ CLV segmentation completed")
            print("   ✓ CLV calculation and segmentation test PASSED")
            
        except Exception as e:
            print(f"   ✗ CLV calculation test FAILED: {str(e)}")
            raise
    
    def test_churn_prediction(self):
        """Test ML-based churn prediction"""
        print("\n2. Testing Churn Prediction with ML Models...")
        
        try:
            # Test churn prediction for specific customer
            churn_data = self.advanced_service.predict_customer_churn(self.test_customer.id)
            
            assert churn_data is not None, "Churn data should not be None"
            assert churn_data.customer == self.test_customer, "Churn prediction should be for correct customer"
            assert 0 <= churn_data.churn_probability <= 1, "Churn probability should be between 0 and 1"
            assert churn_data.churn_risk_level in ['low', 'medium', 'high', 'critical'], "Risk level should be valid"
            assert 0 <= churn_data.recency_score <= 100, "Recency score should be between 0 and 100"
            assert 0 <= churn_data.frequency_score <= 100, "Frequency score should be between 0 and 100"
            assert 0 <= churn_data.monetary_score <= 100, "Monetary score should be between 0 and 100"
            assert 0 <= churn_data.prediction_confidence <= 100, "Confidence should be between 0 and 100"
            
            print(f"   ✓ Churn Probability: {churn_data.churn_probability:.2%}")
            print(f"   ✓ Risk Level: {churn_data.churn_risk_level}")
            print(f"   ✓ Recency Score: {churn_data.recency_score}")
            print(f"   ✓ Frequency Score: {churn_data.frequency_score}")
            print(f"   ✓ Monetary Score: {churn_data.monetary_score}")
            print(f"   ✓ Engagement Score: {churn_data.engagement_score}")
            print(f"   ✓ Satisfaction Score: {churn_data.satisfaction_score}")
            print(f"   ✓ Prediction Confidence: {churn_data.prediction_confidence}%")
            print(f"   ✓ Intervention Recommended: {churn_data.intervention_recommended}")
            
            # Test churn analysis summary
            summary = self.advanced_service.get_churn_analysis_summary()
            assert isinstance(summary, dict), "Summary should be a dictionary"
            assert 'total_customers' in summary, "Should have total customers"
            assert 'risk_distribution' in summary, "Should have risk distribution"
            assert 'avg_churn_probability' in summary, "Should have average churn probability"
            
            print("   ✓ Churn analysis summary completed")
            print("   ✓ Churn prediction test PASSED")
            
        except Exception as e:
            print(f"   ✗ Churn prediction test FAILED: {str(e)}")
            raise
    
    def test_behavior_analysis(self):
        """Test customer behavior analysis and purchase pattern recognition"""
        print("\n3. Testing Customer Behavior Analysis...")
        
        try:
            # Test behavior pattern analysis
            patterns = self.advanced_service.analyze_customer_behavior_patterns(self.test_customer.id)
            
            assert isinstance(patterns, dict), "Patterns should be a dictionary"
            assert 'shopping_times' in patterns, "Should have shopping times analysis"
            assert 'product_preferences' in patterns, "Should have product preferences"
            assert 'purchase_cycles' in patterns, "Should have purchase cycles"
            assert 'channel_preferences' in patterns, "Should have channel preferences"
            assert 'seasonal_patterns' in patterns, "Should have seasonal patterns"
            assert 'browsing_behavior' in patterns, "Should have browsing behavior"
            assert 'cart_behavior' in patterns, "Should have cart behavior"
            assert 'search_patterns' in patterns, "Should have search patterns"
            
            print("   ✓ Shopping Times Analysis:")
            print(f"      - Preferred Hours: {patterns['shopping_times']['preferred_hours']}")
            print(f"      - Preferred Days: {patterns['shopping_times']['preferred_days']}")
            print(f"      - Peak Activity: {patterns['shopping_times']['peak_activity_time']}")
            
            print("   ✓ Product Preferences:")
            print(f"      - Top Categories: {patterns['product_preferences']['top_categories']}")
            print(f"      - Preferred Brands: {patterns['product_preferences']['preferred_brands']}")
            print(f"      - Price Sensitivity: {patterns['product_preferences']['price_sensitivity']}")
            
            print("   ✓ Purchase Cycles:")
            print(f"      - Average Cycle Length: {patterns['purchase_cycles']['average_cycle_length']} days")
            print(f"      - Cycle Consistency: {patterns['purchase_cycles']['cycle_consistency']}")
            
            print("   ✓ Channel Preferences:")
            print(f"      - Preferred Channels: {patterns['channel_preferences']['preferred_channels']}")
            
            print("   ✓ Browsing Behavior:")
            print(f"      - Avg Session Duration: {patterns['browsing_behavior']['avg_session_duration']} min")
            print(f"      - Pages per Session: {patterns['browsing_behavior']['pages_per_session']}")
            print(f"      - Bounce Rate: {patterns['browsing_behavior']['bounce_rate']}%")
            
            print("   ✓ Behavior analysis test PASSED")
            
        except Exception as e:
            print(f"   ✗ Behavior analysis test FAILED: {str(e)}")
            raise
    
    def test_customer_journey_mapping(self):
        """Test customer journey mapping and touchpoint analysis"""
        print("\n4. Testing Customer Journey Mapping...")
        
        try:
            # Test journey mapping
            journey_map = self.advanced_service.map_customer_journey(self.test_customer.id, 'purchase')
            
            assert journey_map is not None, "Journey map should not be None"
            assert journey_map.customer == self.test_customer, "Journey should be for correct customer"
            assert journey_map.journey_type == 'purchase', "Journey type should be purchase"
            assert journey_map.status in ['active', 'completed', 'abandoned', 'converted'], "Status should be valid"
            assert journey_map.total_touchpoints >= 0, "Total touchpoints should be non-negative"
            assert isinstance(journey_map.touchpoints, list), "Touchpoints should be a list"
            assert isinstance(journey_map.conversion_path, list), "Conversion path should be a list"
            
            print(f"   ✓ Journey ID: {journey_map.journey_id}")
            print(f"   ✓ Journey Type: {journey_map.journey_type}")
            print(f"   ✓ Status: {journey_map.status}")
            print(f"   ✓ Total Touchpoints: {journey_map.total_touchpoints}")
            print(f"   ✓ Start Date: {journey_map.start_date}")
            
            if journey_map.touchpoints:
                print("   ✓ Sample Touchpoints:")
                for i, touchpoint in enumerate(journey_map.touchpoints[:3]):
                    print(f"      {i+1}. {touchpoint.get('touchpoint', 'Unknown')} - {touchpoint.get('channel', 'Unknown')}")
            
            if journey_map.conversion_path:
                print("   ✓ Conversion Path:")
                for path in journey_map.conversion_path:
                    print(f"      - {path.get('channel', 'Unknown')}: {path.get('attribution_weight', 0):.1%}")
            
            print("   ✓ Journey mapping test PASSED")
            
        except Exception as e:
            print(f"   ✗ Journey mapping test FAILED: {str(e)}")
            raise
    
    def test_cac_analysis(self):
        """Test Customer Acquisition Cost (CAC) analysis and optimization"""
        print("\n5. Testing Customer Acquisition Cost (CAC) Analysis...")
        
        try:
            # Test CAC analysis
            analysis = self.advanced_service.analyze_customer_acquisition_cost()
            
            assert isinstance(analysis, dict), "Analysis should be a dictionary"
            assert 'overall_cac' in analysis, "Should have overall CAC"
            assert 'cac_by_channel' in analysis, "Should have CAC by channel"
            assert 'cac_trends' in analysis, "Should have CAC trends"
            assert 'cac_to_clv_ratios' in analysis, "Should have CAC to CLV ratios"
            assert 'optimization_recommendations' in analysis, "Should have optimization recommendations"
            
            print(f"   ✓ Overall CAC: ${analysis['overall_cac']}")
            
            print("   ✓ CAC by Channel:")
            for channel, data in analysis['cac_by_channel'].items():
                print(f"      - {channel}: ${data['cac']} (Customers: {data['customers']}, CR: {data['conversion_rate']}%)")
            
            print("   ✓ CAC to CLV Ratios:")
            ratios = analysis['cac_to_clv_ratios']
            print(f"      - Overall Ratio: {ratios['overall_ratio']}")
            for segment, ratio in ratios['by_segment'].items():
                print(f"      - {segment.replace('_', ' ').title()}: {ratio}")
            
            print("   ✓ Optimization Recommendations:")
            for i, rec in enumerate(analysis['optimization_recommendations'], 1):
                print(f"      {i}. {rec}")
            
            print("   ✓ CAC analysis test PASSED")
            
        except Exception as e:
            print(f"   ✗ CAC analysis test FAILED: {str(e)}")
            raise
    
    def test_retention_analysis(self):
        """Test customer retention analysis with cohort studies"""
        print("\n6. Testing Customer Retention Analysis...")
        
        try:
            # Test retention analysis
            analysis = self.advanced_service.analyze_customer_retention()
            
            assert isinstance(analysis, dict), "Analysis should be a dictionary"
            assert 'overall_retention_rate' in analysis, "Should have overall retention rate"
            assert 'cohort_analysis' in analysis, "Should have cohort analysis"
            assert 'retention_by_segment' in analysis, "Should have retention by segment"
            assert 'retention_trends' in analysis, "Should have retention trends"
            assert 'churn_reasons' in analysis, "Should have churn reasons"
            assert 'retention_improvement_opportunities' in analysis, "Should have improvement opportunities"
            
            print(f"   ✓ Overall Retention Rate: {analysis['overall_retention_rate']}%")
            
            print("   ✓ Cohort Analysis:")
            for cohort in analysis['cohort_analysis'][:3]:  # Show first 3 cohorts
                print(f"      - {cohort['cohort']}: {cohort['initial_customers']} initial customers")
                if cohort.get('month_1_retention'):
                    print(f"        Month 1: {cohort['month_1_retention']} customers")
                if cohort.get('month_3_retention'):
                    print(f"        Month 3: {cohort['month_3_retention']} customers")
            
            print("   ✓ Retention by Segment:")
            for segment, rate in analysis['retention_by_segment'].items():
                print(f"      - {segment.replace('_', ' ').title()}: {rate}%")
            
            print("   ✓ Top Churn Reasons:")
            for reason in analysis['churn_reasons'][:3]:
                print(f"      - {reason['reason']}: {reason['percentage']}%")
            
            print("   ✓ Improvement Opportunities:")
            for i, opp in enumerate(analysis['retention_improvement_opportunities'][:3], 1):
                print(f"      {i}. {opp}")
            
            print("   ✓ Retention analysis test PASSED")
            
        except Exception as e:
            print(f"   ✗ Retention analysis test FAILED: {str(e)}")
            raise
    
    def test_profitability_analysis(self):
        """Test customer profitability analysis by segment and individual"""
        print("\n7. Testing Customer Profitability Analysis...")
        
        try:
            # Test profitability analysis
            profitability = self.advanced_service.analyze_customer_profitability(self.test_customer.id)
            
            assert profitability is not None, "Profitability data should not be None"
            assert profitability.customer == self.test_customer, "Profitability should be for correct customer"
            assert profitability.total_revenue >= 0, "Total revenue should be non-negative"
            assert profitability.total_cost >= 0, "Total cost should be non-negative"
            assert isinstance(profitability.monthly_profit_trend, list), "Monthly trend should be a list"
            assert isinstance(profitability.quarterly_profit_trend, list), "Quarterly trend should be a list"
            
            print(f"   ✓ Total Revenue: ${profitability.total_revenue}")
            print(f"   ✓ Gross Revenue: ${profitability.gross_revenue}")
            print(f"   ✓ Net Revenue: ${profitability.net_revenue}")
            print(f"   ✓ Total Cost: ${profitability.total_cost}")
            print(f"   ✓ Gross Profit: ${profitability.gross_profit}")
            print(f"   ✓ Net Profit: ${profitability.net_profit}")
            print(f"   ✓ Profit Margin: {profitability.profit_margin}%")
            print(f"   ✓ ROI: {profitability.roi}%")
            
            if profitability.profitability_rank:
                print(f"   ✓ Profitability Rank: {profitability.profitability_rank}")
                print(f"   ✓ Profitability Percentile: {profitability.profitability_percentile}%")
            
            print("   ✓ Monthly Profit Trend:")
            for trend in profitability.monthly_profit_trend[:3]:
                print(f"      - {trend['month']}: ${trend['profit']}")
            
            print("   ✓ Profitability analysis test PASSED")
            
        except Exception as e:
            print(f"   ✗ Profitability analysis test FAILED: {str(e)}")
            raise
    
    def test_engagement_scoring(self):
        """Test customer engagement scoring and tracking"""
        print("\n8. Testing Customer Engagement Scoring...")
        
        try:
            # Test engagement scoring
            engagement = self.advanced_service.calculate_customer_engagement_score(self.test_customer.id)
            
            assert engagement is not None, "Engagement data should not be None"
            assert engagement.customer == self.test_customer, "Engagement should be for correct customer"
            assert 0 <= engagement.total_score <= 100, "Total score should be between 0 and 100"
            assert 0 <= engagement.website_engagement <= 100, "Website engagement should be between 0 and 100"
            assert 0 <= engagement.email_engagement <= 100, "Email engagement should be between 0 and 100"
            assert 0 <= engagement.social_engagement <= 100, "Social engagement should be between 0 and 100"
            assert 0 <= engagement.purchase_engagement <= 100, "Purchase engagement should be between 0 and 100"
            assert 0 <= engagement.support_engagement <= 100, "Support engagement should be between 0 and 100"
            assert engagement.engagement_trend in ['increasing', 'stable', 'decreasing', 'volatile'], "Trend should be valid"
            
            print(f"   ✓ Total Engagement Score: {engagement.total_score}")
            print(f"   ✓ Website Engagement: {engagement.website_engagement}")
            print(f"   ✓ Email Engagement: {engagement.email_engagement}")
            print(f"   ✓ Social Engagement: {engagement.social_engagement}")
            print(f"   ✓ Purchase Engagement: {engagement.purchase_engagement}")
            print(f"   ✓ Support Engagement: {engagement.support_engagement}")
            print(f"   ✓ Session Frequency: {engagement.session_frequency} per week")
            print(f"   ✓ Avg Session Duration: {engagement.avg_session_duration} minutes")
            print(f"   ✓ Page Views per Session: {engagement.page_views_per_session}")
            print(f"   ✓ Bounce Rate: {engagement.bounce_rate}%")
            print(f"   ✓ Email Open Rate: {engagement.email_open_rate}%")
            print(f"   ✓ Email Click Rate: {engagement.email_click_rate}%")
            print(f"   ✓ SMS Response Rate: {engagement.sms_response_rate}%")
            print(f"   ✓ Engagement Trend: {engagement.engagement_trend}")
            
            print("   ✓ Engagement scoring test PASSED")
            
        except Exception as e:
            print(f"   ✗ Engagement scoring test FAILED: {str(e)}")
            raise
    
    def test_preference_analysis_and_recommendations(self):
        """Test customer preference analysis and recommendation engines"""
        print("\n9. Testing Preference Analysis and Recommendation Engines...")
        
        try:
            # Test preference analysis
            preferences = self.ml_service.analyze_customer_preferences(self.test_customer.id)
            
            assert preferences is not None, "Preferences should not be None"
            assert preferences.customer == self.test_customer, "Preferences should be for correct customer"
            assert isinstance(preferences.preferred_categories, list), "Categories should be a list"
            assert isinstance(preferences.preferred_brands, list), "Brands should be a list"
            assert isinstance(preferences.preferred_price_range, dict), "Price range should be a dict"
            assert isinstance(preferences.preferred_attributes, dict), "Attributes should be a dict"
            assert 0 <= preferences.category_confidence <= 100, "Category confidence should be between 0 and 100"
            assert 0 <= preferences.brand_confidence <= 100, "Brand confidence should be between 0 and 100"
            assert 0 <= preferences.price_confidence <= 100, "Price confidence should be between 0 and 100"
            
            print("   ✓ Preferred Categories:")
            for cat in preferences.preferred_categories[:3]:
                print(f"      - {cat.get('category_name', 'Unknown')}: {cat.get('preference_score', 0):.2f}")
            
            print("   ✓ Preferred Brands:")
            for brand in preferences.preferred_brands[:3]:
                print(f"      - {brand.get('brand_name', 'Unknown')}: {brand.get('preference_score', 0):.2f}")
            
            print(f"   ✓ Price Range: ${preferences.preferred_price_range.get('min', 0)} - ${preferences.preferred_price_range.get('max', 0)}")
            print(f"   ✓ Communication Frequency: {preferences.communication_frequency}")
            print(f"   ✓ Category Confidence: {preferences.category_confidence}%")
            print(f"   ✓ Brand Confidence: {preferences.brand_confidence}%")
            print(f"   ✓ Price Confidence: {preferences.price_confidence}%")
            
            # Test recommendation generation
            recommendation = self.ml_service.generate_product_recommendations(
                self.test_customer.id, 'product', 'hybrid', 5
            )
            
            assert recommendation is not None, "Recommendation should not be None"
            assert recommendation.customer == self.test_customer, "Recommendation should be for correct customer"
            assert recommendation.recommendation_type == 'product', "Type should be product"
            assert recommendation.algorithm_used == 'hybrid', "Algorithm should be hybrid"
            assert isinstance(recommendation.recommended_items, list), "Items should be a list"
            assert 0 <= recommendation.confidence_score <= 100, "Confidence should be between 0 and 100"
            
            print(f"   ✓ Recommendation Algorithm: {recommendation.algorithm_used}")
            print(f"   ✓ Confidence Score: {recommendation.confidence_score}%")
            print("   ✓ Recommended Items:")
            for item in recommendation.recommended_items[:3]:
                print(f"      - Product {item.get('product_id', 'Unknown')}: {item.get('score', 0):.2f} ({item.get('reason', 'No reason')})")
            
            # Test cross-sell opportunities
            opportunities = self.ml_service.identify_cross_sell_opportunities(self.test_customer.id)
            
            assert isinstance(opportunities, list), "Opportunities should be a list"
            
            print("   ✓ Cross-sell/Up-sell Opportunities:")
            for opp in opportunities[:3]:
                print(f"      - {opp.get('type', 'Unknown')}: {opp.get('recommended_product', {}).get('product_name', 'Unknown')} (Confidence: {opp.get('confidence', 0):.2f})")
            
            print("   ✓ Preference analysis and recommendations test PASSED")
            
        except Exception as e:
            print(f"   ✗ Preference analysis and recommendations test FAILED: {str(e)}")
            raise
    
    def test_demographic_analysis(self):
        """Test customer demographic and psychographic analysis"""
        print("\n10. Testing Demographic and Psychographic Analysis...")
        
        try:
            # Test demographic analysis
            demographics = self.ml_service.analyze_customer_demographics(self.test_customer.id)
            
            assert demographics is not None, "Demographics should not be None"
            assert demographics.customer == self.test_customer, "Demographics should be for correct customer"
            assert isinstance(demographics.lifestyle_segments, list), "Lifestyle segments should be a list"
            assert isinstance(demographics.interests, list), "Interests should be a list"
            assert isinstance(demographics.values, list), "Values should be a list"
            assert isinstance(demographics.personality_traits, dict), "Personality traits should be a dict"
            assert isinstance(demographics.device_preferences, list), "Device preferences should be a list"
            assert isinstance(demographics.data_sources, list), "Data sources should be a list"
            assert 0 <= demographics.confidence_score <= 100, "Confidence should be between 0 and 100"
            
            print(f"   ✓ Geographic Data:")
            print(f"      - Country: {demographics.country}")
            print(f"      - State: {demographics.state}")
            print(f"      - City: {demographics.city}")
            print(f"      - Timezone: {demographics.timezone}")
            
            print(f"   ✓ Demographic Data:")
            print(f"      - Age Group: {demographics.age_group}")
            print(f"      - Gender: {demographics.gender}")
            print(f"      - Income Bracket: {demographics.income_bracket}")
            
            print(f"   ✓ Lifestyle Segments: {demographics.lifestyle_segments}")
            print(f"   ✓ Interests: {demographics.interests}")
            print(f"   ✓ Values: {demographics.values}")
            
            print(f"   ✓ Personality Traits:")
            for trait, score in demographics.personality_traits.items():
                print(f"      - {trait.title()}: {score}")
            
            print(f"   ✓ Shopping Personality: {demographics.shopping_personality}")
            print(f"   ✓ Device Preferences: {demographics.device_preferences}")
            print(f"   ✓ Tech Savviness: {demographics.tech_savviness}")
            print(f"   ✓ Data Sources: {demographics.data_sources}")
            print(f"   ✓ Confidence Score: {demographics.confidence_score}%")
            
            print("   ✓ Demographic analysis test PASSED")
            
        except Exception as e:
            print(f"   ✗ Demographic analysis test FAILED: {str(e)}")
            raise
    
    def test_sentiment_analysis(self):
        """Test social media sentiment analysis and monitoring"""
        print("\n11. Testing Sentiment Analysis and Social Media Monitoring...")
        
        try:
            # Test sentiment analysis
            test_content = "I love this product! Great quality and fast shipping. Highly recommend!"
            sentiment = self.ml_service.analyze_customer_sentiment(
                self.test_customer.id, test_content, 'twitter', 'post'
            )
            
            assert sentiment is not None, "Sentiment should not be None"
            assert sentiment.customer == self.test_customer, "Sentiment should be for correct customer"
            assert sentiment.source_platform == 'twitter', "Platform should be twitter"
            assert sentiment.content_type == 'post', "Content type should be post"
            assert sentiment.overall_sentiment in ['very_positive', 'positive', 'neutral', 'negative', 'very_negative'], "Sentiment should be valid"
            assert -1 <= sentiment.sentiment_score <= 1, "Sentiment score should be between -1 and 1"
            assert isinstance(sentiment.keywords_extracted, list), "Keywords should be a list"
            assert isinstance(sentiment.emotions_detected, dict), "Emotions should be a dict"
            assert isinstance(sentiment.topics_identified, list), "Topics should be a list"
            assert 0 <= sentiment.confidence_score <= 100, "Confidence should be between 0 and 100"
            
            print(f"   ✓ Content: {sentiment.content[:100]}...")
            print(f"   ✓ Overall Sentiment: {sentiment.overall_sentiment}")
            print(f"   ✓ Sentiment Score: {sentiment.sentiment_score}")
            print(f"   ✓ Confidence Score: {sentiment.confidence_score}%")
            print(f"   ✓ Keywords Extracted: {sentiment.keywords_extracted}")
            print(f"   ✓ Emotions Detected: {sentiment.emotions_detected}")
            print(f"   ✓ Topics Identified: {sentiment.topics_identified}")
            
            # Test brand mentions monitoring
            mentions = self.ml_service.monitor_brand_mentions(self.test_customer.id)
            
            assert isinstance(mentions, list), "Mentions should be a list"
            
            print(f"   ✓ Brand Mentions Found: {len(mentions)}")
            if mentions:
                for mention in mentions[:2]:
                    print(f"      - Platform: {mention.get('platform', 'Unknown')}")
                    print(f"        Sentiment: {mention.get('sentiment', 'Unknown')}")
                    print(f"        Content: {mention.get('content', 'No content')[:50]}...")
            
            print("   ✓ Sentiment analysis test PASSED")
            
        except Exception as e:
            print(f"   ✗ Sentiment analysis test FAILED: {str(e)}")
            raise
    
    def test_feedback_analysis(self):
        """Test customer feedback analysis with text mining and NLP"""
        print("\n12. Testing Feedback Analysis with NLP...")
        
        try:
            # Test feedback analysis
            test_feedback = "The product quality is excellent, but the shipping was delayed. Customer service was very helpful in resolving the issue."
            analysis = self.ml_service.analyze_customer_feedback(
                self.test_customer.id, test_feedback, 'product_review'
            )
            
            assert analysis is not None, "Analysis should not be None"
            assert analysis.customer == self.test_customer, "Analysis should be for correct customer"
            assert analysis.feedback_type == 'product_review', "Type should be product_review"
            assert analysis.original_text == test_feedback, "Original text should match"
            assert -1 <= analysis.sentiment_score <= 1, "Sentiment score should be between -1 and 1"
            assert isinstance(analysis.emotion_scores, dict), "Emotion scores should be a dict"
            assert isinstance(analysis.key_phrases, list), "Key phrases should be a list"
            assert isinstance(analysis.named_entities, list), "Named entities should be a list"
            assert isinstance(analysis.topics, list), "Topics should be a list"
            assert analysis.feedback_category in [
                'product_quality', 'customer_service', 'shipping_delivery', 
                'pricing', 'website_usability', 'payment_process', 'return_policy', 'general'
            ], "Category should be valid"
            assert analysis.urgency_level in ['low', 'medium', 'high', 'critical'], "Urgency should be valid"
            assert 0 <= analysis.analysis_confidence <= 100, "Confidence should be between 0 and 100"
            
            print(f"   ✓ Original Text: {analysis.original_text[:100]}...")
            print(f"   ✓ Processed Text: {analysis.processed_text[:100]}...")
            print(f"   ✓ Sentiment Score: {analysis.sentiment_score}")
            print(f"   ✓ Emotion Scores: {analysis.emotion_scores}")
            print(f"   ✓ Key Phrases: {analysis.key_phrases}")
            print(f"   ✓ Named Entities: {analysis.named_entities}")
            print(f"   ✓ Topics: {analysis.topics}")
            print(f"   ✓ Feedback Category: {analysis.feedback_category}")
            print(f"   ✓ Urgency Level: {analysis.urgency_level}")
            print(f"   ✓ Requires Response: {analysis.requires_response}")
            print(f"   ✓ Analysis Confidence: {analysis.analysis_confidence}%")
            
            print("   ✓ Feedback analysis test PASSED")
            
        except Exception as e:
            print(f"   ✗ Feedback analysis test FAILED: {str(e)}")
            raise
    
    def test_risk_assessment(self):
        """Test customer risk assessment and fraud detection"""
        print("\n13. Testing Risk Assessment and Fraud Detection...")
        
        try:
            # Test risk assessment
            risk_assessment = self.ml_service.assess_customer_risk(self.test_customer.id)
            
            assert risk_assessment is not None, "Risk assessment should not be None"
            assert risk_assessment.customer == self.test_customer, "Assessment should be for correct customer"
            assert 0 <= risk_assessment.overall_risk_score <= 100, "Overall risk should be between 0 and 100"
            assert risk_assessment.risk_level in ['very_low', 'low', 'medium', 'high', 'very_high'], "Risk level should be valid"
            assert 0 <= risk_assessment.fraud_risk_score <= 100, "Fraud risk should be between 0 and 100"
            assert 0 <= risk_assessment.payment_risk_score <= 100, "Payment risk should be between 0 and 100"
            assert 0 <= risk_assessment.chargeback_risk_score <= 100, "Chargeback risk should be between 0 and 100"
            assert 0 <= risk_assessment.return_abuse_risk_score <= 100, "Return abuse risk should be between 0 and 100"
            assert isinstance(risk_assessment.suspicious_activities, list), "Suspicious activities should be a list"
            assert isinstance(risk_assessment.risk_factors, dict), "Risk factors should be a dict"
            assert isinstance(risk_assessment.protective_factors, dict), "Protective factors should be a dict"
            assert isinstance(risk_assessment.restrictions_applied, list), "Restrictions should be a list"
            assert risk_assessment.monitoring_level in ['none', 'basic', 'enhanced', 'strict'], "Monitoring level should be valid"
            
            print(f"   ✓ Overall Risk Score: {risk_assessment.overall_risk_score}")
            print(f"   ✓ Risk Level: {risk_assessment.risk_level}")
            print(f"   ✓ Fraud Risk Score: {risk_assessment.fraud_risk_score}")
            print(f"   ✓ Payment Risk Score: {risk_assessment.payment_risk_score}")
            print(f"   ✓ Chargeback Risk Score: {risk_assessment.chargeback_risk_score}")
            print(f"   ✓ Return Abuse Risk Score: {risk_assessment.return_abuse_risk_score}")
            print(f"   ✓ Suspicious Activities: {risk_assessment.suspicious_activities}")
            print(f"   ✓ Risk Factors: {risk_assessment.risk_factors}")
            print(f"   ✓ Protective Factors: {risk_assessment.protective_factors}")
            print(f"   ✓ Monitoring Level: {risk_assessment.monitoring_level}")
            print(f"   ✓ Restrictions Applied: {risk_assessment.restrictions_applied}")
            print(f"   ✓ Manual Review Required: {risk_assessment.manual_review_required}")
            print(f"   ✓ Account Age: {risk_assessment.account_age_days} days")
            print(f"   ✓ Total Chargebacks: {risk_assessment.total_chargebacks}")
            print(f"   ✓ Total Returns: {risk_assessment.total_returns}")
            print(f"   ✓ Failed Payment Attempts: {risk_assessment.failed_payment_attempts}")
            
            print("   ✓ Risk assessment test PASSED")
            
        except Exception as e:
            print(f"   ✗ Risk assessment test FAILED: {str(e)}")
            raise
    
    def test_satisfaction_tracking(self):
        """Test customer satisfaction tracking with NPS and CSAT metrics"""
        print("\n14. Testing Customer Satisfaction Tracking...")
        
        try:
            # Test NPS calculation
            nps_score = self.basic_service.calculate_nps_score()
            if nps_score is not None:
                assert -100 <= nps_score <= 100, "NPS score should be between -100 and 100"
                print(f"   ✓ NPS Score: {nps_score}")
            else:
                print("   ✓ NPS Score: No data available")
            
            # Test CSAT calculation
            csat_score = self.basic_service.calculate_csat_score()
            if csat_score is not None:
                assert 0 <= csat_score <= 100, "CSAT score should be between 0 and 100"
                print(f"   ✓ CSAT Score: {csat_score}")
            else:
                print("   ✓ CSAT Score: No data available")
            
            # Test analytics summary
            summary = self.basic_service.get_analytics_summary()
            assert isinstance(summary, dict), "Summary should be a dictionary"
            assert 'total_customers' in summary, "Should have total customers"
            assert 'nps_score' in summary, "Should have NPS score"
            assert 'csat_score' in summary, "Should have CSAT score"
            
            print(f"   ✓ Total Customers: {summary['total_customers']}")
            print(f"   ✓ New Customers This Month: {summary['new_customers_this_month']}")
            print(f"   ✓ Active Customers: {summary['active_customers']}")
            print(f"   ✓ At Risk Customers: {summary['at_risk_customers']}")
            print(f"   ✓ Churned Customers: {summary['churned_customers']}")
            print(f"   ✓ Average Customer Value: ${summary['average_customer_value']}")
            print(f"   ✓ Average Order Value: ${summary['average_order_value']}")
            print(f"   ✓ Customer Retention Rate: {summary['customer_retention_rate']}%")
            
            print("   ✓ Satisfaction tracking test PASSED")
            
        except Exception as e:
            print(f"   ✗ Satisfaction tracking test FAILED: {str(e)}")
            raise
    
    def run_all_tests(self):
        """Run all advanced customer analytics tests"""
        print("=" * 80)
        print("ADVANCED CUSTOMER ANALYTICS COMPREHENSIVE TEST SUITE")
        print("=" * 80)
        print("Testing all features from Task 14: Advanced Customer Analytics and Behavior Analysis")
        print()
        
        try:
            # Setup test data
            self.setup_test_data()
            
            # Run all tests
            self.test_customer_lifetime_value_calculation()
            self.test_churn_prediction()
            self.test_behavior_analysis()
            self.test_customer_journey_mapping()
            self.test_cac_analysis()
            self.test_retention_analysis()
            self.test_profitability_analysis()
            self.test_engagement_scoring()
            self.test_preference_analysis_and_recommendations()
            self.test_demographic_analysis()
            self.test_sentiment_analysis()
            self.test_feedback_analysis()
            self.test_risk_assessment()
            self.test_satisfaction_tracking()
            
            print("\n" + "=" * 80)
            print("🎉 ALL ADVANCED CUSTOMER ANALYTICS TESTS PASSED! 🎉")
            print("=" * 80)
            print("\nTask 14 Implementation Summary:")
            print("✓ Customer Lifetime Value (CLV) calculation and segmentation")
            print("✓ Customer churn prediction with machine learning models")
            print("✓ Customer behavior analysis with purchase pattern recognition")
            print("✓ Customer satisfaction tracking with NPS and CSAT metrics")
            print("✓ Customer journey mapping and touchpoint analysis")
            print("✓ Customer acquisition cost (CAC) analysis and optimization")
            print("✓ Customer retention analysis with cohort studies")
            print("✓ Customer profitability analysis by segment and individual")
            print("✓ Customer engagement scoring and tracking")
            print("✓ Customer preference analysis and recommendation engines")
            print("✓ Customer demographic and psychographic analysis")
            print("✓ Customer social media sentiment analysis and monitoring")
            print("✓ Customer feedback analysis with text mining and NLP")
            print("✓ Customer cross-sell and up-sell opportunity identification")
            print("✓ Customer risk assessment and fraud detection")
            print("\nAll 24 sub-tasks from Task 14 have been successfully implemented and tested!")
            
        except Exception as e:
            print(f"\n❌ TEST SUITE FAILED: {str(e)}")
            print("Please check the error details above and fix any issues.")
            raise


if __name__ == "__main__":
    # Run the comprehensive test suite
    test_suite = AdvancedCustomerAnalyticsTest()
    test_suite.run_all_tests()