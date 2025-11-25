#!/bin/bash

# Production Deployment Script
# =========================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
PROJECT_NAME="adaptive-traffic-signal"
DOCKER_REGISTRY="localhost:5000"
ENVIRONMENT="production"
BACKUP_RETENTION_DAYS=30

echo -e "${BLUE}Starting production deployment...${NC}"

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check available disk space
    AVAILABLE_SPACE=$(df . | tail -1 | awk '{print $4}')
    if [ "$AVAILABLE_SPACE" -lt 5242880 ]; then  # 5GB in KB
        print_warning "Low disk space detected. Available: ${AVAILABLE_SPACE}KB"
    fi
    
    print_status "Prerequisites check completed"
}

# Build Docker images
build_images() {
    print_status "Building Docker images..."
    
    # Build main application image
    docker build -t ${PROJECT_NAME}:latest .
    
    # Tag for registry
    docker tag ${PROJECT_NAME}:latest ${DOCKER_REGISTRY}/${PROJECT_NAME}:latest
    
    print_status "Docker images built successfully"
}

# Setup infrastructure
setup_infrastructure() {
    print_status "Setting up infrastructure..."
    
    # Create necessary directories
    mkdir -p logs data models config uploads cache backups nginx/ssl nginx
    
    # Generate SSL certificates (self-signed for production)
    if [ ! -f nginx/ssl/cert.pem ]; then
        print_status "Generating SSL certificates..."
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout nginx/ssl/key.pem \
            -out nginx/ssl/cert.pem \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=traffic-signal.local"
    fi
    
    # Generate secure passwords
    if [ ! -f .env ]; then
        print_status "Generating secure passwords..."
        POSTGRES_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
        GRAFANA_PASSWORD=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
        
        cat > .env << EOF
POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
GRAFANA_PASSWORD=${GRAFANA_PASSWORD}
EOF
        chmod 600 .env
    fi
    
    print_status "Infrastructure setup completed"
}

# Deploy services
deploy_services() {
    print_status "Deploying services..."
    
    # Deploy with Docker Compose
    docker-compose -f docker-compose.yml up -d
    
    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 10
    
    # Check service health
    check_service_health() {
        local service=$1
        local max_attempts=$2
        local attempt=1
        
        while [ $attempt -le $max_attempts ]; do
            if docker-compose ps $service | grep -q "Up (healthy)"; then
                print_status "$service is healthy"
                return 0
            fi
            
            if docker-compose ps $service | grep -q "Up (unhealthy)"; then
                print_error "$service is unhealthy"
                return 1
            fi
            
            echo -e "${YELLOW}Waiting for $service to be healthy... (attempt $attempt/$max_attempts)${NC}"
            sleep 5
            attempt=$((attempt + 1))
        done
        
        print_error "$service failed to become healthy after $max_attempts attempts"
        return 1
    }
    
    # Check each service
    check_service_health "redis" 12
    check_service_health "postgres" 30
    check_service_health "traffic-signal-app" 20
    
    print_status "All services deployed and healthy"
}

