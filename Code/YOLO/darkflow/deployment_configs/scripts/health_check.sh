#!/bin/bash
# Health Check Script

services=("traffic-controller" "vehicle-detection" "streaming-service" "analytics-service" "environmental-service")

for service in "${services[@]}"; do
    echo "Checking $service..."
    
    if docker-compose ps $service | grep -q "Up"; then
        echo "OK $service is running"
    else
        echo "ERROR $service is not running"
        exit 1
    fi
done

echo "All services are healthy!"
