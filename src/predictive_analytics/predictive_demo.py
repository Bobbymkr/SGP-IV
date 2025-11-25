"""
Predictive Analytics Demo

Comprehensive demonstration of predictive analytics capabilities:
Graph Neural Networks, Transformers, and Social Media integration
"""

import numpy as np
import pandas as pd
import torch
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
import argparse
import networkx as nx
from sklearn.metrics import mean_absolute_error, mean_squared_error

# Import our modules
from predictive_models import (
    PredictiveAnalyticsEngine, GraphNeuralNetwork, TrafficTransformer,
    SocialMediaAnalyzer, TrafficNode, TrafficEdge, SocialMediaEvent,
    create_gnn_model, create_transformer_model, create_social_analyzer, create_predictive_engine
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PredictiveAnalyticsDemo:
    """Main demonstration class for predictive analytics"""
    
    def __init__(self, output_dir: str = "predictive_demo_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self.engine = create_predictive_engine()
        self.social_analyzer = create_social_analyzer()
        
        # Demo data
        self.demo_graph = None
        self.demo_sequences = None
        self.demo_social_posts = None
        
        # Results storage
        self.results = {}
        
    def create_demo_traffic_network(self) -> nx.DiGraph:
        """Create demonstration traffic network"""
        logger.info("Creating demo traffic network...")
        
        # Create nodes (intersections)
        nodes = []
        for i in range(20):  # 20 intersections
            node = TrafficNode(
                node_id=f"intersection_{i}",
                latitude=40.7128 + np.random.uniform(-0.1, 0.1),
                longitude=-74.0060 + np.random.uniform(-0.1, 0.1),
                features={
                    'flow': np.random.uniform(100, 1000),
                    'speed': np.random.uniform(20, 60),
                    'occupancy': np.random.uniform(0.1, 0.9),
                    'density': np.random.uniform(10, 100),
                    'travel_time': np.random.uniform(1, 10),
                    'delay': np.random.uniform(0, 5),
                    'queue_length': np.random.uniform(0, 20),
                    'stop_rate': np.random.uniform(0, 0.5),
                    'saturation': np.random.uniform(0.2, 1.0),
                    'level_of_service': np.random.uniform(1, 6)
                }
            )
            nodes.append(node)
        
        # Create edges (road segments)
        edges = []
        for i in range(20):
            # Connect to nearby nodes
            for j in range(i+1, min(i+4, 20)):  # Connect to next 3 nodes
                edge = TrafficEdge(
                    source=f"intersection_{i}",
                    target=f"intersection_{j}",
                    distance=np.random.uniform(0.5, 5.0),
                    capacity=np.random.uniform(500, 2000),
                    current_flow=np.random.uniform(100, 1500),
                    travel_time=np.random.uniform(1, 10),
                    features={
                        'congestion_index': np.random.uniform(0, 1),
                        'free_flow_speed': np.random.uniform(40, 80),
                        'actual_speed': np.random.uniform(20, 60)
                    }
                )
                edges.append(edge)
        
        # Build graph
        self.engine.build_traffic_graph(nodes, edges)
        self.demo_graph = self.engine.traffic_graph
        
        logger.info(f"Created traffic network with {len(nodes)} nodes and {len(edges)} edges")
        return self.demo_graph
    
    def create_demo_time_series(self, num_sequences: int = 1000, 
                               sequence_length: int = 48) -> np.ndarray:
        """Create demonstration time series data"""
        logger.info("Creating demo time series data...")
        
        # Generate synthetic traffic data
        sequences = []
        
        for _ in range(num_sequences):
            # Create sequence with daily patterns
            sequence = []
            base_flow = np.random.uniform(200, 800)
            
            for t in range(sequence_length):
                # Add daily pattern (peak hours)
                hour_of_day = (t % 24)
                if 7 <= hour_of_day <= 9 or 17 <= hour_of_day <= 19:  # Rush hours
                    flow_multiplier = 1.5
                elif 10 <= hour_of_day <= 16:  # Daytime
                    flow_multiplier = 1.2
                elif 22 <= hour_of_day or hour_of_day <= 6:  # Night
                    flow_multiplier = 0.6
                else:
                    flow_multiplier = 1.0
                
                # Add noise and trends
                flow = base_flow * flow_multiplier + np.random.normal(0, 50)
                speed = max(10, 60 - flow/20 + np.random.normal(0, 5))
                occupancy = min(0.95, flow/1000 + np.random.normal(0, 0.1))
                
                sequence.append([flow, speed, occupancy])
            
            sequences.append(sequence)
        
        self.demo_sequences = np.array(sequences)
        logger.info(f"Created {num_sequences} sequences of length {sequence_length}")
        return self.demo_sequences
    
    def create_demo_social_media_posts(self, num_posts: int = 200) -> List[Dict]:
        """Create demonstration social media posts"""
        logger.info("Creating demo social media posts...")
        
        posts = []
        platforms = ['twitter', 'facebook', 'reddit', 'news']
        
        # Traffic event templates
        event_templates = [
            "Major accident on {location} causing heavy traffic delays",
            "Construction work on {location} - expect delays",
            "Traffic jam on {location} due to {cause}",
            "Road closure on {location} for {event}",
            "Heavy {weather} causing traffic issues on {location}",
            "Concert at {location} causing traffic congestion",
            "Marathon route includes {location} - expect delays"
        ]
        
        locations = ["Main Street", "Highway 101", "Downtown", "Airport Road", 
                    "Bridge Street", "Park Avenue", "Station Road", "Mall Area"]
        
        causes = ["accident", "breakdown", "weather", "event", "construction"]
        events = ["festival", "game", "parade", "marathon", "concert"]
        weather_conditions = ["rain", "snow", "fog", "storm"]
        
        for i in range(num_posts):
            # Random post generation
            template = np.random.choice(event_templates)
            location = np.random.choice(locations)
            
            # Fill template
            if "{cause}" in template:
                cause = np.random.choice(causes)
                content = template.format(location=location, cause=cause)
            elif "{event}" in template:
                event = np.random.choice(events)
                content = template.format(location=location, event=event)
            elif "{weather}" in template:
                weather = np.random.choice(weather_conditions)
                content = template.format(location=location, weather=weather)
            else:
                content = template.format(location=location)
            
            post = {
                'content': content,
                'platform': np.random.choice(platforms),
                'timestamp': datetime.now() - timedelta(minutes=np.random.randint(0, 1440)),
                'location': (40.7128 + np.random.uniform(-0.05, 0.05),
                            -74.0060 + np.random.uniform(-0.05, 0.05))
            }
            posts.append(post)
        
        self.demo_social_posts = posts
        logger.info(f"Created {num_posts} social media posts")
        return posts
    
    def run_gnn_demo(self):
        """Demonstrate Graph Neural Network capabilities"""
        logger.info("Running GNN Demo...")
        
        # Create demo data
        if self.demo_graph is None:
            self.create_demo_traffic_network()
        
        # Prepare graph data
        graph_data = self.engine.prepare_graph_data()
        
        # Initialize GNN
        self.engine.initialize_gnn(hidden_dim=64, num_layers=2)
        
        # Create training data (simplified)
        train_data = [graph_data] * 10  # Duplicate for demo
        
        # Train model (simplified training)
        logger.info("Training GNN model...")
        losses = self.engine.train_gnn(train_data, epochs=20, learning_rate=0.01)
        
        # Make predictions
        predictions = self.engine.predict_traffic_gnn(graph_data)
        
        # Store results
        self.results['gnn'] = {
            'training_losses': losses,
            'predictions': predictions,
            'num_nodes': graph_data.x.shape[0],
            'num_edges': graph_data.edge_index.shape[1],
            'final_loss': losses[-1] if losses else 0
        }
        
        logger.info(f"GNN Demo completed. Final loss: {losses[-1]:.4f}")
        self._plot_gnn_results()
    
    def run_transformer_demo(self):
        """Demonstrate Transformer capabilities"""
        logger.info("Running Transformer Demo...")
        
        # Create demo data
        if self.demo_sequences is None:
            self.create_demo_time_series()
        
        # Prepare data
        sequences = torch.FloatTensor(self.demo_sequences)
        
        # Split into train/test
        train_size = int(0.8 * len(sequences))
        train_sequences = sequences[:train_size]
        test_sequences = sequences[train_size:]
        
        # Create targets (next 24 time steps)
        train_targets = train_sequences[:, -24:, 0]  # Flow values
        test_targets = test_sequences[:, -24:, 0]
        
        # Create external factors (weather, events, etc.)
        train_external = torch.randn(train_sequences.shape[0], 10)
        test_external = torch.randn(test_sequences.shape[0], 10)
        
        # Initialize Transformer
        self.engine.initialize_transformer(d_model=128, num_layers=4)
        
        # Train model
        logger.info("Training Transformer model...")
        losses = self.engine.train_transformer(
            train_sequences[:, :-24, :],  # Use all but last 24 steps
            train_targets,
            train_external,
            epochs=30,
            learning_rate=0.001
        )
        
        # Make predictions
        with torch.no_grad():
            predictions = self.engine.predict_traffic_transformer(
                test_sequences[0, :-24, :],
                test_external[0]
            )
        
        # Calculate metrics
        mae = mean_absolute_error(test_targets[0].numpy(), predictions['flow'])
        mse = mean_squared_error(test_targets[0].numpy(), predictions['flow'])
        
        # Store results
        self.results['transformer'] = {
            'training_losses': losses,
            'predictions': predictions,
            'targets': test_targets[0].numpy(),
            'mae': mae,
            'mse': mse,
            'rmse': np.sqrt(mse),
            'final_loss': losses[-1] if losses else 0
        }
        
        logger.info(f"Transformer Demo completed. MAE: {mae:.2f}, RMSE: {np.sqrt(mse):.2f}")
        self._plot_transformer_results()
    
    def run_social_media_demo(self):
        """Demonstrate Social Media integration"""
        logger.info("Running Social Media Demo...")
        
        # Create demo posts
        if self.demo_social_posts is None:
            self.create_demo_social_media_posts()
        
        # Process posts
        events = []
        for post in self.demo_social_posts:
            event = self.social_analyzer.analyze_post(
                content=post['content'],
                platform=post['platform'],
                timestamp=post['timestamp'],
                location=post['location']
            )
            if event:
                events.append(event)
        
        # Aggregate events
        aggregated_events = self.social_analyzer.aggregate_events(events)
        
        # Analyze event distribution
        event_types = {}
        platform_distribution = {}
        confidence_scores = []
        
        for event in events:
            # Event types
            event_type = event.event_type
            event_types[event_type] = event_types.get(event_type, 0) + 1
            
            # Platform distribution
            platform = event.platform
            platform_distribution[platform] = platform_distribution.get(platform, 0) + 1
            
            # Confidence scores
            confidence_scores.append(event.confidence)
        
        # Store results
        self.results['social_media'] = {
            'total_posts': len(self.demo_social_posts),
            'detected_events': len(events),
            'aggregated_events': len(aggregated_events),
            'event_types': event_types,
            'platform_distribution': platform_distribution,
            'avg_confidence': np.mean(confidence_scores) if confidence_scores else 0,
            'events': events,
            'aggregated_events_data': aggregated_events
        }
        
        logger.info(f"Social Media Demo completed. Detected {len(events)} events from {len(self.demo_social_posts)} posts")
        self._plot_social_media_results()
    
    def run_integrated_demo(self):
        """Demonstrate integrated predictive analytics"""
        logger.info("Running Integrated Demo...")
        
        # Ensure all components are ready
        if self.demo_graph is None:
            self.create_demo_traffic_network()
        if self.demo_sequences is None:
            self.create_demo_time_series()
        if self.demo_social_posts is None:
            self.create_demo_social_media_posts()
        
        # Get GNN predictions
        graph_data = self.engine.prepare_graph_data()
        gnn_predictions = self.engine.predict_traffic_gnn(graph_data)
        
        # Get Transformer predictions
        sequence = torch.FloatTensor(self.demo_sequences[0])
        external = torch.randn(10)
        transformer_predictions = self.engine.predict_traffic_transformer(sequence, external)
        
        # Process social media events
        social_events = self.engine.process_social_media_events(self.demo_social_posts)
        
        # Integrate social events into predictions
        integrated_predictions = self.engine.integrate_social_events(
            social_events, gnn_predictions
        )
        
        # Generate comprehensive report
        report = self.engine.generate_predictions_report(
            integrated_predictions, social_events
        )
        
        # Compare prediction methods
        comparison = {
            'gnn_avg_flow': np.mean(gnn_predictions['flow']),
            'transformer_avg_flow': np.mean(transformer_predictions['flow']),
            'integrated_avg_flow': np.mean(integrated_predictions.get('flow', gnn_predictions['flow'])),
            'social_events_count': len(social_events),
            'high_impact_events': len([e for e in social_events if e.get('total_impact', 0) > 0.7])
        }
        
        # Store results
        self.results['integrated'] = {
            'gnn_predictions': gnn_predictions,
            'transformer_predictions': transformer_predictions,
            'integrated_predictions': integrated_predictions,
            'social_events': social_events,
            'comparison': comparison,
            'report': report
        }
        
        logger.info("Integrated Demo completed")
        self._plot_integrated_results()
    
    def _plot_gnn_results(self):
        """Plot GNN results"""
        if 'gnn' not in self.results:
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Graph Neural Network Results', fontsize=16)
        
        gnn_results = self.results['gnn']
        
        # Training loss
        axes[0, 0].plot(gnn_results['training_losses'])
        axes[0, 0].set_title('Training Loss')
        axes[0, 0].set_xlabel('Epoch')
        axes[0, 0].set_ylabel('Loss')
        axes[0, 0].grid(True)
        
        # Flow predictions
        flow_pred = gnn_results['predictions']['flow']
        axes[0, 1].hist(flow_pred.flatten(), bins=30, alpha=0.7)
        axes[0, 1].set_title('Flow Predictions Distribution')
        axes[0, 1].set_xlabel('Flow Rate')
        axes[0, 1].set_ylabel('Frequency')
        
        # Speed predictions
        speed_pred = gnn_results['predictions']['speed']
        axes[1, 0].hist(speed_pred.flatten(), bins=30, alpha=0.7, color='orange')
        axes[1, 0].set_title('Speed Predictions Distribution')
        axes[1, 0].set_xlabel('Speed (km/h)')
        axes[1, 0].set_ylabel('Frequency')
        
        # Congestion predictions
        congestion_pred = gnn_results['predictions']['congestion']
        axes[1, 1].hist(congestion_pred.flatten(), bins=30, alpha=0.7, color='red')
        axes[1, 1].set_title('Congestion Predictions Distribution')
        axes[1, 1].set_xlabel('Congestion Level')
        axes[1, 1].set_ylabel('Frequency')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'gnn_results.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_transformer_results(self):
        """Plot Transformer results"""
        if 'transformer' not in self.results:
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Transformer Model Results', fontsize=16)
        
        transformer_results = self.results['transformer']
        
        # Training loss
        axes[0, 0].plot(transformer_results['training_losses'])
        axes[0, 0].set_title('Training Loss')
        axes[0, 0].set_xlabel('Epoch')
        axes[0, 0].set_ylabel('Loss')
        axes[0, 0].grid(True)
        
        # Predictions vs Targets
        time_steps = range(len(transformer_results['targets']))
        axes[0, 1].plot(time_steps, transformer_results['targets'], label='Actual', linewidth=2)
        axes[0, 1].plot(time_steps, transformer_results['predictions']['flow'], label='Predicted', linewidth=2)
        axes[0, 1].set_title('Flow Predictions vs Actual')
        axes[0, 1].set_xlabel('Time Step')
        axes[0, 1].set_ylabel('Flow Rate')
        axes[0, 1].legend()
        axes[0, 1].grid(True)
        
        # Speed predictions
        axes[1, 0].plot(transformer_results['predictions']['speed'], label='Speed', linewidth=2)
        axes[1, 0].set_title('Speed Predictions')
        axes[1, 0].set_xlabel('Time Step')
        axes[1, 0].set_ylabel('Speed (km/h)')
        axes[1, 0].grid(True)
        
        # Demand predictions
        axes[1, 1].plot(transformer_results['predictions']['demand'], label='Demand', linewidth=2, color='orange')
        axes[1, 1].set_title('Demand Predictions')
        axes[1, 1].set_xlabel('Time Step')
        axes[1, 1].set_ylabel('Demand')
        axes[1, 1].grid(True)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'transformer_results.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_social_media_results(self):
        """Plot social media results"""
        if 'social_media' not in self.results:
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Social Media Analysis Results', fontsize=16)
        
        sm_results = self.results['social_media']
        
        # Event types
        if sm_results['event_types']:
            event_types = list(sm_results['event_types'].keys())
            event_counts = list(sm_results['event_types'].values())
            axes[0, 0].bar(event_types, event_counts)
            axes[0, 0].set_title('Detected Event Types')
            axes[0, 0].set_ylabel('Count')
            axes[0, 0].tick_params(axis='x', rotation=45)
        
        # Platform distribution
        if sm_results['platform_distribution']:
            platforms = list(sm_results['platform_distribution'].keys())
            platform_counts = list(sm_results['platform_distribution'].values())
            axes[0, 1].pie(platform_counts, labels=platforms, autopct='%1.1f%%')
            axes[0, 1].set_title('Posts by Platform')
        
        # Confidence scores
        events = sm_results['events']
        if events:
            confidences = [e.confidence for e in events]
            axes[1, 0].hist(confidences, bins=20, alpha=0.7)
            axes[1, 0].set_title('Confidence Score Distribution')
            axes[1, 0].set_xlabel('Confidence')
            axes[1, 0].set_ylabel('Frequency')
        
        # Impact scores
        if events:
            impact_scores = [e.impact_score for e in events]
            axes[1, 1].hist(impact_scores, bins=20, alpha=0.7, color='orange')
            axes[1, 1].set_title('Impact Score Distribution')
            axes[1, 1].set_xlabel('Impact Score')
            axes[1, 1].set_ylabel('Frequency')
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'social_media_results.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def _plot_integrated_results(self):
        """Plot integrated results"""
        if 'integrated' not in self.results:
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Integrated Predictive Analytics Results', fontsize=16)
        
        integrated_results = self.results['integrated']
        comparison = integrated_results['comparison']
        
        # Model comparison
        models = ['GNN', 'Transformer', 'Integrated']
        avg_flows = [
            comparison['gnn_avg_flow'],
            comparison['transformer_avg_flow'],
            comparison['integrated_avg_flow']
        ]
        axes[0, 0].bar(models, avg_flows, color=['blue', 'green', 'red'])
        axes[0, 0].set_title('Average Flow Predictions by Model')
        axes[0, 0].set_ylabel('Average Flow')
        
        # Social events impact
        event_counts = [comparison['social_events_count'], comparison['high_impact_events']]
        event_labels = ['Total Events', 'High Impact Events']
        axes[0, 1].bar(event_labels, event_counts, color=['orange', 'red'])
        axes[0, 1].set_title('Social Media Events')
        axes[0, 1].set_ylabel('Count')
        
        # GNN vs Integrated predictions
        gnn_flow = integrated_results['gnn_predictions']['flow'].flatten()
        integrated_flow = integrated_results['integrated_predictions'].get('flow', gnn_flow).flatten()
        
        axes[1, 0].scatter(gnn_flow[:100], integrated_flow[:100], alpha=0.6)
        axes[1, 0].plot([min(gnn_flow), max(gnn_flow)], [min(gnn_flow), max(gnn_flow)], 'r--')
        axes[1, 0].set_title('GNN vs Integrated Predictions')
        axes[1, 0].set_xlabel('GNN Flow')
        axes[1, 0].set_ylabel('Integrated Flow')
        axes[1, 0].grid(True)
        
        # Timeline of social events
        events = integrated_results['social_events']
        if events:
            event_times = [e.timestamp.hour for e in events]
            event_impacts = [e.impact_score for e in events]
            axes[1, 1].scatter(event_times, event_impacts, alpha=0.7)
            axes[1, 1].set_title('Social Events Timeline')
            axes[1, 1].set_xlabel('Hour of Day')
            axes[1, 1].set_ylabel('Impact Score')
            axes[1, 1].grid(True)
        
        plt.tight_layout()
        plt.savefig(self.output_dir / 'integrated_results.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def save_results(self):
        """Save all results to files"""
        # Save JSON results
        json_path = self.output_dir / "predictive_demo_results.json"
        with open(json_path, 'w') as f:
            # Convert numpy arrays to lists for JSON serialization
            json_results = self._convert_numpy_to_lists(self.results)
            json.dump(json_results, f, indent=2, default=str)
        
        # Generate summary report
        report = self._generate_summary_report()
        report_path = self.output_dir / "demo_report.md"
        with open(report_path, 'w') as f:
            f.write(report)
        
        logger.info(f"Results saved to {self.output_dir}")
    
    def _convert_numpy_to_lists(self, obj):
        """Convert numpy arrays to lists for JSON serialization"""
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: self._convert_numpy_to_lists(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_numpy_to_lists(item) for item in obj]
        else:
            return obj
    
    def _generate_summary_report(self) -> str:
        """Generate comprehensive summary report"""
        report = []
        report.append("# Predictive Analytics Demo Report")
        report.append("=" * 50)
        
        # Demo overview
        report.append("\n## Demo Overview")
        report.append(f"- Traffic Network Nodes: {len(self.demo_graph.nodes) if self.demo_graph else 0}")
        report.append(f"- Traffic Network Edges: {len(self.demo_graph.edges) if self.demo_graph else 0}")
        report.append(f"- Time Series Sequences: {len(self.demo_sequences) if self.demo_sequences is not None else 0}")
        report.append(f"- Social Media Posts: {len(self.demo_social_posts) if self.demo_social_posts else 0}")
        
        # GNN results
        if 'gnn' in self.results:
            report.append("\n## Graph Neural Network Results")
            gnn = self.results['gnn']
            report.append(f"- Final Training Loss: {gnn['final_loss']:.4f}")
            report.append(f"- Number of Nodes: {gnn['num_nodes']}")
            report.append(f"- Number of Edges: {gnn['num_edges']}")
        
        # Transformer results
        if 'transformer' in self.results:
            report.append("\n## Transformer Model Results")
            transformer = self.results['transformer']
            report.append(f"- Final Training Loss: {transformer['final_loss']:.4f}")
            report.append(f"- Mean Absolute Error: {transformer['mae']:.2f}")
            report.append(f"- Root Mean Square Error: {transformer['rmse']:.2f}")
        
        # Social media results
        if 'social_media' in self.results:
            report.append("\n## Social Media Analysis Results")
            sm = self.results['social_media']
            report.append(f"- Total Posts Processed: {sm['total_posts']}")
            report.append(f"- Events Detected: {sm['detected_events']}")
            report.append(f"- Average Confidence: {sm['avg_confidence']:.2f}")
            report.append(f"- Event Types: {list(sm['event_types'].keys())}")
        
        # Integrated results
        if 'integrated' in self.results:
            report.append("\n## Integrated Analytics Results")
            integrated = self.results['integrated']
            comp = integrated['comparison']
            report.append(f"- GNN Average Flow: {comp['gnn_avg_flow']:.2f}")
            report.append(f"- Transformer Average Flow: {comp['transformer_avg_flow']:.2f}")
            report.append(f"- Integrated Average Flow: {comp['integrated_avg_flow']:.2f}")
            report.append(f"- Social Events Processed: {comp['social_events_count']}")
            report.append(f"- High Impact Events: {comp['high_impact_events']}")
        
        # Recommendations
        report.append("\n## Recommendations")
        report.append("1. Deploy GNN for city-wide traffic prediction")
        report.append("2. Use Transformer for long-term forecasting")
        report.append("3. Integrate social media for real-time event detection")
        report.append("4. Combine multiple models for robust predictions")
        report.append("5. Implement continuous learning from new data")
        
        return "\n".join(report)
    
    def run_all_demos(self):
        """Run all demonstration modules"""
        logger.info("🚀 Starting Predictive Analytics Comprehensive Demo")
        
        # Create demo data
        self.create_demo_traffic_network()
        self.create_demo_time_series()
        self.create_demo_social_media_posts()
        
        # Run individual demos
        self.run_gnn_demo()
        self.run_transformer_demo()
        self.run_social_media_demo()
        self.run_integrated_demo()
        
        # Save results
        self.save_results()
        
        # Print summary
        self._print_summary()
    
    def _print_summary(self):
        """Print demo summary"""
        print("\n" + "="*60)
        print("🎯 PREDICTIVE ANALYTICS DEMO SUMMARY")
        print("="*60)
        
        print(f"🌐 Traffic Network: {len(self.demo_graph.nodes)} nodes, {len(self.demo_graph.edges)} edges")
        print(f"📊 Time Series: {len(self.demo_sequences)} sequences")
        print(f"📱 Social Media: {len(self.demo_social_posts)} posts")
        
        print("\n🤖 Model Performance:")
        if 'gnn' in self.results:
            print(f"  • GNN Final Loss: {self.results['gnn']['final_loss']:.4f}")
        if 'transformer' in self.results:
            print(f"  • Transformer MAE: {self.results['transformer']['mae']:.2f}")
        if 'social_media' in self.results:
            print(f"  • Events Detected: {self.results['social_media']['detected_events']}")
        
        print("\n📈 Key Insights:")
        if 'integrated' in self.results:
            comp = self.results['integrated']['comparison']
            improvement = (comp['integrated_avg_flow'] - comp['gnn_avg_flow']) / comp['gnn_avg_flow'] * 100
            print(f"  • Integration improvement: {improvement:.1f}%")
        
        print(f"\n💾 Results saved to: {self.output_dir}")
        print("🎉 Predictive Analytics Demo completed successfully!")
        print("="*60)


def main():
    """Main demonstration function"""
    parser = argparse.ArgumentParser(description='Predictive Analytics Demo')
    parser.add_argument('--output-dir', default='predictive_demo_output', 
                       help='Output directory for results')
    parser.add_argument('--demo', choices=['all', 'gnn', 'transformer', 'social', 'integrated'],
                       default='all', help='Specific demo to run')
    
    args = parser.parse_args()
    
    # Initialize demo
    demo = PredictiveAnalyticsDemo(args.output_dir)
    
    # Run specified demo
    if args.demo == 'all':
        demo.run_all_demos()
    elif args.demo == 'gnn':
        demo.create_demo_traffic_network()
        demo.run_gnn_demo()
    elif args.demo == 'transformer':
        demo.create_demo_time_series()
        demo.run_transformer_demo()
    elif args.demo == 'social':
        demo.create_demo_social_media_posts()
        demo.run_social_media_demo()
    elif args.demo == 'integrated':
        demo.run_all_demos()  # Integrated needs all components
    
    # Save results
    demo.save_results()


if __name__ == "__main__":
    main()