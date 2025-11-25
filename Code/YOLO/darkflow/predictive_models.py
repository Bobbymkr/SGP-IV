"""
Predictive Analytics Integration
=============================

Advanced ML-based traffic forecasting system with:
- Time series forecasting models
- Traffic pattern recognition
- Event impact prediction
- Anomaly detection
- Social media integration
- Continuous model improvement

Author: Top 0.1% Expert Team
Date: November 2025
Version: 3.0.0
"""

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from sklearn.ensemble import RandomForestRegressor, IsolationForest
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib
import threading
import time
import logging
from typing import Dict, List, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime, timedelta
import requests
import re
from collections import deque, defaultdict
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PredictionModel(Enum):
    """Types of prediction models"""
    LSTM = "lstm"
    GRU = "gru"
    TRANSFORMER = "transformer"
    RANDOM_FOREST = "random_forest"
    ENSEMBLE = "ensemble"
    PROPHET = "prophet"

class PredictionHorizon(Enum):
    """Prediction time horizons"""
    SHORT_TERM = "short_term"      # 15-30 minutes
    MEDIUM_TERM = "medium_term"    # 1-4 hours
    LONG_TERM = "long_term"         # 6-24 hours
    WEEKLY = "weekly"              # 7 days
    MONTHLY = "monthly"            # 30 days

class AnomalyType(Enum):
    """Types of traffic anomalies"""
    SUDDEN_CONGESTION = "sudden_congestion"
    UNUSUAL_PATTERN = "unusual_pattern"
    INCIDENT_IMPACT = "incident_impact"
    WEATHER_IMPACT = "weather_impact"
    EVENT_IMPACT = "event_impact"
    EQUIPMENT_FAILURE = "equipment_failure"

@dataclass
class TrafficPrediction:
    """Traffic prediction result"""
    prediction_id: str
    model_type: PredictionModel
    horizon: PredictionHorizon
    timestamp: float
    target_time: float
    predicted_volume: float
    predicted_speed: float
    confidence: float
    features_used: List[str]
    model_version: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AnomalyDetection:
    """Anomaly detection result"""
    anomaly_id: str
    anomaly_type: AnomalyType
    severity: str  # low, medium, high, critical
    confidence: float
    location: str
    timestamp: float
    description: str
    affected_metrics: List[str]
    recommended_action: str

