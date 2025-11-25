"""
Infrastructure Digital Twin Module

Implements BIM integration, multi-sensor fusion, 5G V2I communication,
and edge computing for real-time infrastructure management.
"""

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Dict, Tuple, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json
import logging
from collections import defaultdict, deque
import asyncio
import websockets
import threading
import time
from enum import Enum
import math
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest

logger = logging.getLogger(__name__)


class InfrastructureType(Enum):
    """Infrastructure component types"""
    ROAD_SEGMENT = "road_segment"
    INTERSECTION = "intersection"
    TRAFFIC_SIGNAL = "traffic_signal"
    BRIDGE = "bridge"
    TUNNEL = "tunnel"
    PEDESTRIAN_CROSSING = "pedestrian_crossing"
    PARKING_FACILITY = "parking_facility"
    PUBLIC_TRANSPORT = "public_transport"


class SensorType(Enum):
    """Sensor types for infrastructure monitoring"""
    INDUCTIVE_LOOP = "inductive_loop"
    BLUETOOTH_DETECTOR = "bluetooth_detector"
    VIDEO_CAMERA = "video_camera"
    RADAR_DETECTOR = "radar_detector"
    LIDAR_DETECTOR = "lidar_detector"
    WEATHER_STATION = "weather_station"
    VIBRATION_SENSOR = "vibration_sensor"
    STRAIN_GAUGE = "strain_gauge"
    TEMPERATURE_SENSOR = "temperature_sensor"


class CommunicationProtocol(Enum):
    """Communication protocols for V2I"""
    DSRC = "dsrc"  # Dedicated Short Range Communications
    C_V2X = "c_v2x"  # Cellular V2X
    5G_NR = "5g_nr"  # 5G New Radio
    WIFI = "wifi"
    LORA = "lora"


@dataclass
class BIMComponent:
    """Building Information Modeling component"""
    component_id: str
    component_type: InfrastructureType
    geometry: Dict[str, Any]  # 3D geometry data
    properties: Dict[str, Any]  # Material, age, condition, etc.
    spatial_data: Dict[str, float]  # Location, orientation
    maintenance_history: List[Dict] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    digital_twin_id: Optional[str] = None


@dataclass
class SensorData:
    """Sensor measurement data"""
    sensor_id: str
    sensor_type: SensorType
    timestamp: datetime
    location: Tuple[float, float, float]  # x, y, z
    measurements: Dict[str, float]
    quality_score: float
    processing_latency: float


@dataclass
class V2IMessage:
    """Vehicle-to-Infrastructure communication message"""
    message_id: str
    vehicle_id: str
    infrastructure_id: str
    message_type: str
    payload: Dict[str, Any]
    timestamp: datetime
    protocol: CommunicationProtocol
    signal_strength: float
    latency: float


@dataclass
class EdgeComputingNode:
    """Edge computing node specification"""
    node_id: str
    location: Tuple[float, float, float]
    computing_power: float  # GFLOPS
    memory_capacity: float  # GB
    storage_capacity: float  # GB
    network_bandwidth: float  # Mbps
    power_consumption: float  # Watts
    supported_tasks: List[str] = field(default_factory=list)


