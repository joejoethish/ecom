from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.ml_ai.services import AIInsightsService
from apps.ml_ai.models import AIInsight, MLModel
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Generate AI-powered business insights'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--insight-type',
            type=str,
            help='Specific insight type to generate',
            choices=['sales', 'customer', 'operational', 'all']
        )
        parser.add_argument(
            '--priority',
            type=str,
            help='Minimum priority level to generate',
            choices=['low', 'medium', 'high', 'critical'],
            default='medium'
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Maximum number of insights to generate',
            default=10
        )
    
    def handle(self, *args, **options):
        insight_type = options.get('insight_type', 'all')
        priority = options.get('priority', 'medium')
        limit = options.get('limit', 10)
        
        self.stdout.write(f"Generating {insight_type} insights...")
        
        try:
            service = AIInsightsService()
            
            if insight_type == 'sales':
                insights = service.generate_sales_insights()
            elif insight_type == 'customer':
                insights = service.generate_customer_insights()
            elif insight_type == 'operational':
                insights = service.generate_operational_insights()
            else:
                insights = service.generate_all_insights()
            
            # Filter by priority
            priority_order = {'low': 1, 'medium': 2, 'high': 3, 'critical': 4}
            min_priority = priority_order.get(priority, 2)
            
            filtered_insights = [
                insight for insight in insights
                if priority_order.get(insight['priority'], 1) >= min_priority
            ]
            
            # Limit results
            filtered_insights = filtered_insights[:limit]
            
            # Save insights to database
            saved_count = 0
            for insight in filtered_insights:
                # Find or create a generic AI model for insights
                ml_model, created = MLModel.objects.get_or_create(
                    name="AI Business Insights",
                    model_type='nlp',
                    defaults={
                        'description': 'AI-powered business insights generator',
                        'status': 'active',
                        'created_by_id': 1
                    }
                )
                
                # Check if similar insight already exists recently
                existing_insight = AIInsight.objects.filter(
                    title=insight['title'],
                    created_at__gte=timezone.now() - timezone.timedelta(hours=24)
                ).first()
                
                if not existing_insight:
                    AIInsight.objects.create(
                        title=insight['title'],
                        insight_type=insight['type'],
                        priority=insight['priority'],
                        description=insight['description'],
                        recommendations=insight['recommendations'],
                        potential_impact=f"Confidence: {insight['confidence']:.2%}",
                        confidence_level=insight['confidence'],
                        model=ml_model
                    )
                    saved_count += 1
                    
                    self.stdout.write(
                        f"Generated insight: {insight['title']} ({insight['priority']})"
                    )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully generated {saved_count} new insights '
                    f'({len(filtered_insights)} total, {saved_count} new)'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error generating insights: {str(e)}')
            )
            logger.error(f"Error generating insights: {str(e)}")