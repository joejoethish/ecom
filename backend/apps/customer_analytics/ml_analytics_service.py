"""
Machine Learning Analytics Service
Implements ML-based customer analytics including recommendation engines,
sentiment analysis, and predictive modeling.
"""

import re
import json
from typing import Dict, List, Any, Tuple, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Count, Avg, Sum, Q, F

from .models import (
    CustomerPreferenceAnalysis,
    CustomerDemographicAnalysis,
    CustomerSentimentAnalysis,
    CustomerFeedbackAnalysis,
    CustomerRiskAssessment,
    CustomerRecommendation,
    CustomerBehaviorEvent
)

User = get_user_model()


class MLCustomerAnalyticsService:
    """Machine Learning-based customer analytics service"""
    
    def __init__(self):
        # In production, these would be actual ML models
        self.sentiment_model = None
        self.recommendation_model = None
        self.risk_model = None
    
    # ============ Preference Analysis and Recommendation Engine ============
    
    def analyze_customer_preferences(self, customer_id: int) -> CustomerPreferenceAnalysis:
        """Analyze customer preferences using collaborative and content-based filtering"""
        try:
            customer = User.objects.get(id=customer_id)
            
            # Get or create preference record
            preferences, created = CustomerPreferenceAnalysis.objects.get_or_create(
                customer=customer,
                defaults={}
            )
            
            # Analyze product preferences
            product_preferences = self._analyze_product_preferences(customer_id)
            shopping_preferences = self._analyze_shopping_behavior_preferences(customer_id)
            communication_preferences = self._analyze_communication_preferences(customer_id)
            
            # Generate recommendation engine data
            collaborative_data = self._generate_collaborative_filtering_data(customer_id)
            content_based_data = self._generate_content_based_data(customer_id)
            hybrid_data = self._generate_hybrid_model_data(customer_id)
            
            # Update preferences record
            preferences.preferred_categories = product_preferences['categories']
            preferences.preferred_brands = product_preferences['brands']
            preferences.preferred_price_range = product_preferences['price_range']
            preferences.preferred_attributes = product_preferences['attributes']
            preferences.preferred_shopping_times = shopping_preferences['times']
            preferences.preferred_channels = shopping_preferences['channels']
            preferences.preferred_payment_methods = shopping_preferences['payment_methods']
            preferences.preferred_shipping_methods = shopping_preferences['shipping_methods']
            preferences.communication_frequency = communication_preferences['frequency']
            preferences.preferred_communication_channels = communication_preferences['channels']
            preferences.collaborative_filtering_data = collaborative_data
            preferences.content_based_data = content_based_data
            preferences.hybrid_model_data = hybrid_data
            preferences.category_confidence = self._calculate_preference_confidence('category', customer_id)
            preferences.brand_confidence = self._calculate_preference_confidence('brand', customer_id)
            preferences.price_confidence = self._calculate_preference_confidence('price', customer_id)
            preferences.save()
            
            return preferences
            
        except Exception as e:
            raise Exception(f"Error analyzing preferences for customer {customer_id}: {str(e)}")
    
    def generate_product_recommendations(self, customer_id: int, 
                                       recommendation_type: str = 'product',
                                       algorithm: str = 'hybrid',
                                       limit: int = 10) -> CustomerRecommendation:
        """Generate product recommendations using ML algorithms"""
        try:
            customer = User.objects.get(id=customer_id)
            
            # Get customer preferences
            try:
                preferences = CustomerPreferenceAnalysis.objects.get(customer=customer)
            except CustomerPreferenceAnalysis.DoesNotExist:
                preferences = self.analyze_customer_preferences(customer_id)
            
            # Generate recommendations based on algorithm
            if algorithm == 'collaborative':
                recommendations = self._collaborative_filtering_recommendations(customer_id, limit)
            elif algorithm == 'content_based':
                recommendations = self._content_based_recommendations(customer_id, limit)
            elif algorithm == 'hybrid':
                recommendations = self._hybrid_recommendations(customer_id, limit)
            else:
                recommendations = self._popularity_based_recommendations(limit)
            
            # Calculate confidence score
            confidence_score = self._calculate_recommendation_confidence(
                customer_id, recommendations, algorithm
            )
            
            # Create recommendation record
            recommendation = CustomerRecommendation.objects.create(
                customer=customer,
                recommendation_type=recommendation_type,
                recommended_items=recommendations,
                confidence_score=confidence_score,
                algorithm_used=algorithm,
                expires_at=timezone.now() + timedelta(days=7)
            )
            
            return recommendation
            
        except Exception as e:
            raise Exception(f"Error generating recommendations for customer {customer_id}: {str(e)}")
    
    def identify_cross_sell_opportunities(self, customer_id: int) -> List[Dict]:
        """Identify cross-sell and up-sell opportunities"""
        try:
            # Analyze customer purchase history
            purchase_history = self._get_customer_purchase_history(customer_id)
            
            # Identify complementary products
            cross_sell_opportunities = []
            for purchased_item in purchase_history:
                complementary_products = self._find_complementary_products(purchased_item)
                for product in complementary_products:
                    cross_sell_opportunities.append({
                        'type': 'cross_sell',
                        'base_product': purchased_item,
                        'recommended_product': product,
                        'confidence': self._calculate_cross_sell_confidence(purchased_item, product),
                        'expected_revenue': product.get('price', 0)
                    })
            
            # Identify up-sell opportunities
            up_sell_opportunities = []
            for purchased_item in purchase_history:
                premium_alternatives = self._find_premium_alternatives(purchased_item)
                for product in premium_alternatives:
                    up_sell_opportunities.append({
                        'type': 'up_sell',
                        'base_product': purchased_item,
                        'recommended_product': product,
                        'confidence': self._calculate_up_sell_confidence(purchased_item, product),
                        'expected_revenue': product.get('price', 0) - purchased_item.get('price', 0)
                    })
            
            # Combine and rank opportunities
            all_opportunities = cross_sell_opportunities + up_sell_opportunities
            all_opportunities.sort(key=lambda x: x['confidence'] * x['expected_revenue'], reverse=True)
            
            return all_opportunities[:10]  # Return top 10 opportunities
            
        except Exception as e:
            raise Exception(f"Error identifying cross-sell opportunities for customer {customer_id}: {str(e)}")
    
    # ============ Demographic and Psychographic Analysis ============
    
    def analyze_customer_demographics(self, customer_id: int) -> CustomerDemographicAnalysis:
        """Analyze customer demographics and psychographics"""
        try:
            customer = User.objects.get(id=customer_id)
            
            # Get or create demographic record
            demographics, created = CustomerDemographicAnalysis.objects.get_or_create(
                customer=customer,
                defaults={}
            )
            
            # Analyze geographic data
            geographic_data = self._analyze_geographic_data(customer_id)
            
            # Infer demographic data from behavior
            demographic_data = self._infer_demographic_data(customer_id)
            
            # Analyze psychographic data
            psychographic_data = self._analyze_psychographic_data(customer_id)
            
            # Determine shopping personality
            shopping_personality = self._determine_shopping_personality(customer_id)
            
            # Analyze technology adoption
            tech_data = self._analyze_technology_adoption(customer_id)
            
            # Update demographics record
            demographics.country = geographic_data.get('country', '')
            demographics.state = geographic_data.get('state', '')
            demographics.city = geographic_data.get('city', '')
            demographics.postal_code = geographic_data.get('postal_code', '')
            demographics.timezone = geographic_data.get('timezone', '')
            demographics.age_group = demographic_data.get('age_group', '')
            demographics.gender = demographic_data.get('gender', '')
            demographics.income_bracket = demographic_data.get('income_bracket', '')
            demographics.lifestyle_segments = psychographic_data.get('lifestyle_segments', [])
            demographics.interests = psychographic_data.get('interests', [])
            demographics.values = psychographic_data.get('values', [])
            demographics.personality_traits = psychographic_data.get('personality_traits', {})
            demographics.shopping_personality = shopping_personality
            demographics.device_preferences = tech_data.get('device_preferences', [])
            demographics.tech_savviness = tech_data.get('tech_savviness', 'medium')
            demographics.data_sources = self._get_data_sources(customer_id)
            demographics.confidence_score = self._calculate_demographic_confidence(customer_id)
            demographics.save()
            
            return demographics
            
        except Exception as e:
            raise Exception(f"Error analyzing demographics for customer {customer_id}: {str(e)}")
    
    # ============ Sentiment Analysis and Social Media Monitoring ============
    
    def analyze_customer_sentiment(self, customer_id: int, content: str, 
                                 source_platform: str, content_type: str) -> CustomerSentimentAnalysis:
        """Analyze customer sentiment from social media and feedback"""
        try:
            customer = User.objects.get(id=customer_id)
            
            # Perform sentiment analysis
            sentiment_result = self._analyze_text_sentiment(content)
            
            # Extract keywords and topics
            keywords = self._extract_keywords(content)
            emotions = self._detect_emotions(content)
            topics = self._identify_topics(content)
            
            # Create sentiment analysis record
            sentiment_analysis = CustomerSentimentAnalysis.objects.create(
                customer=customer,
                overall_sentiment=sentiment_result['sentiment'],
                sentiment_score=sentiment_result['score'],
                source_platform=source_platform,
                content=content,
                content_type=content_type,
                confidence_score=sentiment_result['confidence'],
                keywords_extracted=keywords,
                emotions_detected=emotions,
                topics_identified=topics,
                content_date=timezone.now()
            )
            
            return sentiment_analysis
            
        except Exception as e:
            raise Exception(f"Error analyzing sentiment for customer {customer_id}: {str(e)}")
    
    def monitor_brand_mentions(self, customer_id: int = None) -> List[Dict]:
        """Monitor brand mentions and sentiment across social media"""
        try:
            # Get recent sentiment analyses
            query = CustomerSentimentAnalysis.objects.filter(
                analyzed_at__gte=timezone.now() - timedelta(days=7)
            )
            
            if customer_id:
                query = query.filter(customer_id=customer_id)
            
            mentions = []
            for analysis in query:
                mentions.append({
                    'customer_id': analysis.customer.id,
                    'customer_name': analysis.customer.get_full_name() or analysis.customer.username,
                    'platform': analysis.source_platform,
                    'sentiment': analysis.overall_sentiment,
                    'sentiment_score': float(analysis.sentiment_score),
                    'content': analysis.content[:200] + '...' if len(analysis.content) > 200 else analysis.content,
                    'date': analysis.content_date.isoformat(),
                    'engagement': {
                        'likes': analysis.likes,
                        'shares': analysis.shares,
                        'comments': analysis.comments,
                        'reach': analysis.reach
                    }
                })
            
            return mentions
            
        except Exception as e:
            raise Exception(f"Error monitoring brand mentions: {str(e)}")
    
    # ============ Feedback Analysis with NLP ============
    
    def analyze_customer_feedback(self, customer_id: int, feedback_text: str,
                                feedback_type: str, source_id: str = '') -> CustomerFeedbackAnalysis:
        """Analyze customer feedback using NLP techniques"""
        try:
            customer = User.objects.get(id=customer_id)
            
            # Process the text
            processed_text = self._preprocess_text(feedback_text)
            
            # Perform NLP analysis
            sentiment_score = self._analyze_text_sentiment(feedback_text)['score']
            emotion_scores = self._analyze_emotions(feedback_text)
            key_phrases = self._extract_key_phrases(feedback_text)
            named_entities = self._extract_named_entities(feedback_text)
            topics = self._perform_topic_modeling(feedback_text)
            
            # Classify feedback
            feedback_category = self._classify_feedback(feedback_text)
            urgency_level = self._determine_urgency(feedback_text, sentiment_score)
            
            # Determine if response is required
            requires_response = self._requires_response(feedback_text, sentiment_score, urgency_level)
            
            # Create feedback analysis record
            feedback_analysis = CustomerFeedbackAnalysis.objects.create(
                customer=customer,
                feedback_type=feedback_type,
                source_id=source_id,
                original_text=feedback_text,
                processed_text=processed_text,
                sentiment_score=sentiment_score,
                emotion_scores=emotion_scores,
                key_phrases=key_phrases,
                named_entities=named_entities,
                topics=topics,
                feedback_category=feedback_category,
                urgency_level=urgency_level,
                requires_response=requires_response,
                analysis_confidence=self._calculate_analysis_confidence(feedback_text),
                feedback_date=timezone.now()
            )
            
            return feedback_analysis
            
        except Exception as e:
            raise Exception(f"Error analyzing feedback for customer {customer_id}: {str(e)}")
    
    # ============ Risk Assessment and Fraud Detection ============
    
    def assess_customer_risk(self, customer_id: int) -> CustomerRiskAssessment:
        """Assess customer risk including fraud detection"""
        try:
            customer = User.objects.get(id=customer_id)
            
            # Get or create risk assessment record
            risk_assessment, created = CustomerRiskAssessment.objects.get_or_create(
                customer=customer,
                defaults={}
            )
            
            # Calculate risk component scores
            fraud_risk = self._calculate_fraud_risk(customer_id)
            payment_risk = self._calculate_payment_risk(customer_id)
            chargeback_risk = self._calculate_chargeback_risk(customer_id)
            return_abuse_risk = self._calculate_return_abuse_risk(customer_id)
            
            # Calculate overall risk score
            overall_risk = (fraud_risk + payment_risk + chargeback_risk + return_abuse_risk) / 4
            
            # Determine risk level
            if overall_risk >= 80:
                risk_level = 'very_high'
            elif overall_risk >= 60:
                risk_level = 'high'
            elif overall_risk >= 40:
                risk_level = 'medium'
            elif overall_risk >= 20:
                risk_level = 'low'
            else:
                risk_level = 'very_low'
            
            # Analyze behavioral patterns
            behavioral_analysis = self._analyze_risk_behavioral_patterns(customer_id)
            
            # Get historical risk data
            historical_data = self._get_historical_risk_data(customer_id)
            
            # Determine monitoring level and restrictions
            monitoring_level = self._determine_monitoring_level(overall_risk)
            restrictions = self._determine_restrictions(overall_risk, behavioral_analysis)
            
            # Update risk assessment record
            risk_assessment.overall_risk_score = overall_risk
            risk_assessment.risk_level = risk_level
            risk_assessment.fraud_risk_score = fraud_risk
            risk_assessment.payment_risk_score = payment_risk
            risk_assessment.chargeback_risk_score = chargeback_risk
            risk_assessment.return_abuse_risk_score = return_abuse_risk
            risk_assessment.suspicious_activities = behavioral_analysis['suspicious_activities']
            risk_assessment.risk_factors = behavioral_analysis['risk_factors']
            risk_assessment.protective_factors = behavioral_analysis['protective_factors']
            risk_assessment.unusual_purchase_patterns = behavioral_analysis['unusual_purchase_patterns']
            risk_assessment.velocity_violations = behavioral_analysis['velocity_violations']
            risk_assessment.geographic_anomalies = behavioral_analysis['geographic_anomalies']
            risk_assessment.device_fingerprint_changes = behavioral_analysis['device_fingerprint_changes']
            risk_assessment.total_chargebacks = historical_data['total_chargebacks']
            risk_assessment.total_returns = historical_data['total_returns']
            risk_assessment.failed_payment_attempts = historical_data['failed_payment_attempts']
            risk_assessment.account_age_days = historical_data['account_age_days']
            risk_assessment.monitoring_level = monitoring_level
            risk_assessment.restrictions_applied = restrictions
            risk_assessment.manual_review_required = overall_risk >= 70
            risk_assessment.next_assessment_due = timezone.now() + timedelta(days=30)
            risk_assessment.save()
            
            return risk_assessment
            
        except Exception as e:
            raise Exception(f"Error assessing risk for customer {customer_id}: {str(e)}")
    
    # ============ Helper Methods ============
    
    def _analyze_product_preferences(self, customer_id: int) -> Dict:
        """Analyze customer product preferences"""
        # Mock analysis - in production, analyze actual purchase history
        return {
            'categories': [
                {'category_id': 1, 'category_name': 'Electronics', 'preference_score': 0.85},
                {'category_id': 2, 'category_name': 'Books', 'preference_score': 0.72},
                {'category_id': 3, 'category_name': 'Clothing', 'preference_score': 0.68}
            ],
            'brands': [
                {'brand_id': 1, 'brand_name': 'Apple', 'preference_score': 0.90},
                {'brand_id': 2, 'brand_name': 'Nike', 'preference_score': 0.75},
                {'brand_id': 3, 'brand_name': 'Samsung', 'preference_score': 0.65}
            ],
            'price_range': {'min': 50, 'max': 500, 'preferred': 200},
            'attributes': {
                'quality': 0.95,
                'brand_reputation': 0.80,
                'price_value': 0.70,
                'innovation': 0.85
            }
        }
    
    def _analyze_shopping_behavior_preferences(self, customer_id: int) -> Dict:
        """Analyze shopping behavior preferences"""
        return {
            'times': [
                {'day': 'Monday', 'hour': 19, 'frequency': 0.3},
                {'day': 'Wednesday', 'hour': 14, 'frequency': 0.25},
                {'day': 'Saturday', 'hour': 11, 'frequency': 0.4}
            ],
            'channels': [
                {'channel': 'Mobile App', 'preference_score': 0.8},
                {'channel': 'Website', 'preference_score': 0.6},
                {'channel': 'Email', 'preference_score': 0.4}
            ],
            'payment_methods': [
                {'method': 'Credit Card', 'preference_score': 0.9},
                {'method': 'PayPal', 'preference_score': 0.6},
                {'method': 'Bank Transfer', 'preference_score': 0.3}
            ],
            'shipping_methods': [
                {'method': 'Express Delivery', 'preference_score': 0.8},
                {'method': 'Standard Delivery', 'preference_score': 0.6},
                {'method': 'Pickup', 'preference_score': 0.2}
            ]
        }
    
    def _analyze_communication_preferences(self, customer_id: int) -> Dict:
        """Analyze communication preferences"""
        return {
            'frequency': 'weekly',
            'channels': [
                {'channel': 'Email', 'preference_score': 0.9},
                {'channel': 'SMS', 'preference_score': 0.6},
                {'channel': 'Push Notification', 'preference_score': 0.7}
            ]
        }
    
    def _generate_collaborative_filtering_data(self, customer_id: int) -> Dict:
        """Generate collaborative filtering data"""
        return {
            'similar_customers': [101, 205, 308, 412, 567],
            'similarity_scores': [0.85, 0.78, 0.72, 0.69, 0.65],
            'common_preferences': ['Electronics', 'Premium brands', 'Fast shipping']
        }
    
    def _generate_content_based_data(self, customer_id: int) -> Dict:
        """Generate content-based filtering data"""
        return {
            'feature_weights': {
                'category': 0.3,
                'brand': 0.25,
                'price': 0.2,
                'rating': 0.15,
                'features': 0.1
            },
            'preferred_features': ['High quality', 'Latest technology', 'Good reviews']
        }
    
    def _generate_hybrid_model_data(self, customer_id: int) -> Dict:
        """Generate hybrid model data"""
        return {
            'collaborative_weight': 0.6,
            'content_based_weight': 0.4,
            'model_performance': 0.82
        }
    
    def _calculate_preference_confidence(self, preference_type: str, customer_id: int) -> Decimal:
        """Calculate confidence in preference analysis"""
        # Mock calculation based on data availability
        return Decimal('75.5')
    
    def _collaborative_filtering_recommendations(self, customer_id: int, limit: int) -> List[Dict]:
        """Generate collaborative filtering recommendations"""
        # Mock recommendations
        return [
            {'product_id': 101, 'score': 0.92, 'reason': 'Customers like you also bought'},
            {'product_id': 205, 'score': 0.88, 'reason': 'Popular among similar customers'},
            {'product_id': 308, 'score': 0.85, 'reason': 'Highly rated by similar users'}
        ][:limit]
    
    def _content_based_recommendations(self, customer_id: int, limit: int) -> List[Dict]:
        """Generate content-based recommendations"""
        # Mock recommendations
        return [
            {'product_id': 401, 'score': 0.90, 'reason': 'Matches your preferences'},
            {'product_id': 502, 'score': 0.87, 'reason': 'Similar to your purchases'},
            {'product_id': 603, 'score': 0.84, 'reason': 'From your favorite brand'}
        ][:limit]
    
    def _hybrid_recommendations(self, customer_id: int, limit: int) -> List[Dict]:
        """Generate hybrid recommendations"""
        # Combine collaborative and content-based
        collab_recs = self._collaborative_filtering_recommendations(customer_id, limit//2)
        content_recs = self._content_based_recommendations(customer_id, limit//2)
        
        # Merge and re-score
        all_recs = collab_recs + content_recs
        return sorted(all_recs, key=lambda x: x['score'], reverse=True)[:limit]
    
    def _popularity_based_recommendations(self, limit: int) -> List[Dict]:
        """Generate popularity-based recommendations"""
        # Mock popular products
        return [
            {'product_id': 701, 'score': 0.95, 'reason': 'Trending now'},
            {'product_id': 802, 'score': 0.93, 'reason': 'Best seller'},
            {'product_id': 903, 'score': 0.91, 'reason': 'Highly rated'}
        ][:limit]
    
    def _calculate_recommendation_confidence(self, customer_id: int, 
                                          recommendations: List[Dict], 
                                          algorithm: str) -> Decimal:
        """Calculate confidence in recommendations"""
        # Mock confidence calculation
        base_confidence = {
            'collaborative': 0.85,
            'content_based': 0.78,
            'hybrid': 0.88,
            'popularity': 0.65
        }
        return Decimal(str(base_confidence.get(algorithm, 0.75)))
    
    def _get_customer_purchase_history(self, customer_id: int) -> List[Dict]:
        """Get customer purchase history"""
        # Mock purchase history
        return [
            {'product_id': 101, 'product_name': 'iPhone 13', 'category': 'Electronics', 'price': 999},
            {'product_id': 205, 'product_name': 'Nike Shoes', 'category': 'Footwear', 'price': 150},
            {'product_id': 308, 'product_name': 'MacBook Pro', 'category': 'Electronics', 'price': 2499}
        ]
    
    def _find_complementary_products(self, purchased_item: Dict) -> List[Dict]:
        """Find products that complement the purchased item"""
        # Mock complementary products
        if purchased_item['category'] == 'Electronics':
            return [
                {'product_id': 401, 'product_name': 'Phone Case', 'price': 25},
                {'product_id': 402, 'product_name': 'Screen Protector', 'price': 15},
                {'product_id': 403, 'product_name': 'Wireless Charger', 'price': 45}
            ]
        return []
    
    def _find_premium_alternatives(self, purchased_item: Dict) -> List[Dict]:
        """Find premium alternatives to the purchased item"""
        # Mock premium alternatives
        return [
            {
                'product_id': 501,
                'product_name': f"Premium {purchased_item['product_name']}",
                'price': purchased_item['price'] * 1.5
            }
        ]
    
    def _calculate_cross_sell_confidence(self, base_product: Dict, recommended_product: Dict) -> float:
        """Calculate confidence for cross-sell recommendation"""
        return 0.75  # Mock confidence
    
    def _calculate_up_sell_confidence(self, base_product: Dict, recommended_product: Dict) -> float:
        """Calculate confidence for up-sell recommendation"""
        return 0.68  # Mock confidence
    
    def _analyze_geographic_data(self, customer_id: int) -> Dict:
        """Analyze customer geographic data"""
        # Mock geographic analysis
        return {
            'country': 'United States',
            'state': 'California',
            'city': 'San Francisco',
            'postal_code': '94102',
            'timezone': 'America/Los_Angeles'
        }
    
    def _infer_demographic_data(self, customer_id: int) -> Dict:
        """Infer demographic data from behavior"""
        # Mock demographic inference
        return {
            'age_group': '25-34',
            'gender': 'M',
            'income_bracket': 'high'
        }
    
    def _analyze_psychographic_data(self, customer_id: int) -> Dict:
        """Analyze psychographic data"""
        # Mock psychographic analysis
        return {
            'lifestyle_segments': ['Tech Enthusiast', 'Early Adopter', 'Quality Seeker'],
            'interests': ['Technology', 'Innovation', 'Design', 'Productivity'],
            'values': ['Quality', 'Innovation', 'Efficiency', 'Status'],
            'personality_traits': {
                'openness': 0.85,
                'conscientiousness': 0.78,
                'extraversion': 0.65,
                'agreeableness': 0.72,
                'neuroticism': 0.35
            }
        }
    
    def _determine_shopping_personality(self, customer_id: int) -> str:
        """Determine customer shopping personality"""
        # Mock personality determination
        return 'quality_seeker'
    
    def _analyze_technology_adoption(self, customer_id: int) -> Dict:
        """Analyze technology adoption patterns"""
        # Mock tech analysis
        return {
            'device_preferences': ['Mobile', 'Desktop', 'Tablet'],
            'tech_savviness': 'high'
        }
    
    def _get_data_sources(self, customer_id: int) -> List[str]:
        """Get data sources for demographic analysis"""
        return ['Purchase History', 'Behavior Analysis', 'Survey Data', 'Social Media']
    
    def _calculate_demographic_confidence(self, customer_id: int) -> Decimal:
        """Calculate confidence in demographic analysis"""
        return Decimal('82.5')
    
    def _analyze_text_sentiment(self, text: str) -> Dict:
        """Analyze sentiment of text"""
        # Mock sentiment analysis
        # In production, use actual NLP models like VADER, TextBlob, or transformers
        positive_words = ['good', 'great', 'excellent', 'amazing', 'love', 'perfect']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'worst', 'horrible']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            sentiment = 'positive'
            score = Decimal('0.7')
        elif negative_count > positive_count:
            sentiment = 'negative'
            score = Decimal('-0.7')
        else:
            sentiment = 'neutral'
            score = Decimal('0.0')
        
        return {
            'sentiment': sentiment,
            'score': score,
            'confidence': Decimal('0.75')
        }
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text"""
        # Mock keyword extraction
        words = re.findall(r'\b\w+\b', text.lower())
        # Filter out common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        keywords = [word for word in words if word not in stop_words and len(word) > 3]
        return list(set(keywords))[:10]  # Return top 10 unique keywords
    
    def _detect_emotions(self, text: str) -> Dict:
        """Detect emotions in text"""
        # Mock emotion detection
        return {
            'joy': 0.3,
            'anger': 0.1,
            'fear': 0.05,
            'sadness': 0.15,
            'surprise': 0.2,
            'disgust': 0.05
        }
    
    def _identify_topics(self, text: str) -> List[str]:
        """Identify topics in text"""
        # Mock topic identification
        return ['Product Quality', 'Customer Service', 'Shipping']
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for analysis"""
        # Basic text preprocessing
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)  # Remove punctuation
        text = re.sub(r'\s+', ' ', text)  # Normalize whitespace
        return text.strip()
    
    def _analyze_emotions(self, text: str) -> Dict:
        """Analyze emotions in text"""
        return self._detect_emotions(text)
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from text"""
        # Mock key phrase extraction
        return ['great product', 'fast shipping', 'excellent service']
    
    def _extract_named_entities(self, text: str) -> List[Dict]:
        """Extract named entities from text"""
        # Mock named entity recognition
        return [
            {'entity': 'iPhone', 'type': 'PRODUCT'},
            {'entity': 'Apple', 'type': 'ORGANIZATION'},
            {'entity': 'San Francisco', 'type': 'LOCATION'}
        ]
    
    def _perform_topic_modeling(self, text: str) -> List[str]:
        """Perform topic modeling on text"""
        return self._identify_topics(text)
    
    def _classify_feedback(self, text: str) -> str:
        """Classify feedback into categories"""
        # Mock classification
        text_lower = text.lower()
        if any(word in text_lower for word in ['quality', 'defect', 'broken']):
            return 'product_quality'
        elif any(word in text_lower for word in ['service', 'support', 'help']):
            return 'customer_service'
        elif any(word in text_lower for word in ['shipping', 'delivery', 'arrived']):
            return 'shipping_delivery'
        elif any(word in text_lower for word in ['price', 'cost', 'expensive']):
            return 'pricing'
        else:
            return 'general'
    
    def _determine_urgency(self, text: str, sentiment_score: Decimal) -> str:
        """Determine urgency level of feedback"""
        text_lower = text.lower()
        urgent_words = ['urgent', 'emergency', 'immediately', 'asap', 'critical']
        
        if any(word in text_lower for word in urgent_words) or sentiment_score < -0.8:
            return 'critical'
        elif sentiment_score < -0.5:
            return 'high'
        elif sentiment_score < -0.2:
            return 'medium'
        else:
            return 'low'
    
    def _requires_response(self, text: str, sentiment_score: Decimal, urgency_level: str) -> bool:
        """Determine if feedback requires a response"""
        return urgency_level in ['critical', 'high'] or sentiment_score < -0.3
    
    def _calculate_analysis_confidence(self, text: str) -> Decimal:
        """Calculate confidence in analysis"""
        # Mock confidence based on text length and clarity
        confidence = min(Decimal('95.0'), Decimal(str(len(text) / 10 + 50)))
        return max(Decimal('50.0'), confidence)
    
    def _calculate_fraud_risk(self, customer_id: int) -> Decimal:
        """Calculate fraud risk score"""
        # Mock fraud risk calculation
        return Decimal('25.5')
    
    def _calculate_payment_risk(self, customer_id: int) -> Decimal:
        """Calculate payment risk score"""
        # Mock payment risk calculation
        return Decimal('15.2')
    
    def _calculate_chargeback_risk(self, customer_id: int) -> Decimal:
        """Calculate chargeback risk score"""
        # Mock chargeback risk calculation
        return Decimal('8.7')
    
    def _calculate_return_abuse_risk(self, customer_id: int) -> Decimal:
        """Calculate return abuse risk score"""
        # Mock return abuse risk calculation
        return Decimal('12.3')
    
    def _analyze_risk_behavioral_patterns(self, customer_id: int) -> Dict:
        """Analyze behavioral patterns for risk assessment"""
        # Mock behavioral analysis
        return {
            'suspicious_activities': ['Multiple failed login attempts', 'Unusual purchase pattern'],
            'risk_factors': {
                'new_account': 0.2,
                'high_value_orders': 0.3,
                'multiple_addresses': 0.1
            },
            'protective_factors': {
                'long_account_history': 0.4,
                'consistent_behavior': 0.3,
                'verified_identity': 0.5
            },
            'unusual_purchase_patterns': False,
            'velocity_violations': False,
            'geographic_anomalies': False,
            'device_fingerprint_changes': False
        }
    
    def _get_historical_risk_data(self, customer_id: int) -> Dict:
        """Get historical risk data for customer"""
        # Mock historical data
        return {
            'total_chargebacks': 0,
            'total_returns': 2,
            'failed_payment_attempts': 1,
            'account_age_days': 365
        }
    
    def _determine_monitoring_level(self, risk_score: Decimal) -> str:
        """Determine appropriate monitoring level"""
        if risk_score >= 70:
            return 'strict'
        elif risk_score >= 50:
            return 'enhanced'
        elif risk_score >= 30:
            return 'basic'
        else:
            return 'none'
    
    def _determine_restrictions(self, risk_score: Decimal, behavioral_analysis: Dict) -> List[str]:
        """Determine restrictions to apply"""
        restrictions = []
        
        if risk_score >= 80:
            restrictions.extend(['Manual review required', 'Payment verification'])
        elif risk_score >= 60:
            restrictions.append('Enhanced verification')
        elif risk_score >= 40:
            restrictions.append('Transaction monitoring')
        
        return restrictions