class BIMIntegration:
    """Building Information Modeling integration system"""
    
    def __init__(self):
        self.bim_components = {}
        self.spatial_index = {}  # Spatial indexing for fast queries
        self.relationship_graph = {}  # Component relationships
        
        # BIM data schemas
        self.geometry_schemas = {
            InfrastructureType.ROAD_SEGMENT: {
                'required_fields': ['start_point', 'end_point', 'width', 'lanes'],
                'optional_fields': ['elevation_profile', 'surface_material', 'curvature']
            },
            InfrastructureType.INTERSECTION: {
                'required_fields': ['center_point', 'approaches', 'control_type'],
                'optional_fields': ['turning_movements', 'pedestrian_facilities', 'signal_timing']
            },
            InfrastructureType.TRAFFIC_SIGNAL: {
                'required_fields': ['location', 'phases', 'timing_plan'],
                'optional_fields': ['detection_zones', 'pedestrian_phases', 'coordination']
            }
        }
        
        # Performance models
        self.performance_models = {
            'deterioration_rate': {
                'road_segment': 0.02,  # per year
                'bridge': 0.01,
                'traffic_signal': 0.05
            },
            'maintenance_cost': {
                'road_segment': 100,  # per meter per year
                'bridge': 1000,  # per square meter per year
                'traffic_signal': 500  # per unit per year
            }
        }
    
    def add_bim_component(self, component: BIMComponent) -> bool:
        """Add BIM component to the digital twin"""
        # Validate component
        if not self._validate_component(component):
            return False
        
        # Add to storage
        self.bim_components[component.component_id] = component
        
        # Update spatial index
        self._update_spatial_index(component)
        
        # Update relationships
        self._update_relationships(component)
        
        # Generate digital twin ID
        if component.digital_twin_id is None:
            component.digital_twin_id = f"DT_{component.component_id}_{int(time.time())}"
        
        return True
    
    def _validate_component(self, component: BIMComponent) -> bool:
        """Validate BIM component data"""
        schema = self.geometry_schemas.get(component.component_type)
        if not schema:
            return False
        
        # Check required fields
        for field in schema['required_fields']:
            if field not in component.geometry:
                logger.error(f"Missing required field {field} for {component.component_type}")
                return False
        
        return True
    
    def _update_spatial_index(self, component: BIMComponent):
        """Update spatial indexing for component"""
        # Simple grid-based spatial indexing
        if 'center_point' in component.spatial_data:
            x, y = component.spatial_data['center_point'][:2]
            grid_x, grid_y = int(x * 100), int(y * 100)  # 0.01 degree grid
            
            if (grid_x, grid_y) not in self.spatial_index:
                self.spatial_index[(grid_x, grid_y)] = []
            
            self.spatial_index[(grid_x, grid_y)].append(component.component_id)
    
    def _update_relationships(self, component: BIMComponent):
        """Update component relationships"""
        component_id = component.component_id
        self.relationship_graph[component_id] = {
            'connected_to': [],
            'contains': [],
            'part_of': []
        }
        
        # Find spatially related components
        nearby_components = self._find_nearby_components(component, radius=0.01)  # ~1km
        
        for nearby_id in nearby_components:
            if nearby_id != component_id:
                self.relationship_graph[component_id]['connected_to'].append(nearby_id)
    
    def _find_nearby_components(self, component: BIMComponent, radius: float) -> List[str]:
        """Find components within specified radius"""
        if 'center_point' not in component.spatial_data:
            return []
        
        cx, cy = component.spatial_data['center_point'][:2]
        nearby = []
        
        for comp_id, comp in self.bim_components.items():
            if comp_id == component.component_id:
                continue
            
            if 'center_point' in comp.spatial_data:
                px, py = comp.spatial_data['center_point'][:2]
                distance = math.sqrt((cx - px)**2 + (cy - py)**2)
                if distance <= radius:
                    nearby.append(comp_id)
        
        return nearby
    
    def query_spatial(self, bbox: Tuple[float, float, float, float]) -> List[str]:
        """Query components within bounding box"""
        min_x, min_y, max_x, max_y = bbox
        result = []
        
        for component_id, component in self.bim_components.items():
            if 'center_point' in component.spatial_data:
                x, y = component.spatial_data['center_point'][:2]
                if min_x <= x <= max_x and min_y <= y <= max_y:
                    result.append(component_id)
        
        return result
    
    def get_component_performance(self, component_id: str) -> Dict[str, float]:
        """Get performance metrics for component"""
        if component_id not in self.bim_components:
            return {}
        
        component = self.bim_components[component_id]
        
        # Calculate performance metrics
        age = datetime.now().year - component.properties.get('construction_year', 2020)
        deterioration = self.performance_models['deterioration_rate'].get(
            component.component_type.value, 0.02
        ) * age
        
        condition_score = max(0, 1.0 - deterioration)
        
        # Maintenance cost
        maintenance_cost = self.performance_models['maintenance_cost'].get(
            component.component_type.value, 100
        )
        
        if component.component_type == InfrastructureType.ROAD_SEGMENT:
            length = component.geometry.get('length', 100)
            maintenance_cost *= length
        elif component.component_type == InfrastructureType.BRIDGE:
            area = component.geometry.get('area', 1000)
            maintenance_cost *= area
        
        return {
            'condition_score': condition_score,
            'deterioration_rate': deterioration,
            'annual_maintenance_cost': maintenance_cost,
            'age_years': age,
            'performance_index': condition_score * 0.7 + (1 - deterioration) * 0.3
        }
    
    def predict_maintenance_needs(self, horizon_years: int = 5) -> Dict[str, Dict]:
        """Predict maintenance needs for all components"""
        predictions = {}
        
        for component_id, component in self.bim_components.items():
            current_performance = self.get_component_performance(component_id)
            
            # Predict future performance
            future_deterioration = (
                self.performance_models['deterioration_rate'].get(
                    component.component_type.value, 0.02
                ) * horizon_years
            )
            
            future_condition = max(0, current_performance['condition_score'] - future_deterioration)
            
            # Maintenance recommendation
            maintenance_urgency = 'low'
            if future_condition < 0.3:
                maintenance_urgency = 'critical'
            elif future_condition < 0.5:
                maintenance_urgency = 'high'
            elif future_condition < 0.7:
                maintenance_urgency = 'medium'
            
            predictions[component_id] = {
                'current_condition': current_performance['condition_score'],
                'predicted_condition': future_condition,
                'maintenance_urgency': maintenance_urgency,
                'estimated_cost': current_performance['annual_maintenance_cost'] * horizon_years,
                'recommended_actions': self._get_maintenance_actions(
                    component.component_type, maintenance_urgency
                )
            }
        
        return predictions
    
    def _get_maintenance_actions(self, component_type: InfrastructureType, 
                                urgency: str) -> List[str]:
        """Get recommended maintenance actions"""
        actions = {
            'road_segment': {
                'critical': ['resurfacing', 'structural_repair'],
                'high': ['patching', 'crack_sealing'],
                'medium': ['routine_inspection', 'cleaning'],
                'low': ['monitoring']
            },
            'bridge': {
                'critical': ['structural_repair', 'replacement'],
                'high': ['major_rehabilitation', 'corrosion_control'],
                'medium': ['routine_inspection', 'minor_repairs'],
                'low': ['visual_inspection']
            },
            'traffic_signal': {
                'critical': ['controller_replacement', 'full_system_upgrade'],
                'high': ['major_repair', 'component_replacement'],
                'medium': ['routine_maintenance', 'calibration'],
                'low': ['cleaning', 'inspection']
            }
        }
        
        return actions.get(component_type.value, {}).get(urgency, ['inspection'])


