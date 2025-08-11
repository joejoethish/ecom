# Management command for generating performance predictions
from django.core.management.base import BaseCommand
from django.utils import timezone
import json

from ...predictive_analytics import PerformancePredictiveAnalytics, AnomalyDetectionEngine
from ...models import PerformanceReport

class Command(BaseCommand):
    help = 'Generate performance predictions and anomaly detection'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--metric-type',
            type=str,
            default='response_time',
            help='Metric type to analyze'
        )
        parser.add_argument(
            '--days-back',
            type=int,
            default=30,
            help='Days of historical data to use'
        )
        parser.add_argument(
            '--train-anomaly-detector',
            action='store_true',
            help='Train anomaly detection model'
        )
        parser.add_argument(
            '--detect-anomalies',
            action='store_true',
            help='Detect anomalies in recent data'
        )
        parser.add_argument(
            '--generate-predictions',
            action='store_true',
            help='Generate performance predictions'
        )
        parser.add_argument(
            '--save-report',
            action='store_true',
            help='Save results as performance report'
        )
    
    def handle(self, *args, **options):
        metric_type = options['metric_type']
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting predictive analytics for {metric_type}')
        )
        
        results = {}
        
        try:
            if options['generate_predictions']:
                # Generate predictions
                analytics = PerformancePredictiveAnalytics()
                predictions = analytics.predict_performance_trends(
                    metric_type, 
                    options['days_back']
                )
                
                results['predictions'] = predictions
                
                if 'error' not in predictions:
                    self.stdout.write(
                        self.style.SUCCESS(f'Generated {len(predictions["predictions"])} predictions')
                    )
                    
                    # Display trend analysis
                    trend = predictions['trend_analysis']
                    self.stdout.write(f"Historical trend: {trend['historical_trend']['direction']}")
                    self.stdout.write(f"Predicted trend: {trend['predicted_trend']['direction']}")
                    
                    if predictions['anomalies']:
                        self.stdout.write(
                            self.style.WARNING(f'Predicted anomalies: {len(predictions["anomalies"])}')
                        )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'Prediction failed: {predictions["error"]}')
                    )
            
            if options['train_anomaly_detector']:
                # Train anomaly detector
                detector = AnomalyDetectionEngine()
                training_result = detector.train_anomaly_detector(
                    metric_type, 
                    options['days_back']
                )
                
                results['anomaly_training'] = training_result
                
                if 'error' not in training_result:
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Trained anomaly detector on {training_result["training_samples"]} samples'
                        )
                    )
                    self.stdout.write(
                        f'Anomaly rate: {training_result["anomaly_rate"]:.2%}'
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'Training failed: {training_result["error"]}')
                    )
            
            if options['detect_anomalies']:
                # Detect anomalies
                detector = AnomalyDetectionEngine()
                
                # Train first if not already trained
                if not detector.is_trained:
                    self.stdout.write('Training anomaly detector first...')
                    detector.train_anomaly_detector(metric_type, options['days_back'])
                
                anomaly_result = detector.detect_anomalies(metric_type, 24)
                results['anomaly_detection'] = anomaly_result
                
                if 'error' not in anomaly_result:
                    anomaly_count = anomaly_result['anomaly_count']
                    if anomaly_count > 0:
                        self.stdout.write(
                            self.style.WARNING(f'Detected {anomaly_count} anomalies in recent data')
                        )
                        
                        for anomaly in anomaly_result['anomalies'][:5]:  # Show first 5
                            self.stdout.write(
                                f"- {anomaly['timestamp']}: {anomaly['value']} "
                                f"(severity: {anomaly['severity']})"
                            )
                    else:
                        self.stdout.write(
                            self.style.SUCCESS('No anomalies detected in recent data')
                        )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'Anomaly detection failed: {anomaly_result["error"]}')
                    )
            
            if options['save_report'] and results:
                # Save results as performance report
                report = PerformanceReport.objects.create(
                    name=f'Predictive Analytics Report - {metric_type}',
                    report_type='custom',
                    date_range_start=timezone.now() - timezone.timedelta(days=options['days_back']),
                    date_range_end=timezone.now(),
                    metrics_included=[metric_type],
                    report_data=results,
                    insights=self._generate_insights(results),
                    recommendations=self._generate_recommendations(results)
                )
                
                self.stdout.write(
                    self.style.SUCCESS(f'Saved report with ID: {report.id}')
                )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Predictive analytics failed: {str(e)}')
            )
    
    def _generate_insights(self, results):
        """Generate insights from results"""
        insights = []
        
        if 'predictions' in results and 'error' not in results['predictions']:
            predictions = results['predictions']
            
            if predictions.get('anomalies'):
                insights.append(f"Predicted {len(predictions['anomalies'])} future anomalies")
            
            trend = predictions.get('trend_analysis', {})
            if trend.get('trend_change'):
                insights.append("Significant trend change detected between historical and predicted data")
        
        if 'anomaly_detection' in results and 'error' not in results['anomaly_detection']:
            anomaly_result = results['anomaly_detection']
            if anomaly_result['anomaly_count'] > 0:
                insights.append(f"Detected {anomaly_result['anomaly_count']} anomalies in recent data")
        
        return json.dumps(insights)
    
    def _generate_recommendations(self, results):
        """Generate recommendations from results"""
        recommendations = []
        
        if 'predictions' in results and 'error' not in results['predictions']:
            predictions = results['predictions']
            
            if predictions.get('anomalies'):
                recommendations.append({
                    'type': 'predictive_alert',
                    'priority': 'medium',
                    'message': 'Future anomalies predicted - consider proactive measures'
                })
            
            model_accuracy = predictions.get('model_accuracy', {})
            if model_accuracy.get('mape', 100) > 20:  # Mean Absolute Percentage Error > 20%
                recommendations.append({
                    'type': 'model_improvement',
                    'priority': 'low',
                    'message': 'Prediction model accuracy could be improved with more data'
                })
        
        if 'anomaly_detection' in results and 'error' not in results['anomaly_detection']:
            anomaly_result = results['anomaly_detection']
            if anomaly_result['anomaly_rate'] > 0.1:  # More than 10% anomalies
                recommendations.append({
                    'type': 'system_investigation',
                    'priority': 'high',
                    'message': 'High anomaly rate detected - investigate system health'
                })
        
        return json.dumps(recommendations)