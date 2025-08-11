from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.ml_ai.services import *
from apps.ml_ai.models import MLModel
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Train ML models for various business functions'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--model-type',
            type=str,
            help='Specific model type to train',
            choices=[
                'demand_forecasting', 'customer_segmentation', 'fraud_detection',
                'recommendation', 'pricing_optimization', 'churn_prediction',
                'sentiment_analysis', 'anomaly_detection'
            ]
        )
        parser.add_argument(
            '--product-id',
            type=str,
            help='Product ID for product-specific models'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force retrain even if model exists'
        )
    
    def handle(self, *args, **options):
        model_type = options.get('model_type')
        product_id = options.get('product_id')
        force = options.get('force', False)
        
        if model_type:
            self.train_specific_model(model_type, product_id, force)
        else:
            self.train_all_models(force)
    
    def train_specific_model(self, model_type, product_id=None, force=False):
        """Train a specific model type"""
        self.stdout.write(f"Training {model_type} model...")
        
        try:
            if model_type == 'demand_forecasting':
                if not product_id:
                    self.stdout.write(
                        self.style.ERROR('Product ID required for demand forecasting')
                    )
                    return
                
                service = DemandForecastingService()
                model = service.train_model(product_id)
                
            elif model_type == 'customer_segmentation':
                service = CustomerSegmentationService()
                model = service.train_segmentation_model()
                
            elif model_type == 'fraud_detection':
                service = FraudDetectionService()
                model = service.train_fraud_model()
                
            elif model_type == 'recommendation':
                service = RecommendationService()
                model = service.train_recommendation_model()
                
            elif model_type == 'pricing_optimization':
                if not product_id:
                    self.stdout.write(
                        self.style.ERROR('Product ID required for pricing optimization')
                    )
                    return
                
                service = PricingOptimizationService()
                model = service.train_pricing_model(product_id)
                
            elif model_type == 'churn_prediction':
                service = ChurnPredictionService()
                model = service.train_churn_model()
                
            elif model_type == 'sentiment_analysis':
                service = SentimentAnalysisService()
                model = service.train_sentiment_model()
                
            elif model_type == 'anomaly_detection':
                service = AnomalyDetectionService()
                model = service.train_anomaly_model()
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully trained {model_type} model: {model.id}')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error training {model_type} model: {str(e)}')
            )
            logger.error(f"Error training {model_type} model: {str(e)}")
    
    def train_all_models(self, force=False):
        """Train all available models"""
        self.stdout.write("Training all ML models...")
        
        # Models that don't require specific parameters
        general_models = [
            'customer_segmentation',
            'fraud_detection',
            'recommendation',
            'churn_prediction',
            'sentiment_analysis',
            'anomaly_detection'
        ]
        
        for model_type in general_models:
            # Check if model already exists and is recent
            if not force:
                existing_model = MLModel.objects.filter(
                    model_type=model_type,
                    status='active',
                    last_trained__gte=timezone.now() - timezone.timedelta(days=7)
                ).first()
                
                if existing_model:
                    self.stdout.write(
                        f"Skipping {model_type} - recent model exists (use --force to retrain)"
                    )
                    continue
            
            self.train_specific_model(model_type, force=force)
        
        self.stdout.write(
            self.style.SUCCESS('Completed training all general ML models')
        )