class MultiSensorFusion:
    """Multi-sensor data fusion system"""
    
    def __init__(self):
        self.sensors = {}
        self.sensor_data = defaultdict(deque)
        self.fusion_models = {}
        self.anomaly_detectors = {}
        
        # Sensor characteristics
        self.sensor_specs = {
            SensorType.INDUCTIVE_LOOP: {
                'accuracy': 0.95,
                'update_rate': 1.0,  # Hz
                'coverage': 'point',
                'measurements': ['vehicle_count', 'speed', 'occupancy']
            },
            SensorType.BLUETOOTH_DETECTOR: {
                'accuracy': 0.85,
                'update_rate': 0.1,  # Hz
                'coverage': 'area',
                'measurements': ['travel_time', 'origin_destination']
            },
            SensorType.VIDEO_CAMERA: {
                'accuracy': 0.90,
                'update_rate': 10.0,  # Hz
                'coverage': 'visual',
                'measurements': ['vehicle_count', 'classification', 'trajectory']
            },
            SensorType.RADAR_DETECTOR: {
                'accuracy': 0.92,
                'update_rate': 20.0,  # Hz
                'coverage': 'directional',
                'measurements': ['speed', 'distance', 'angle']
            }
        }
        
        # Initialize anomaly detectors
        self._initialize_anomaly_detectors()
    
    def _initialize_anomaly_detectors(self):
        """Initialize anomaly detection models"""
        for sensor_type in SensorType:
            if sensor_type in [SensorType.INDUCTIVE_LOOP, SensorType.VIDEO_CAMERA]:
                self.anomaly_detectors[sensor_type] = IsolationForest(
                    contamination=0.1, random_state=42
                )
    
    def register_sensor(self, sensor_id: str, sensor_type: SensorType,
                      location: Tuple[float, float, float],
                      specifications: Dict[str, Any]):
        """Register new sensor"""
        self.sensors[sensor_id] = {
            'type': sensor_type,
            'location': location,
            'specifications': specifications,
            'status': 'active',
            'last_update': None
        }
        
        logger.info(f"Registered sensor {sensor_id} of type {sensor_type.value}")
    
    def process_sensor_data(self, sensor_data: SensorData) -> Dict[str, Any]:
        """Process incoming sensor data"""
        # Validate data
        if not self._validate_sensor_data(sensor_data):
            return {'status': 'error', 'message': 'Invalid sensor data'}
        
        # Store data
        self.sensor_data[sensor_data.sensor_id].append(sensor_data)
        
        # Keep only recent data (last hour)
        cutoff_time = datetime.now() - timedelta(hours=1)
        while (self.sensor_data[sensor_data.sensor_id] and 
               self.sensor_data[sensor_data.sensor_id][0].timestamp < cutoff_time):
            self.sensor_data[sensor_data.sensor_id].popleft()
        
        # Detect anomalies
        anomalies = self._detect_anomalies(sensor_data)
        
        # Fuse with other sensors
        fused_data = self._fuse_sensor_data(sensor_data)
        
        return {
            'status': 'success',
            'anomalies': anomalies,
            'fused_data': fused_data,
            'processing_time': time.time()
        }
    
    def _validate_sensor_data(self, sensor_data: SensorData) -> bool:
        """Validate sensor data format and values"""
        if sensor_data.sensor_id not in self.sensors:
            return False
        
        # Check measurement ranges
        specs = self.sensor_specs.get(self.sensors[sensor_data.sensor_id]['type'])
        if not specs:
            return False
        
        for measurement, value in sensor_data.measurements.items():
            if measurement == 'speed' and (value < 0 or value > 200):  # km/h
                return False
            elif measurement == 'vehicle_count' and value < 0:
                return False
            elif measurement == 'occupancy' and (value < 0 or value > 1):
                return False
        
        return True
    
    def _detect_anomalies(self, sensor_data: SensorData) -> List[Dict]:
        """Detect anomalies in sensor data"""
        anomalies = []
        sensor_type = self.sensors[sensor_data.sensor_id]['type']
        
        if sensor_type not in self.anomaly_detectors:
            return anomalies
        
        # Get historical data
        historical_data = list(self.sensor_data[sensor_data.sensor_id])
        if len(historical_data) < 10:  # Need enough data for anomaly detection
            return anomalies
        
        # Prepare features for anomaly detection
        features = []
        for data in historical_data[-50:]:  # Use last 50 measurements
            feature_vector = [
                data.measurements.get('vehicle_count', 0),
                data.measurements.get('speed', 0),
                data.measurements.get('occupancy', 0)
            ]
            features.append(feature_vector)
        
        if len(features) < 10:
            return anomalies
        
        # Detect anomalies
        try:
            anomaly_detector = self.anomaly_detectors[sensor_type]
            anomaly_detector.fit(features)
            
            current_features = [
                sensor_data.measurements.get('vehicle_count', 0),
                sensor_data.measurements.get('speed', 0),
                sensor_data.measurements.get('occupancy', 0)
            ]
            
            anomaly_score = anomaly_detector.decision_function([current_features])[0]
            
            if anomaly_score < -0.5:  # Anomaly threshold
                anomalies.append({
                    'type': 'statistical_anomaly',
                    'score': float(anomaly_score),
                    'measurements': sensor_data.measurements,
                    'timestamp': sensor_data.timestamp
                })
        except Exception as e:
            logger.warning(f"Anomaly detection failed: {e}")
        
        return anomalies
    
    def _fuse_sensor_data(self, current_data: SensorData) -> Dict[str, Any]:
        """Fuse data from multiple sensors"""
        sensor_location = current_data.location
        fused_result = {
            'location': sensor_location,
            'timestamp': current_data.timestamp,
            'fused_measurements': {},
            'contributing_sensors': [current_data.sensor_id],
            'confidence': current_data.quality_score
        }
        
        # Find nearby sensors
        nearby_sensors = self._find_nearby_sensors(sensor_location, radius=0.005)  # ~500m
        
        # Collect measurements from nearby sensors
        all_measurements = defaultdict(list)
        total_confidence = 0
        
        for nearby_sensor_id in nearby_sensors:
            if nearby_sensor_id == current_data.sensor_id:
                all_measurements[current_data.sensor_id] = current_data.measurements
                total_confidence += current_data.quality_score
                continue
            
            # Get recent data from nearby sensor
            recent_data = self._get_recent_sensor_data(nearby_sensor_id, minutes=5)
            if recent_data:
                all_measurements[nearby_sensor_id] = recent_data.measurements
                fused_result['contributing_sensors'].append(nearby_sensor_id)
                total_confidence += recent_data.quality_score
        
        # Fuse measurements using weighted average
        if len(all_measurements) > 1:
            for measurement_type in ['vehicle_count', 'speed', 'occupancy']:
                values = []
                weights = []
                
                for sensor_id, measurements in all_measurements.items():
                    if measurement_type in measurements:
                        values.append(measurements[measurement_type])
                        sensor_quality = self._get_sensor_quality(sensor_id)
                        weights.append(sensor_quality)
                
                if values and weights:
                    # Weighted average
                    weighted_value = np.average(values, weights=weights)
                    fused_result['fused_measurements'][measurement_type] = float(weighted_value)
        
        # Update confidence
        if len(fused_result['contributing_sensors']) > 1:
            fused_result['confidence'] = min(1.0, total_confidence / len(fused_result['contributing_sensors']))
        
        return fused_result
    
    def _find_nearby_sensors(self, location: Tuple[float, float, float], 
                             radius: float) -> List[str]:
        """Find sensors within specified radius"""
        nearby = []
        x, y, z = location
        
        for sensor_id, sensor_info in self.sensors.items():
            sx, sy, sz = sensor_info['location']
            distance = math.sqrt((x - sx)**2 + (y - sy)**2 + (z - sz)**2)
            if distance <= radius:
                nearby.append(sensor_id)
        
        return nearby
    
    def _get_recent_sensor_data(self, sensor_id: str, minutes: int = 5) -> Optional[SensorData]:
        """Get most recent data from sensor"""
        if sensor_id not in self.sensor_data:
            return None
        
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        for data in reversed(self.sensor_data[sensor_id]):
            if data.timestamp >= cutoff_time:
                return data
        
        return None
    
    def _get_sensor_quality(self, sensor_id: str) -> float:
        """Get sensor quality score"""
        if sensor_id not in self.sensors:
            return 0.5
        
        sensor_type = self.sensors[sensor_id]['type']
        base_quality = self.sensor_specs.get(sensor_type, {}).get('accuracy', 0.8)
        
        # Adjust based on recent performance
        recent_data = list(self.sensor_data[sensor_id])
        if len(recent_data) > 10:
            avg_quality = np.mean([d.quality_score for d in recent_data[-10:]])
            return (base_quality + avg_quality) / 2
        
        return base_quality
    
    def get_traffic_state(self, region_bbox: Tuple[float, float, float, float]) -> Dict[str, Any]:
        """Get comprehensive traffic state for region"""
        # Get sensors in region
        sensors_in_region = []
        for sensor_id, sensor_info in self.sensors.items():
            x, y, z = sensor_info['location']
            min_x, min_y, max_x, max_y = region_bbox
            if min_x <= x <= max_x and min_y <= y <= max_y:
                sensors_in_region.append(sensor_id)
        
        # Collect recent data
        region_data = []
        for sensor_id in sensors_in_region:
            recent_data = self._get_recent_sensor_data(sensor_id, minutes=10)
            if recent_data:
                region_data.append(recent_data)
        
        if not region_data:
            return {'status': 'no_data', 'region': region_bbox}
        
        # Aggregate measurements
        total_vehicles = 0
        total_speed = 0
        total_occupancy = 0
        count = 0
        
        for data in region_data:
            measurements = data.measurements
            if 'vehicle_count' in measurements:
                total_vehicles += measurements['vehicle_count']
            if 'speed' in measurements:
                total_speed += measurements['speed']
                count += 1
            if 'occupancy' in measurements:
                total_occupancy += measurements['occupancy']
        
        avg_speed = total_speed / count if count > 0 else 0
        avg_occupancy = total_occupancy / len(region_data) if region_data else 0
        
        # Determine traffic condition
        traffic_condition = 'free_flow'
        if avg_speed < 20:
            traffic_condition = 'congested'
        elif avg_speed < 40:
            traffic_condition = 'moderate'
        
        return {
            'status': 'success',
            'region': region_bbox,
            'timestamp': datetime.now(),
            'total_vehicles': total_vehicles,
            'average_speed': avg_speed,
            'average_occupancy': avg_occupancy,
            'traffic_condition': traffic_condition,
            'active_sensors': len(sensors_in_region),
            'data_points': len(region_data)
        }