class TrafficDataProcessor:
    """Advanced traffic data processing for ML models"""
    
    def __init__(self):
        self.data_buffer = deque(maxlen=10000)  # Store last 10k records
        self.feature_cache = {}
        self.scalers = {}
        
        # Feature engineering parameters
        self.time_windows = [5, 15, 30, 60]  # minutes
        self.lag_periods = [1, 2, 3, 6, 12, 24]  # hours
        self.seasonal_periods = [24, 168]  # daily, weekly
        
        logger.info("Traffic data processor initialized")
    
    def add_traffic_data(self, data: Dict[str, Any]):
        """Add new traffic data point"""
        processed_data = self._process_raw_data(data)
        self.data_buffer.append(processed_data)
        
        # Update feature cache
        self._update_feature_cache()
    
    def _process_raw_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw traffic data into features"""
        processed = data.copy()
        
        # Add temporal features
        timestamp = data.get('timestamp', time.time())
        dt = datetime.fromtimestamp(timestamp)
        
        processed['hour'] = dt.hour
        processed['day_of_week'] = dt.weekday()
        processed['day_of_month'] = dt.day
        processed['month'] = dt.month
        processed['is_weekend'] = 1 if dt.weekday() >= 5 else 0
        processed['is_rush_hour'] = self._is_rush_hour(dt.hour)
        
        # Add cyclical features
        processed['hour_sin'] = np.sin(2 * np.pi * dt.hour / 24)
        processed['hour_cos'] = np.cos(2 * np.pi * dt.hour / 24)
        processed['day_sin'] = np.sin(2 * np.pi * dt.weekday() / 7)
        processed['day_cos'] = np.cos(2 * np.pi * dt.weekday() / 7)
        
        return processed
    
    def _is_rush_hour(self, hour: int) -> int:
        """Check if hour is during rush hour"""
        morning_rush = 7 <= hour <= 9
        evening_rush = 17 <= hour <= 19
        return 1 if morning_rush or evening_rush else 0
    
    def _update_feature_cache(self):
        """Update cached features for ML models"""
        if len(self.data_buffer) < 100:
            return
        
        # Convert to DataFrame for easier processing
        df = pd.DataFrame(list(self.data_buffer))
        
        # Calculate rolling statistics
        for window in self.time_windows:
            df[f'volume_ma_{window}'] = df['vehicle_count'].rolling(window=window).mean()
            df[f'speed_ma_{window}'] = df['average_speed'].rolling(window=window).mean()
            df[f'volume_std_{window}'] = df['vehicle_count'].rolling(window=window).std()
        
        # Calculate lag features
        for lag in self.lag_periods:
            df[f'volume_lag_{lag}'] = df['vehicle_count'].shift(lag)
            df[f'speed_lag_{lag}'] = df['average_speed'].shift(lag)
        
        # Calculate seasonal features
        for period in self.seasonal_periods:
            df[f'volume_seasonal_{period}'] = df['vehicle_count'].rolling(period).mean()
        
        # Store latest features
        if not df.empty:
            latest_features = df.iloc[-1].to_dict()
            self.feature_cache = latest_features
    
    def get_training_data(self, lookback_hours: int = 24) -> Tuple[np.ndarray, np.ndarray]:
        """Get training data for ML models"""
        if len(self.data_buffer) < 100:
            return np.array([]), np.array([])
        
        df = pd.DataFrame(list(self.data_buffer))
        
        # Filter to recent data
        cutoff_time = time.time() - (lookback_hours * 3600)
        df = df[df['timestamp'] >= cutoff_time]
        
        if len(df) < 50:
            return np.array([]), np.array([])
        
        # Prepare features and targets
        feature_columns = [col for col in df.columns if col not in ['timestamp', 'vehicle_count', 'average_speed']]
        target_columns = ['vehicle_count', 'average_speed']
        
        X = df[feature_columns].fillna(0).values
        y = df[target_columns].fillna(0).values
        
        return X, y
    
    def get_latest_features(self) -> np.ndarray:
        """Get latest features for prediction"""
        if not self.feature_cache:
            return np.array([])
        
        feature_columns = [col for col in self.feature_cache.keys() 
                         if col not in ['timestamp', 'vehicle_count', 'average_speed']]
        
        features = [self.feature_cache.get(col, 0) for col in feature_columns]
        return np.array(features)

class LSTMTrafficPredictor:
    """LSTM-based traffic prediction model"""
    
    def __init__(self, sequence_length: int = 24, n_features: int = 20):
        self.sequence_length = sequence_length
        self.n_features = n_features
        self.model = None
        self.scaler = MinMaxScaler()
        self.is_trained = False
        
        self._build_model()
        logger.info("LSTM traffic predictor initialized")
    
    def _build_model(self):
        """Build LSTM model architecture"""
        self.model = keras.Sequential([
            keras.layers.LSTM(50, return_sequences=True, input_shape=(self.sequence_length, self.n_features)),
            keras.layers.Dropout(0.2),
            keras.layers.LSTM(50, return_sequences=False),
            keras.layers.Dropout(0.2),
            keras.layers.Dense(25, activation='relu'),
            keras.layers.Dense(10, activation='relu'),
            keras.layers.Dense(2, activation='linear')  # Predict volume and speed
        ])
        
        self.model.compile(
            optimizer='adam',
            loss='mse',
            metrics=['mae', 'mse']
        )
    
    def train(self, X: np.ndarray, y: np.ndarray, epochs: int = 50, batch_size: int = 32):
        """Train LSTM model"""
        if len(X) < self.sequence_length:
            logger.warning("Insufficient data for LSTM training")
            return
        
        # Prepare sequences
        X_sequences, y_sequences = self._prepare_sequences(X, y)
        
        if len(X_sequences) == 0:
            logger.warning("No valid sequences for training")
            return
        
        # Scale features
        X_reshaped = X_sequences.reshape(-1, X_sequences.shape[-1])
        X_scaled = self.scaler.fit_transform(X_reshaped)
        X_scaled = X_scaled.reshape(X_sequences.shape)
        
        # Scale targets
        y_scaler = MinMaxScaler()
        y_scaled = y_scaler.fit_transform(y_sequences)
        
        # Train model
        history = self.model.fit(
            X_scaled, y_scaled,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=0.2,
            verbose=0
        )
        
        self.is_trained = True
        self.y_scaler = y_scaler
        
        logger.info(f"LSTM model trained with {len(X_sequences)} sequences")
        return history
    
    def _prepare_sequences(self, X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare sequences for LSTM training"""
        X_sequences, y_sequences = [], []
        
        for i in range(self.sequence_length, len(X)):
            X_sequences.append(X[i-self.sequence_length:i])
            y_sequences.append(y[i])
        
        return np.array(X_sequences), np.array(y_sequences)
    
    def predict(self, features: np.ndarray, steps_ahead: int = 1) -> np.ndarray:
        """Make traffic prediction"""
        if not self.is_trained:
            logger.warning("Model not trained")
            return np.array([0, 0])
        
        # Get last sequence
        if len(features) < self.n_features:
            return np.array([0, 0])
        
        # Reshape for prediction
        features_reshaped = features.reshape(1, -1, self.n_features)
        
        # Scale features
        features_scaled = self.scaler.transform(features_reshaped.reshape(-1, self.n_features))
        features_scaled = features_scaled.reshape(1, -1, self.n_features)
        
        # Make prediction
        prediction_scaled = self.model.predict(features_scaled, verbose=0)
        
        # Inverse scale
        prediction = self.y_scaler.inverse_transform(prediction_scaled)
        
        return prediction[0]  # Return [volume, speed]

