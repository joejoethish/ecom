import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib
import logging
from django.conf import settings
from django.db.models import Q, Avg, Sum, Count
from .models import *

logger = logging.getLogger(__name__)


class DemandForecastingService:
    """Service for demand forecasting using ML"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
        
    def prepare_data(self, product_id: str, days_back: int = 365) -> pd.DataFrame:
        """Prepare historical data for training"""
        try:
            # This would typically fetch from your orders/products models
            # For now, we'll create a mock implementation
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # Mock data - replace with actual database queries
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            data = []
            
            for date in dates:
                # Simulate demand with seasonality and trend
                base_demand = 100
                seasonal = 20 * np.sin(2 * np.pi * date.dayofyear / 365)
                trend = 0.1 * (date - start_date).days
                noise = np.random.normal(0, 10)
                demand = max(0, base_demand + seasonal + trend + noise)
                
                data.append({
                    'date': date,
                    'product_id': product_id,
                    'demand': int(demand),
                    'day_of_week': date.weekday(),
                    'month': date.month,
                    'is_weekend': date.weekday() >= 5,
                    'day_of_year': date.dayofyear
                })
            
            return pd.DataFrame(data)
            
        except Exception as e:
            logger.error(f"Error preparing demand data: {str(e)}")
            raise
    
    def train_model(self, product_id: str) -> MLModel:
        """Train demand forecasting model"""
        try:
            # Prepare data
            df = self.prepare_data(product_id)
            
            # Feature engineering
            features = ['day_of_week', 'month', 'is_weekend', 'day_of_year']
            X = df[features]
            y = df['demand']
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model
            self.model = RandomForestRegressor(n_estimators=100, random_state=42)
            self.model.fit(X_train_scaled, y_train)
            
            # Evaluate
            y_pred = self.model.predict(X_test_scaled)
            mae = mean_absolute_error(y_test, y_pred)
            mse = mean_squared_error(y_test, y_pred)
            
            # Save model
            model_path = f"ml_models/demand_forecast_{product_id}.joblib"
            joblib.dump({
                'model': self.model,
                'scaler': self.scaler
            }, model_path)
            
            # Create ML model record
            ml_model = MLModel.objects.create(
                name=f"Demand Forecast - {product_id}",
                model_type='demand_forecasting',
                description=f"Demand forecasting model for product {product_id}",
                parameters={'product_id': product_id},
                accuracy=1 - (mae / y.mean()),  # Simple accuracy metric
                model_file_path=model_path,
                created_by_id=1,  # Replace with actual user
                last_trained=datetime.now()
            )
            
            return ml_model
            
        except Exception as e:
            logger.error(f"Error training demand forecast model: {str(e)}")
            raise
    
    def predict_demand(self, product_id: str, forecast_days: int = 30) -> List[Dict]:
        """Predict demand for future days"""
        try:
            # Load model
            model_path = f"ml_models/demand_forecast_{product_id}.joblib"
            model_data = joblib.load(model_path)
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            
            predictions = []
            start_date = datetime.now().date() + timedelta(days=1)
            
            for i in range(forecast_days):
                forecast_date = start_date + timedelta(days=i)
                
                # Prepare features
                features = np.array([[
                    forecast_date.weekday(),
                    forecast_date.month,
                    1 if forecast_date.weekday() >= 5 else 0,
                    forecast_date.timetuple().tm_yday
                ]])
                
                features_scaled = self.scaler.transform(features)
                demand = self.model.predict(features_scaled)[0]
                
                # Calculate confidence intervals (simplified)
                confidence_range = demand * 0.2
                
                predictions.append({
                    'date': forecast_date,
                    'predicted_demand': int(max(0, demand)),
                    'confidence_lower': int(max(0, demand - confidence_range)),
                    'confidence_upper': int(demand + confidence_range)
                })
            
            return predictions
            
        except Exception as e:
            logger.error(f"Error predicting demand: {str(e)}")
            raise


class CustomerSegmentationService:
    """Service for customer segmentation using ML"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
    
    def prepare_customer_data(self) -> pd.DataFrame:
        """Prepare customer data for segmentation"""
        try:
            # Mock customer data - replace with actual database queries
            customers = []
            for i in range(1000):
                customer = {
                    'customer_id': f'CUST_{i:04d}',
                    'total_orders': np.random.poisson(5),
                    'total_spent': np.random.exponential(500),
                    'avg_order_value': np.random.normal(100, 30),
                    'days_since_last_order': np.random.exponential(30),
                    'lifetime_days': np.random.uniform(30, 1000),
                    'return_rate': np.random.beta(2, 8),
                    'support_tickets': np.random.poisson(1)
                }
                customers.append(customer)
            
            return pd.DataFrame(customers)
            
        except Exception as e:
            logger.error(f"Error preparing customer data: {str(e)}")
            raise
    
    def train_segmentation_model(self, n_clusters: int = 5) -> MLModel:
        """Train customer segmentation model"""
        try:
            # Prepare data
            df = self.prepare_customer_data()
            
            # Select features for clustering
            features = [
                'total_orders', 'total_spent', 'avg_order_value',
                'days_since_last_order', 'lifetime_days', 'return_rate'
            ]
            X = df[features]
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train clustering model
            self.model = KMeans(n_clusters=n_clusters, random_state=42)
            clusters = self.model.fit_predict(X_scaled)
            
            # Add cluster labels to dataframe
            df['cluster'] = clusters
            
            # Analyze clusters
            cluster_analysis = {}
            for cluster_id in range(n_clusters):
                cluster_data = df[df['cluster'] == cluster_id]
                cluster_analysis[cluster_id] = {
                    'size': len(cluster_data),
                    'avg_total_spent': cluster_data['total_spent'].mean(),
                    'avg_orders': cluster_data['total_orders'].mean(),
                    'avg_order_value': cluster_data['avg_order_value'].mean(),
                    'characteristics': self._analyze_cluster_characteristics(cluster_data)
                }
            
            # Save model
            model_path = "ml_models/customer_segmentation.joblib"
            joblib.dump({
                'model': self.model,
                'scaler': self.scaler,
                'cluster_analysis': cluster_analysis
            }, model_path)
            
            # Create ML model record
            ml_model = MLModel.objects.create(
                name="Customer Segmentation",
                model_type='customer_segmentation',
                description="K-means clustering for customer segmentation",
                parameters={'n_clusters': n_clusters},
                model_file_path=model_path,
                created_by_id=1,
                last_trained=datetime.now()
            )
            
            return ml_model
            
        except Exception as e:
            logger.error(f"Error training segmentation model: {str(e)}")
            raise
    
    def _analyze_cluster_characteristics(self, cluster_data: pd.DataFrame) -> str:
        """Analyze cluster characteristics"""
        avg_spent = cluster_data['total_spent'].mean()
        avg_orders = cluster_data['total_orders'].mean()
        avg_recency = cluster_data['days_since_last_order'].mean()
        
        if avg_spent > 1000 and avg_orders > 10:
            return 'high_value'
        elif avg_recency < 30 and avg_orders > 5:
            return 'loyal'
        elif avg_recency > 90:
            return 'at_risk'
        elif avg_orders < 2:
            return 'new'
        else:
            return 'regular'
    
    def segment_customer(self, customer_data: Dict) -> Dict:
        """Segment a single customer"""
        try:
            # Load model
            model_path = "ml_models/customer_segmentation.joblib"
            model_data = joblib.load(model_path)
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            
            # Prepare features
            features = np.array([[
                customer_data['total_orders'],
                customer_data['total_spent'],
                customer_data['avg_order_value'],
                customer_data['days_since_last_order'],
                customer_data['lifetime_days'],
                customer_data['return_rate']
            ]])
            
            features_scaled = self.scaler.transform(features)
            cluster = self.model.predict(features_scaled)[0]
            
            return {
                'cluster_id': int(cluster),
                'segment_characteristics': model_data['cluster_analysis'][cluster]['characteristics']
            }
            
        except Exception as e:
            logger.error(f"Error segmenting customer: {str(e)}")
            raise


