"""
Real-time Data Streaming System
==============================

Advanced live traffic data integration with:
- WebSocket streaming for real-time updates
- RESTful APIs for external integration
- Message queue for data processing
- Real-time analytics and monitoring
- Data validation and error handling
- Scalable architecture for multiple clients

Author: Top 0.1% Expert Team
Date: November 2025
Version: 3.0.0
"""

import asyncio
import websockets
import json
import time
import logging
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
import queue
import threading
import uuid
from datetime import datetime, timezone
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn
from concurrent.futures import ThreadPoolExecutor
import redis
import aioredis
from pydantic import BaseModel
import structlog

# Configure structured logging
logger = structlog.get_logger()

class StreamDataType(Enum):
    """Types of streaming data"""
    TRAFFIC_FLOW = "traffic_flow"
    VEHICLE_DETECTION = "vehicle_detection"
    SIGNAL_STATUS = "signal_status"
    EMERGENCY_ALERT = "emergency_alert"
    PERFORMANCE_METRICS = "performance_metrics"
    INCIDENT_REPORT = "incident_report"
    WEATHER_DATA = "weather_data"
    COORDINATION_EVENTS = "coordination_events"

class ClientType(Enum):
    """Types of connected clients"""
    DASHBOARD = "dashboard"
    MOBILE_APP = "mobile_app"
    TRAFFIC_CENTER = "traffic_center"
    EMERGENCY_SERVICES = "emergency_services"
    ANALYTICS_ENGINE = "analytics_engine"
    EXTERNAL_API = "external_api"

@dataclass
class StreamMessage:
    """Standard message format for data streaming"""
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=time.time)
    data_type: StreamDataType = StreamDataType.TRAFFIC_FLOW
    source: str = "traffic_system"
    data: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1  # 1-10, higher = more important
    ttl: Optional[float] = None  # Time to live in seconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)

@dataclass
class ClientConnection:
    """Client connection information"""
    client_id: str
    websocket: WebSocket
    client_type: ClientType
    subscriptions: Set[StreamDataType] = field(default_factory=set)
    last_ping: float = field(default_factory=time.time)
    message_count: int = 0
    connected_at: float = field(default_factory=time.time)
    