class V2ICommunicationSystem:
    """Vehicle-to-Infrastructure communication system"""
    
    def __init__(self):
        self.infrastructure_nodes = {}
        self.connected_vehicles = {}
        self.message_queue = deque()
        self.protocol_handlers = {}
        
        # Communication parameters
        self.protocol_specs = {
            CommunicationProtocol.DSRC: {
                'range': 300,  # meters
                'bandwidth': 27,  # Mbps
                'latency': 0.1,  # seconds
                'reliability': 0.99
            },
            CommunicationProtocol.C_V2X: {
                'range': 1000,  # meters
                'bandwidth': 100,  # Mbps
                'latency': 0.05,  # seconds
                'reliability': 0.95
            },
            CommunicationProtocol._5G_NR: {
                'range': 5000,  # meters
                'bandwidth': 1000,  # Mbps
                'latency': 0.01,  # seconds
                'reliability': 0.999
            }
        }
        
        # Message types
        self.message_types = {
            'SPAT': 'Signal Phase and Timing',
            'MAP': 'Map Data',
            'RTCM': 'Road Topology and Condition',
            'BSM': 'Basic Safety Message',
            'TRAFFIC_INFO': 'Traffic Information',
            'WEATHER_ALERT': 'Weather Alert',
            'EMERGENCY': 'Emergency Vehicle Alert'
        }
        
        # Initialize protocol handlers
        self._initialize_protocol_handlers()
    
    def _initialize_protocol_handlers(self):
        """Initialize communication protocol handlers"""
        for protocol in CommunicationProtocol:
            self.protocol_handlers[protocol] = {
                'active_connections': 0,
                'messages_sent': 0,
                'messages_received': 0,
                'total_latency': 0,
                'errors': 0
            }
    
    def register_infrastructure_node(self, node_id: str, location: Tuple[float, float, float],
                                   capabilities: List[str], protocols: List[CommunicationProtocol]):
        """Register infrastructure communication node"""
        self.infrastructure_nodes[node_id] = {
            'location': location,
            'capabilities': capabilities,
            'protocols': protocols,
            'status': 'active',
            'last_heartbeat': datetime.now()
        }
        
        logger.info(f"Registered infrastructure node {node_id}")
    
    def connect_vehicle(self, vehicle_id: str, location: Tuple[float, float, float],
                      protocol: CommunicationProtocol, capabilities: List[str]):
        """Connect vehicle to V2I network"""
        self.connected_vehicles[vehicle_id] = {
            'location': location,
            'protocol': protocol,
            'capabilities': capabilities,
            'connection_time': datetime.now(),
            'last_communication': datetime.now()
        }
        
        # Update protocol handler
        self.protocol_handlers[protocol]['active_connections'] += 1
        
        logger.info(f"Connected vehicle {vehicle_id} via {protocol.value}")
    
    def send_message(self, message: V2IMessage) -> bool:
        """Send V2I message"""
        # Validate message
        if not self._validate_message(message):
            return False
        
        # Check connectivity
        if not self._check_connectivity(message):
            return False
        
        # Calculate message parameters
        protocol_specs = self.protocol_specs[message.protocol]
        
        # Simulate transmission
        transmission_success = self._simulate_transmission(message, protocol_specs)
        
        if transmission_success:
            # Update statistics
            handler = self.protocol_handlers[message.protocol]
            handler['messages_sent'] += 1
            handler['total_latency'] += message.latency
            
            # Add to message queue
            self.message_queue.append(message)
            
            logger.debug(f"Sent message {message.message_id} via {message.protocol.value}")
            return True
        else:
            handler['errors'] += 1
            return False
    
    def _validate_message(self, message: V2IMessage) -> bool:
        """Validate V2I message"""
        if not message.message_id or not message.vehicle_id or not message.infrastructure_id:
            return False
        
        if message.message_type not in self.message_types:
            return False
        
        if message.protocol not in CommunicationProtocol:
            return False
        
        return True
    
    def _check_connectivity(self, message: V2IMessage) -> bool:
        """Check if vehicle and infrastructure are connected"""
        if message.vehicle_id not in self.connected_vehicles:
            return False
        
        if message.infrastructure_id not in self.infrastructure_nodes:
            return False
        
        vehicle = self.connected_vehicles[message.vehicle_id]
        infra = self.infrastructure_nodes[message.infrastructure_id]
        
        # Check protocol compatibility
        if message.protocol not in infra['protocols']:
            return False
        
        # Check range
        distance = self._calculate_distance(vehicle['location'], infra['location'])
        max_range = self.protocol_specs[message.protocol]['range']
        
        return distance <= max_range
    
    def _calculate_distance(self, pos1: Tuple[float, float, float], 
                           pos2: Tuple[float, float, float]) -> float:
        """Calculate distance between two positions"""
        return math.sqrt(sum((a - b)**2 for a, b in zip(pos1, pos2)))
    
    def _simulate_transmission(self, message: V2IMessage, 
                             protocol_specs: Dict[str, float]) -> bool:
        """Simulate message transmission"""
        # Simulate reliability
        if np.random.random() > protocol_specs['reliability']:
            return False
        
        # Simulate latency
        expected_latency = protocol_specs['latency']
        if message.latency > expected_latency * 2:  # Too much latency
            return False
        
        return True
    
    def broadcast_traffic_information(self, region_bbox: Tuple[float, float, float, float],
                                   traffic_data: Dict[str, Any]):
        """Broadcast traffic information to vehicles in region"""
        messages_sent = 0
        
        for vehicle_id, vehicle_info in self.connected_vehicles.items():
            # Check if vehicle is in region
            x, y, z = vehicle_info['location']
            min_x, min_y, max_x, max_y = region_bbox
            
            if min_x <= x <= max_x and min_y <= y <= max_y:
                # Find nearest infrastructure node
                nearest_node = self._find_nearest_infrastructure(vehicle_info['location'])
                
                if nearest_node:
                    # Create traffic info message
                    message = V2IMessage(
                        message_id=f"TRAFFIC_{int(time.time())}_{vehicle_id}",
                        vehicle_id=vehicle_id,
                        infrastructure_id=nearest_node,
                        message_type='TRAFFIC_INFO',
                        payload=traffic_data,
                        timestamp=datetime.now(),
                        protocol=vehicle_info['protocol'],
                        signal_strength=0.8,  # Simulated
                        latency=0.05  # Simulated
                    )
                    
                    if self.send_message(message):
                        messages_sent += 1
        
        logger.info(f"Broadcast traffic info to {messages_sent} vehicles")
        return messages_sent
    
    def _find_nearest_infrastructure(self, location: Tuple[float, float, float]) -> Optional[str]:
        """Find nearest infrastructure node"""
        min_distance = float('inf')
        nearest_node = None
        
        for node_id, node_info in self.infrastructure_nodes.items():
            distance = self._calculate_distance(location, node_info['location'])
            if distance < min_distance:
                min_distance = distance
                nearest_node = node_id
        
        return nearest_node
    
    def get_network_statistics(self) -> Dict[str, Any]:
        """Get V2I network statistics"""
        stats = {
            'total_infrastructure_nodes': len(self.infrastructure_nodes),
            'connected_vehicles': len(self.connected_vehicles),
            'messages_in_queue': len(self.message_queue),
            'protocol_statistics': {}
        }
        
        for protocol, handler in self.protocol_handlers.items():
            avg_latency = (handler['total_latency'] / handler['messages_sent'] 
                          if handler['messages_sent'] > 0 else 0)
            
            stats['protocol_statistics'][protocol.value] = {
                'active_connections': handler['active_connections'],
                'messages_sent': handler['messages_sent'],
                'messages_received': handler['messages_received'],
                'average_latency': avg_latency,
                'errors': handler['errors']
            }
        
        return stats


