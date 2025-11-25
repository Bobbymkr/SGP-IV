"""
Predictive Analytics Module

Implements Graph Neural Networks, Transformers, and Social Media integration
for advanced traffic prediction and forecasting.
"""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.nn import GCNConv, GATConv, GraphConv
from torch_geometric.data import Data, Batch
import networkx as nx
from typing import List, Dict, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import logging
from collections import defaultdict, deque
import math
import requests
import re
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error

logger = logging.getLogger(__name__)


@dataclass
class TrafficNode:
    """Traffic intersection node data"""
    node_id: str
    latitude: float
    longitude: float
    features: Dict[str, float] = field(default_factory=dict)
    historical_data: List[Dict] = field(default_factory=list)
    connectivity: List[str] = field(default_factory=list)


@dataclass
class TrafficEdge:
    """Traffic road segment edge data"""
    source: str
    target: str
    distance: float
    capacity: float
    current_flow: float
    travel_time: float
    features: Dict[str, float] = field(default_factory=dict)


@dataclass
class SocialMediaEvent:
    """Social media traffic event"""
    platform: str
    post_id: str
    content: str
    timestamp: datetime
    location: Tuple[float, float]  # (lat, lon)
    confidence: float
    event_type: str
    impact_score: float


class GraphNeuralNetwork(nn.Module):
    """Graph Neural Network for city-wide traffic prediction"""
    
    def __init__(self, 
                 node_features: int,
                 edge_features: int,
                 hidden_dim: int = 128,
                 num_layers: int = 3,
                 gnn_type: str = 'gcn',
                 prediction_horizon: int = 12):
        super().__init__()
        
        self.node_features = node_features
        self.edge_features = edge_features
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.prediction_horizon = prediction_horizon
        
        # GNN layers
        self.gnn_layers = nn.ModuleList()
        
        if gnn_type == 'gcn':
            self.gnn_layers.append(GCNConv(node_features, hidden_dim))
            for _ in range(num_layers - 1):
                self.gnn_layers.append(GCNConv(hidden_dim, hidden_dim))
        elif gnn_type == 'gat':
            self.gnn_layers.append(GATConv(node_features, hidden_dim, heads=4, concat=False))
            for _ in range(num_layers - 1):
                self.gnn_layers.append(GATConv(hidden_dim, hidden_dim, heads=4, concat=False))
        elif gnn_type == 'graphconv':
            self.gnn_layers.append(GraphConv(node_features, hidden_dim))
            for _ in range(num_layers - 1):
                self.gnn_layers.append(GraphConv(hidden_dim, hidden_dim))
        
        # Temporal processing
        self.temporal_encoder = nn.LSTM(
            input_size=hidden_dim,
            hidden_size=hidden_dim,
            num_layers=2,
            batch_first=True,
            dropout=0.2
        )
        
        # Edge processing
        self.edge_encoder = nn.Sequential(
            nn.Linear(edge_features, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim)
        )
        
        # Prediction heads
        self.flow_predictor = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, prediction_horizon)
        )
        
        self.speed_predictor = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, prediction_horizon)
        )
        
        self.congestion_predictor = nn.Sequential(
            nn.Linear(hidden_dim * 2, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, prediction_horizon),
            nn.Sigmoid()
        )
    
    def forward(self, 
                node_features: torch.Tensor,
                edge_index: torch.Tensor,
                edge_features: torch.Tensor,
                historical_sequence: Optional[torch.Tensor] = None) -> Dict[str, torch.Tensor]:
        """Forward pass through GNN"""
        
        # Graph convolution
        x = node_features
        for gnn_layer in self.gnn_layers:
            x = gnn_layer(x, edge_index)
            x = F.relu(x)
            x = F.dropout(x, p=0.2, training=self.training)
        
        # Process edges
        edge_emb = self.edge_encoder(edge_features)
        
        # Temporal processing if historical data provided
        if historical_sequence is not None:
            # Reshape for LSTM: [batch, seq_len, features]
            h, _ = self.temporal_encoder(historical_sequence)
            temporal_emb = h[:, -1, :]  # Use last time step
            x = x + temporal_emb  # Residual connection
        
        # Combine node and edge information
        # Aggregate edge information for each node
        row, col = edge_index
        edge_aggregation = torch.zeros_like(x)
        edge_aggregation.index_add_(0, row, edge_emb)
        edge_aggregation = edge_aggregation / (torch.bincount(row, minlength=x.size(0)).unsqueeze(1) + 1e-6)
        
        combined_features = torch.cat([x, edge_aggregation], dim=1)
        
        # Predictions
        flow_pred = self.flow_predictor(combined_features)
        speed_pred = self.speed_predictor(combined_features)
        congestion_pred = self.congestion_predictor(combined_features)
        
        return {
            'flow': flow_pred,
            'speed': speed_pred,
            'congestion': congestion_pred,
            'node_embeddings': x
        }