class TrafficDataValidator:
    """Validator for incoming traffic data"""
    
    def __init__(self):
        # Validation rules
        self.vehicle_count_range = (0, 1000)
        self.speed_range = (0, 200)  # km/h
        self.density_range = (0, 500)  # vehicles per km
        self.flow_rate_range = (0, 3000)  # vehicles per hour
        
        logger.info("Traffic data validator initialized")
    
    def validate_traffic_flow(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate traffic flow data"""
        errors = []
        
        # Check required fields
        required_fields = ['intersection_id', 'vehicle_count', 'average_speed', 'flow_rate']
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        if errors:
            return False, errors
        
        # Validate ranges
        vehicle_count = data.get('vehicle_count', 0)
        if not self.vehicle_count_range[0] <= vehicle_count <= self.vehicle_count_range[1]:
            errors.append(f"Vehicle count {vehicle_count} out of range {self.vehicle_count_range}")
        
        avg_speed = data.get('average_speed', 0)
        if not self.speed_range[0] <= avg_speed <= self.speed_range[1]:
            errors.append(f"Average speed {avg_speed} out of range {self.speed_range}")
        
        flow_rate = data.get('flow_rate', 0)
        if not self.flow_rate_range[0] <= flow_rate <= self.flow_rate_range[1]:
            errors.append(f"Flow rate {flow_rate} out of range {self.flow_rate_range}")
        
        return len(errors) == 0, errors
    
    def validate_vehicle_detection(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate vehicle detection data"""
        errors = []
        
        # Check required fields
        required_fields = ['detections', 'timestamp', 'camera_id']
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        if not errors:
            detections = data.get('detections', [])
            if not isinstance(detections, list):
                errors.append("Detections must be a list")
            else:
                for i, detection in enumerate(detections):
                    if not isinstance(detection, dict):
                        errors.append(f"Detection {i} must be a dictionary")
                        continue
                    
                    # Validate individual detection
                    detection_fields = ['bbox', 'confidence', 'vehicle_type']
                    for field in detection_fields:
                        if field not in detection:
                            errors.append(f"Detection {i} missing field: {field}")
                    
                    # Validate confidence
                    confidence = detection.get('confidence', 0)
                    if not 0 <= confidence <= 1:
                        errors.append(f"Detection {i} confidence {confidence} out of range [0,1]")
        
        return len(errors) == 0, errors

class RealTimeDataProcessor:
    """Real-time data processing and analytics"""
    
    def __init__(self):
        self.data_buffer = queue.Queue(maxsize=10000)
        self.processing_thread = None
        self.running = False
        
        # Analytics
        self.traffic_stats = {}
        self.performance_metrics = {}
        self.alert_thresholds = {}
        
        # Data aggregation
        self.aggregation_window = 60  # seconds
        self.aggregated_data = {}
        
        logger.info("Real-time data processor initialized")
    
    def start_processing(self):
        """Start data processing thread"""
        self.running = True
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()
        logger.info("Real-time data processing started")
    
    def stop_processing(self):
        """Stop data processing"""
        self.running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=5)
        logger.info("Real-time data processing stopped")
    
    def _processing_loop(self):
        """Main processing loop"""
        while self.running:
            try:
                # Get data from buffer
                data = self.data_buffer.get(timeout=1.0)
                
                # Process based on data type
                if data.get('data_type') == StreamDataType.TRAFFIC_FLOW.value:
                    self._process_traffic_flow(data)
                elif data.get('data_type') == StreamDataType.VEHICLE_DETECTION.value:
                    self._process_vehicle_detection(data)
                elif data.get('data_type') == StreamDataType.SIGNAL_STATUS.value:
                    self._process_signal_status(data)
                elif data.get('data_type') == StreamDataType.EMERGENCY_ALERT.value:
                    self._process_emergency_alert(data)
                
                # Update aggregated data
                self._update_aggregated_data(data)
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error("Error in data processing loop", error=str(e))
    
    def _process_traffic_flow(self, data: Dict[str, Any]):
        """Process traffic flow data"""
        intersection_id = data.get('intersection_id')
        if not intersection_id:
            return
        
        # Update statistics
        if intersection_id not in self.traffic_stats:
            self.traffic_stats[intersection_id] = {
                'vehicle_count': 0,
                'total_speed': 0,
                'flow_rate': 0,
                'last_update': time.time()
            }
        
        stats = self.traffic_stats[intersection_id]
        stats['vehicle_count'] = data.get('vehicle_count', 0)
        stats['total_speed'] = data.get('average_speed', 0) * stats['vehicle_count']
        stats['flow_rate'] = data.get('flow_rate', 0)
        stats['last_update'] = time.time()
        
        # Check for anomalies
        self._check_traffic_anomalies(intersection_id, data)
    
    def _process_vehicle_detection(self, data: Dict[str, Any]):
        """Process vehicle detection data"""
        detections = data.get('detections', [])
        camera_id = data.get('camera_id')
        
        # Count vehicles by type
        vehicle_counts = {}
        for detection in detections:
            vehicle_type = detection.get('vehicle_type', 'unknown')
            vehicle_counts[vehicle_type] = vehicle_counts.get(vehicle_type, 0) + 1
        
        # Store detection summary
        self.traffic_stats[f"camera_{camera_id}"] = {
            'vehicle_counts': vehicle_counts,
            'total_detections': len(detections),
            'last_detection': time.time()
        }
    
    def _process_signal_status(self, data: Dict[str, Any]):
        """Process signal status data"""
        intersection_id = data.get('intersection_id')
        if not intersection_id:
            return
        
        # Update signal status
        self.traffic_stats[f"signal_{intersection_id}"] = {
            'current_phase': data.get('current_phase'),
            'phase_timer': data.get('phase_timer'),
            'cycle_length': data.get('cycle_length'),
            'last_update': time.time()
        }
    
    def _process_emergency_alert(self, data: Dict[str, Any]):
        """Process emergency alert data"""
        alert_type = data.get('alert_type', 'unknown')
        severity = data.get('severity', 'medium')
        
        # Log emergency alert
        logger.warning("Emergency alert received", 
                     alert_type=alert_type, 
                     severity=severity,
                     data=data)
        
        # Trigger immediate processing for high severity
        if severity in ['high', 'critical']:
            self._trigger_emergency_processing(data)
    
    def _check_traffic_anomalies(self, intersection_id: str, data: Dict[str, Any]):
        """Check for traffic anomalies and generate alerts"""
        # Get historical data
        if intersection_id not in self.traffic_stats:
            return
        
        stats = self.traffic_stats[intersection_id]
        
        # Check for unusual congestion
        vehicle_count = data.get('vehicle_count', 0)
        if vehicle_count > 100:  # Congestion threshold
            self._generate_alert('congestion', {
                'intersection_id': intersection_id,
                'vehicle_count': vehicle_count,
                'severity': 'high' if vehicle_count > 150 else 'medium'
            })
        
        # Check for unusual speed patterns
        avg_speed = data.get('average_speed', 0)
        if avg_speed < 10 and vehicle_count > 20:  # Slow traffic with many vehicles
            self._generate_alert('slow_traffic', {
                'intersection_id': intersection_id,
                'average_speed': avg_speed,
                'vehicle_count': vehicle_count,
                'severity': 'medium'
            })
    
    def _generate_alert(self, alert_type: str, alert_data: Dict[str, Any]):
        """Generate system alert"""
        alert = {
            'alert_id': str(uuid.uuid4()),
            'alert_type': alert_type,
            'timestamp': time.time(),
            'data': alert_data
        }
        
        # Add to processing queue for broadcasting
        self.data_buffer.put({
            'data_type': StreamDataType.EMERGENCY_ALERT.value,
            'data': alert
        })
        
        logger.info("Alert generated", alert_type=alert_type, alert_id=alert['alert_id'])
    
    def _trigger_emergency_processing(self, data: Dict[str, Any]):
        """Trigger emergency processing workflow"""
        logger.critical("Emergency processing triggered", data=data)
        
        # In real implementation, would trigger:
        # - Signal preemption
        # - Emergency corridor activation
        # - Notification to emergency services
        # - Traffic diversion protocols
    
    def _update_aggregated_data(self, data: Dict[str, Any]):
        """Update aggregated data for analytics"""
        current_time = time.time()
        window_start = current_time - self.aggregation_window
        
        # Initialize aggregation bucket
        time_bucket = int(current_time // self.aggregation_window)
        if time_bucket not in self.aggregated_data:
            self.aggregated_data[time_bucket] = {}
        
        # Add data to current bucket
        data_type = data.get('data_type')
        if data_type not in self.aggregated_data[time_bucket]:
            self.aggregated_data[time_bucket][data_type] = []
        
        self.aggregated_data[time_bucket][data_type].append(data)
        
        # Clean old data
        old_buckets = [
            bucket for bucket in self.aggregated_data.keys()
            if bucket < int(window_start // self.aggregation_window)
        ]
        for bucket in old_buckets:
            del self.aggregated_data[bucket]
    
    def get_aggregated_metrics(self) -> Dict[str, Any]:
        """Get aggregated metrics for dashboard"""
        current_time = time.time()
        current_bucket = int(current_time // self.aggregation_window)
        
        metrics = {
            'timestamp': current_time,
            'aggregation_window': self.aggregation_window,
            'total_intersections': len(self.traffic_stats),
            'active_alerts': 0,
            'average_vehicle_count': 0,
            'average_flow_rate': 0
        }
        
        # Calculate averages from current bucket
        if current_bucket in self.aggregated_data:
            bucket_data = self.aggregated_data[current_bucket]
            
            if StreamDataType.TRAFFIC_FLOW.value in bucket_data:
                flow_data = bucket_data[StreamDataType.TRAFFIC_FLOW.value]
                if flow_data:
                    total_vehicles = sum(d.get('vehicle_count', 0) for d in flow_data)
                    total_flow = sum(d.get('flow_rate', 0) for d in flow_data)
                    
                    metrics['average_vehicle_count'] = total_vehicles / len(flow_data)
                    metrics['average_flow_rate'] = total_flow / len(flow_data)
        
        return metrics

class WebSocketStreamManager:
    """WebSocket connection manager for real-time streaming"""
    
    def __init__(self):
        self.active_connections: Dict[str, ClientConnection] = {}
        self.data_processor = RealTimeDataProcessor()
        self.validator = TrafficDataValidator()
        
        # Message broadcasting
        self.broadcast_queue = queue.Queue(maxsize=1000)
        self.broadcast_thread = None
        
        # Redis for pub/sub (optional, for scaling)
        self.redis_client = None
        self.use_redis = False
        
        logger.info("WebSocket stream manager initialized")
    
    async def connect(self, websocket: WebSocket, client_id: str, client_type: str):
        """Accept WebSocket connection"""
        await websocket.accept()
        
        # Create client connection
        client = ClientConnection(
            client_id=client_id,
            websocket=websocket,
            client_type=ClientType(client_type.lower())
        )
        
        self.active_connections[client_id] = client
        
        logger.info("Client connected", 
                   client_id=client_id, 
                   client_type=client_type,
                   total_clients=len(self.active_connections))
        
        # Send welcome message
        await self.send_to_client(client_id, {
            'type': 'connection_established',
            'client_id': client_id,
            'server_time': time.time()
        })
        
        # Start data processor if not running
        if not self.data_processor.running:
            self.data_processor.start_processing()
        
        # Start broadcast thread
        if not self.broadcast_thread:
            self.broadcast_thread = threading.Thread(target=self._broadcast_loop, daemon=True)
            self.broadcast_thread.start()
    
    async def disconnect(self, client_id: str):
        """Handle client disconnection"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            
            logger.info("Client disconnected", 
                       client_id=client_id,
                       remaining_clients=len(self.active_connections))
        
        # Stop data processor if no clients
        if len(self.active_connections) == 0:
            self.data_processor.stop_processing()
    
    async def send_to_client(self, client_id: str, message: Dict[str, Any]):
        """Send message to specific client"""
        if client_id not in self.active_connections:
            return
        
        client = self.active_connections[client_id]
        
        try:
            await client.websocket.send_text(json.dumps(message))
            client.message_count += 1
        except Exception as e:
            logger.error("Error sending message to client", 
                        client_id=client_id, 
                        error=str(e))
            await self.disconnect(client_id)
    
    async def broadcast_to_all(self, message: StreamMessage):
        """Broadcast message to all connected clients"""
        if not self.active_connections:
            return
        
        message_json = json.dumps(message.to_dict())
        disconnected_clients = []
        
        for client_id, client in self.active_connections.items():
            try:
                # Check if client is subscribed to this data type
                if message.data_type in client.subscriptions or not client.subscriptions:
                    await client.websocket.send_text(message_json)
                    client.message_count += 1
            except Exception as e:
                logger.error("Error broadcasting to client", 
                           client_id=client_id, 
                           error=str(e))
                disconnected_clients.append(client_id)
        
        # Remove disconnected clients
        for client_id in disconnected_clients:
            await self.disconnect(client_id)
        
        logger.debug("Message broadcasted", 
                    data_type=message.data_type.value,
                    recipients=len(self.active_connections) - len(disconnected_clients))
    
    async def handle_client_message(self, client_id: str, message: str):
        """Handle incoming message from client"""
        try:
            data = json.loads(message)
            message_type = data.get('type', 'unknown')
            
            if message_type == 'subscribe':
                # Handle subscription request
                await self._handle_subscription(client_id, data)
            elif message_type == 'unsubscribe':
                # Handle unsubscription request
                await self._handle_unsubscription(client_id, data)
            elif message_type == 'ping':
                # Handle ping for connection health
                await self._handle_ping(client_id)
            elif message_type == 'data':
                # Handle incoming data from client
                await self._handle_incoming_data(client_id, data)
            else:
                logger.warning("Unknown message type", 
                           client_id=client_id, 
                           message_type=message_type)
        
        except json.JSONDecodeError:
            logger.error("Invalid JSON received", client_id=client_id)
        except Exception as e:
            logger.error("Error handling client message", 
                        client_id=client_id, 
                        error=str(e))
    
    async def _handle_subscription(self, client_id: str, data: Dict[str, Any]):
        """Handle subscription request"""
        if client_id not in self.active_connections:
            return
        
        client = self.active_connections[client_id]
        subscriptions = data.get('subscriptions', [])
        
        for sub in subscriptions:
            try:
                data_type = StreamDataType(sub)
                client.subscriptions.add(data_type)
            except ValueError:
                logger.warning("Invalid subscription data type", 
                           client_id=client_id, 
                           data_type=sub)
        
        await self.send_to_client(client_id, {
            'type': 'subscription_confirmed',
            'subscriptions': [dt.value for dt in client.subscriptions]
        })
        
        logger.info("Client subscribed", 
                   client_id=client_id, 
                   subscriptions=[dt.value for dt in client.subscriptions])
    
    async def _handle_unsubscription(self, client_id: str, data: Dict[str, Any]):
        """Handle unsubscription request"""
        if client_id not in self.active_connections:
            return
        
        client = self.active_connections[client_id]
        unsubscriptions = data.get('unsubscriptions', [])
        
        for unsub in unsubscriptions:
            try:
                data_type = StreamDataType(unsub)
                client.subscriptions.discard(data_type)
            except ValueError:
                logger.warning("Invalid unsubscription data type", 
                           client_id=client_id, 
                           data_type=unsub)
        
        await self.send_to_client(client_id, {
            'type': 'unsubscription_confirmed',
            'subscriptions': [dt.value for dt in client.subscriptions]
        })
    
    async def _handle_ping(self, client_id: str):
        """Handle ping for connection health"""
        if client_id in self.active_connections:
            self.active_connections[client_id].last_ping = time.time()
            
            await self.send_to_client(client_id, {
                'type': 'pong',
                'timestamp': time.time()
            })
    
    async def _handle_incoming_data(self, client_id: str, data: Dict[str, Any]):
        """Handle incoming data from client"""
        # Validate data
        data_type = data.get('data_type')
        payload = data.get('data', {})
        
        if data_type == StreamDataType.TRAFFIC_FLOW.value:
            is_valid, errors = self.validator.validate_traffic_flow(payload)
        elif data_type == StreamDataType.VEHICLE_DETECTION.value:
            is_valid, errors = self.validator.validate_vehicle_detection(payload)
        else:
            is_valid = True
            errors = []
        
        if not is_valid:
            await self.send_to_client(client_id, {
                'type': 'validation_error',
                'errors': errors
            })
            return
        
        # Add to processing queue
        self.data_processor.data_buffer.put({
            'client_id': client_id,
            'timestamp': time.time(),
            'data_type': data_type,
            'data': payload
        })
        
        # Broadcast to other clients
        message = StreamMessage(
            data_type=StreamDataType(data_type),
            source=client_id,
            data=payload
        )
        
        await self.broadcast_to_all(message)
    
    def _broadcast_loop(self):
        """Background thread for broadcasting queued messages"""
        while True:
            try:
                # Get message from broadcast queue
                message = self.broadcast_queue.get(timeout=1.0)
                
                # Schedule broadcast
                asyncio.run_coroutine_threadsafe(
                    self.broadcast_to_all(message),
                    self.broadcast_queue
                )
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error("Error in broadcast loop", error=str(e))
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        current_time = time.time()
        
        stats = {
            'total_connections': len(self.active_connections),
            'connections_by_type': {},
            'average_messages_per_connection': 0,
            'oldest_connection': None,
            'newest_connection': None
        }
        
        if not self.active_connections:
            return stats
        
        # Count by type
        for client in self.active_connections.values():
            client_type = client.client_type.value
            stats['connections_by_type'][client_type] = stats['connections_by_type'].get(client_type, 0) + 1
        
        # Calculate message statistics
        total_messages = sum(client.message_count for client in self.active_connections.values())
        stats['average_messages_per_connection'] = total_messages / len(self.active_connections)
        
        # Find oldest and newest connections
        connection_times = [(client_id, client.connected_at) for client_id, client in self.active_connections.items()]
        if connection_times:
            stats['oldest_connection'] = min(connection_times, key=lambda x: x[1])
            stats['newest_connection'] = max(connection_times, key=lambda x: x[1])
        
        return stats

# FastAPI application
app = FastAPI(title="Traffic System Real-time Streaming API")
stream_manager = WebSocketStreamManager()

@app.websocket("/ws/{client_id}/{client_type}")
async def websocket_endpoint(websocket: WebSocket, client_id: str, client_type: str):
    """WebSocket endpoint for real-time streaming"""
    await stream_manager.connect(websocket, client_id, client_type)
    
    try:
        while True:
            # Receive message from client
            message = await websocket.receive_text()
            await stream_manager.handle_client_message(client_id, message)
    except WebSocketDisconnect:
        finally:
        await stream_manager.disconnect(client_id)

@app.get("/api/stats")
async def get_stats():
    """Get system statistics"""
    return {
        'connections': stream_manager.get_connection_stats(),
        'metrics': stream_manager.data_processor.get_aggregated_metrics(),
        'timestamp': time.time()
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        'status': 'healthy',
        'timestamp': time.time(),
        'version': '3.0.0'
    }

@app.post("/api/data/{data_type}")
async def receive_data(data_type: str, data: Dict[str, Any]):
    """Receive data via REST API"""
    try:
        # Create stream message
        message = StreamMessage(
            data_type=StreamDataType(data_type),
            source='rest_api',
            data=data
        )
        
        # Add to processing queue
        stream_manager.data_processor.data_buffer.put({
            'client_id': 'rest_api',
            'timestamp': time.time(),
            'data_type': data_type,
            'data': data
        })
        
        # Broadcast to WebSocket clients
        await stream_manager.broadcast_to_all(message)
        
        return {'status': 'success', 'message_id': message.message_id}
    
    except ValueError as e:
        return {'status': 'error', 'message': f'Invalid data type: {e}'}
    except Exception as e:
        return {'status': 'error', 'message': f'Internal error: {e}'}

@app.get("/")
async def get_client():
    """Serve simple WebSocket client for testing"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Traffic System Real-time Client</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .container { max-width: 1200px; margin: 0 auto; }
            .stats { background: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
            .messages { height: 400px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; }
            .message { margin-bottom: 10px; padding: 8px; border-radius: 3px; }
            .traffic-flow { background: #e3f2fd; }
            .vehicle-detection { background: #f3e5f5; }
            .emergency-alert { background: #ffebee; border-left: 4px solid #f44336; }
            .controls { margin: 20px 0; }
            button { margin: 5px; padding: 10px 15px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Traffic System Real-time Monitor</h1>
            
            <div class="stats" id="stats">
                <h3>Connection Statistics</h3>
                <p>Connected clients: <span id="client-count">0</span></p>
                <p>Messages received: <span id="message-count">0</span></p>
            </div>
            
            <div class="controls">
                <button onclick="subscribe('traffic_flow')">Subscribe Traffic Flow</button>
                <button onclick="subscribe('vehicle_detection')">Subscribe Vehicle Detection</button>
                <button onclick="subscribe('emergency_alert')">Subscribe Emergency Alerts</button>
                <button onclick="sendTestData()">Send Test Data</button>
            </div>
            
            <div class="messages" id="messages"></div>
        </div>
        
        <script>
            let ws;
            let messageCount = 0;
            
            function connect() {
                const clientId = 'client_' + Math.random().toString(36).substr(2, 9);
                const clientType = 'dashboard';
                
                ws = new WebSocket(`ws://localhost:8000/ws/${clientId}/${clientType}`);
                
                ws.onopen = function(event) {
                    console.log('Connected to server');
                    updateStats();
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    displayMessage(data);
                    messageCount++;
                    updateStats();
                };
                
                ws.onclose = function(event) {
                    console.log('Disconnected from server');
                    setTimeout(connect, 5000); // Reconnect after 5 seconds
                };
                
                ws.onerror = function(error) {
                    console.error('WebSocket error:', error);
                };
            }
            
            function subscribe(dataType) {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({
                        type: 'subscribe',
                        subscriptions: [dataType]
                    }));
                }
            }
            
            function sendTestData() {
                if (ws && ws.readyState === WebSocket.OPEN) {
                    ws.send(JSON.stringify({
                        type: 'data',
                        data_type: 'traffic_flow',
                        data: {
                            intersection_id: 'test_intersection',
                            vehicle_count: Math.floor(Math.random() * 50),
                            average_speed: Math.floor(Math.random() * 60) + 20,
                            flow_rate: Math.floor(Math.random() * 500) + 100
                        }
                    }));
                }
            }
            
            function displayMessage(data) {
                const messagesDiv = document.getElementById('messages');
                const messageDiv = document.createElement('div');
                messageDiv.className = 'message ' + data.data_type;
                
                const timestamp = new Date(data.timestamp * 1000).toLocaleTimeString();
                messageDiv.innerHTML = `
                    <strong>[${timestamp}] ${data.data_type.toUpperCase()}</strong><br>
                    ${JSON.stringify(data.data, null, 2)}
                `;
                
                messagesDiv.appendChild(messageDiv);
                messagesDiv.scrollTop = messagesDiv.scrollHeight;
            }
            
            function updateStats() {
                fetch('/api/stats')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('client-count').textContent = data.connections.total_connections;
                        document.getElementById('message-count').textContent = messageCount;
                    });
            }
            
            // Connect on page load
            connect();
            
            // Update stats every 5 seconds
            setInterval(updateStats, 5000);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# Export main classes
__all__ = [
    'WebSocketStreamManager',
    'RealTimeDataProcessor',
    'TrafficDataValidator',
    'StreamMessage',
    'ClientConnection',
    'StreamDataType',
    'ClientType',
    'app'
]

if __name__ == "__main__":
    # Run the FastAPI server
    uvicorn.run(
        "real_time_streaming:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )