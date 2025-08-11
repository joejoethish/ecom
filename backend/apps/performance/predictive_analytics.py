# Predictive Analytics for Performance Monitoring
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Avg, Count, Max, Min
import json
import logging
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

from .models import PerformanceMetric, PerformanceAlert, PerformanceIncident

logger = logging.getLogger(__name__)

class PerformancePredictiveAnalytics:
    """Predictive analytics for performance monitoring"""
    
    def __init__(self):
        self.models = {}
        self.scalers = {}
        self.prediction_horizon = 24  # hours
    
    def predict_performance_trends(self, metric_type, days_back=30):
        """Predict performance trends using historical data"""
        try:
            # Get historical data
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days_back)
            
            metrics = PerformanceMetric.objects.filter(
                metric_type=metric_type,
                timestamp__gte=start_date,
                timestamp__lte=end_date
            ).order_by('timestamp')
            
            if len(metrics) < 10:
                return {'error': 'Insufficient data for prediction'}
            
            # Prepare data
            df = self._prepare_time_series_data(metrics)
            
            # Train prediction model
            model, scaler = self._train_prediction_model(df)
            
            # Generate predictions
            predictions = self._generate_predictions(model, scaler, df)
            
            # Detect anomalies in predictions
            anomalies = self._detect_future_anomalies(predictions)
            
            return {
                'metric_type': metric_type,
                'historical_data': df.to_dict('records'),
                'predictions': predictions,
                'anomalies': anomalies,
                'model_accuracy': self._calculate_model_accuracy(model, df),
                'confidence_interval': self._calculate_confidence_interval(predictions),
                'trend_analysis': self._analyze_trend(df, predictions)
            }
            
        except Exception as e:
            logger.error(f"Error in predictive analytics: {str(e)}")
            return {'error': str(e)}
    
    def _prepare_time_series_data(self, metrics):
        """Prepare time series data for modeling"""
        data = []
        
        for metric in metrics:
            data.append({
                'timestamp': metric.timestamp,
                'value': metric.value,
                'hour': metric.timestamp.hour,
                'day_of_week': metric.timestamp.weekday(),
                'day_of_month': metric.timestamp.day,
                'month': metric.timestamp.month
            })
        
        df = pd.DataFrame(data)
        df['timestamp_numeric'] = pd.to_datetime(df['timestamp']).astype(int) / 10**9
        
        # Add rolling averages
        df['rolling_mean_6h'] = df['value'].rolling(window=6, min_periods=1).mean()
        df['rolling_mean_24h'] = df['value'].rolling(window=24, min_periods=1).mean()
        df['rolling_std_6h'] = df['value'].rolling(window=6, min_periods=1).std()
        
        return df
    
    def _train_prediction_model(self, df):
        """Train machine learning model for predictions"""
        # Features for prediction
        features = [
            'timestamp_numeric', 'hour', 'day_of_week', 'day_of_month', 'month',
            'rolling_mean_6h', 'rolling_mean_24h', 'rolling_std_6h'
        ]
        
        X = df[features].fillna(0)
        y = df['value']
        
        # Scale features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Train model
        model = LinearRegression()
        model.fit(X_scaled, y)
        
        return model, scaler
    
    def _generate_predictions(self, model, scaler, df):
        """Generate future predictions"""
        predictions = []
        last_timestamp = df['timestamp'].max()
        
        for i in range(1, self.prediction_horizon + 1):
            future_timestamp = last_timestamp + timedelta(hours=i)
            
            # Create feature vector for future timestamp
            future_features = [
                pd.to_datetime(future_timestamp).timestamp(),
                future_timestamp.hour,
                future_timestamp.weekday(),
                future_timestamp.day,
                future_timestamp.month,
                df['rolling_mean_6h'].iloc[-1],  # Use last known rolling average
                df['rolling_mean_24h'].iloc[-1],
                df['rolling_std_6h'].iloc[-1]
            ]
            
            # Scale and predict
            future_features_scaled = scaler.transform([future_features])
            predicted_value = model.predict(future_features_scaled)[0]
            
            predictions.append({
                'timestamp': future_timestamp,
                'predicted_value': max(0, predicted_value),  # Ensure non-negative
                'hour_ahead': i
            })
        
        return predictions
    
    def _detect_future_anomalies(self, predictions):
        """Detect potential anomalies in predictions"""
        if len(predictions) < 5:
            return []
        
        values = [p['predicted_value'] for p in predictions]
        mean_val = np.mean(values)
        std_val = np.std(values)
        
        anomalies = []
        for pred in predictions:
            z_score = abs(pred['predicted_value'] - mean_val) / std_val if std_val > 0 else 0
            
            if z_score > 2:  # 2 standard deviations
                anomalies.append({
                    'timestamp': pred['timestamp'],
                    'predicted_value': pred['predicted_value'],
                    'z_score': z_score,
                    'severity': 'high' if z_score > 3 else 'medium'
                })
        
        return anomalies
    
    def _calculate_model_accuracy(self, model, df):
        """Calculate model accuracy using cross-validation"""
        try:
            features = [
                'timestamp_numeric', 'hour', 'day_of_week', 'day_of_month', 'month',
                'rolling_mean_6h', 'rolling_mean_24h', 'rolling_std_6h'
            ]
            
            X = df[features].fillna(0)
            y = df['value']
            
            # Simple train-test split for accuracy calculation
            split_point = int(len(X) * 0.8)
            X_train, X_test = X[:split_point], X[split_point:]
            y_train, y_test = y[:split_point], y[split_point:]
            
            if len(X_test) == 0:
                return {'error': 'Insufficient data for accuracy calculation'}
            
            # Scale and predict
            scaler = StandardScaler()
            X_train_scaled = scaler.fit_transform(X_train)
            X_test_scaled = scaler.transform(X_test)
            
            model.fit(X_train_scaled, y_train)
            predictions = model.predict(X_test_scaled)
            
            # Calculate metrics
            mse = np.mean((y_test - predictions) ** 2)
            mae = np.mean(np.abs(y_test - predictions))
            mape = np.mean(np.abs((y_test - predictions) / y_test)) * 100
            
            return {
                'mse': float(mse),
                'mae': float(mae),
                'mape': float(mape),
                'r2_score': float(model.score(X_test_scaled, y_test))
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _calculate_confidence_interval(self, predictions):
        """Calculate confidence intervals for predictions"""
        values = [p['predicted_value'] for p in predictions]
        
        if len(values) < 2:
            return {'error': 'Insufficient predictions for confidence interval'}
        
        mean_val = np.mean(values)
        std_val = np.std(values)
        
        # 95% confidence interval
        confidence_95 = {
            'lower': mean_val - (1.96 * std_val),
            'upper': mean_val + (1.96 * std_val)
        }
        
        # 99% confidence interval
        confidence_99 = {
            'lower': mean_val - (2.58 * std_val),
            'upper': mean_val + (2.58 * std_val)
        }
        
        return {
            '95_percent': confidence_95,
            '99_percent': confidence_99,
            'mean': mean_val,
            'std_dev': std_val
        }
    
    def _analyze_trend(self, historical_df, predictions):
        """Analyze trend in historical and predicted data"""
        # Historical trend
        historical_values = historical_df['value'].values
        historical_trend = np.polyfit(range(len(historical_values)), historical_values, 1)[0]
        
        # Predicted trend
        predicted_values = [p['predicted_value'] for p in predictions]
        predicted_trend = np.polyfit(range(len(predicted_values)), predicted_values, 1)[0]
        
        return {
            'historical_trend': {
                'slope': float(historical_trend),
                'direction': 'increasing' if historical_trend > 0 else 'decreasing' if historical_trend < 0 else 'stable'
            },
            'predicted_trend': {
                'slope': float(predicted_trend),
                'direction': 'increasing' if predicted_trend > 0 else 'decreasing' if predicted_trend < 0 else 'stable'
            },
            'trend_change': abs(predicted_trend - historical_trend) > 0.1
        }


class AnomalyDetectionEngine:
    """Advanced anomaly detection using machine learning"""
    
    def __init__(self):
        self.isolation_forest = IsolationForest(contamination=0.1, random_state=42)
        self.scaler = StandardScaler()
        self.is_trained = False
    
    def train_anomaly_detector(self, metric_type, days_back=30):
        """Train anomaly detection model"""
        try:
            # Get training data
            end_date = timezone.now()
            start_date = end_date - timedelta(days=days_back)
            
            metrics = PerformanceMetric.objects.filter(
                metric_type=metric_type,
                timestamp__gte=start_date,
                timestamp__lte=end_date
            ).order_by('timestamp')
            
            if len(metrics) < 50:
                return {'error': 'Insufficient data for training'}
            
            # Prepare features
            features = self._extract_anomaly_features(metrics)
            
            # Scale features
            features_scaled = self.scaler.fit_transform(features)
            
            # Train isolation forest
            self.isolation_forest.fit(features_scaled)
            self.is_trained = True
            
            # Calculate training statistics
            anomaly_scores = self.isolation_forest.decision_function(features_scaled)
            outliers = self.isolation_forest.predict(features_scaled)
            
            return {
                'training_samples': len(metrics),
                'anomalies_detected': np.sum(outliers == -1),
                'anomaly_rate': float(np.sum(outliers == -1) / len(outliers)),
                'score_statistics': {
                    'mean': float(np.mean(anomaly_scores)),
                    'std': float(np.std(anomaly_scores)),
                    'min': float(np.min(anomaly_scores)),
                    'max': float(np.max(anomaly_scores))
                }
            }
            
        except Exception as e:
            logger.error(f"Error training anomaly detector: {str(e)}")
            return {'error': str(e)}
    
    def detect_anomalies(self, metric_type, hours_back=24):
        """Detect anomalies in recent data"""
        if not self.is_trained:
            return {'error': 'Anomaly detector not trained'}
        
        try:
            # Get recent data
            end_date = timezone.now()
            start_date = end_date - timedelta(hours=hours_back)
            
            metrics = PerformanceMetric.objects.filter(
                metric_type=metric_type,
                timestamp__gte=start_date,
                timestamp__lte=end_date
            ).order_by('timestamp')
            
            if len(metrics) == 0:
                return {'anomalies': [], 'message': 'No recent data available'}
            
            # Extract features
            features = self._extract_anomaly_features(metrics)
            features_scaled = self.scaler.transform(features)
            
            # Detect anomalies
            anomaly_scores = self.isolation_forest.decision_function(features_scaled)
            outliers = self.isolation_forest.predict(features_scaled)
            
            # Compile anomaly results
            anomalies = []
            for i, (metric, score, is_outlier) in enumerate(zip(metrics, anomaly_scores, outliers)):
                if is_outlier == -1:  # Anomaly detected
                    anomalies.append({
                        'timestamp': metric.timestamp,
                        'value': metric.value,
                        'anomaly_score': float(score),
                        'severity': self._calculate_anomaly_severity(score),
                        'metadata': metric.metadata
                    })
            
            return {
                'anomalies': anomalies,
                'total_samples': len(metrics),
                'anomaly_count': len(anomalies),
                'anomaly_rate': len(anomalies) / len(metrics) if len(metrics) > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {str(e)}")
            return {'error': str(e)}
    
    def _extract_anomaly_features(self, metrics):
        """Extract features for anomaly detection"""
        features = []
        
        for i, metric in enumerate(metrics):
            feature_vector = [
                metric.value,
                metric.timestamp.hour,
                metric.timestamp.weekday(),
                metric.timestamp.day,
                metric.timestamp.month
            ]
            
            # Add contextual features
            if i > 0:
                prev_metric = metrics[i-1]
                feature_vector.extend([
                    metric.value - prev_metric.value,  # Change from previous
                    (metric.timestamp - prev_metric.timestamp).total_seconds() / 3600  # Time gap in hours
                ])
            else:
                feature_vector.extend([0, 0])
            
            # Add rolling statistics if enough data
            if i >= 5:
                recent_values = [m.value for m in metrics[max(0, i-5):i]]
                feature_vector.extend([
                    np.mean(recent_values),
                    np.std(recent_values) if len(recent_values) > 1 else 0,
                    np.max(recent_values),
                    np.min(recent_values)
                ])
            else:
                feature_vector.extend([metric.value, 0, metric.value, metric.value])
            
            features.append(feature_vector)
        
        return np.array(features)
    
    def _calculate_anomaly_severity(self, score):
        """Calculate anomaly severity based on score"""
        if score < -0.5:
            return 'critical'
        elif score < -0.3:
            return 'high'
        elif score < -0.1:
            return 'medium'
        else:
            return 'low'


class PerformanceForecasting:
    """Performance forecasting and capacity planning"""
    
    def __init__(self):
        self.forecast_models = {}
    
    def forecast_resource_demand(self, resource_type, forecast_days=30):
        """Forecast resource demand for capacity planning"""
        try:
            # Get historical resource usage
            end_date = timezone.now()
            start_date = end_date - timedelta(days=90)  # 3 months of data
            
            metrics = PerformanceMetric.objects.filter(
                metric_type=resource_type,
                timestamp__gte=start_date,
                timestamp__lte=end_date
            ).order_by('timestamp')
            
            if len(metrics) < 30:
                return {'error': 'Insufficient historical data for forecasting'}
            
            # Prepare time series data
            df = pd.DataFrame([{
                'timestamp': m.timestamp,
                'value': m.value,
                'day_of_week': m.timestamp.weekday(),
                'hour': m.timestamp.hour,
                'day_of_month': m.timestamp.day
            } for m in metrics])
            
            # Generate forecast
            forecast = self._generate_resource_forecast(df, forecast_days)
            
            # Calculate capacity recommendations
            recommendations = self._generate_capacity_recommendations(forecast, resource_type)
            
            return {
                'resource_type': resource_type,
                'forecast_period': forecast_days,
                'historical_data_points': len(metrics),
                'forecast': forecast,
                'capacity_recommendations': recommendations,
                'peak_demand_forecast': self._calculate_peak_demand(forecast),
                'growth_rate': self._calculate_growth_rate(df, forecast)
            }
            
        except Exception as e:
            logger.error(f"Error in resource forecasting: {str(e)}")
            return {'error': str(e)}
    
    def _generate_resource_forecast(self, df, forecast_days):
        """Generate resource usage forecast"""
        # Simple trend-based forecasting
        df['timestamp_numeric'] = pd.to_datetime(df['timestamp']).astype(int) / 10**9
        
        # Fit linear trend
        X = df[['timestamp_numeric', 'day_of_week', 'hour']].values
        y = df['value'].values
        
        model = LinearRegression()
        model.fit(X, y)
        
        # Generate future predictions
        forecast = []
        last_timestamp = df['timestamp'].max()
        
        for i in range(1, forecast_days * 24 + 1):  # Hourly forecasts
            future_timestamp = last_timestamp + timedelta(hours=i)
            
            future_features = [
                pd.to_datetime(future_timestamp).timestamp(),
                future_timestamp.weekday(),
                future_timestamp.hour
            ]
            
            predicted_value = model.predict([future_features])[0]
            
            forecast.append({
                'timestamp': future_timestamp,
                'predicted_value': max(0, predicted_value),
                'day': i // 24 + 1,
                'hour': i % 24
            })
        
        return forecast
    
    def _generate_capacity_recommendations(self, forecast, resource_type):
        """Generate capacity planning recommendations"""
        predicted_values = [f['predicted_value'] for f in forecast]
        max_predicted = max(predicted_values)
        avg_predicted = np.mean(predicted_values)
        
        # Current capacity thresholds
        capacity_thresholds = {
            'cpu_usage': {'warning': 70, 'critical': 85, 'max_safe': 80},
            'memory_usage': {'warning': 75, 'critical': 90, 'max_safe': 85},
            'disk_usage': {'warning': 80, 'critical': 95, 'max_safe': 90}
        }
        
        threshold = capacity_thresholds.get(resource_type, {'warning': 70, 'critical': 85, 'max_safe': 80})
        
        recommendations = []
        
        if max_predicted > threshold['critical']:
            recommendations.append({
                'priority': 'critical',
                'action': 'immediate_scaling',
                'message': f"Predicted peak {resource_type} ({max_predicted:.1f}%) exceeds critical threshold ({threshold['critical']}%)",
                'recommended_capacity_increase': '50%',
                'timeline': 'immediate'
            })
        elif max_predicted > threshold['warning']:
            recommendations.append({
                'priority': 'high',
                'action': 'planned_scaling',
                'message': f"Predicted peak {resource_type} ({max_predicted:.1f}%) exceeds warning threshold ({threshold['warning']}%)",
                'recommended_capacity_increase': '25%',
                'timeline': 'within 2 weeks'
            })
        
        if avg_predicted > threshold['max_safe']:
            recommendations.append({
                'priority': 'medium',
                'action': 'capacity_optimization',
                'message': f"Average predicted {resource_type} ({avg_predicted:.1f}%) is above safe operating level",
                'recommended_capacity_increase': '20%',
                'timeline': 'within 1 month'
            })
        
        return recommendations
    
    def _calculate_peak_demand(self, forecast):
        """Calculate peak demand periods"""
        predicted_values = [f['predicted_value'] for f in forecast]
        max_value = max(predicted_values)
        
        # Find peak periods (top 10% of values)
        threshold = np.percentile(predicted_values, 90)
        
        peak_periods = []
        for f in forecast:
            if f['predicted_value'] >= threshold:
                peak_periods.append({
                    'timestamp': f['timestamp'],
                    'predicted_value': f['predicted_value'],
                    'day': f['day'],
                    'hour': f['hour']
                })
        
        return {
            'max_predicted_value': max_value,
            'peak_threshold': threshold,
            'peak_periods': peak_periods,
            'peak_hours_per_day': len(peak_periods) / (len(forecast) / 24)
        }
    
    def _calculate_growth_rate(self, historical_df, forecast):
        """Calculate growth rate from historical to forecasted data"""
        historical_avg = historical_df['value'].mean()
        forecast_avg = np.mean([f['predicted_value'] for f in forecast])
        
        growth_rate = ((forecast_avg - historical_avg) / historical_avg) * 100
        
        return {
            'historical_average': float(historical_avg),
            'forecast_average': float(forecast_avg),
            'growth_rate_percent': float(growth_rate),
            'growth_direction': 'increasing' if growth_rate > 0 else 'decreasing' if growth_rate < 0 else 'stable'
        }