class TrafficTransformer(nn.Module):
    """Transformer model for long-term traffic forecasting"""
    
    def __init__(self,
                 input_dim: int,
                 d_model: int = 256,
                 nhead: int = 8,
                 num_layers: int = 6,
                 dim_feedforward: int = 512,
                 dropout: float = 0.1,
                 prediction_horizon: int = 24,
                 sequence_length: int = 48):
        super().__init__()
        
        self.d_model = d_model
        self.prediction_horizon = prediction_horizon
        self.sequence_length = sequence_length
        
        # Input embedding
        self.input_embedding = nn.Linear(input_dim, d_model)
        self.positional_encoding = PositionalEncoding(d_model, dropout)
        
        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            activation='relu',
            batch_first=True
        )
        self.transformer_encoder = nn.TransformerEncoder(encoder_layer, num_layers)
        
        # External factors embedding (weather, events, etc.)
        self.external_embedding = nn.Sequential(
            nn.Linear(10, d_model // 4),  # 10 external features
            nn.ReLU(),
            nn.Linear(d_model // 4, d_model // 4)
        )
        
        # Decoder for prediction
        self.decoder = nn.Sequential(
            nn.Linear(d_model + d_model // 4, d_model),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_model, d_model // 2),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_model // 2, prediction_horizon)
        )
        
        # Multi-task heads
        self.flow_head = nn.Linear(prediction_horizon, prediction_horizon)
        self.speed_head = nn.Linear(prediction_horizon, prediction_horizon)
        self.demand_head = nn.Linear(prediction_horizon, prediction_horizon)
        
    def forward(self, 
                input_sequence: torch.Tensor,
                external_factors: Optional[torch.Tensor] = None,
                mask: Optional[torch.Tensor] = None) -> Dict[str, torch.Tensor]:
        """Forward pass through transformer"""
        
        # Input embedding
        x = self.input_embedding(input_sequence) * math.sqrt(self.d_model)
        x = self.positional_encoding(x)
        
        # Transformer encoding
        encoded = self.transformer_encoder(x, src_key_padding_mask=mask)
        
        # Use the last encoded state for prediction
        encoded_last = encoded[:, -1, :]  # [batch, d_model]
        
        # Process external factors
        if external_factors is not None:
            external_emb = self.external_embedding(external_factors)
            combined = torch.cat([encoded_last, external_emb], dim=1)
        else:
            combined = encoded_last
        
        # Decode to predictions
        predictions = self.decoder(combined)
        
        # Multi-task outputs
        flow_pred = self.flow_head(predictions)
        speed_pred = self.speed_head(predictions)
        demand_pred = self.demand_head(predictions)
        
        return {
            'flow': flow_pred,
            'speed': speed_pred,
            'demand': demand_pred,
            'encoded_features': encoded_last
        }


class PositionalEncoding(nn.Module):
    """Positional encoding for transformer"""
    
    def __init__(self, d_model: int, dropout: float = 0.1, max_len: int = 5000):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)
        
        position = torch.arange(max_len).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2) * (-math.log(10000.0) / d_model))
        pe = torch.zeros(max_len, 1, d_model)
        pe[:, 0, 0::2] = torch.sin(position * div_term)
        pe[:, 0, 1::2] = torch.cos(position * div_term)
        self.register_buffer('pe', pe)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.pe[:x.size(0)].transpose(0, 1)
        return self.dropout(x)


