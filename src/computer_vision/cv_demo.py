"""
Advanced Computer Vision Demo

Comprehensive demonstration of all computer vision components:
3D Vehicle Detection, License Plate Recognition, Optical Flow, and Multi-Camera Fusion
"""

import numpy as np
import cv2
import torch
import time
import json
import logging
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
import matplotlib.pyplot as plt
from pathlib import Path

# Import our modules
from vehicle_detection_3d import Vehicle3DDetector, MultiViewDetector, create_3d_detector
from license_plate_recognition import LicensePlateRecognizer, create_plate_recognizer
from optical_flow_speed import OpticalFlowSystem, create_optical_flow_system
from multi_camera_fusion import MultiCameraFusion, create_multi_camera_fusion, CameraConfig

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class DemoConfig:
    """Configuration for computer vision demo"""
    # 3D Detection
    use_3d_detection: bool = True
    use_stereo: bool = False
    camera_matrix: List[List[float]] = None
    
    # License Plate Recognition
    use_lpr: bool = True
    lpr_method: str = 'easyocr'
    
    # Optical Flow
    use_optical_flow: bool = True
    flow_method: str = 'farneback'
    
    # Multi-Camera Fusion
    use_fusion: bool = True
    num_cameras: int = 2
    
    # General
    fps: float = 30.0
    output_dir: str = "cv_demo_output"
    save_results: bool = True


