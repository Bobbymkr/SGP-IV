import cv2
import os
import random
import numpy as np

# Mock vehicle detection since we don't have actual YOLO weights
# In a real scenario, you would load a pre-trained model here

def detectVehicles(filename):
    """
    Mock vehicle detection function that simulates YOLO detection
    In a real implementation, this would use a trained YOLO model
    """
    global inputPath, outputPath
    
    # Load image
    img = cv2.imread(inputPath + filename, cv2.IMREAD_COLOR)
    if img is None:
        print(f"Could not load image: {filename}")
        return
    
    height, width = img.shape[:2]
    
    # Mock detection results - simulate finding vehicles
    # In real implementation, this would come from YOLO model
    mock_detections = []
    
    # Generate some random mock detections
    num_detections = random.randint(1, 8)  # Random number of vehicles
    vehicle_types = ["car", "bus", "bike", "truck", "rickshaw"]
    
    for i in range(num_detections):
        # Random bounding box
        x1 = random.randint(0, width // 2)
        y1 = random.randint(0, height // 2)
        x2 = x1 + random.randint(50, min(200, width - x1))
        y2 = y1 + random.randint(30, min(150, height - y1))
        
        # Random vehicle type
        vehicle_type = random.choice(vehicle_types)
        
        mock_detections.append({
            'label': vehicle_type,
            'topleft': {'x': x1, 'y': y1},
            'bottomright': {'x': x2, 'y': y2},
            'confidence': random.uniform(0.3, 0.9)
        })
    
    # Draw bounding boxes and labels
    for detection in mock_detections:
        label = detection['label']
        confidence = detection['confidence']
        top_left = (detection['topleft']['x'], detection['topleft']['y'])
        bottom_right = (detection['bottomright']['x'], detection['bottomright']['y'])
        
        # Draw green bounding box
        img = cv2.rectangle(img, top_left, bottom_right, (0, 255, 0), 3)
        
        # Draw label with confidence
        label_text = f"{label} ({confidence:.2f})"
        img = cv2.putText(img, label_text, top_left, cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 0, 0), 1)
    
    # Save output image
    outputFilename = outputPath + "output_" + filename
    cv2.imwrite(outputFilename, img)
    
    # Print detection summary
    vehicle_counts = {}
    for detection in mock_detections:
        vehicle_type = detection['label']
        vehicle_counts[vehicle_type] = vehicle_counts.get(vehicle_type, 0) + 1
    
    print(f'Processed {filename}:')
    for vehicle_type, count in vehicle_counts.items():
        print(f'  {vehicle_type}: {count}')
    print(f'Output image stored at: {outputFilename}')
    print()

# Setup paths
inputPath = os.getcwd() + "/test_images/"
outputPath = os.getcwd() + "/output_images/"

# Process all images in test_images directory
if __name__ == "__main__":
    print("Modern Vehicle Detection System")
    print("==============================")
    print("Note: Using mock detection for demonstration (real YOLO weights not available)")
    print()
    
    # Check if directories exist
    if not os.path.exists(inputPath):
        print(f"Error: Input directory not found: {inputPath}")
        exit(1)
    
    if not os.path.exists(outputPath):
        os.makedirs(outputPath)
        print(f"Created output directory: {outputPath}")
    
    # Process all image files
    processed_count = 0
    for filename in os.listdir(inputPath):
        if filename.lower().endswith((".png", ".jpg", ".jpeg")):
            detectVehicles(filename)
            processed_count += 1
    
    if processed_count == 0:
        print("No image files found in test_images directory")
    else:
        print(f"Processing complete! {processed_count} images processed.")
        print("Check the output_images directory for results.")