class EnsembleTrafficPredictor:
    """Ensemble of multiple prediction models"""
    
    def __init__(self):
        self.models = {}
        self.model_weights = {}
        self.is_trained = False
        
        # Initialize individual models
        self.models['lstm'] = LSTMTrafficPredictor()
        self.models['random_forest'] = RandomForestRegressor(n_estimators=100, random_state=42)
        
        # Default weights (can be optimized)
        self.model_weights = {
            'lstm': 0.6,
            'random_forest': 0.4
        }
        
        logger.info("Ensemble traffic predictor initialized")
    
    def train(self, X: np.ndarray, y: np.ndarray):
        """Train all models in ensemble"""
        logger.info("Training ensemble models...")
        
        # Train LSTM
        if hasattr(self.models['lstm'], 'train'):
            self.models['lstm'].train(X, y)
        
        # Train Random Forest
        self.models['random_forest'].fit(X, y)
        
        self.is_trained = True
        logger.info("Ensemble training completed")
    
    def predict(self, features: np.ndarray) -> np.ndarray:
        """Make ensemble prediction"""
        if not self.is_trained:
            return np.array([0, 0])
        
        predictions = {}
        
        # Get predictions from each model
        for model_name, model in self.models.items():
            try:
                if model_name == 'lstm':
                    pred = model.predict(features)
                else:
                    pred = model.predict(features.reshape(1, -1))
                predictions[model_name] = pred
            except Exception as e:
                logger.error(f"Error in model {model_name}: {e}")
                predictions[model_name] = np.array([0, 0])
        
        # Weighted ensemble
        ensemble_pred = np.zeros(2)
        total_weight = 0
        
        for model_name, pred in predictions.items():
            weight = self.model_weights.get(model_name, 0)
            ensemble_pred += weight * pred
            total_weight += weight
        
        if total_weight > 0:
            ensemble_pred /= total_weight
        
        return ensemble_pred