class ComputerVisionDemo:
    """Main computer vision demonstration class"""
    
    def __init__(self, config: DemoConfig):
        self.config = config
        self.output_dir = Path(config.output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize components
        self._init_components()
        
        # Performance tracking
        self.performance_stats = {
            '3d_detection': [],
            'lpr': [],
            'optical_flow': [],
            'fusion': [],
            'total': []
        }
        
        # Results storage
        self.results_history = []
        
    def _init_components(self):
        """Initialize all computer vision components"""
        logger.info("Initializing computer vision components...")
        
        # 3D Vehicle Detection
        if self.config.use_3d_detection:
            camera_matrix = np.array(self.config.camera_matrix) if self.config.camera_matrix else self._get_default_camera_matrix()
            dist_coeffs = np.zeros(5)
            
            self.detector_3d = Vehicle3DDetector(
                camera_matrix=camera_matrix,
                dist_coeffs=dist_coeffs,
                use_stereo=self.config.use_stereo
            )
            logger.info("✓ 3D Vehicle Detector initialized")
        
        # License Plate Recognition
        if self.config.use_lpr:
            self.plate_recognizer = LicensePlateRecognizer(
                recognition_method=self.config.lpr_method
            )
            logger.info("✓ License Plate Recognizer initialized")
        
        # Optical Flow
        if self.config.use_optical_flow:
            self.optical_flow = OpticalFlowSystem(
                method=self.config.flow_method,
                camera_matrix=np.array(self.config.camera_matrix) if self.config.camera_matrix else None,
                fps=self.config.fps
            )
            logger.info("✓ Optical Flow System initialized")
        
        # Multi-Camera Fusion
        if self.config.use_fusion:
            self.fusion_system = self._create_fusion_system()
            logger.info("✓ Multi-Camera Fusion System initialized")
        
        logger.info("All components initialized successfully!")
    
    def _get_default_camera_matrix(self) -> np.ndarray:
        """Get default camera matrix"""
        return np.array([
            [1000, 0, 320],
            [0, 1000, 240],
            [0, 0, 1]
        ], dtype=np.float32)
    
    def _create_fusion_system(self) -> MultiCameraFusion:
        """Create multi-camera fusion system"""
        # Create sample camera configurations
        camera_configs = []
        
        for i in range(self.config.num_cameras):
            config = {
                'id': i,
                'name': f'Camera_{i}',
                'position': [i * 10, 0, 5],  # 10 meters apart
                'rotation': np.eye(3).tolist(),
                'camera_matrix': self._get_default_camera_matrix().tolist(),
                'dist_coeffs': [0, 0, 0, 0, 0],
                'fov': 60,
                'resolution': [640, 480],
                'fps': self.config.fps,
                'overlap_regions': [i-1, i+1] if 0 < i < self.config.num_cameras-1 else []
            }
            camera_configs.append(config)
        
        return create_multi_camera_fusion(camera_configs)
    
    def process_single_image(self, image_path: str) -> Dict[str, Any]:
        """Process a single image with all components"""
        logger.info(f"Processing single image: {image_path}")
        
        # Load image
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")
        
        start_time = time.time()
        results = {'image_path': image_path, 'image_shape': image.shape}
        
        # 3D Vehicle Detection
        if self.config.use_3d_detection:
            det_start = time.time()
            detections_3d = self.detector_3d.detect_3d_vehicles(image)
            det_time = time.time() - det_start
            
            results['3d_detections'] = detections_3d
            results['3d_detection_time'] = det_time
            self.performance_stats['3d_detection'].append(det_time)
            
            # Visualize 3D detections
            vis_3d = self.detector_3d.visualize_detections(image, detections_3d)
            results['visualization_3d'] = vis_3d
        
        # License Plate Recognition
        if self.config.use_lpr:
            lpr_start = time.time()
            license_plates = self.plate_recognizer.process_image(image)
            lpr_time = time.time() - lpr_start
            
            results['license_plates'] = license_plates
            results['lpr_time'] = lpr_time
            self.performance_stats['lpr'].append(lpr_time)
            
            # Visualize LPR results
            vis_lpr = self.plate_recognizer.visualize_results(image, license_plates)
            results['visualization_lpr'] = vis_lpr
        
        # Optical Flow (requires previous frame)
        if self.config.use_optical_flow and hasattr(self, 'prev_frame'):
            flow_start = time.time()
            flow_results = self.optical_flow.process_frame(image, self.prev_frame)
            flow_time = time.time() - flow_start
            
            results['optical_flow'] = flow_results
            results['flow_time'] = flow_time
            self.performance_stats['optical_flow'].append(flow_time)
            
            # Visualize optical flow
            vis_flow = self.optical_flow.visualize_flow(image, flow_results, 'hsv')
            results['visualization_flow'] = vis_flow
        
        # Store current frame for next iteration
        self.prev_frame = image.copy()
        
        total_time = time.time() - start_time
        results['total_time'] = total_time
        self.performance_stats['total'].append(total_time)
        
        return results
    
    def process_video_sequence(self, video_path: str, max_frames: int = 100) -> List[Dict[str, Any]]:
        """Process video sequence with all components"""
        logger.info(f"Processing video sequence: {video_path}")
        
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        frame_count = 0
        results_sequence = []
        
        while frame_count < max_frames:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Process frame
            frame_results = self.process_frame(frame, frame_count)
            results_sequence.append(frame_results)
            
            frame_count += 1
            
            if frame_count % 10 == 0:
                logger.info(f"Processed {frame_count} frames")
        
        cap.release()
        logger.info(f"Video processing complete. Processed {frame_count} frames.")
        
        return results_sequence
    
    def process_frame(self, frame: np.ndarray, frame_id: int) -> Dict[str, Any]:
        """Process a single frame in video sequence"""
        start_time = time.time()
        results = {'frame_id': frame_id, 'timestamp': time.time()}
        
        # 3D Detection
        if self.config.use_3d_detection:
            detections_3d = self.detector_3d.detect_3d_vehicles(frame)
            results['3d_detections'] = detections_3d
        
        # License Plate Recognition
        if self.config.use_lpr:
            license_plates = self.plate_recognizer.process_image(frame)
            results['license_plates'] = license_plates
        
        # Optical Flow
        if self.config.use_optical_flow and hasattr(self, 'prev_frame'):
            flow_results = self.optical_flow.process_frame(frame, self.prev_frame)
            results['optical_flow'] = flow_results
        
        # Multi-Camera Fusion (simulated)
        if self.config.use_fusion:
            fusion_results = self._simulate_multi_camera_fusion(frame)
            results['fusion'] = fusion_results
        
        self.prev_frame = frame.copy()
        results['processing_time'] = time.time() - start_time
        
        return results
    
    def _simulate_multi_camera_fusion(self, frame: np.ndarray) -> Dict[str, Any]:
        """Simulate multi-camera fusion with synthetic data"""
        # Simulate detections from multiple cameras
        detections_by_camera = {}
        
        for i in range(self.config.num_cameras):
            # Simulate slight variations in the frame
            noise = np.random.normal(0, 5, frame.shape).astype(np.uint8)
            noisy_frame = np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)
            
            # Detect vehicles
            detections = self.detector_3d.detect_3d_vehicles(noisy_frame)
            
            # Convert to simple format
            simple_detections = []
            for det in detections:
                simple_detections.append({
                    'bbox': det.bbox_2d,
                    'confidence': det.confidence,
                    'class_name': det.class_name,
                    'depth': det.depth
                })
            
            detections_by_camera[i] = simple_detections
        
        # Fuse detections
        fused_detections = self.fusion_system.fuse_detections(detections_by_camera)
        
        # Create bird's eye view
        bev_image = self.fusion_system.create_birds_eye_view(fused_detections)
        
        return {
            'fused_detections': fused_detections,
            'bev_image': bev_image,
            'detections_by_camera': detections_by_camera
        }
    
    def run_comprehensive_demo(self, image_paths: List[str]) -> Dict[str, Any]:
        """Run comprehensive demo on multiple images"""
        logger.info("Starting comprehensive computer vision demo...")
        
        demo_results = {
            'config': self.config,
            'images_processed': 0,
            'total_detections': 0,
            'total_license_plates': 0,
            'performance_stats': {},
            'results': []
        }
        
        for image_path in image_paths:
            try:
                results = self.process_single_image(image_path)
                demo_results['results'].append(results)
                demo_results['images_processed'] += 1
                
                if '3d_detections' in results:
                    demo_results['total_detections'] += len(results['3d_detections'])
                
                if 'license_plates' in results:
                    demo_results['total_license_plates'] += len(results['license_plates'])
                
            except Exception as e:
                logger.error(f"Error processing {image_path}: {e}")
        
        # Calculate performance statistics
        for component, times in self.performance_stats.items():
            if times:
                demo_results['performance_stats'][component] = {
                    'mean': np.mean(times),
                    'std': np.std(times),
                    'min': np.min(times),
                    'max': np.max(times)
                }
        
        # Save results
        if self.config.save_results:
            self._save_demo_results(demo_results)
        
        logger.info("Comprehensive demo completed!")
        return demo_results
    
    def _save_demo_results(self, results: Dict[str, Any]):
        """Save demo results to files"""
        # Save JSON results
        json_path = self.output_dir / "demo_results.json"
        with open(json_path, 'w') as f:
            # Convert numpy arrays to lists for JSON serialization
            json_results = self._convert_numpy_to_lists(results)
            json.dump(json_results, f, indent=2)
        
        # Save visualizations
        for i, result in enumerate(results['results']):
            if 'visualization_3d' in result:
                vis_path = self.output_dir / f"3d_detection_{i}.jpg"
                cv2.imwrite(str(vis_path), result['visualization_3d'])
            
            if 'visualization_lpr' in result:
                vis_path = self.output_dir / f"lpr_{i}.jpg"
                cv2.imwrite(str(vis_path), result['visualization_lpr'])
            
            if 'visualization_flow' in result:
                vis_path = self.output_dir / f"optical_flow_{i}.jpg"
                cv2.imwrite(str(vis_path), result['visualization_flow'])
        
        # Save performance plots
        self._save_performance_plots()
        
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
    
    def _save_performance_plots(self):
        """Save performance analysis plots"""
        if not any(self.performance_stats.values()):
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Computer Vision Performance Analysis', fontsize=16)
        
        # Plot 1: Processing times by component
        ax1 = axes[0, 0]
        components = []
        times = []
        for component, time_list in self.performance_stats.items():
            if time_list:
                components.append(component.replace('_', ' ').title())
                times.append(np.mean(time_list))
        
        if components:
            ax1.bar(components, times)
            ax1.set_title('Average Processing Time by Component')
            ax1.set_ylabel('Time (seconds)')
            ax1.tick_params(axis='x', rotation=45)
        
        # Plot 2: Detection counts
        ax2 = axes[0, 1]
        detection_counts = []
        frame_numbers = []
        
        for i, result in enumerate(self.results_history):
            if '3d_detections' in result:
                detection_counts.append(len(result['3d_detections']))
                frame_numbers.append(i)
        
        if detection_counts:
            ax2.plot(frame_numbers, detection_counts, 'b-o')
            ax2.set_title('Vehicle Detection Count Over Time')
            ax2.set_xlabel('Frame Number')
            ax2.set_ylabel('Detection Count')
        
        # Plot 3: License plate recognition confidence
        ax3 = axes[1, 0]
        confidences = []
        
        for result in self.results_history:
            if 'license_plates' in result:
                for plate in result['license_plates']:
                    confidences.append(plate.confidence_text)
        
        if confidences:
            ax3.hist(confidences, bins=20, alpha=0.7)
            ax3.set_title('License Plate Recognition Confidence Distribution')
            ax3.set_xlabel('Confidence')
            ax3.set_ylabel('Frequency')
        
        # Plot 4: Optical flow magnitude
        ax4 = axes[1, 1]
        flow_magnitudes = []
        
        for result in self.results_history:
            if 'optical_flow' in result and 'flow_metrics' in result['optical_flow']:
                flow_magnitudes.append(result['optical_flow']['flow_metrics']['avg_magnitude'])
        
        if flow_magnitudes:
            ax4.plot(flow_magnitudes, 'r-')
            ax4.set_title('Average Optical Flow Magnitude Over Time')
            ax4.set_xlabel('Frame Number')
            ax4.set_ylabel('Flow Magnitude')
        
        plt.tight_layout()
        plot_path = self.output_dir / "performance_analysis.png"
        plt.savefig(plot_path, dpi=300, bbox_inches='tight')
        plt.close()
    
    def generate_report(self) -> str:
        """Generate comprehensive performance report"""
        report = []
        report.append("# Computer Vision Demo Report")
        report.append("=" * 50)
        
        # Configuration
        report.append("\n## Configuration")
        for key, value in self.config.__dict__.items():
            report.append(f"- {key}: {value}")
        
        # Performance Statistics
        report.append("\n## Performance Statistics")
        for component, times in self.performance_stats.items():
            if times:
                report.append(f"\n### {component.replace('_', ' ').title()}")
                report.append(f"- Mean: {np.mean(times):.4f}s")
                report.append(f"- Std: {np.std(times):.4f}s")
                report.append(f"- Min: {np.min(times):.4f}s")
                report.append(f"- Max: {np.max(times):.4f}s")
                report.append(f"- Total frames: {len(times)}")
        
        # Detection Summary
        report.append("\n## Detection Summary")
        total_3d_detections = sum(len(r.get('3d_detections', [])) for r in self.results_history)
        total_license_plates = sum(len(r.get('license_plates', [])) for r in self.results_history)
        
        report.append(f"- Total 3D Detections: {total_3d_detections}")
        report.append(f"- Total License Plates: {total_license_plates}")
        report.append(f"- Frames Processed: {len(self.results_history)}")
        
        # Recommendations
        report.append("\n## Recommendations")
        
        avg_total_time = np.mean(self.performance_stats['total']) if self.performance_stats['total'] else 0
        if avg_total_time > 0.1:
            report.append("- Consider optimizing for real-time performance (>100ms per frame)")
        
        if self.performance_stats['3d_detection']:
            avg_3d_time = np.mean(self.performance_stats['3d_detection'])
            if avg_3d_time > 0.05:
                report.append("- 3D detection is time-consuming, consider model optimization")
        
        if self.performance_stats['lpr']:
            avg_lpr_time = np.mean(self.performance_stats['lpr'])
            if avg_lpr_time > 0.02:
                report.append("- License plate recognition could be optimized")
        
        return "\n".join(report)