class SocialMediaAnalyzer:
    """Social media integration for traffic event detection"""
    
    def __init__(self):
        # Traffic-related keywords
        self.traffic_keywords = {
            'accident': ['accident', 'crash', 'collision', 'wreck', 'pileup'],
            'congestion': ['traffic', 'jam', 'congestion', 'backup', 'gridlock'],
            'construction': ['construction', 'roadwork', 'closure', 'detour', 'maintenance'],
            'weather': ['snow', 'rain', 'flood', 'ice', 'storm', 'fog'],
            'events': ['concert', 'game', 'parade', 'festival', 'marathon']
        }
        
        # Event impact scores
        self.impact_scores = {
            'accident': 0.9,
            'congestion': 0.5,
            'construction': 0.6,
            'weather': 0.7,
            'events': 0.8
        }
        
        # Platform weights (reliability scores)
        self.platform_weights = {
            'twitter': 0.8,
            'facebook': 0.6,
            'instagram': 0.4,
            'reddit': 0.7,
            'news': 0.9
        }
        
        # Location extraction patterns
        self.location_patterns = [
            r'at\s+([A-Z][a-z]+\s+(Street|St|Ave|Avenue|Blvd|Boulevard|Road|Rd))',
            r'near\s+([A-Z][a-z]+\s+(Street|St|Ave|Avenue|Blvd|Boulevard|Road|Rd))',
            r'intersection\s+of\s+([A-Z][a-z]+\s+(and|&)\s+[A-Z][a-z]+)',
            r'on\s+([A-Z][a-z]+\s+(Highway|Hwy|Interstate|I-\d+))'
        ]
    
    def analyze_post(self, content: str, platform: str, 
                    timestamp: datetime, location: Optional[Tuple[float, float]] = None) -> Optional[SocialMediaEvent]:
        """Analyze social media post for traffic events"""
        
        # Detect event type
        event_type = self._detect_event_type(content)
        if not event_type:
            return None
        
        # Calculate confidence
        confidence = self._calculate_confidence(content, platform, event_type)
        if confidence < 0.3:  # Minimum confidence threshold
            return None
        
        # Extract location
        extracted_location = self._extract_location(content)
        final_location = location or extracted_location
        
        # Calculate impact score
        impact_score = self.impact_scores[event_type] * confidence * self.platform_weights.get(platform, 0.5)
        
        return SocialMediaEvent(
            platform=platform,
            post_id=f"{platform}_{timestamp.timestamp()}",
            content=content,
            timestamp=timestamp,
            location=final_location,
            confidence=confidence,
            event_type=event_type,
            impact_score=impact_score
        )
    
    def _detect_event_type(self, content: str) -> Optional[str]:
        """Detect traffic event type from content"""
        content_lower = content.lower()
        
        for event_type, keywords in self.traffic_keywords.items():
            for keyword in keywords:
                if keyword in content_lower:
                    return event_type
        
        return None
    
    def _calculate_confidence(self, content: str, platform: str, event_type: str) -> float:
        """Calculate confidence score for event detection"""
        confidence = 0.0
        
        # Platform reliability
        confidence += self.platform_weights.get(platform, 0.5) * 0.3
        
        # Keyword matching
        content_lower = content.lower()
        keywords = self.traffic_keywords.get(event_type, [])
        keyword_matches = sum(1 for kw in keywords if kw in content_lower)
        confidence += min(keyword_matches / len(keywords), 1.0) * 0.4
        
        # Content length (longer posts often more reliable)
        length_score = min(len(content) / 200, 1.0)
        confidence += length_score * 0.1
        
        # Urgency indicators
        urgency_words = ['now', 'happening', 'currently', 'right now', 'emergency']
        urgency_matches = sum(1 for word in urgency_words if word in content_lower)
        confidence += min(urgency_matches / len(urgency_words), 1.0) * 0.2
        
        return min(confidence, 1.0)
    
    def _extract_location(self, content: str) -> Optional[Tuple[float, float]]:
        """Extract location from content (simplified)"""
        # In real implementation, this would use geocoding APIs
        for pattern in self.location_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                # Return dummy coordinates for demo
                # In real implementation, geocode the location
                return (40.7128, -74.0060)  # NYC coordinates as placeholder
        
        return None
    
    def aggregate_events(self, events: List[SocialMediaEvent], 
                        time_window: timedelta = timedelta(minutes=30),
                        spatial_radius: float = 1.0) -> List[Dict]:
        """Aggregate similar events in time and space"""
        if not events:
            return []
        
        # Sort by timestamp
        events.sort(key=lambda e: e.timestamp)
        
        aggregated = []
        current_cluster = [events[0]]
        
        for event in events[1:]:
            # Check if event belongs to current cluster
            if self._should_cluster(event, current_cluster[0], time_window, spatial_radius):
                current_cluster.append(event)
            else:
                # Process current cluster
                aggregated.append(self._process_cluster(current_cluster))
                current_cluster = [event]
        
        # Process last cluster
        if current_cluster:
            aggregated.append(self._process_cluster(current_cluster))
        
        return aggregated
    
    def _should_cluster(self, event1: SocialMediaEvent, event2: SocialMediaEvent,
                       time_window: timedelta, spatial_radius: float) -> bool:
        """Check if two events should be clustered together"""
        # Time proximity
        time_diff = abs(event1.timestamp - event2.timestamp)
        if time_diff > time_window:
            return False
        
        # Spatial proximity (if both have locations)
        if event1.location and event2.location:
            distance = self._calculate_distance(event1.location, event2.location)
            if distance > spatial_radius:
                return False
        
        # Event type similarity
        if event1.event_type != event2.event_type:
            return False
        
        return True
    
    def _calculate_distance(self, loc1: Tuple[float, float], 
                           loc2: Tuple[float, float]) -> float:
        """Calculate distance between two coordinates"""
        # Simplified distance calculation
        lat_diff = loc1[0] - loc2[0]
        lon_diff = loc1[1] - loc2[1]
        return math.sqrt(lat_diff**2 + lon_diff**2)
    
    def _process_cluster(self, cluster: List[SocialMediaEvent]) -> Dict:
        """Process a cluster of events"""
        if not cluster:
            return {}
        
        # Aggregate information
        event_type = cluster[0].event_type
        platforms = list(set(e.platform for e in cluster))
        
        # Calculate aggregated confidence
        confidences = [e.confidence for e in cluster]
        avg_confidence = np.mean(confidences)
        
        # Calculate aggregated impact
        impacts = [e.impact_score for e in cluster]
        total_impact = sum(impacts)
        
        # Time range
        start_time = min(e.timestamp for e in cluster)
        end_time = max(e.timestamp for e in cluster)
        
        # Location (average if available)
        locations = [e.location for e in cluster if e.location]
        avg_location = np.mean(locations, axis=0) if locations else None
        
        return {
            'event_type': event_type,
            'platforms': platforms,
            'num_reports': len(cluster),
            'avg_confidence': avg_confidence,
            'total_impact': total_impact,
            'start_time': start_time,
            'end_time': end_time,
            'duration': (end_time - start_time).total_seconds() / 60,  # minutes
            'location': tuple(avg_location) if avg_location is not None else None,
            'reports': cluster
        }


