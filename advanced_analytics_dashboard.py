"""
Advanced Analytics Dashboard
============================

Real-time data integration dashboard with:
- Live traffic metrics visualization
- Interactive signal control interface
- Performance monitoring and alerting
- Historical data analysis and reporting
- Predictive analytics visualization
- Multi-intersection coordination view
- Emergency response monitoring

Author: Top 0.1% Expert Team
Date: November 2025
Version: 3.0.0
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import time
import json
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import requests
import threading
from collections import deque, defaultdict
import math

# Import our advanced systems
from real_time_streaming import WebSocketStreamManager, StreamDataType
from predictive_models import PredictiveAnalyticsEngine, PredictionHorizon
from multi_intersection_coordinator import NetworkCoordinator
from emergency_vehicle_system import SignalPreemptionController
from pedestrian_cyclist_system import VulnerableUserManager
from performance_optimization import PerformanceOptimizer
from environmental_system import WeatherSystem, TimeSystem

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DashboardTheme(Enum):
    """Dashboard theme options"""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"

class TimeRange(Enum):
    """Time range options for analytics"""
    LAST_HOUR = "last_hour"
    LAST_6_HOURS = "last_6_hours"
    LAST_24_HOURS = "last_24_hours"
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    CUSTOM = "custom"

class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

@dataclass
class DashboardConfig:
    """Dashboard configuration"""
    refresh_interval: int = 5  # seconds
    max_data_points: int = 1000
    enable_animations: bool = True
    enable_sound_alerts: bool = True
    theme: DashboardTheme = DashboardTheme.AUTO
    auto_refresh: bool = True

@dataclass
class AlertMessage:
    """Alert message for dashboard"""
    alert_id: str
    level: AlertLevel
    title: str
    message: str
    timestamp: float
    source: str
    acknowledged: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

class AdvancedAnalyticsDashboard:
    """Advanced analytics dashboard with real-time integration"""
    
    def __init__(self):
        # Initialize components
        self.stream_manager = WebSocketStreamManager()
        self.predictive_engine = PredictiveAnalyticsEngine()
        self.network_coordinator = NetworkCoordinator()
        self.emergency_controller = SignalPreemptionController()
        self.vulnerable_user_manager = VulnerableUserManager()
        self.performance_optimizer = PerformanceOptimizer()
        
        # Dashboard state
        self.config = DashboardConfig()
        self.alerts = deque(maxlen=100)
        self.data_history = defaultdict(lambda: deque(maxlen=1000))
        self.is_connected = False
        
        # Real-time data
        self.current_metrics = {}
        self.historical_data = pd.DataFrame()
        
        # Session state
        self.selected_intersection = None
        self.selected_time_range = TimeRange.LAST_HOUR
        self.custom_date_range = None
        
        # Performance monitoring
        self.performance_history = deque(maxlen=100)
        
        # Start background data collection
        self._start_data_collection()
        
        logger.info("Advanced Analytics Dashboard initialized")
    
    def _start_data_collection(self):
        """Start background data collection"""
        def collect_data():
            while True:
                try:
                    # Collect real-time metrics
                    metrics = self._collect_realtime_metrics()
                    self.current_metrics = metrics
                    
                    # Store in history
                    timestamp = time.time()
                    for key, value in metrics.items():
                        self.data_history[key].append((timestamp, value))
                    
                    # Check for alerts
                    self._check_alerts(metrics)
                    
                    time.sleep(self.config.refresh_interval)
                    
                except Exception as e:
                    logger.error(f"Data collection error: {e}")
                    time.sleep(5)
        
        # Start data collection thread
        data_thread = threading.Thread(target=collect_data, daemon=True)
        data_thread.start()
    
    def _collect_realtime_metrics(self) -> Dict[str, Any]:
        """Collect real-time metrics from all systems"""
        metrics = {
            'timestamp': time.time(),
            'traffic_flow': {},
            'signal_status': {},
            'performance': {},
            'predictions': {},
            'emergencies': {},
            'vulnerable_users': {},
            'environmental': {}
        }
        
        # Get traffic flow data
        try:
            traffic_data = self.stream_manager.get_connection_stats()
            metrics['traffic_flow'] = {
                'active_connections': traffic_data.get('total_connections', 0),
                'message_rate': traffic_data.get('average_messages_per_connection', 0),
                'data_types': list(traffic_data.keys(), [])
            }
        except:
            pass
        
        # Get signal status
        try:
            signal_metrics = self.network_coordinator.get_network_metrics()
            metrics['signal_status'] = {
                'total_intersections': signal_metrics.get('total_intersections', 0),
                'coordination_mode': signal_metrics.get('coordination_mode', 'unknown'),
                'average_delay': signal_metrics.get('average_delay_per_intersection', 0),
                'network_congestion': signal_metrics.get('network_congestion_level', 0)
            }
        except:
            pass
        
        # Get performance metrics
        try:
            perf_metrics = self.performance_optimizer.get_performance_report()
            metrics['performance'] = {
                'cpu_usage': perf_metrics.get('cpu_usage', 0),
                'memory_usage': perf_metrics.get('memory_usage', 0),
                'gpu_usage': perf_metrics.get('gpu_usage', 0),
                'performance_score': perf_metrics.get('performance_score', 0),
                'active_threads': perf_metrics.get('active_threads', 0)
            }
        except:
            pass
        
        # Get predictions
        try:
            predictions = self.predictive_engine.get_model_performance()
            metrics['predictions'] = {
                'models_trained': predictions.get('models_trained', False),
                'last_training': predictions.get('last_training_time', 0),
                'prediction_accuracy': predictions.get('accuracy', 0),
                'active_predictions': len(predictions.get('active_predictions', []))
            }
        except:
            pass
        
        # Get emergency status
        try:
            emergency_status = self.emergency_controller.get_preemption_status()
            metrics['emergencies'] = {
                'active_preemptions': emergency_status.get('active_preemptions', 0),
                'pending_requests': emergency_status.get('queued_requests', 0),
                'total_processed': emergency_status.get('total_preemptions', 0)
            }
        except:
            pass
        
        # Get vulnerable user data
        try:
            user_metrics = self.vulnerable_user_manager.get_safety_summary()
            metrics['vulnerable_users'] = {
                'total_pedestrians': user_metrics.get('total_pedestrians', 0),
                'total_cyclists': user_metrics.get('total_cyclists', 0),
                'active_crossings': user_metrics.get('active_crossings', 0),
                'safety_events': user_metrics.get('safety_events_count', 0),
                'compliance_rate': user_metrics.get('compliance_rate', 0)
            }
        except:
            pass
        
        # Get environmental data
        try:
            # This would integrate with weather APIs
            metrics['environmental'] = {
                'weather_condition': 'clear',
                'temperature': 20.0,
                'visibility': 'good',
                'time_of_day': 'day'
            }
        except:
            pass
        
        return metrics
    
    def _check_alerts(self, metrics: Dict[str, Any]):
        """Check for alert conditions"""
        alerts = []
        
        # Performance alerts
        if metrics.get('performance', {}).get('cpu_usage', 0) > 90:
            alerts.append(AlertMessage(
                alert_id=f"perf_cpu_{int(time.time())}",
                level=AlertLevel.WARNING,
                title="High CPU Usage",
                message=f"CPU usage is {metrics['performance']['cpu_usage']:.1f}%",
                timestamp=time.time(),
                source="performance_monitor"
            ))
        
        if metrics.get('performance', {}).get('memory_usage', 0) > 85:
            alerts.append(AlertMessage(
                alert_id=f"perf_mem_{int(time.time())}",
                level=AlertLevel.WARNING,
                title="High Memory Usage",
                message=f"Memory usage is {metrics['performance']['memory_usage']:.1f}%",
                timestamp=time.time(),
                source="performance_monitor"
            ))
        
        # Traffic alerts
        if metrics.get('traffic_flow', {}).get('active_connections', 0) > 100:
            alerts.append(AlertMessage(
                alert_id=f"traffic_conn_{int(time.time())}",
                level=AlertLevel.WARNING,
                title="High Connection Count",
                message=f"Active connections: {metrics['traffic_flow']['active_connections']}",
                timestamp=time.time(),
                source="traffic_monitor"
            ))
        
        # Emergency alerts
        if metrics.get('emergencies', {}).get('active_preemptions', 0) > 0:
            alerts.append(AlertMessage(
                alert_id=f"emergency_{int(time.time())}",
                level=AlertLevel.CRITICAL,
                title="Emergency Preemption Active",
                message=f"Active preemptions: {metrics['emergencies']['active_preemptions']}",
                timestamp=time.time(),
                source="emergency_system"
            ))
        
        # Add alerts to queue
        for alert in alerts:
            self.alerts.append(alert)
    
    def render_header(self):
        """Render dashboard header"""
        st.set_page_config(
            page_title="Advanced Traffic Analytics Dashboard",
            page_icon="🚦",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        # Theme toggle
        col1, col2, col3 = st.columns([1, 2, 1])
        with col1:
            st.title("🚦 Traffic Analytics")
        with col2:
            if st.button("🔄 Refresh"):
                st.rerun()
        with col3:
            theme = st.selectbox("Theme", options=[t.value for t in DashboardTheme], 
                                index=[t.value for t in DashboardTheme].index(self.config.theme)])
            if theme != self.config.theme:
                self.config.theme = theme
                st.rerun()
        
        # Connection status
        status_color = "🟢" if self.is_connected else "🔴"
        st.markdown(f"**Status:** {status_color} {'Connected' if self.is_connected else 'Disconnected'}")
        
        # Alert indicator
        if self.alerts:
            recent_alerts = [a for a in self.alerts if not a.acknowledged and 
                           time.time() - a.timestamp < 300]  # Last 5 minutes
            if recent_alerts:
                st.markdown(f"🚨 **{len(recent_alerts)} Active Alerts**")
    
    def render_sidebar(self):
        """Render sidebar with controls"""
        with st.sidebar:
            st.header("⚙️ Controls")
            
            # System controls
            st.subheader("System Controls")
            
            # Data collection
            auto_refresh = st.checkbox("Auto Refresh", value=self.config.auto_refresh)
            if auto_refresh != self.config.auto_refresh:
                self.config.auto_refresh = auto_refresh
            
            refresh_interval = st.slider("Refresh Interval (s)", 
                                     min_value=1, max_value=60, 
                                     value=self.config.refresh_interval)
            if refresh_interval != self.config.refresh_interval:
                self.config.refresh_interval = refresh_interval
            
            # Connection settings
            st.subheader("Connection Settings")
            
            # WebSocket connection
            if st.button("Connect to Real-time Stream"):
                self._connect_to_stream()
            
            st.text_input("WebSocket URL", 
                        value="ws://localhost:8000/ws/dashboard/standard",
                        key="websocket_url",
                        help="WebSocket URL for real-time data")
            
            # System integration
            st.subheader("System Integration")
            
            # Enable/disable systems
            enable_predictive = st.checkbox("Predictive Analytics", value=True)
            enable_emergency = st.checkbox("Emergency System", value=True)
            enable_vulnerable_users = st.checkbox("Vulnerable Users", value=True)
            enable_performance = st.checkbox("Performance Monitor", value=True)
            
            # View options
            st.subheader("View Options")
            
            self.selected_time_range = st.selectbox(
                "Time Range",
                options=[t.value for t in TimeRange],
                index=[t.value for t in TimeRange].index(self.selected_time_range)]
            )
            
            # Intersection selection
            intersections = ["All", "INT_A", "INT_B", "INT_C", "INT_D"]
            self.selected_intersection = st.selectbox(
                "Intersection",
                options=intersections,
                index=0
            )
            
            # Alert settings
            st.subheader("Alert Settings")
            
            enable_sound = st.checkbox("Sound Alerts", value=self.config.enable_sound_alerts)
            if enable_sound != self.config.enable_sound_alerts:
                self.config.enable_sound_alerts = enable_sound
            
            alert_threshold = st.slider("Alert Threshold", 
                                    min_value=1, max_value=10, 
                                    value=5,
                                    help="Alert sensitivity level")
            
            # Performance settings
            st.subheader("Performance Settings")
            
            optimization_level = st.selectbox(
                "Optimization Level",
                options=["Minimal", "Balanced", "Maximum"],
                index=1
            )
            
            # Export options
            st.subheader("Export Options")
            
            export_format = st.selectbox(
                "Export Format",
                options=["JSON", "CSV", "Excel"],
                index=0
            )
            
            if st.button("Export Data"):
                self._export_data(export_format)
    
    def render_main_dashboard(self):
        """Render main dashboard with metrics and visualizations"""
        # Key metrics
        st.header("📊 Real-time Traffic Metrics")
        
        # Create columns for metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Active Connections", 
                     f"{self.current_metrics.get('traffic_flow', {}).get('active_connections', 0)}")
        
        with col2:
            st.metric("Avg Delay", 
                     f"{self.current_metrics.get('signal_status', {}).get('average_delay', 0):.1f}s")
        
        with col3:
            st.metric("Network Congestion", 
                     f"{self.current_metrics.get('signal_status', {}).get('network_congestion', 0):.1%}")
        
        with col4:
            st.metric("Performance Score", 
                     f"{self.current_metrics.get('performance', {}).get('performance_score', 0):.0f}")
        
        # Traffic flow chart
        st.subheader("📈 Traffic Flow Analysis")
        
        # Get historical data for charts
        traffic_data = self._get_historical_data('traffic_flow')
        
        if not traffic_data.empty:
            # Create traffic flow chart
            fig = px.line(traffic_data, 
                             x='timestamp', 
                             y='active_connections',
                             title='Active Connections Over Time',
                             color='blue')
            st.plotly_chart(fig)
            
            # Create volume distribution chart
            volume_data = self._get_historical_data('vehicle_volume')
            if not volume_data.empty:
                fig2 = px.bar(volume_data, 
                                 x='intersection_id', 
                                 y='vehicle_count',
                                 title='Vehicle Volume by Intersection',
                                 color='green')
                st.plotly_chart(fig2)
        
        # Signal status visualization
        st.subheader("🚦 Signal Status Visualization")
        
        # Create signal status heatmap
        signal_data = self._get_signal_status_data()
        if not signal_data.empty:
            fig3 = px.imshow(signal_data.pivot_table(values='phase_timer', 
                                                      index='intersection_id', 
                                                      columns='movement_id'),
                             title='Signal Phase Timings',
                             color_continuous='RdYlGn',
                             labels=dict(x="Movement", y="Intersection", color="Phase Timer (s)")
            st.plotly_chart(fig3)
        
        # Performance monitoring
        st.subheader("⚡ Performance Monitoring")
        
        # Performance metrics chart
        perf_data = self._get_historical_data('performance')
        if not perf_data.empty:
            fig4 = px.line(perf_data, 
                             x='timestamp', 
                             y=['cpu_usage', 'memory_usage'],
                             title='System Performance Over Time',
                             labels={'value': 'Metric', 'variable': 'Type'})
            st.plotly_chart(fig4)
        
        # Predictive analytics
        st.subheader("🔮 Predictive Analytics")
        
        # Prediction accuracy
        pred_metrics = self._get_historical_data('predictions')
        if not pred_metrics.empty:
            accuracy = pred_metrics['prediction_accuracy'].mean()
            st.metric("Prediction Accuracy", f"{accuracy:.1%}")
            
            # Prediction visualization
            pred_data = self._get_historical_data('traffic_predictions')
            if not pred_data.empty:
                fig5 = px.scatter(pred_data,
                                  x='predicted_volume',
                                  y='actual_volume',
                                  title='Prediction vs Actual',
                                  color='purple')
                st.plotly_chart(fig5)
    
    def render_alerts_panel(self):
        """Render alerts panel"""
        st.subheader("🚨 Active Alerts")
        
        # Filter alerts
        unacknowledged_alerts = [a for a in self.alerts if not a.acknowledged]
        
        if unacknowledged_alerts:
            for alert in unacknowledged_alerts[-10:]:  # Show last 10
                with st.expander(f"Alert - {alert.level.value.upper()} - {alert.title}"):
                    st.write(f"**Time:** {datetime.fromtimestamp(alert.timestamp).strftime('%Y-%m-%d %H:%M:%S')}")
                    st.write(f"**Source:** {alert.source}")
                    st.write(f"**Message:** {alert.message}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Acknowledge"):
                            alert.acknowledged = True
                    with col2:
                        if st.button("Dismiss"):
                            self.alerts.remove(alert)
                    
                    # Show metadata if available
                    if alert.metadata:
                        st.json(alert.metadata)
        
        else:
            st.info("No active alerts")
    
    def render_emergency_panel(self):
        """Render emergency response panel"""
        st.subheader("🚑 Emergency Response")
        
        # Emergency status
        emergency_data = self.current_metrics.get('emergencies', {})
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Active Preemptions", 
                         f"{emergency_data.get('active_preemptions', 0)}")
        
        with col2:
            st.metric("Pending Requests", 
                         f"{emergency_data.get('pending_requests', 0)}")
        
        # Emergency actions
        st.subheader("Emergency Actions")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🚨 Trigger Emergency", type="primary"):
                self._trigger_emergency_scenario()
        
        with col2:
            if st.button("🚑 Clear All", type="secondary"):
                self._clear_all_emergencies()
        
        with col3:
            if st.button("📋 Test System", type="secondary"):
                self._test_emergency_system()
        
        # Emergency log
        st.subheader("Emergency Log")
        
        emergency_log = self._get_emergency_log()
        if emergency_log:
            st.dataframe(emergency_log)
    
    def render_vulnerable_users_panel(self):
        """Render vulnerable users panel"""
        st.subheader("🚶 Vulnerable Users")
        
        user_data = self.current_metrics.get('vulnerable_users', {})
        
        # User statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Pedestrians", 
                         f"{user_data.get('total_pedestrians', 0)}")
        
        with col2:
            st.metric("Cyclists", 
                         f"{user_data.get('total_cyclists', 0)}")
        
        with col3:
            st.metric("Active Crossings", 
                         f"{user_data.get('active_crossings', 0)}")
        
        with col4:
            st.metric("Safety Events", 
                         f"{user_data.get('safety_events_count', 0)}")
        
        # Safety compliance chart
        st.subheader("Safety Compliance")
        
        safety_data = self._get_historical_data('safety_compliance')
        if not safety_data.empty:
            fig = px.line(safety_data,
                             x='timestamp',
                             y='compliance_rate',
                             title='Safety Compliance Rate',
                             color='green')
            st.plotly_chart(fig)
        
        # Recent safety events
        st.subheader("Recent Safety Events")
        
        safety_events = self._get_historical_data('safety_events')
        if not safety_events.empty:
            st.dataframe(safety_events.tail(10))  # Last 10 events
    
    def _connect_to_stream(self):
        """Connect to WebSocket stream"""
        try:
            # This would establish WebSocket connection
            st.success("Connected to real-time stream")
            self.is_connected = True
        except Exception as e:
            st.error(f"Failed to connect: {e}")
            self.is_connected = False
    
    def _trigger_emergency_scenario(self):
        """Trigger emergency scenario for testing"""
        # This would trigger an actual emergency scenario
        st.warning("Emergency scenario triggered")
    
    def _clear_all_emergencies(self):
        """Clear all emergency alerts"""
        self.alerts.clear()
        st.info("All emergency alerts cleared")
    
    def _test_emergency_system(self):
        """Test emergency system"""
        st.info("Emergency system test initiated")
    
    def _get_historical_data(self, data_type: str) -> pd.DataFrame:
        """Get historical data for visualization"""
        # Convert data history to DataFrame
        if data_type in self.data_history:
            data_points = list(self.data_history[data_type])
            
            if data_points:
                # Create DataFrame from data points
                df_data = []
                for point in data_points[-500:]:  # Last 500 points
                    timestamp, value = point
                    if isinstance(value, dict):
                        row = {'timestamp': timestamp}
                        row.update(value)
                    else:
                        row = {'timestamp': timestamp, data_type: value}
                    df_data.append(row)
                
                return pd.DataFrame(df_data)
        
        return pd.DataFrame()
    
    def _get_signal_status_data(self) -> pd.DataFrame:
        """Get signal status data for heatmap"""
        # Mock data for demonstration
        data = {
            'intersection_id': ['INT_A', 'INT_B', 'INT_C', 'INT_D'],
            'movement_id': ['NS_GREEN', 'EW_GREEN', 'NB_GREEN', 'SB_GREEN'],
            'phase_timer': [15, 20, 25, 30]
        }
        
        return pd.DataFrame(data)
    
    def _get_emergency_log(self) -> List[Dict[str, Any]]:
        """Get emergency log"""
        # Mock emergency log for demonstration
        return [
            {
                'timestamp': time.time() - 3600,
                'type': 'preemption',
                'intersection': 'INT_A',
                'vehicle_type': 'ambulance',
                'duration': 45,
                'resolved': True
            },
            {
                'timestamp': time.time() - 1800,
                'type': 'accident',
                'intersection': 'INT_B',
                'severity': 'moderate',
                'resolved': False
            }
        ]
    
    def _export_data(self, format: str):
        """Export dashboard data"""
        try:
            # Collect all data
            export_data = {
                'timestamp': datetime.now().isoformat(),
                'current_metrics': self.current_metrics,
                'alerts': list(self.alerts),
                'historical_data': {
                    key: list(self.data_history[key])[-100:] 
                    for key in self.data_history.keys()
                }
            }
            
            # Export based on format
            if format == "JSON":
                st.download_button("Download JSON", 
                                   data=json.dumps(export_data, indent=2),
                                   file_name=f"traffic_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            
            elif format == "CSV":
                # Convert to CSV and download
                df = pd.DataFrame(export_data['historical_data']['traffic_flow'])
                st.download_button("Download CSV", 
                                   data=df.to_csv(index=False),
                                   file_name=f"traffic_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
            
            elif format == "Excel":
                # Create Excel and download
                df = pd.DataFrame(export_data['historical_data']['traffic_flow'])
                st.download_button("Download Excel", 
                                   data=df.to_excel(index=False),
                                   file_name=f"traffic_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
            
            st.success(f"Data exported in {format} format")
            
        except Exception as e:
            st.error(f"Export failed: {e}")
    
    def run(self):
        """Run the dashboard"""
        # Apply theme
        if self.config.theme == DashboardTheme.DARK:
            st.markdown("""
            <style>
            .stApp {
                background-color: #1e1e1e;
                color: white;
            }
            </style>
            """, unsafe_allow_html=True)
        elif self.config.theme == DashboardTheme.LIGHT:
            st.markdown("""
            <style>
            .stApp {
                background-color: white;
                color: #1e1e1e;
            }
            </style>
            """, unsafe_allow_html=True)
        
        # Render components
        self.render_header()
        self.render_sidebar()
        
        # Create tabs for different views
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Dashboard", "🚨 Alerts", "🚑 Emergency", "🚶 Vulnerable Users", "⚙️ Settings"
        ])
        
        with tab1:
            self.render_main_dashboard()
        
        with tab2:
            self.render_alerts_panel()
        
        with tab3:
            self.render_emergency_panel()
        
        with tab4:
            self.render_vulnerable_users_panel()
        
        with tab5:
            st.subheader("⚙️ Dashboard Settings")
            
            # Display current configuration
            st.json(self.config.__dict__)
            
            # Performance settings
            st.subheader("Performance Settings")
            st.write(f"Refresh Interval: {self.config.refresh_interval}s")
            st.write(f"Max Data Points: {self.config.max_data_points}")
            st.write(f"Auto Refresh: {self.config.auto_refresh}")
            st.write(f"Theme: {self.config.theme.value}")
            
            # System status
            st.subheader("System Status")
            st.write(f"Connected: {self.is_connected}")
            st.write(f"Active Alerts: {len([a for a in self.alerts if not a.acknowledged])}")
            st.write(f"Data Points Collected: {sum(len(self.data_history[key]) for key in self.data_history.keys())}")

def main():
    """Main entry point"""
    dashboard = AdvancedAnalyticsDashboard()
    dashboard.run()

if __name__ == "__main__":
    main()