class FraudDetectionService:
    """Service for fraud detection using ML"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
    
    def prepare_transaction_data(self) -> pd.DataFrame:
        """Prepare transaction data for fraud detection"""
        try:
            # Mock transaction data
            transactions = []
            for i in range(10000):
                # Generate normal transactions (90%)
                if np.random.random() < 0.9:
                    transaction = {
                        'transaction_id': f'TXN_{i:06d}',
                        'amount': np.random.lognormal(4, 1),
                        'hour_of_day': np.random.normal(14, 4) % 24,
                        'day_of_week': np.random.randint(0, 7),
                        'num_items': np.random.poisson(3),
                        'customer_age_days': np.random.exponential(365),
                        'payment_method': np.random.choice([0, 1, 2]),  # card, paypal, bank
                        'shipping_address_matches': 1,
                        'is_fraud': 0
                    }
                else:
                    # Generate fraudulent transactions (10%)
                    transaction = {
                        'transaction_id': f'TXN_{i:06d}',
                        'amount': np.random.lognormal(6, 1.5),  # Higher amounts
                        'hour_of_day': np.random.choice([2, 3, 4, 23, 0, 1]),  # Unusual hours
                        'day_of_week': np.random.randint(0, 7),
                        'num_items': np.random.poisson(8),  # More items
                        'customer_age_days': np.random.exponential(30),  # New customers
                        'payment_method': np.random.choice([0, 1, 2]),
                        'shipping_address_matches': np.random.choice([0, 1], p=[0.7, 0.3]),
                        'is_fraud': 1
                    }
                
                transactions.append(transaction)
            
            return pd.DataFrame(transactions)
            
        except Exception as e:
            logger.error(f"Error preparing transaction data: {str(e)}")
            raise
    
    def train_fraud_model(self) -> MLModel:
        """Train fraud detection model"""
        try:
            # Prepare data
            df = self.prepare_transaction_data()
            
            # Select features
            features = [
                'amount', 'hour_of_day', 'day_of_week', 'num_items',
                'customer_age_days', 'payment_method', 'shipping_address_matches'
            ]
            X = df[features]
            y = df['is_fraud']
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model using Isolation Forest for anomaly detection
            self.model = IsolationForest(contamination=0.1, random_state=42)
            self.model.fit(X_train_scaled[y_train == 0])  # Train on normal transactions
            
            # Evaluate
            y_pred = self.model.predict(X_test_scaled)
            y_pred_binary = (y_pred == -1).astype(int)  # -1 for anomalies, 1 for normal
            
            # Calculate metrics
            from sklearn.metrics import precision_score, recall_score, f1_score
            precision = precision_score(y_test, y_pred_binary)
            recall = recall_score(y_test, y_pred_binary)
            f1 = f1_score(y_test, y_pred_binary)
            
            # Save model
            model_path = "ml_models/fraud_detection.joblib"
            joblib.dump({
                'model': self.model,
                'scaler': self.scaler
            }, model_path)
            
            # Create ML model record
            ml_model = MLModel.objects.create(
                name="Fraud Detection",
                model_type='fraud_detection',
                description="Isolation Forest for fraud detection",
                precision=precision,
                recall=recall,
                f1_score=f1,
                model_file_path=model_path,
                created_by_id=1,
                last_trained=datetime.now()
            )
            
            return ml_model
            
        except Exception as e:
            logger.error(f"Error training fraud model: {str(e)}")
            raise
    
    def detect_fraud(self, transaction_data: Dict) -> Dict:
        """Detect fraud in a transaction"""
        try:
            # Load model
            model_path = "ml_models/fraud_detection.joblib"
            model_data = joblib.load(model_path)
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            
            # Prepare features
            features = np.array([[
                transaction_data['amount'],
                transaction_data['hour_of_day'],
                transaction_data['day_of_week'],
                transaction_data['num_items'],
                transaction_data['customer_age_days'],
                transaction_data['payment_method'],
                transaction_data['shipping_address_matches']
            ]])
            
            features_scaled = self.scaler.transform(features)
            
            # Get anomaly score
            anomaly_score = self.model.decision_function(features_scaled)[0]
            is_anomaly = self.model.predict(features_scaled)[0] == -1
            
            # Convert to risk score (0-1)
            risk_score = max(0, min(1, (0.5 - anomaly_score) / 0.5))
            
            # Determine risk level
            if risk_score > 0.8:
                risk_level = 'critical'
            elif risk_score > 0.6:
                risk_level = 'high'
            elif risk_score > 0.4:
                risk_level = 'medium'
            else:
                risk_level = 'low'
            
            # Identify risk factors
            risk_factors = []
            if transaction_data['amount'] > 1000:
                risk_factors.append('High transaction amount')
            if transaction_data['hour_of_day'] in [0, 1, 2, 3, 23]:
                risk_factors.append('Unusual transaction time')
            if transaction_data['customer_age_days'] < 30:
                risk_factors.append('New customer account')
            if not transaction_data['shipping_address_matches']:
                risk_factors.append('Shipping address mismatch')
            
            return {
                'is_fraud_risk': is_anomaly,
                'risk_score': risk_score,
                'risk_level': risk_level,
                'risk_factors': risk_factors,
                'anomaly_score': anomaly_score
            }
            
        except Exception as e:
            logger.error(f"Error detecting fraud: {str(e)}")
            raise


class RecommendationService:
    """Service for product recommendations using collaborative filtering"""
    
    def __init__(self):
        self.model = None
        self.user_item_matrix = None
        self.item_similarity = None
    
    def prepare_interaction_data(self) -> pd.DataFrame:
        """Prepare user-item interaction data"""
        try:
            # Mock interaction data
            interactions = []
            for user_id in range(1, 1001):  # 1000 users
                num_interactions = np.random.poisson(10)
                for _ in range(num_interactions):
                    product_id = np.random.randint(1, 501)  # 500 products
                    rating = np.random.choice([3, 4, 5], p=[0.2, 0.3, 0.5])  # Positive bias
                    interactions.append({
                        'user_id': user_id,
                        'product_id': product_id,
                        'rating': rating,
                        'timestamp': datetime.now() - timedelta(days=np.random.randint(0, 365))
                    })
            
            return pd.DataFrame(interactions)
            
        except Exception as e:
            logger.error(f"Error preparing interaction data: {str(e)}")
            raise
    
    def train_recommendation_model(self) -> MLModel:
        """Train collaborative filtering recommendation model"""
        try:
            # Prepare data
            df = self.prepare_interaction_data()
            
            # Create user-item matrix
            self.user_item_matrix = df.pivot_table(
                index='user_id',
                columns='product_id',
                values='rating',
                fill_value=0
            )
            
            # Calculate item-item similarity using cosine similarity
            from sklearn.metrics.pairwise import cosine_similarity
            item_features = self.user_item_matrix.T  # Transpose to get items as rows
            self.item_similarity = cosine_similarity(item_features)
            
            # Save model
            model_path = "ml_models/recommendation_system.joblib"
            joblib.dump({
                'user_item_matrix': self.user_item_matrix,
                'item_similarity': self.item_similarity
            }, model_path)
            
            # Create ML model record
            ml_model = MLModel.objects.create(
                name="Product Recommendation System",
                model_type='recommendation',
                description="Collaborative filtering recommendation system",
                parameters={'similarity_metric': 'cosine'},
                model_file_path=model_path,
                created_by_id=1,
                last_trained=datetime.now()
            )
            
            return ml_model
            
        except Exception as e:
            logger.error(f"Error training recommendation model: {str(e)}")
            raise
    
    def get_recommendations(self, user_id: int, num_recommendations: int = 10) -> List[Dict]:
        """Get product recommendations for a user"""
        try:
            # Load model
            model_path = "ml_models/recommendation_system.joblib"
            model_data = joblib.load(model_path)
            self.user_item_matrix = model_data['user_item_matrix']
            self.item_similarity = model_data['item_similarity']
            
            if user_id not in self.user_item_matrix.index:
                # New user - return popular items
                popular_items = self.user_item_matrix.mean().sort_values(ascending=False)
                recommendations = []
                for i, (product_id, score) in enumerate(popular_items.head(num_recommendations).items()):
                    recommendations.append({
                        'product_id': product_id,
                        'score': float(score),
                        'rank': i + 1,
                        'reason': 'Popular item'
                    })
                return recommendations
            
            # Get user's ratings
            user_ratings = self.user_item_matrix.loc[user_id]
            
            # Find items the user hasn't rated
            unrated_items = user_ratings[user_ratings == 0].index
            
            # Calculate predicted ratings for unrated items
            predictions = {}
            for item in unrated_items:
                if item in self.user_item_matrix.columns:
                    item_idx = list(self.user_item_matrix.columns).index(item)
                    
                    # Find similar items that the user has rated
                    similar_items = []
                    for rated_item in user_ratings[user_ratings > 0].index:
                        if rated_item in self.user_item_matrix.columns:
                            rated_item_idx = list(self.user_item_matrix.columns).index(rated_item)
                            similarity = self.item_similarity[item_idx][rated_item_idx]
                            if similarity > 0.1:  # Threshold for similarity
                                similar_items.append((rated_item, similarity, user_ratings[rated_item]))
                    
                    if similar_items:
                        # Calculate weighted average
                        weighted_sum = sum(sim * rating for _, sim, rating in similar_items)
                        similarity_sum = sum(sim for _, sim, _ in similar_items)
                        predicted_rating = weighted_sum / similarity_sum if similarity_sum > 0 else 0
                        predictions[item] = predicted_rating
            
            # Sort by predicted rating
            sorted_predictions = sorted(predictions.items(), key=lambda x: x[1], reverse=True)
            
            # Format recommendations
            recommendations = []
            for i, (product_id, score) in enumerate(sorted_predictions[:num_recommendations]):
                recommendations.append({
                    'product_id': int(product_id),
                    'score': float(score),
                    'rank': i + 1,
                    'reason': 'Collaborative filtering'
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting recommendations: {str(e)}")
            raise


class PricingOptimizationService:
    """Service for dynamic pricing optimization"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
    
    def prepare_pricing_data(self, product_id: str) -> pd.DataFrame:
        """Prepare historical pricing and sales data"""
        try:
            # Mock pricing data
            data = []
            base_price = 100
            
            for i in range(365):  # One year of data
                date = datetime.now() - timedelta(days=365-i)
                
                # Simulate price changes
                price_variation = np.random.normal(0, 5)
                price = max(50, base_price + price_variation)
                
                # Simulate demand based on price elasticity
                price_elasticity = -1.5
                base_demand = 100
                demand = base_demand * (price / base_price) ** price_elasticity
                demand += np.random.normal(0, 10)  # Add noise
                demand = max(0, demand)
                
                # Add external factors
                competitor_price = price * np.random.uniform(0.9, 1.1)
                inventory_level = np.random.randint(50, 500)
                is_weekend = date.weekday() >= 5
                
                data.append({
                    'date': date,
                    'product_id': product_id,
                    'price': price,
                    'demand': int(demand),
                    'competitor_price': competitor_price,
                    'inventory_level': inventory_level,
                    'is_weekend': is_weekend,
                    'day_of_week': date.weekday(),
                    'month': date.month
                })
            
            return pd.DataFrame(data)
            
        except Exception as e:
            logger.error(f"Error preparing pricing data: {str(e)}")
            raise
    
    def train_pricing_model(self, product_id: str) -> MLModel:
        """Train pricing optimization model"""
        try:
            # Prepare data
            df = self.prepare_pricing_data(product_id)
            
            # Feature engineering
            features = [
                'price', 'competitor_price', 'inventory_level',
                'is_weekend', 'day_of_week', 'month'
            ]
            X = df[features]
            y = df['demand']
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model
            self.model = RandomForestRegressor(n_estimators=100, random_state=42)
            self.model.fit(X_train_scaled, y_train)
            
            # Evaluate
            y_pred = self.model.predict(X_test_scaled)
            mae = mean_absolute_error(y_test, y_pred)
            
            # Save model
            model_path = f"ml_models/pricing_optimization_{product_id}.joblib"
            joblib.dump({
                'model': self.model,
                'scaler': self.scaler
            }, model_path)
            
            # Create ML model record
            ml_model = MLModel.objects.create(
                name=f"Pricing Optimization - {product_id}",
                model_type='pricing_optimization',
                description=f"Dynamic pricing model for product {product_id}",
                parameters={'product_id': product_id},
                accuracy=1 - (mae / y.mean()),
                model_file_path=model_path,
                created_by_id=1,
                last_trained=datetime.now()
            )
            
            return ml_model
            
        except Exception as e:
            logger.error(f"Error training pricing model: {str(e)}")
            raise
    
    def optimize_price(self, product_id: str, current_context: Dict) -> Dict:
        """Optimize price for given context"""
        try:
            # Load model
            model_path = f"ml_models/pricing_optimization_{product_id}.joblib"
            model_data = joblib.load(model_path)
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            
            # Test different price points
            price_range = np.arange(
                current_context['current_price'] * 0.7,
                current_context['current_price'] * 1.3,
                current_context['current_price'] * 0.05
            )
            
            best_price = current_context['current_price']
            best_revenue = 0
            
            for test_price in price_range:
                # Prepare features
                features = np.array([[
                    test_price,
                    current_context['competitor_price'],
                    current_context['inventory_level'],
                    current_context['is_weekend'],
                    current_context['day_of_week'],
                    current_context['month']
                ]])
                
                features_scaled = self.scaler.transform(features)
                predicted_demand = self.model.predict(features_scaled)[0]
                predicted_revenue = test_price * max(0, predicted_demand)
                
                if predicted_revenue > best_revenue:
                    best_revenue = predicted_revenue
                    best_price = test_price
            
            # Calculate demand elasticity
            current_features = np.array([[
                current_context['current_price'],
                current_context['competitor_price'],
                current_context['inventory_level'],
                current_context['is_weekend'],
                current_context['day_of_week'],
                current_context['month']
            ]])
            
            current_features_scaled = self.scaler.transform(current_features)
            current_demand = self.model.predict(current_features_scaled)[0]
            
            return {
                'current_price': current_context['current_price'],
                'optimized_price': float(best_price),
                'current_demand': int(max(0, current_demand)),
                'expected_demand': int(max(0, best_revenue / best_price)),
                'expected_revenue': float(best_revenue),
                'price_change_percent': float((best_price - current_context['current_price']) / current_context['current_price'] * 100)
            }
            
        except Exception as e:
            logger.error(f"Error optimizing price: {str(e)}")
            raise