class PredictiveAnalyticsEngine:
    """Main predictive analytics engine"""
    
    def __init__(self):
        self.gnn_model = None
        self.transformer_model = None
        self.social_analyzer = SocialMediaAnalyzer()
        
        # Data storage
        self.traffic_graph = nx.DiGraph()
        self.historical_data = defaultdict(list)
        self.social_events = deque(maxlen=1000)
        
        # Scalers
        self.node_scaler = StandardScaler()
        self.edge_scaler = StandardScaler()
        self.target_scaler = MinMaxScaler()
        
        # Model parameters
        self.node_features = 10  # flow, speed, occupancy, etc.
        self.edge_features = 5    # distance, capacity, etc.
        
    def build_traffic_graph(self, nodes: List[TrafficNode], edges: List[TrafficEdge]):
        """Build traffic network graph"""
        # Add nodes
        for node in nodes:
            self.traffic_graph.add_node(
                node.node_id,
                latitude=node.latitude,
                longitude=node.longitude,
                features=node.features
            )
        
        # Add edges
        for edge in edges:
            self.traffic_graph.add_edge(
                edge.source,
                edge.target,
                distance=edge.distance,
                capacity=edge.capacity,
                current_flow=edge.current_flow,
                travel_time=edge.travel_time,
                features=edge.features
            )
    
    def initialize_gnn(self, hidden_dim: int = 128, num_layers: int = 3):
        """Initialize Graph Neural Network"""
        self.gnn_model = GraphNeuralNetwork(
            node_features=self.node_features,
            edge_features=self.edge_features,
            hidden_dim=hidden_dim,
            num_layers=num_layers,
            gnn_type='gnn',
            prediction_horizon=12
        )
    
    def initialize_transformer(self, d_model: int = 256, num_layers: int = 6):
        """Initialize Transformer model"""
        self.transformer_model = TrafficTransformer(
            input_dim=self.node_features,
            d_model=d_model,
            num_layers=num_layers,
            prediction_horizon=24,
            sequence_length=48
        )
    
    def prepare_graph_data(self) -> Data:
        """Prepare graph data for GNN"""
        # Get node features
        node_features = []
        node_ids = []
        for node_id in self.traffic_graph.nodes():
            features = self.traffic_graph.nodes[node_id].get('features', {})
            feature_vector = [
                features.get('flow', 0),
                features.get('speed', 0),
                features.get('occupancy', 0),
                features.get('density', 0),
                features.get('travel_time', 0),
                features.get('delay', 0),
                features.get('queue_length', 0),
                features.get('stop_rate', 0),
                features.get('saturation', 0),
                features.get('level_of_service', 1)
            ]
            node_features.append(feature_vector)
            node_ids.append(node_id)
        
        # Get edge indices and features
        edge_index = []
        edge_features = []
        
        for source, target, data in self.traffic_graph.edges(data=True):
            source_idx = node_ids.index(source)
            target_idx = node_ids.index(target)
            edge_index.append([source_idx, target_idx])
            
            feature_vector = [
                data.get('distance', 1),
                data.get('capacity', 100),
                data.get('current_flow', 0),
                data.get('travel_time', 1),
                data.get('features', {}).get('congestion_index', 0)
            ]
            edge_features.append(feature_vector)
        
        # Convert to tensors
        node_features_tensor = torch.FloatTensor(node_features)
        edge_index_tensor = torch.LongTensor(edge_index).t().contiguous()
        edge_features_tensor = torch.FloatTensor(edge_features)
        
        return Data(
            x=node_features_tensor,
            edge_index=edge_index_tensor,
            edge_attr=edge_features_tensor
        )
    
    def train_gnn(self, train_data: List[Data], epochs: int = 100, 
                  learning_rate: float = 0.001):
        """Train Graph Neural Network"""
        if self.gnn_model is None:
            self.initialize_gnn()
        
        optimizer = torch.optim.Adam(self.gnn_model.parameters(), lr=learning_rate)
        criterion = nn.MSELoss()
        
        self.gnn_model.train()
        losses = []
        
        for epoch in range(epochs):
            epoch_loss = 0
            
            for data in train_data:
                optimizer.zero_grad()
                
                # Forward pass
                output = self.gnn_model(
                    data.x,
                    data.edge_index,
                    data.edge_attr
                )
                
                # Calculate loss (assuming targets are in data.y)
                if hasattr(data, 'y'):
                    loss = criterion(output['flow'], data.y)
                    loss.backward()
                    optimizer.step()
                    epoch_loss += loss.item()
            
            avg_loss = epoch_loss / len(train_data)
            losses.append(avg_loss)
            
            if epoch % 10 == 0:
                logger.info(f"GNN Epoch {epoch}, Loss: {avg_loss:.4f}")
        
        return losses
    
    def train_transformer(self, train_sequences: torch.Tensor, 
                         train_targets: torch.Tensor,
                         external_factors: Optional[torch.Tensor] = None,
                         epochs: int = 100, learning_rate: float = 0.001):
        """Train Transformer model"""
        if self.transformer_model is None:
            self.initialize_transformer()
        
        optimizer = torch.optim.Adam(self.transformer_model.parameters(), lr=learning_rate)
        criterion = nn.MSELoss()
        
        self.transformer_model.train()
        losses = []
        
        for epoch in range(epochs):
            epoch_loss = 0
            
            # Batch processing
            for i in range(0, len(train_sequences), 32):
                batch_sequences = train_sequences[i:i+32]
                batch_targets = train_targets[i:i+32]
                batch_external = external_factors[i:i+32] if external_factors is not None else None
                
                optimizer.zero_grad()
                
                # Forward pass
                output = self.transformer_model(
                    batch_sequences,
                    batch_external
                )
                
                # Calculate loss
                loss = criterion(output['flow'], batch_targets)
                loss.backward()
                optimizer.step()
                epoch_loss += loss.item()
            
            avg_loss = epoch_loss / (len(train_sequences) // 32)
            losses.append(avg_loss)
            
            if epoch % 10 == 0:
                logger.info(f"Transformer Epoch {epoch}, Loss: {avg_loss:.4f}")
        
        return losses
    
    def predict_traffic_gnn(self, graph_data: Data, 
                           historical_sequence: Optional[torch.Tensor] = None) -> Dict[str, np.ndarray]:
        """Make predictions using GNN"""
        if self.gnn_model is None:
            raise ValueError("GNN model not initialized")
        
        self.gnn_model.eval()
        with torch.no_grad():
            output = self.gnn_model(
                graph_data.x,
                graph_data.edge_index,
                graph_data.edge_attr,
                historical_sequence
            )
        
        return {
            'flow': output['flow'].cpu().numpy(),
            'speed': output['speed'].cpu().numpy(),
            'congestion': output['congestion'].cpu().numpy()
        }
    
    def predict_traffic_transformer(self, input_sequence: torch.Tensor,
                                  external_factors: Optional[torch.Tensor] = None) -> Dict[str, np.ndarray]:
        """Make predictions using Transformer"""
        if self.transformer_model is None:
            raise ValueError("Transformer model not initialized")
        
        self.transformer_model.eval()
        with torch.no_grad():
            output = self.transformer_model(
                input_sequence.unsqueeze(0),  # Add batch dimension
                external_factors.unsqueeze(0) if external_factors is not None else None
            )
        
        return {
            'flow': output['flow'].cpu().numpy().squeeze(),
            'speed': output['speed'].cpu().numpy().squeeze(),
            'demand': output['demand'].cpu().numpy().squeeze()
        }
    
    def process_social_media_events(self, posts: List[Dict]) -> List[Dict]:
        """Process social media posts for traffic events"""
        events = []
        
        for post in posts:
            event = self.social_analyzer.analyze_post(
                content=post['content'],
                platform=post['platform'],
                timestamp=post['timestamp'],
                location=post.get('location')
            )
            if event:
                events.append(event)
                self.social_events.append(event)
        
        # Aggregate events
        aggregated_events = self.social_analyzer.aggregate_events(events)
        
        return aggregated_events
    
    def integrate_social_events(self, events: List[Dict], 
                            traffic_predictions: Dict[str, np.ndarray]) -> Dict[str, np.ndarray]:
        """Integrate social media events into traffic predictions"""
        adjusted_predictions = traffic_predictions.copy()
        
        for event in events:
            # Find affected nodes (simplified)
            affected_nodes = self._find_affected_nodes(event)
            
            # Adjust predictions based on event impact
            for node_id in affected_nodes:
                if node_id in adjusted_predictions:
                    impact_factor = 1.0 + event['total_impact']
                    adjusted_predictions[node_id] *= impact_factor
        
        return adjusted_predictions
    
    def _find_affected_nodes(self, event: Dict) -> List[str]:
        """Find nodes affected by social media event"""
        # Simplified implementation
        # In real system, this would use spatial queries
        affected_nodes = []
        
        for node_id in self.traffic_graph.nodes():
            node_data = self.traffic_graph.nodes[node_id]
            # Simple distance-based selection
            if event['location']:
                node_loc = (node_data.get('latitude', 0), node_data.get('longitude', 0))
                distance = self.social_analyzer._calculate_distance(event['location'], node_loc)
                if distance < 0.1:  # Within ~10km
                    affected_nodes.append(node_id)
        
        return affected_nodes
    
    def generate_predictions_report(self, predictions: Dict[str, np.ndarray],
                                  social_events: List[Dict]) -> Dict[str, Any]:
        """Generate comprehensive predictions report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'predictions_summary': {},
            'social_events': social_events,
            'recommendations': []
        }
        
        # Summarize predictions
        for metric, values in predictions.items():
            report['predictions_summary'][metric] = {
                'mean': float(np.mean(values)),
                'std': float(np.std(values)),
                'min': float(np.min(values)),
                'max': float(np.max(values))
            }
        
        # Generate recommendations based on predictions and events
        if social_events:
            high_impact_events = [e for e in social_events if e['total_impact'] > 0.7]
            if high_impact_events:
                report['recommendations'].append("High-impact events detected - consider rerouting traffic")
        
        avg_congestion = np.mean(predictions.get('congestion', []))
        if avg_congestion > 0.7:
            report['recommendations'].append("High congestion predicted - extend green phases")
        
        return report


# Factory functions
def create_gnn_model(node_features: int, edge_features: int, 
                    hidden_dim: int = 128, num_layers: int = 3) -> GraphNeuralNetwork:
    """Create Graph Neural Network model"""
    return GraphNeuralNetwork(
        node_features=node_features,
        edge_features=edge_features,
        hidden_dim=hidden_dim,
        num_layers=num_layers,
        gnn_type='gcn',
        prediction_horizon=12
    )


def create_transformer_model(input_dim: int, d_model: int = 256,
                           num_layers: int = 6) -> TrafficTransformer:
    """Create Transformer model"""
    return TrafficTransformer(
        input_dim=input_dim,
        d_model=d_model,
        num_layers=num_layers,
        prediction_horizon=24,
        sequence_length=48
    )


def create_social_analyzer() -> SocialMediaAnalyzer:
    """Create social media analyzer"""
    return SocialMediaAnalyzer()


def create_predictive_engine() -> PredictiveAnalyticsEngine:
    """Create predictive analytics engine"""
    return PredictiveAnalyticsEngine()