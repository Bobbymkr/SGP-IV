#!/usr/bin/env python3
"""
Adaptive Traffic Signal Timer - Project Runner
==============================================

This script provides an easy way to run both components of the project:
1. Vehicle Detection Module (modernized version)
2. Traffic Simulation Module (with adaptive signal timing)

Usage:
    python run_project.py --demo        # Run vehicle detection then ask about simulation
    python run_project.py --detection   # Run only vehicle detection
    python run_project.py --simulation  # Run only traffic simulation
    python run_project.py --help        # Show this help message
"""

import sys
import os
import subprocess
import argparse
import time

def print_banner():
    """Print project banner"""
    print("=" * 60)
    print("    ADAPTIVE TRAFFIC SIGNAL TIMER")
    print("    Computer Vision + Traffic Simulation")
    print("=" * 60)
    print()

def print_status(message, status="INFO"):
    """Print formatted status message"""
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp}] {status}: {message}")

def run_vehicle_detection():
    """Run the vehicle detection module"""
    print_status("Starting Vehicle Detection Module...")
    print()
    print("This will process all images in test_images/ and save results to output_images/")
    print("Note: Using mock detection (real YOLO weights not available)")
    print()
    
    try:
        # Run the modern vehicle detection
        result = subprocess.run([sys.executable, "vehicle_detection_modern.py"], 
                              capture_output=False, text=True)
        
        if result.returncode == 0:
            print_status("Vehicle detection completed successfully!", "SUCCESS")
            return True
        else:
            print_status("Vehicle detection failed!", "ERROR")
            return False
            
    except Exception as e:
        print_status(f"Error running vehicle detection: {e}", "ERROR")
        return False

def run_traffic_simulation():
    """Run the traffic simulation module"""
    print_status("Starting Traffic Simulation Module...")
    print()
    print("This will open a Pygame window showing:")
    print("  - 4-way intersection with traffic lights")
    print("  - Vehicles moving with realistic physics")
    print("  - Adaptive signal timing based on traffic density")
    print("  - Real-time statistics and vehicle counts")
    print()
    print("Controls:")
    print("  - Close the window or press Ctrl+C to stop")
    print("  - Simulation runs for 300 seconds by default")
    print()
    
    input("Press Enter to start the simulation...")
    
    try:
        # Run the fixed simulation
        subprocess.run([sys.executable, "simulation.py"])
        print_status("Traffic simulation completed!", "SUCCESS")
        return True
        
    except KeyboardInterrupt:
        print_status("Simulation stopped by user", "INFO")
        return True
    except Exception as e:
        print_status(f"Error running simulation: {e}", "ERROR")
        return False

def run_demo():
    """Run the complete demo"""
    print_status("Running complete project demo...")
    print()
    
    # Run vehicle detection first
    if not run_vehicle_detection():
        return False
    
    print()
    print("=" * 40)
    print("VEHICLE DETECTION COMPLETE!")
    print("Check the output_images/ folder for results.")
    print("=" * 40)
    print()
    
    # Ask if user wants to run simulation
    while True:
        choice = input("Would you like to run the traffic simulation? (y/n): ").lower().strip()
        if choice in ['y', 'yes']:
            print()
            return run_traffic_simulation()
        elif choice in ['n', 'no']:
            print_status("Demo complete. Simulation skipped.", "INFO")
            return True
        else:
            print("Please enter 'y' or 'n'")

def show_project_info():
    """Show information about the project"""
    print("PROJECT COMPONENTS:")
    print()
    print("1. VEHICLE DETECTION MODULE")
    print("   - Processes traffic images to detect vehicles")
    print("   - Identifies: cars, buses, trucks, bikes, rickshaws")
    print("   - Outputs annotated images with bounding boxes")
    print("   - Currently using mock detection (demo purposes)")
    print()
    print("2. TRAFFIC SIMULATION MODULE")
    print("   - Pygame-based 4-way intersection simulation")
    print("   - Adaptive signal timing based on vehicle counts")
    print("   - Realistic vehicle movement and car-following")
    print("   - Real-time performance statistics")
    print()
    print("ARCHITECTURE:")
    print("   - Vehicle Detection: OpenCV + Mock YOLO detection")
    print("   - Signal Algorithm: Queue-based adaptive timing")
    print("   - Simulation: Pygame with multi-threading")
    print()

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Adaptive Traffic Signal Timer - Project Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--demo", action="store_true", 
                      help="Run complete demo (detection + simulation)")
    group.add_argument("--detection", action="store_true",
                      help="Run only vehicle detection")
    group.add_argument("--simulation", action="store_true", 
                      help="Run only traffic simulation")
    group.add_argument("--info", action="store_true",
                      help="Show project information")
    
    args = parser.parse_args()
    
    print_banner()
    
    # Check if we're in the right directory
    if not os.path.exists("simulation.py") or not os.path.exists("vehicle_detection_modern.py"):
        print_status("Error: Please run this script from the darkflow directory", "ERROR")
        print("Expected location: Code/YOLO/darkflow/")
        return 1
    
    # Check required directories
    if not os.path.exists("test_images"):
        print_status("Warning: test_images directory not found", "WARNING")
    if not os.path.exists("output_images"):
        os.makedirs("output_images")
        print_status("Created output_images directory", "INFO")
    
    # Handle command line arguments
    if args.info:
        show_project_info()
        return 0
    elif args.detection:
        return 0 if run_vehicle_detection() else 1
    elif args.simulation:
        return 0 if run_traffic_simulation() else 1
    elif args.demo:
        return 0 if run_demo() else 1
    else:
        # No arguments - show help and run demo
        print("No arguments provided. Running demo mode...")
        print("(Use --help for more options)")
        print()
        return 0 if run_demo() else 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print_status("Program interrupted by user", "INFO")
        sys.exit(0)