class ChurnPredictionService:
    """Service for customer churn prediction"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
    
    def prepare_customer_churn_data(self) -> pd.DataFrame:
        """Prepare customer data for churn prediction"""
        try:
            # Mock customer churn data
            customers = []
            for i in range(5000):
                # Customer features
                days_since_signup = np.random.exponential(365)
                total_orders = np.random.poisson(10)
                total_spent = np.random.exponential(500)
                avg_order_value = total_spent / max(1, total_orders)
                days_since_last_order = np.random.exponential(60)
                support_tickets = np.random.poisson(2)
                return_rate = np.random.beta(1, 10)
                
                # Churn logic (simplified)
                churn_probability = (
                    0.3 * min(1, days_since_last_order / 90) +  # Recency
                    0.2 * max(0, 1 - total_orders / 10) +      # Frequency
                    0.2 * max(0, 1 - total_spent / 1000) +     # Monetary
                    0.1 * min(1, support_tickets / 5) +        # Support issues
                    0.2 * min(1, return_rate * 10)             # Returns
                )
                
                is_churned = np.random.random() < churn_probability
                
                customers.append({
                    'customer_id': f'CUST_{i:04d}',
                    'days_since_signup': days_since_signup,
                    'total_orders': total_orders,
                    'total_spent': total_spent,
                    'avg_order_value': avg_order_value,
                    'days_since_last_order': days_since_last_order,
                    'support_tickets': support_tickets,
                    'return_rate': return_rate,
                    'is_churned': int(is_churned)
                })
            
            return pd.DataFrame(customers)
            
        except Exception as e:
            logger.error(f"Error preparing churn data: {str(e)}")
            raise
    
    def train_churn_model(self) -> MLModel:
        """Train churn prediction model"""
        try:
            # Prepare data
            df = self.prepare_customer_churn_data()
            
            # Select features
            features = [
                'days_since_signup', 'total_orders', 'total_spent',
                'avg_order_value', 'days_since_last_order',
                'support_tickets', 'return_rate'
            ]
            X = df[features]
            y = df['is_churned']
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Scale features
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Train model
            from sklearn.ensemble import RandomForestClassifier
            self.model = RandomForestClassifier(n_estimators=100, random_state=42)
            self.model.fit(X_train_scaled, y_train)
            
            # Evaluate
            y_pred = self.model.predict(X_test_scaled)
            y_pred_proba = self.model.predict_proba(X_test_scaled)[:, 1]
            
            from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
            accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred)
            recall = recall_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred)
            
            # Save model
            model_path = "ml_models/churn_prediction.joblib"
            joblib.dump({
                'model': self.model,
                'scaler': self.scaler,
                'feature_names': features
            }, model_path)
            
            # Create ML model record
            ml_model = MLModel.objects.create(
                name="Customer Churn Prediction",
                model_type='churn_prediction',
                description="Random Forest model for predicting customer churn",
                accuracy=accuracy,
                precision=precision,
                recall=recall,
                f1_score=f1,
                model_file_path=model_path,
                created_by_id=1,
                last_trained=datetime.now()
            )
            
            return ml_model
            
        except Exception as e:
            logger.error(f"Error training churn model: {str(e)}")
            raise
    
    def predict_churn(self, customer_data: Dict) -> Dict:
        """Predict churn probability for a customer"""
        try:
            # Load model
            model_path = "ml_models/churn_prediction.joblib"
            model_data = joblib.load(model_path)
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            feature_names = model_data['feature_names']
            
            # Prepare features
            features = np.array([[
                customer_data['days_since_signup'],
                customer_data['total_orders'],
                customer_data['total_spent'],
                customer_data['avg_order_value'],
                customer_data['days_since_last_order'],
                customer_data['support_tickets'],
                customer_data['return_rate']
            ]])
            
            features_scaled = self.scaler.transform(features)
            
            # Get prediction
            churn_probability = self.model.predict_proba(features_scaled)[0][1]
            
            # Determine risk level
            if churn_probability > 0.7:
                risk_level = 'high'
            elif churn_probability > 0.4:
                risk_level = 'medium'
            else:
                risk_level = 'low'
            
            # Get feature importance for this prediction
            feature_importance = self.model.feature_importances_
            
            # Identify key churn factors
            churn_factors = []
            if customer_data['days_since_last_order'] > 60:
                churn_factors.append('Long time since last order')
            if customer_data['total_orders'] < 3:
                churn_factors.append('Low purchase frequency')
            if customer_data['support_tickets'] > 3:
                churn_factors.append('High support ticket volume')
            if customer_data['return_rate'] > 0.2:
                churn_factors.append('High return rate')
            
            # Generate retention recommendations
            retention_actions = []
            if churn_probability > 0.5:
                retention_actions.append('Send personalized discount offer')
                retention_actions.append('Assign dedicated customer success manager')
            if customer_data['days_since_last_order'] > 30:
                retention_actions.append('Send re-engagement email campaign')
            if customer_data['support_tickets'] > 2:
                retention_actions.append('Proactive customer support outreach')
            
            return {
                'churn_probability': float(churn_probability),
                'risk_level': risk_level,
                'churn_factors': churn_factors,
                'retention_actions': retention_actions,
                'feature_importance': dict(zip(feature_names, feature_importance.tolist()))
            }
            
        except Exception as e:
            logger.error(f"Error predicting churn: {str(e)}")
            raise


class SentimentAnalysisService:
    """Service for sentiment analysis using NLP"""
    
    def __init__(self):
        self.model = None
        self.vectorizer = None
    
    def prepare_sentiment_data(self) -> pd.DataFrame:
        """Prepare text data for sentiment analysis"""
        try:
            # Mock review data with sentiments
            reviews = [
                ("This product is amazing! I love it so much.", "positive"),
                ("Great quality and fast shipping. Highly recommend!", "positive"),
                ("Excellent customer service and product quality.", "positive"),
                ("The product is okay, nothing special.", "neutral"),
                ("Average quality, could be better.", "neutral"),
                ("It's fine, meets basic expectations.", "neutral"),
                ("Terrible product, waste of money!", "negative"),
                ("Poor quality and bad customer service.", "negative"),
                ("I hate this product, returning immediately.", "negative"),
                ("Outstanding product! Exceeded my expectations completely.", "positive"),
                ("Worst purchase ever made. Completely disappointed.", "negative"),
                ("Product is decent for the price point.", "neutral"),
            ]
            
            # Expand the dataset
            expanded_reviews = []
            for text, sentiment in reviews:
                for _ in range(100):  # Create variations
                    expanded_reviews.append({
                        'text': text,
                        'sentiment': sentiment
                    })
            
            return pd.DataFrame(expanded_reviews)
            
        except Exception as e:
            logger.error(f"Error preparing sentiment data: {str(e)}")
            raise
    
    def train_sentiment_model(self) -> MLModel:
        """Train sentiment analysis model"""
        try:
            # Prepare data
            df = self.prepare_sentiment_data()
            
            # Prepare text features
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.naive_bayes import MultinomialNB
            
            self.vectorizer = TfidfVectorizer(max_features=5000, stop_words='english')
            X = self.vectorizer.fit_transform(df['text'])
            y = df['sentiment']
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Train model
            self.model = MultinomialNB()
            self.model.fit(X_train, y_train)
            
            # Evaluate
            y_pred = self.model.predict(X_test)
            from sklearn.metrics import accuracy_score, classification_report
            accuracy = accuracy_score(y_test, y_pred)
            
            # Save model
            model_path = "ml_models/sentiment_analysis.joblib"
            joblib.dump({
                'model': self.model,
                'vectorizer': self.vectorizer
            }, model_path)
            
            # Create ML model record
            ml_model = MLModel.objects.create(
                name="Sentiment Analysis",
                model_type='sentiment_analysis',
                description="Naive Bayes model for sentiment analysis",
                accuracy=accuracy,
                model_file_path=model_path,
                created_by_id=1,
                last_trained=datetime.now()
            )
            
            return ml_model
            
        except Exception as e:
            logger.error(f"Error training sentiment model: {str(e)}")
            raise
    
    def analyze_sentiment(self, text: str) -> Dict:
        """Analyze sentiment of text"""
        try:
            # Load model
            model_path = "ml_models/sentiment_analysis.joblib"
            model_data = joblib.load(model_path)
            self.model = model_data['model']
            self.vectorizer = model_data['vectorizer']
            
            # Prepare text
            text_vector = self.vectorizer.transform([text])
            
            # Get prediction
            sentiment = self.model.predict(text_vector)[0]
            sentiment_proba = self.model.predict_proba(text_vector)[0]
            
            # Get class labels
            classes = self.model.classes_
            sentiment_scores = dict(zip(classes, sentiment_proba))
            
            # Determine confidence
            confidence = max(sentiment_proba)
            
            return {
                'sentiment': sentiment,
                'confidence_score': float(confidence),
                'positive_score': float(sentiment_scores.get('positive', 0)),
                'negative_score': float(sentiment_scores.get('negative', 0)),
                'neutral_score': float(sentiment_scores.get('neutral', 0)),
                'text_length': len(text),
                'word_count': len(text.split())
            }
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment: {str(e)}")
            raise


class AnomalyDetectionService:
    """Service for detecting anomalies in business metrics"""
    
    def __init__(self):
        self.model = None
        self.scaler = StandardScaler()
    
    def prepare_metrics_data(self) -> pd.DataFrame:
        """Prepare business metrics data for anomaly detection"""
        try:
            # Mock business metrics data
            data = []
            base_date = datetime.now() - timedelta(days=365)
            
            for i in range(365):
                date = base_date + timedelta(days=i)
                
                # Normal patterns with seasonality
                base_sales = 10000
                seasonal = 2000 * np.sin(2 * np.pi * i / 365)  # Yearly seasonality
                weekly = 1000 * np.sin(2 * np.pi * i / 7)      # Weekly seasonality
                trend = 10 * i  # Growth trend
                noise = np.random.normal(0, 500)
                
                sales = base_sales + seasonal + weekly + trend + noise
                
                # Inject some anomalies (5% of data)
                if np.random.random() < 0.05:
                    if np.random.random() < 0.5:
                        sales *= 2  # Positive anomaly
                    else:
                        sales *= 0.3  # Negative anomaly
                
                # Other metrics
                orders = max(1, int(sales / 100 + np.random.normal(0, 10)))
                avg_order_value = sales / orders
                conversion_rate = max(0.01, min(0.1, np.random.normal(0.05, 0.01)))
                
                data.append({
                    'date': date,
                    'sales': max(0, sales),
                    'orders': orders,
                    'avg_order_value': avg_order_value,
                    'conversion_rate': conversion_rate,
                    'day_of_week': date.weekday(),
                    'day_of_year': date.timetuple().tm_yday
                })
            
            return pd.DataFrame(data)
            
        except Exception as e:
            logger.error(f"Error preparing metrics data: {str(e)}")
            raise
    
    def train_anomaly_model(self) -> MLModel:
        """Train anomaly detection model"""
        try:
            # Prepare data
            df = self.prepare_metrics_data()
            
            # Select features
            features = ['sales', 'orders', 'avg_order_value', 'conversion_rate']
            X = df[features]
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train isolation forest
            self.model = IsolationForest(contamination=0.05, random_state=42)
            self.model.fit(X_scaled)
            
            # Get anomaly scores for evaluation
            anomaly_scores = self.model.decision_function(X_scaled)
            anomalies = self.model.predict(X_scaled)
            
            # Save model
            model_path = "ml_models/anomaly_detection.joblib"
            joblib.dump({
                'model': self.model,
                'scaler': self.scaler,
                'feature_names': features
            }, model_path)
            
            # Create ML model record
            ml_model = MLModel.objects.create(
                name="Business Metrics Anomaly Detection",
                model_type='anomaly_detection',
                description="Isolation Forest for detecting anomalies in business metrics",
                parameters={'contamination': 0.05},
                model_file_path=model_path,
                created_by_id=1,
                last_trained=datetime.now()
            )
            
            return ml_model
            
        except Exception as e:
            logger.error(f"Error training anomaly model: {str(e)}")
            raise
    
    def detect_anomalies(self, metrics_data: Dict) -> Dict:
        """Detect anomalies in business metrics"""
        try:
            # Load model
            model_path = "ml_models/anomaly_detection.joblib"
            model_data = joblib.load(model_path)
            self.model = model_data['model']
            self.scaler = model_data['scaler']
            feature_names = model_data['feature_names']
            
            # Prepare features
            features = np.array([[
                metrics_data['sales'],
                metrics_data['orders'],
                metrics_data['avg_order_value'],
                metrics_data['conversion_rate']
            ]])
            
            features_scaled = self.scaler.transform(features)
            
            # Get anomaly score
            anomaly_score = self.model.decision_function(features_scaled)[0]
            is_anomaly = self.model.predict(features_scaled)[0] == -1
            
            # Determine anomaly type and severity
            anomaly_type = 'normal'
            severity = 'low'
            
            if is_anomaly:
                # Analyze which metrics are anomalous
                feature_values = features[0]
                feature_means = [10000, 100, 100, 0.05]  # Approximate means
                
                anomalous_features = []
                for i, (name, value, mean) in enumerate(zip(feature_names, feature_values, feature_means)):
                    deviation = abs(value - mean) / mean
                    if deviation > 0.5:  # 50% deviation threshold
                        anomalous_features.append(name)
                
                if 'sales' in anomalous_features:
                    anomaly_type = 'sales'
                elif 'orders' in anomalous_features:
                    anomaly_type = 'orders'
                elif 'conversion_rate' in anomalous_features:
                    anomaly_type = 'conversion'
                else:
                    anomaly_type = 'general'
                
                # Determine severity based on anomaly score
                if anomaly_score < -0.5:
                    severity = 'critical'
                elif anomaly_score < -0.3:
                    severity = 'high'
                elif anomaly_score < -0.1:
                    severity = 'medium'
                else:
                    severity = 'low'
            
            return {
                'is_anomaly': is_anomaly,
                'anomaly_score': float(anomaly_score),
                'anomaly_type': anomaly_type,
                'severity': severity,
                'threshold': -0.1,  # Default threshold
                'metrics': dict(zip(feature_names, feature_values.tolist())),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {str(e)}")
            raise


class AIInsightsService:
    """Service for generating AI-powered business insights"""
    
    def __init__(self):
        self.services = {
            'demand_forecasting': DemandForecastingService(),
            'customer_segmentation': CustomerSegmentationService(),
            'fraud_detection': FraudDetectionService(),
            'recommendation': RecommendationService(),
            'pricing_optimization': PricingOptimizationService(),
            'churn_prediction': ChurnPredictionService(),
            'sentiment_analysis': SentimentAnalysisService(),
            'anomaly_detection': AnomalyDetectionService()
        }
    
    def generate_sales_insights(self) -> List[Dict]:
        """Generate AI insights for sales performance"""
        insights = []
        
        try:
            # Demand forecasting insight
            forecast_service = self.services['demand_forecasting']
            sample_predictions = forecast_service.predict_demand('PROD_001', 7)
            
            total_predicted = sum(p['predicted_demand'] for p in sample_predictions)
            insights.append({
                'type': 'sales_trend',
                'title': 'Weekly Demand Forecast',
                'description': f'Predicted demand for next 7 days: {total_predicted} units',
                'priority': 'medium',
                'recommendations': [
                    'Ensure adequate inventory levels',
                    'Plan marketing campaigns accordingly'
                ],
                'confidence': 0.85
            })
            
            # Pricing optimization insight
            pricing_service = self.services['pricing_optimization']
            pricing_context = {
                'current_price': 100,
                'competitor_price': 95,
                'inventory_level': 200,
                'is_weekend': False,
                'day_of_week': 2,
                'month': 3
            }
            
            pricing_result = pricing_service.optimize_price('PROD_001', pricing_context)
            if abs(pricing_result['price_change_percent']) > 5:
                insights.append({
                    'type': 'pricing_strategy',
                    'title': 'Price Optimization Opportunity',
                    'description': f'Optimal price: ${pricing_result["optimized_price"]:.2f} (current: ${pricing_result["current_price"]:.2f})',
                    'priority': 'high',
                    'recommendations': [
                        f'Adjust price by {pricing_result["price_change_percent"]:.1f}%',
                        f'Expected revenue increase: ${pricing_result["expected_revenue"]:.2f}'
                    ],
                    'confidence': 0.78
                })
            
        except Exception as e:
            logger.error(f"Error generating sales insights: {str(e)}")
        
        return insights
    
    def generate_customer_insights(self) -> List[Dict]:
        """Generate AI insights for customer behavior"""
        insights = []
        
        try:
            # Customer segmentation insight
            segmentation_service = self.services['customer_segmentation']
            
            # Mock customer data for insight generation
            sample_customer = {
                'total_orders': 15,
                'total_spent': 1500,
                'avg_order_value': 100,
                'days_since_last_order': 45,
                'lifetime_days': 365,
                'return_rate': 0.1
            }
            
            segment_result = segmentation_service.segment_customer(sample_customer)
            
            insights.append({
                'type': 'customer_behavior',
                'title': 'Customer Segmentation Analysis',
                'description': f'Customer segment: {segment_result["segment_characteristics"]}',
                'priority': 'medium',
                'recommendations': [
                    'Develop targeted marketing campaigns',
                    'Personalize product recommendations'
                ],
                'confidence': 0.82
            })
            
            # Churn prediction insight
            churn_service = self.services['churn_prediction']
            churn_data = {
                'days_since_signup': 180,
                'total_orders': 2,
                'total_spent': 150,
                'avg_order_value': 75,
                'days_since_last_order': 90,
                'support_tickets': 1,
                'return_rate': 0.0
            }
            
            churn_result = churn_service.predict_churn(churn_data)
            if churn_result['risk_level'] in ['medium', 'high']:
                insights.append({
                    'type': 'risk_assessment',
                    'title': 'Customer Churn Risk Detected',
                    'description': f'Churn probability: {churn_result["churn_probability"]:.2%}',
                    'priority': 'high' if churn_result['risk_level'] == 'high' else 'medium',
                    'recommendations': churn_result['retention_actions'],
                    'confidence': churn_result['churn_probability']
                })
            
        except Exception as e:
            logger.error(f"Error generating customer insights: {str(e)}")
        
        return insights
    
    def generate_operational_insights(self) -> List[Dict]:
        """Generate AI insights for operational efficiency"""
        insights = []
        
        try:
            # Anomaly detection insight
            anomaly_service = self.services['anomaly_detection']
            
            # Mock metrics data
            metrics = {
                'sales': 8000,  # Lower than normal
                'orders': 80,
                'avg_order_value': 100,
                'conversion_rate': 0.03  # Lower than normal
            }
            
            anomaly_result = anomaly_service.detect_anomalies(metrics)
            if anomaly_result['is_anomaly']:
                insights.append({
                    'type': 'operational_alert',
                    'title': f'{anomaly_result["anomaly_type"].title()} Anomaly Detected',
                    'description': f'Anomaly score: {anomaly_result["anomaly_score"]:.3f}',
                    'priority': anomaly_result['severity'],
                    'recommendations': [
                        'Investigate root cause immediately',
                        'Check system performance and marketing campaigns',
                        'Review competitor activities'
                    ],
                    'confidence': abs(anomaly_result['anomaly_score'])
                })
            
            # Fraud detection insight
            fraud_service = self.services['fraud_detection']
            
            # Mock transaction data
            transaction = {
                'amount': 2500,  # High amount
                'hour_of_day': 2,  # Unusual time
                'day_of_week': 3,
                'num_items': 1,
                'customer_age_days': 5,  # New customer
                'payment_method': 0,
                'shipping_address_matches': 0  # Address mismatch
            }
            
            fraud_result = fraud_service.detect_fraud(transaction)
            if fraud_result['risk_level'] in ['high', 'critical']:
                insights.append({
                    'type': 'risk_assessment',
                    'title': 'High Fraud Risk Transaction',
                    'description': f'Risk score: {fraud_result["risk_score"]:.2%}',
                    'priority': 'critical' if fraud_result['risk_level'] == 'critical' else 'high',
                    'recommendations': [
                        'Review transaction manually',
                        'Contact customer for verification',
                        'Hold shipment until verified'
                    ],
                    'confidence': fraud_result['risk_score']
                })
            
        except Exception as e:
            logger.error(f"Error generating operational insights: {str(e)}")
        
        return insights
    
    def generate_all_insights(self) -> List[Dict]:
        """Generate comprehensive AI insights"""
        all_insights = []
        
        all_insights.extend(self.generate_sales_insights())
        all_insights.extend(self.generate_customer_insights())
        all_insights.extend(self.generate_operational_insights())
        
        # Sort by priority and confidence
        priority_order = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
        all_insights.sort(
            key=lambda x: (priority_order.get(x['priority'], 0), x['confidence']),
            reverse=True
        )
        
        return all_insights