from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from unittest.mock import patch, MagicMock
import json

from .models import *
from .services import *


class MLModelTestCase(TestCase):
    """Test cases for ML models"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
    
    def test_ml_model_creation(self):
        """Test ML model creation"""
        model = MLModel.objects.create(
            name='Test Model',
            model_type='demand_forecasting',
            description='Test model description',
            created_by=self.user
        )
        
        self.assertEqual(model.name, 'Test Model')
        self.assertEqual(model.model_type, 'demand_forecasting')
        self.assertEqual(model.status, 'training')
        self.assertEqual(model.created_by, self.user)
    
    def test_ml_model_str_representation(self):
        """Test ML model string representation"""
        model = MLModel.objects.create(
            name='Test Model',
            model_type='fraud_detection',
            created_by=self.user
        )
        
        expected_str = f"Test Model (fraud_detection)"
        self.assertEqual(str(model), expected_str)


class DemandForecastingServiceTestCase(TestCase):
    """Test cases for demand forecasting service"""
    
    def setUp(self):
        self.service = DemandForecastingService()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
    
    def test_prepare_data(self):
        """Test data preparation for demand forecasting"""
        df = self.service.prepare_data('PROD_001', 30)
        
        self.assertEqual(len(df), 30)
        self.assertIn('demand', df.columns)
        self.assertIn('product_id', df.columns)
        self.assertTrue(all(df['demand'] >= 0))
    
    @patch('apps.ml_ai.services.joblib.dump')
    def test_train_model(self, mock_dump):
        """Test model training"""
        mock_dump.return_value = None
        
        model = self.service.train_model('PROD_001')
        
        self.assertIsInstance(model, MLModel)
        self.assertEqual(model.model_type, 'demand_forecasting')
        self.assertIn('PROD_001', model.parameters.get('product_id', ''))
    
    @patch('apps.ml_ai.services.joblib.load')
    def test_predict_demand(self, mock_load):
        """Test demand prediction"""
        # Mock the loaded model data
        mock_model = MagicMock()
        mock_model.predict.return_value = [100]
        mock_scaler = MagicMock()
        mock_scaler.transform.return_value = [[1, 2, 3, 4]]
        
        mock_load.return_value = {
            'model': mock_model,
            'scaler': mock_scaler
        }
        
        predictions = self.service.predict_demand('PROD_001', 7)
        
        self.assertEqual(len(predictions), 7)
        self.assertIn('predicted_demand', predictions[0])
        self.assertIn('confidence_lower', predictions[0])
        self.assertIn('confidence_upper', predictions[0])


class CustomerSegmentationServiceTestCase(TestCase):
    """Test cases for customer segmentation service"""
    
    def setUp(self):
        self.service = CustomerSegmentationService()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
    
    def test_prepare_customer_data(self):
        """Test customer data preparation"""
        df = self.service.prepare_customer_data()
        
        self.assertEqual(len(df), 1000)
        self.assertIn('customer_id', df.columns)
        self.assertIn('total_orders', df.columns)
        self.assertIn('total_spent', df.columns)
    
    @patch('apps.ml_ai.services.joblib.dump')
    def test_train_segmentation_model(self, mock_dump):
        """Test segmentation model training"""
        mock_dump.return_value = None
        
        model = self.service.train_segmentation_model(5)
        
        self.assertIsInstance(model, MLModel)
        self.assertEqual(model.model_type, 'customer_segmentation')
        self.assertEqual(model.parameters.get('n_clusters'), 5)


class FraudDetectionServiceTestCase(TestCase):
    """Test cases for fraud detection service"""
    
    def setUp(self):
        self.service = FraudDetectionService()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
    
    def test_prepare_transaction_data(self):
        """Test transaction data preparation"""
        df = self.service.prepare_transaction_data()
        
        self.assertEqual(len(df), 10000)
        self.assertIn('transaction_id', df.columns)
        self.assertIn('amount', df.columns)
        self.assertIn('is_fraud', df.columns)
        
        # Check fraud ratio is approximately 10%
        fraud_ratio = df['is_fraud'].mean()
        self.assertAlmostEqual(fraud_ratio, 0.1, delta=0.05)
    
    @patch('apps.ml_ai.services.joblib.load')
    def test_detect_fraud(self, mock_load):
        """Test fraud detection"""
        # Mock the loaded model data
        mock_model = MagicMock()
        mock_model.predict.return_value = [-1]  # Anomaly
        mock_model.decision_function.return_value = [-0.5]
        mock_scaler = MagicMock()
        mock_scaler.transform.return_value = [[1, 2, 3, 4, 5, 6, 7]]
        
        mock_load.return_value = {
            'model': mock_model,
            'scaler': mock_scaler
        }
        
        transaction_data = {
            'amount': 1000,
            'hour_of_day': 2,
            'day_of_week': 3,
            'num_items': 5,
            'customer_age_days': 10,
            'payment_method': 0,
            'shipping_address_matches': False
        }
        
        result = self.service.detect_fraud(transaction_data)
        
        self.assertIn('is_fraud_risk', result)
        self.assertIn('risk_score', result)
        self.assertIn('risk_level', result)
        self.assertIn('risk_factors', result)


class MLAIAPITestCase(APITestCase):
    """Test cases for ML/AI API endpoints"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_ml_models_list(self):
        """Test ML models list endpoint"""
        # Create test model
        MLModel.objects.create(
            name='Test Model',
            model_type='demand_forecasting',
            created_by=self.user
        )
        
        url = reverse('mlmodel-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    @patch('apps.ml_ai.views.DemandForecastingService')
    def test_demand_forecasting_train(self, mock_service_class):
        """Test demand forecasting training endpoint"""
        mock_service = MagicMock()
        mock_model = MLModel.objects.create(
            name='Test Model',
            model_type='demand_forecasting',
            created_by=self.user
        )
        mock_service.train_model.return_value = mock_model
        mock_service_class.return_value = mock_service
        
        url = reverse('demand-forecasting-train')
        data = {'product_id': 'PROD_001'}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('model_id', response.data)
    
    @patch('apps.ml_ai.views.DemandForecastingService')
    def test_demand_forecasting_predict(self, mock_service_class):
        """Test demand forecasting prediction endpoint"""
        mock_service = MagicMock()
        mock_predictions = [
            {
                'date': '2024-01-01',
                'predicted_demand': 100,
                'confidence_lower': 80,
                'confidence_upper': 120
            }
        ]
        mock_service.predict_demand.return_value = mock_predictions
        mock_service_class.return_value = mock_service
        
        url = reverse('demand-forecasting-predict')
        data = {
            'product_id': 'PROD_001',
            'forecast_days': 1
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
    
    @patch('apps.ml_ai.views.FraudDetectionService')
    def test_fraud_detection(self, mock_service_class):
        """Test fraud detection endpoint"""
        mock_service = MagicMock()
        mock_result = {
            'is_fraud_risk': True,
            'risk_score': 0.8,
            'risk_level': 'high',
            'risk_factors': ['High amount', 'Unusual time'],
            'anomaly_score': -0.5
        }
        mock_service.detect_fraud.return_value = mock_result
        mock_service_class.return_value = mock_service
        
        url = reverse('fraud-detection-detect')
        data = {
            'transaction_id': 'TXN_001',
            'amount': 1000,
            'hour_of_day': 2,
            'day_of_week': 3,
            'num_items': 5,
            'customer_age_days': 10,
            'payment_method': 0,
            'shipping_address_matches': False
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['risk_level'], 'high')
    
    @patch('apps.ml_ai.views.AIInsightsService')
    def test_ai_insights_generation(self, mock_service_class):
        """Test AI insights generation endpoint"""
        mock_service = MagicMock()
        mock_insights = [
            {
                'type': 'sales_trend',
                'title': 'Test Insight',
                'description': 'Test description',
                'priority': 'high',
                'recommendations': ['Test recommendation'],
                'confidence': 0.85
            }
        ]
        mock_service.generate_all_insights.return_value = mock_insights
        mock_service_class.return_value = mock_service
        
        url = reverse('ai-insights-generate')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'Test Insight')


class AIInsightModelTestCase(TestCase):
    """Test cases for AI Insight model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass'
        )
        self.ml_model = MLModel.objects.create(
            name='Test Model',
            model_type='nlp',
            created_by=self.user
        )
    
    def test_ai_insight_creation(self):
        """Test AI insight creation"""
        insight = AIInsight.objects.create(
            title='Test Insight',
            insight_type='sales_trend',
            priority='high',
            description='Test description',
            recommendations=['Test recommendation'],
            potential_impact='High impact expected',
            confidence_level=0.85,
            model=self.ml_model
        )
        
        self.assertEqual(insight.title, 'Test Insight')
        self.assertEqual(insight.insight_type, 'sales_trend')
        self.assertEqual(insight.priority, 'high')
        self.assertEqual(insight.confidence_level, 0.85)
        self.assertFalse(insight.is_reviewed)
        self.assertFalse(insight.is_implemented)
    
    def test_ai_insight_ordering(self):
        """Test AI insight ordering by priority and creation date"""
        # Create insights with different priorities
        insight1 = AIInsight.objects.create(
            title='Low Priority',
            insight_type='sales_trend',
            priority='low',
            description='Low priority insight',
            confidence_level=0.5,
            model=self.ml_model
        )
        
        insight2 = AIInsight.objects.create(
            title='High Priority',
            insight_type='sales_trend',
            priority='high',
            description='High priority insight',
            confidence_level=0.9,
            model=self.ml_model
        )
        
        insights = list(AIInsight.objects.all())
        
        # High priority should come first
        self.assertEqual(insights[0], insight2)
        self.assertEqual(insights[1], insight1)