def create_demo_config() -> DemoConfig:
    """Create default demo configuration"""
    return DemoConfig(
        use_3d_detection=True,
        use_stereo=False,
        camera_matrix=[
            [1000, 0, 320],
            [0, 1000, 240],
            [0, 0, 1]
        ],
        use_lpr=True,
        lpr_method='easyocr',
        use_optical_flow=True,
        flow_method='farneback',
        use_fusion=True,
        num_cameras=2,
        fps=30.0,
        output_dir="cv_demo_output",
        save_results=True
    )


def main():
    """Main demonstration function"""
    logger.info("🚀 Starting Advanced Computer Vision Demo")
    
    # Create configuration
    config = create_demo_config()
    
    # Initialize demo
    demo = ComputerVisionDemo(config)
    
    # Get sample images (you can modify this to use your own images)
    sample_images = [
        "Code/YOLO/darkflow/images/intersection.jpg",
        "Code/YOLO/darkflow/test_images/1.jpg",
        "Code/YOLO/darkflow/test_images/2.jpg",
        "Code/YOLO/darkflow/test_images/3.jpg"
    ]
    
    # Filter existing images
    existing_images = []
    for img_path in sample_images:
        if Path(img_path).exists():
            existing_images.append(img_path)
        else:
            logger.warning(f"Image not found: {img_path}")
    
    if not existing_images:
        logger.error("No sample images found. Please check the image paths.")
        return
    
    # Run comprehensive demo
    results = demo.run_comprehensive_demo(existing_images)
    
    # Generate and save report
    report = demo.generate_report()
    report_path = Path(config.output_dir) / "demo_report.md"
    with open(report_path, 'w') as f:
        f.write(report)
    
    # Print summary
    print("\n" + "="*60)
    print("🎯 COMPUTER VISION DEMO SUMMARY")
    print("="*60)
    print(f"📸 Images Processed: {results['images_processed']}")
    print(f"🚗 Total 3D Detections: {results['total_detections']}")
    print(f"🪪 Total License Plates: {results['total_license_plates']}")
    print(f"💾 Results saved to: {config.output_dir}")
    
    # Performance summary
    if results['performance_stats']:
        print("\n⚡ PERFORMANCE SUMMARY:")
        for component, stats in results['performance_stats'].items():
            if stats:
                print(f"  {component.replace('_', ' ').title()}: {stats['mean']:.4f}s ± {stats['std']:.4f}s")
    
    print("\n📊 Detailed report saved to: demo_report.md")
    print("🎉 Demo completed successfully!")
    print("="*60)


if __name__ == "__main__":
    main()