class SocialMediaAnalyzer:
    """Social media analysis for traffic event detection"""
    
    def __init__(self):
        self.keywords = {
            'traffic': ['traffic jam', 'congestion', 'heavy traffic', 'traffic accident'],
            'accident': ['accident', 'crash', 'collision', 'car crash', 'pileup'],
            'construction': ['road work', 'construction', 'lane closure', 'road closure'],
            'weather': ['flooding', 'snow', 'ice', 'fog', 'poor visibility'],
            'event': ['concert', 'sports', 'parade', 'festival', 'marathon']
        }
        
        self.location_keywords = ['intersection', 'highway', 'freeway', 'road', 'street']
        
        # Social media APIs (would need actual API keys)
        self.twitter_api = None  # Would initialize with API keys
        self.reddit_api = None
        
        # Event buffer
        self.detected_events = deque(maxlen=100)
        
        logger.info("Social media analyzer initialized")
    
    def analyze_traffic_impact(self, text: str, location: str = None) -> Dict[str, Any]:
        """Analyze text for traffic impact"""
        text_lower = text.lower()
        
        # Detect event types
        detected_events = {}
        for event_type, keywords in self.keywords.items():
            matches = [kw for kw in keywords if kw in text_lower]
            if matches:
                detected_events[event_type] = matches
        
        # Detect location mentions
        location_mentions = []
        if location:
            location_lower = location.lower()
            for loc_kw in self.location_keywords:
                if loc_kw in text_lower or loc_kw in location_lower:
                    location_mentions.append(loc_kw)
        
        # Calculate impact score
        impact_score = self._calculate_impact_score(detected_events, text_lower)
        
        return {
            'text': text,
            'detected_events': detected_events,
            'location_mentions': location_mentions,
            'impact_score': impact_score,
            'timestamp': time.time()
        }
    
    def _calculate_impact_score(self, events: Dict[str, List[str]], text: str) -> float:
        """Calculate traffic impact score"""
        base_score = 0
        
        # High impact events
        if 'accident' in events:
            base_score += 0.8
        if 'construction' in events:
            base_score += 0.6
        
        # Medium impact events
        if 'traffic' in events:
            base_score += 0.4
        if 'weather' in events:
            base_score += 0.3
        
        # Event impact
        if 'event' in events:
            base_score += 0.5
        
        # Urgency indicators
        urgency_words = ['urgent', 'emergency', 'severe', 'major', 'blocked']
        urgency_count = sum(1 for word in urgency_words if word in text)
        base_score += urgency_count * 0.1
        
        return min(1.0, base_score)
    
    def simulate_social_media_data(self) -> List[Dict[str, Any]]:
        """Simulate social media data (replace with real API calls)"""
        # Generate sample social media posts
        sample_posts = [
            "Major traffic jam on Highway 101 due to accident",
            "Road construction causing delays on Main Street",
            "Heavy concert traffic expected downtown tonight",
            "Flooding reported on Interstate 5, avoid area",
            "Multi-car pileup on freeway, all lanes blocked"
        ]
        
        analyzed_posts = []
        for post in sample_posts:
            if np.random.random() < 0.1:  # 10% chance per check
                analysis = self.analyze_traffic_impact(post)
                if analysis['impact_score'] > 0.3:
                    analyzed_posts.append(analysis)
        
        return analyzed_posts