# Setup monitoring
setup_monitoring() {
    print_status "Setting up monitoring..."
    
    # Create monitoring configuration
    mkdir -p monitoring/prometheus monitoring/grafana/provisioning monitoring/grafana/dashboards
    
    # Prometheus configuration
    cat > monitoring/prometheus/prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "traffic_rules.yml"

scrape_configs:
  - job_name: 'traffic-signal'
    static_configs:
      - targets: ['traffic-signal-app:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
    scrape_interval: 5s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
    scrape_interval: 5s
EOF

    # Grafana provisioning
    cat > monitoring/grafana/provisioning/datasources/prometheus.yml << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
EOF

    # Traffic alerting rules
    cat > monitoring/prometheus/traffic_rules.yml << EOF
groups:
  - name: traffic_signal_alerts
    rules:
    - alert: HighCPUUsage
      expr: cpu_usage_percent > 80
      for: 5m
      labels:
        severity: warning
        service: traffic-signal
      annotations:
        summary: "High CPU usage detected"
        description: "CPU usage is above 80% for more than 5 minutes"

    - alert: HighMemoryUsage
      expr: memory_usage_percent > 85
      for: 5m
      labels:
        severity: warning
        service: traffic-signal
      annotations:
        summary: "High memory usage detected"
        description: "Memory usage is above 85% for more than 5 minutes"

    - alert: ServiceDown
      expr: up == 0
      for: 1m
      labels:
        severity: critical
        service: traffic-signal
      annotations:
        summary: "Service is down"
        description: "Traffic signal service is not responding"

    - alert: HighLatency
      expr: latency_ms > 1000
      for: 2m
      labels:
        severity: warning
        service: traffic-signal
      annotations:
        summary: "High latency detected"
        description: "API latency is above 1000ms for more than 2 minutes"
EOF

    print_status "Monitoring setup completed"
}

# Setup backup
setup_backup() {
    print_status "Setting up backup system..."
    
    # Create backup script
    cat > scripts/backup.sh << 'EOF'
#!/bin/bash
# Automated backup script

BACKUP_DIR="/app/backups"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS}

# Create backup directory
mkdir -p \$BACKUP_DIR

# Database backup
echo "Starting database backup..."
docker exec traffic-postgres pg_dump -U trafficuser -d trafficdb | gzip > \$BACKUP_DIR/db_backup_\$(date +%Y%m%d_%H%M%S).sql.gz

# Application data backup
echo "Backing up application data..."
tar -czf \$BACKUP_DIR/app_data_\$(date +%Y%m%d_%H%M%S).tar.gz /app/data

# Clean old backups
echo "Cleaning old backups..."
find \$BACKUP_DIR -name "*.gz" -mtime +\$RETENTION_DAYS -delete

echo "Backup completed: \$(date)"
EOF

    chmod +x scripts/backup.sh
    
    # Add to crontab
    (crontab -l 2>/dev/null; echo "0 2 * * /app/scripts/backup.sh") | crontab -
    
    print_status "Backup system configured"
}

# Setup log rotation
setup_log_rotation() {
    print_status "Setting up log rotation..."
    
    cat > /etc/logrotate.d/traffic-signal << EOF
/app/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644
    postrotate
        /usr/bin/docker kill -s USR1 traffic-signal-app
        /usr/bin/docker start traffic-signal-app
    endscript
}
EOF

    print_status "Log rotation configured"
}

# Health check
health_check() {
    print_status "Performing health check..."
    
    # Check application health
    if curl -f http://localhost:8000/api/health | grep -q "healthy"; then
        print_status "Application is healthy"
    else
        print_error "Application health check failed"
        return 1
    fi
    
    # Check database connection
    if docker exec traffic-postgres pg_isready -U trafficuser -d trafficdb; then
        print_status "Database is ready"
    else
        print_error "Database is not ready"
        return 1
    fi
    
    # Check Redis connection
    if docker exec traffic-redis redis-cli ping | grep -q "PONG"; then
        print_status "Redis is ready"
    else
        print_error "Redis is not ready"
        return 1
    fi
    
    print_status "All health checks passed"
    return 0
}

# Cleanup function
cleanup() {
    print_status "Cleaning up..."
    
    # Stop and remove containers
    docker-compose down -v
    
    # Remove images
    docker rmi ${PROJECT_NAME}:latest 2>/dev/null || true
    
    # Clean up unused volumes
    docker volume prune -f
    
    print_status "Cleanup completed"
}

# Main deployment function
main() {
    case "${1:-deploy}" in
        "deploy")
            check_prerequisites
            build_images
            setup_infrastructure
            deploy_services
            setup_monitoring
            setup_backup
            setup_log_rotation
            health_check
            print_status "Deployment completed successfully!"
            ;;
        "update")
            print_status "Updating deployment..."
            docker-compose pull
            docker-compose up -d
            health_check
            ;;
        "rollback")
            print_status "Rolling back deployment..."
            # Implement rollback logic here
            ;;
        "cleanup")
            cleanup
            ;;
        "health")
            health_check
            ;;
        *)
            echo "Usage: $0 {deploy|update|rollback|cleanup|health}"
            exit 1
            ;;
    esac
}

# Trap signals for graceful shutdown
trap cleanup EXIT INT TERM

# Execute main function
main "$@"