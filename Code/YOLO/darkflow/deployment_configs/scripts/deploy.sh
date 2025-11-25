#!/bin/bash
# Adaptive Traffic System Deployment Script

set -e

echo "Starting deployment of Adaptive Traffic Signal System..."

# Check environment
if [ -z "$ENVIRONMENT" ]; then
    echo "Error: ENVIRONMENT variable not set"
    exit 1
fi

# Pull latest changes
git pull origin main

# Build and start services
echo "Building Docker images..."
docker-compose build

echo "Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 30

# Run health checks
echo "Running health checks..."
./scripts/health_check.sh

# Run database migrations
echo "Running database migrations..."
docker-compose exec traffic-controller python manage.py migrate

echo "Deployment completed successfully!"