class AnomalyDetector:
    """Traffic anomaly detection system"""
    
    def __init__(self):
        self.isolation_forest = IsolationForest(contamination=0.1, random_state=42)
        self.baseline_stats = {}
        self.anomaly_threshold = 2.0  # Standard deviations from baseline
        
        # Anomaly history
        self.anomaly_history = deque(maxlen=100)
        
        logger.info("Anomaly detector initialized")
    
    def fit_baseline(self, traffic_data: List[Dict[str, Any]]):
        """Fit baseline traffic patterns"""
        if not traffic_data:
            return
        
        df = pd.DataFrame(traffic_data)
        
        # Calculate baseline statistics by hour and day
        self.baseline_stats = {}
        
        for hour in range(24):
            for day in range(7):
                hour_data = df[(df['hour'] == hour) & (df['day_of_week'] == day)]
                
                if len(hour_data) > 0:
                    self.baseline_stats[f"{hour}_{day}"] = {
                        'mean_volume': hour_data['vehicle_count'].mean(),
                        'std_volume': hour_data['vehicle_count'].std(),
                        'mean_speed': hour_data['average_speed'].mean(),
                        'std_speed': hour_data['average_speed'].std()
                    }
        
        # Train isolation forest
        feature_columns = ['vehicle_count', 'average_speed', 'hour', 'day_of_week']
        X = df[feature_columns].fillna(0)
        self.isolation_forest.fit(X)
        
        logger.info("Baseline patterns fitted")
    
    def detect_anomalies(self, current_data: Dict[str, Any]) -> List[AnomalyDetection]:
        """Detect anomalies in current traffic data"""
        anomalies = []
        
        # Statistical anomaly detection
        stat_anomaly = self._detect_statistical_anomaly(current_data)
        if stat_anomaly:
            anomalies.append(stat_anomaly)
        
        # Isolation forest anomaly detection
        ml_anomaly = self._detect_ml_anomaly(current_data)
        if ml_anomaly:
            anomalies.append(ml_anomaly)
        
        # Pattern anomaly detection
        pattern_anomaly = self._detect_pattern_anomaly(current_data)
        if pattern_anomaly:
            anomalies.append(pattern_anomaly)
        
        return anomalies
    
    def _detect_statistical_anomaly(self, data: Dict[str, Any]) -> Optional[AnomalyDetection]:
        """Detect statistical anomalies"""
        hour = data.get('hour', datetime.now().hour)
        day = data.get('day_of_week', datetime.now().weekday())
        
        key = f"{hour}_{day}"
        if key not in self.baseline_stats:
            return None
        
        baseline = self.baseline_stats[key]
        current_volume = data.get('vehicle_count', 0)
        current_speed = data.get('average_speed', 0)
        
        # Z-score calculation
        volume_z = abs(current_volume - baseline['mean_volume']) / max(0.1, baseline['std_volume'])
        speed_z = abs(current_speed - baseline['mean_speed']) / max(0.1, baseline['std_speed'])
        
        if volume_z > self.anomaly_threshold or speed_z > self.anomaly_threshold:
            return AnomalyDetection(
                anomaly_id=f"STAT_{int(time.time())}",
                anomaly_type=AnomalyType.UNUSUAL_PATTERN,
                severity='high' if volume_z > 3 else 'medium',
                confidence=min(1.0, max(volume_z, speed_z) / 3),
                location=data.get('intersection_id', 'unknown'),
                timestamp=time.time(),
                description=f"Unusual traffic pattern detected: Volume Z-score: {volume_z:.2f}, Speed Z-score: {speed_z:.2f}",
                affected_metrics=['vehicle_count', 'average_speed'],
                recommended_action='Investigate unusual traffic conditions'
            )
        
        return None
    
    def _detect_ml_anomaly(self, data: Dict[str, Any]) -> Optional[AnomalyDetection]:
        """Detect anomalies using machine learning"""
        features = [
            data.get('vehicle_count', 0),
            data.get('average_speed', 0),
            data.get('hour', 0),
            data.get('day_of_week', 0)
        ]
        
        # Predict anomaly score
        anomaly_score = self.isolation_forest.decision_function([features])[0]
        
        if anomaly_score < 0:  # Negative score indicates anomaly
            confidence = abs(anomaly_score)
            
            return AnomalyDetection(
                anomaly_id=f"ML_{int(time.time())}",
                anomaly_type=AnomalyType.INCIDENT_IMPACT,
                severity='high' if confidence > 0.5 else 'medium',
                confidence=min(1.0, confidence),
                location=data.get('intersection_id', 'unknown'),
                timestamp=time.time(),
                description=f"ML-based anomaly detected with score: {anomaly_score:.3f}",
                affected_metrics=['all'],
                recommended_action='Check for traffic incidents or equipment issues'
            )
        
        return None
    
    def _detect_pattern_anomaly(self, data: Dict[str, Any]) -> Optional[AnomalyDetection]:
        """Detect pattern-based anomalies"""
        # Sudden drop in speed with high volume (congestion)
        volume = data.get('vehicle_count', 0)
        speed = data.get('average_speed', 0)
        
        if volume > 50 and speed < 15:  # High volume, low speed
            return AnomalyDetection(
                anomaly_id=f"PATTERN_{int(time.time())}",
                anomaly_type=AnomalyType.SUDDEN_CONGESTION,
                severity='high' if volume > 100 else 'medium',
                confidence=min(1.0, volume / 100),
                location=data.get('intersection_id', 'unknown'),
                timestamp=time.time(),
                description=f"Sudden congestion detected: Volume={volume}, Speed={speed}",
                affected_metrics=['vehicle_count', 'average_speed'],
                recommended_action='Consider traffic signal adjustment or diversion'
            )
        
        return None