class EdgeComputingManager:
    """Edge computing management system"""
    
    def __init__(self):
        self.edge_nodes = {}
        self.task_queue = deque()
        self.active_tasks = {}
        self.resource_monitor = {}
        
        # Task types and requirements
        self.task_requirements = {
            'traffic_signal_optimization': {
                'cpu': 2.0,  # GFLOPS
                'memory': 1.0,  # GB
                'deadline': 1.0,  # seconds
                'priority': 'high'
            },
            'video_processing': {
                'cpu': 5.0,
                'memory': 4.0,
                'deadline': 0.5,
                'priority': 'medium'
            },
            'sensor_fusion': {
                'cpu': 1.0,
                'memory': 0.5,
                'deadline': 0.1,
                'priority': 'high'
            },
            'anomaly_detection': {
                'cpu': 0.5,
                'memory': 0.2,
                'deadline': 2.0,
                'priority': 'medium'
            }
        }
    
    def register_edge_node(self, node: EdgeComputingNode):
        """Register edge computing node"""
        self.edge_nodes[node.node_id] = {
            'specifications': node,
            'available_resources': {
                'cpu': node.computing_power,
                'memory': node.memory_capacity,
                'storage': node.storage_capacity,
                'bandwidth': node.network_bandwidth
            },
            'current_tasks': [],
            'utilization': 0.0,
            'last_heartbeat': datetime.now()
        }
        
        # Initialize resource monitoring
        self.resource_monitor[node.node_id] = {
            'cpu_history': deque(maxlen=100),
            'memory_history': deque(maxlen=100),
            'task_completion_times': deque(maxlen=50)
        }
        
        logger.info(f"Registered edge node {node.node_id}")
    
    def submit_task(self, task_id: str, task_type: str, data: Dict[str, Any],
                   deadline: Optional[float] = None, priority: Optional[str] = None) -> bool:
        """Submit computational task to edge network"""
        # Validate task type
        if task_type not in self.task_requirements:
            logger.error(f"Unknown task type: {task_type}")
            return False
        
        # Create task
        task = {
            'task_id': task_id,
            'task_type': task_type,
            'data': data,
            'requirements': self.task_requirements[task_type].copy(),
            'deadline': deadline or self.task_requirements[task_type]['deadline'],
            'priority': priority or self.task_requirements[task_type]['priority'],
            'submission_time': time.time(),
            'status': 'queued'
        }
        
        # Add to queue
        self.task_queue.append(task)
        
        # Try to schedule immediately
        self._schedule_tasks()
        
        logger.info(f"Submitted task {task_id} of type {task_type}")
        return True
    
    def _schedule_tasks(self):
        """Schedule tasks to available edge nodes"""
        while self.task_queue:
            task = self.task_queue[0]
            
            # Find suitable node
            suitable_node = self._find_suitable_node(task)
            
            if suitable_node:
                # Assign task to node
                self._assign_task_to_node(task, suitable_node)
                self.task_queue.popleft()
            else:
                # No suitable node available
                break
    
    def _find_suitable_node(self, task: Dict[str, Any]) -> Optional[str]:
        """Find suitable edge node for task"""
        best_node = None
        best_score = -1
        
        for node_id, node_info in self.edge_nodes.items():
            # Check resource availability
            req = task['requirements']
            avail = node_info['available_resources']
            
            if (avail['cpu'] >= req['cpu'] and 
                avail['memory'] >= req['memory']):
                
                # Calculate suitability score
                score = self._calculate_node_score(node_id, task)
                
                if score > best_score:
                    best_score = score
                    best_node = node_id
        
        return best_node
    
    def _calculate_node_score(self, node_id: str, task: Dict[str, Any]) -> float:
        """Calculate suitability score for node"""
        node_info = self.edge_nodes[node_id]
        req = task['requirements']
        avail = node_info['available_resources']
        
        # Resource utilization score
        cpu_score = (avail['cpu'] - req['cpu']) / avail['cpu']
        memory_score = (avail['memory'] - req['memory']) / avail['memory']
        
        # Load balancing score
        load_score = 1.0 - node_info['utilization']
        
        # Priority score
        priority_score = 1.0
        if task['priority'] == 'high':
            priority_score = 2.0
        elif task['priority'] == 'medium':
            priority_score = 1.5
        
        # Combined score
        total_score = (cpu_score * 0.3 + memory_score * 0.3 + 
                      load_score * 0.2 + priority_score * 0.2)
        
        return total_score
    
    def _assign_task_to_node(self, task: Dict[str, Any], node_id: str):
        """Assign task to specific edge node"""
        node_info = self.edge_nodes[node_id]
        req = task['requirements']
        
        # Update node resources
        node_info['available_resources']['cpu'] -= req['cpu']
        node_info['available_resources']['memory'] -= req['memory']
        node_info['current_tasks'].append(task['task_id'])
        
        # Update utilization
        total_cpu = node_info['specifications'].computing_power
        used_cpu = total_cpu - node_info['available_resources']['cpu']
        node_info['utilization'] = used_cpu / total_cpu
        
        # Update task status
        task['status'] = 'running'
        task['assigned_node'] = node_id
        task['start_time'] = time.time()
        self.active_tasks[task['task_id']] = task
        
        # Simulate task execution
        self._simulate_task_execution(task, node_id)
    
    def _simulate_task_execution(self, task: Dict[str, Any], node_id: str):
        """Simulate task execution on edge node"""
        def execute_task():
            # Simulate processing time
            processing_time = np.random.uniform(0.1, task['deadline'] * 0.8)
            time.sleep(processing_time)  # Simulate computation
            
            # Task completion
            self._complete_task(task['task_id'], node_id, processing_time)
        
        # Run in separate thread
        thread = threading.Thread(target=execute_task)
        thread.daemon = True
        thread.start()
    
    def _complete_task(self, task_id: str, node_id: str, execution_time: float):
        """Complete task execution"""
        if task_id not in self.active_tasks:
            return
        
        task = self.active_tasks[task_id]
        node_info = self.edge_nodes[node_id]
        req = task['requirements']
        
        # Release resources
        node_info['available_resources']['cpu'] += req['cpu']
        node_info['available_resources']['memory'] += req['memory']
        node_info['current_tasks'].remove(task_id)
        
        # Update utilization
        total_cpu = node_info['specifications'].computing_power
        used_cpu = total_cpu - node_info['available_resources']['cpu']
        node_info['utilization'] = used_cpu / total_cpu
        
        # Update monitoring
        if node_id in self.resource_monitor:
            self.resource_monitor[node_id]['task_completion_times'].append(execution_time)
        
        # Update task status
        task['status'] = 'completed'
        task['completion_time'] = time.time()
        task['execution_time'] = execution_time
        
        # Remove from active tasks
        del self.active_tasks[task_id]
        
        logger.info(f"Completed task {task_id} on node {node_id} in {execution_time:.3f}s")
        
        # Schedule more tasks
        self._schedule_tasks()
    
    def get_network_status(self) -> Dict[str, Any]:
        """Get edge computing network status"""
        status = {
            'total_nodes': len(self.edge_nodes),
            'active_tasks': len(self.active_tasks),
            'queued_tasks': len(self.task_queue),
            'node_status': {},
            'network_utilization': 0.0
        }
        
        total_cpu = 0
        used_cpu = 0
        
        for node_id, node_info in self.edge_nodes.items():
            total_cpu += node_info['specifications'].computing_power
            used_cpu += node_info['specifications'].computing_power * node_info['utilization']
            
            status['node_status'][node_id] = {
                'utilization': node_info['utilization'],
                'active_tasks': len(node_info['current_tasks']),
                'available_cpu': node_info['available_resources']['cpu'],
                'available_memory': node_info['available_resources']['memory']
            }
        
        status['network_utilization'] = used_cpu / total_cpu if total_cpu > 0 else 0
        
        return status


# Factory functions
def create_bim_integration() -> BIMIntegration:
    """Create BIM integration system"""
    return BIMIntegration()


def create_multi_sensor_fusion() -> MultiSensorFusion:
    """Create multi-sensor fusion system"""
    return MultiSensorFusion()


def create_v2i_communication() -> V2ICommunicationSystem:
    """Create V2I communication system"""
    return V2ICommunicationSystem()


def create_edge_computing_manager() -> EdgeComputingManager:
    """Create edge computing manager"""
    return EdgeComputingManager()


def create_digital_twin_system() -> Dict[str, Any]:
    """Create complete digital twin system"""
    return {
        'bim': create_bim_integration(),
        'sensor_fusion': create_multi_sensor_fusion(),
        'v2i_communication': create_v2i_communication(),
        'edge_computing': create_edge_computing_manager()
    }