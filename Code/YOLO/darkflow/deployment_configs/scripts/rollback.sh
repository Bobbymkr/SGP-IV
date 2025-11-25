#!/bin/bash
# Rollback Script

if [ -z "$PREVIOUS_VERSION" ]; then
    echo "Error: PREVIOUS_VERSION not specified"
    exit 1
fi

echo "Rolling back to version $PREVIOUS_VERSION..."

git checkout $PREVIOUS_VERSION

# Restart services with previous version
docker-compose down
docker-compose up -d

echo "Rollback completed!"