class PredictiveAnalyticsEngine:
    """Main predictive analytics engine"""
    
    def __init__(self):
        self.data_processor = TrafficDataProcessor()
        self.predictor = EnsembleTrafficPredictor()
        self.anomaly_detector = AnomalyDetector()
        self.social_analyzer = SocialMediaAnalyzer()
        
        # Prediction cache
        self.prediction_cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        # Training data
        self.training_data = []
        self.last_training_time = 0
        self.training_interval = 86400  # 24 hours
        
        # Background processing
        self.running = False
        self.processing_thread = None
        
        logger.info("Predictive analytics engine initialized")
    
    def start_processing(self):
        """Start background processing"""
        self.running = True
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()
        logger.info("Predictive analytics processing started")
    
    def stop_processing(self):
        """Stop background processing"""
        self.running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=5)
        logger.info("Predictive analytics processing stopped")
    
    def _processing_loop(self):
        """Main processing loop"""
        while self.running:
            try:
                # Process social media data
                social_events = self.social_analyzer.simulate_social_media_data()
                for event in social_events:
                    self._process_social_event(event)
                
                # Check if retraining is needed
                current_time = time.time()
                if current_time - self.last_training_time > self.training_interval:
                    self._retrain_models()
                    self.last_training_time = current_time
                
                # Clean old predictions
                self._clean_prediction_cache()
                
                time.sleep(60)  # Process every minute
                
            except Exception as e:
                logger.error(f"Error in processing loop: {e}")
                time.sleep(10)
    
    def add_traffic_data(self, data: Dict[str, Any]):
        """Add traffic data for analysis"""
        self.data_processor.add_traffic_data(data)
        self.training_data.append(data)
        
        # Detect anomalies
        anomalies = self.anomaly_detector.detect_anomalies(data)
        for anomaly in anomalies:
            self._handle_anomaly(anomaly)
    
    def _process_social_event(self, event: Dict[str, Any]):
        """Process social media event"""
        impact_score = event.get('impact_score', 0)
        
        if impact_score > 0.5:
            # High impact event - adjust predictions
            self._adjust_predictions_for_event(event)
            
            logger.warning(f"High impact social event detected: {event.get('text', '')}")
    
    def _handle_anomaly(self, anomaly: AnomalyDetection):
        """Handle detected anomaly"""
        self.anomaly_detector.anomaly_history.append(anomaly)
        
        # Trigger appropriate response
        if anomaly.severity == 'critical':
            self._trigger_emergency_response(anomaly)
        elif anomaly.severity == 'high':
            self._trigger_alert(anomaly)
        
        logger.warning(f"Anomaly detected: {anomaly.description}")
    
    def _trigger_emergency_response(self, anomaly: AnomalyDetection):
        """Trigger emergency response for critical anomalies"""
        # In real implementation, would:
        # - Notify traffic management center
        # - Adjust signal timing
        # - Dispatch traffic units
        # - Update public information systems
        
        logger.critical(f"Emergency response triggered for anomaly: {anomaly.anomaly_id}")
    
    def _trigger_alert(self, anomaly: AnomalyDetection):
        """Trigger alert for high severity anomalies"""
        # In real implementation, would:
        # - Send notifications
        # - Update dashboards
        # - Log incident
        
        logger.error(f"Alert triggered for anomaly: {anomaly.anomaly_id}")
    
    def _adjust_predictions_for_event(self, event: Dict[str, Any]):
        """Adjust predictions based on external events"""
        # Increase predicted volume for event areas
        impact_multiplier = 1 + event.get('impact_score', 0)
        
        # Update prediction cache with event adjustments
        for prediction_id in self.prediction_cache:
            prediction = self.prediction_cache[prediction_id]
            prediction['predicted_volume'] *= impact_multiplier
            prediction['metadata']['event_adjustment'] = True
    
    def _retrain_models(self):
        """Retrain prediction models with new data"""
        if len(self.training_data) < 1000:
            logger.info("Insufficient data for retraining")
            return
        
        logger.info("Retraining predictive models...")
        
        # Get training data
        X, y = self.data_processor.get_training_data(lookback_hours=168)  # 1 week
        
        if len(X) > 0:
            # Train ensemble predictor
            self.predictor.train(X, y)
            
            # Retrain anomaly detector
            self.anomaly_detector.fit_baseline(self.training_data[-1000:])
            
            logger.info("Model retraining completed")
    
    def _clean_prediction_cache(self):
        """Clean expired predictions from cache"""
        current_time = time.time()
        expired_keys = [
            key for key, pred in self.prediction_cache.items()
            if current_time - pred['timestamp'] > self.cache_ttl
        ]
        
        for key in expired_keys:
            del self.prediction_cache[key]
    
    def generate_predictions(self, horizon: PredictionHorizon, 
                          location: str = None) -> List[TrafficPrediction]:
        """Generate traffic predictions"""
        current_time = time.time()
        
        # Check cache first
        cache_key = f"{horizon.value}_{location or 'all'}"
        if cache_key in self.prediction_cache:
            cached = self.prediction_cache[cache_key]
            if current_time - cached['timestamp'] < 60:  # 1 minute cache
                return [cached['prediction']]
        
        # Get latest features
        features = self.data_processor.get_latest_features()
        if len(features) == 0:
            return []
        
        # Generate predictions for different time horizons
        predictions = []
        
        if horizon == PredictionHorizon.SHORT_TERM:
            # 15-30 minute predictions
            for minutes_ahead in [15, 30]:
                prediction = self._create_prediction(
                    features, horizon, minutes_ahead * 60, location
                )
                predictions.append(prediction)
        
        elif horizon == PredictionHorizon.MEDIUM_TERM:
            # 1-4 hour predictions
            for hours_ahead in [1, 2, 4]:
                prediction = self._create_prediction(
                    features, horizon, hours_ahead * 3600, location
                )
                predictions.append(prediction)
        
        elif horizon == PredictionHorizon.LONG_TERM:
            # 6-24 hour predictions
            for hours_ahead in [6, 12, 24]:
                prediction = self._create_prediction(
                    features, horizon, hours_ahead * 3600, location
                )
                predictions.append(prediction)
        
        # Cache predictions
        if predictions:
            self.prediction_cache[cache_key] = {
                'prediction': predictions[0],  # Store first prediction
                'timestamp': current_time
            }
        
        return predictions
    
    def _create_prediction(self, features: np.ndarray, horizon: PredictionHorizon,
                         seconds_ahead: int, location: str) -> TrafficPrediction:
        """Create individual prediction"""
        # Make prediction
        predicted_values = self.predictor.predict(features)
        predicted_volume = max(0, predicted_values[0])
        predicted_speed = max(0, predicted_values[1])
        
        # Calculate confidence based on horizon
        base_confidence = 0.8
        if horizon == PredictionHorizon.SHORT_TERM:
            confidence = base_confidence
        elif horizon == PredictionHorizon.MEDIUM_TERM:
            confidence = base_confidence * 0.8
        elif horizon == PredictionHorizon.LONG_TERM:
            confidence = base_confidence * 0.6
        
        return TrafficPrediction(
            prediction_id=f"PRED_{int(time.time())}_{horizon.value}",
            model_type=PredictionModel.ENSEMBLE,
            horizon=horizon,
            timestamp=time.time(),
            target_time=time.time() + seconds_ahead,
            predicted_volume=predicted_volume,
            predicted_speed=predicted_speed,
            confidence=confidence,
            features_used=list(range(len(features))),
            model_version="3.0.0",
            metadata={
                'location': location,
                'seconds_ahead': seconds_ahead,
                'prediction_method': 'ensemble'
            }
        )
    
    def get_anomaly_summary(self) -> Dict[str, Any]:
        """Get summary of recent anomalies"""
        if not self.anomaly_detector.anomaly_history:
            return {
                'total_anomalies': 0,
                'recent_anomalies': [],
                'anomaly_types': {},
                'severity_distribution': {}
            }
        
        recent_anomalies = list(self.anomaly_detector.anomaly_history)[-50:]  # Last 50
        
        # Count by type and severity
        type_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        
        for anomaly in recent_anomalies:
            type_counts[anomaly.anomaly_type.value] += 1
            severity_counts[anomaly.severity] += 1
        
        return {
            'total_anomalies': len(self.anomaly_detector.anomaly_history),
            'recent_anomalies': len(recent_anomalies),
            'anomaly_types': dict(type_counts),
            'severity_distribution': dict(severity_counts),
            'last_anomaly': recent_anomalies[-1].timestamp if recent_anomalies else None
        }
    
    def get_model_performance(self) -> Dict[str, Any]:
        """Get model performance metrics"""
        return {
            'models_trained': self.predictor.is_trained,
            'last_training': self.last_training_time,
            'training_data_points': len(self.training_data),
            'cache_size': len(self.prediction_cache),
            'anomaly_detector_trained': len(self.anomaly_detector.baseline_stats) > 0,
            'social_media_events_processed': len(self.social_analyzer.detected_events)
        }

# Factory functions
def create_predictive_engine() -> PredictiveAnalyticsEngine:
    """Create predictive analytics engine"""
    return PredictiveAnalyticsEngine()

# Export main classes
__all__ = [
    'PredictiveAnalyticsEngine',
    'EnsembleTrafficPredictor',
    'LSTMTrafficPredictor',
    'TrafficDataProcessor',
    'AnomalyDetector',
    'SocialMediaAnalyzer',
    'TrafficPrediction',
    'AnomalyDetection',
    'PredictionModel',
    'PredictionHorizon',
    'AnomalyType',
    'create_predictive_engine'
]