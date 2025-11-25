#!/bin/bash
# Backup Script

BACKUP_DIR="/backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# Backup database
echo "Backing up database..."
docker-compose exec postgres pg_dump -U postgres traffic_db > $BACKUP_DIR/database.sql

# Backup models
echo "Backing up models..."
cp -r ./models $BACKUP_DIR/

# Backup configuration
echo "Backing up configuration..."
cp -r ./config $BACKUP_DIR/

echo "Backup completed: $BACKUP_DIR"
