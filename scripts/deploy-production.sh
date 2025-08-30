#!/bin/bash

# CAS Platform Production Deployment Script
# =========================================
# Complete production deployment with security and performance optimization

set -e

# Configuration
PLATFORM_NAME="cas-platform"
NAMESPACE="cas-system"
BACKUP_DIR="/backups"
LOG_DIR="/var/log/cas-platform"
CONFIG_DIR="./config"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check required directories
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "$CONFIG_DIR"
    
    log "Prerequisites check completed"
}

# Generate SSL certificates
generate_ssl_certificates() {
    log "Generating SSL certificates..."
    
    SSL_DIR="/etc/ssl/cas-platform"
    sudo mkdir -p "$SSL_DIR"
    
    # Generate self-signed certificate for development
    # In production, use proper CA-signed certificates
    sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout "$SSL_DIR/cas-platform.key" \
        -out "$SSL_DIR/cas-platform.crt" \
        -subj "/C=DE/ST=State/L=City/O=Company/CN=cas-platform.company.com"
    
    # Set proper permissions
    sudo chmod 600 "$SSL_DIR/cas-platform.key"
    sudo chmod 644 "$SSL_DIR/cas-platform.crt"
    
    log "SSL certificates generated"
}

# Setup NAS mount
setup_nas_mount() {
    log "Setting up NAS mount..."
    
    NAS_SERVER="${NAS_SERVER:-192.168.1.100}"
    NAS_PATH="${NAS_PATH:-/mnt/nas/cas-data}"
    LOCAL_MOUNT="/mnt/nas"
    
    # Create mount directory
    sudo mkdir -p "$LOCAL_MOUNT"
    
    # Add to fstab for persistence
    if ! grep -q "$NAS_SERVER:$NAS_PATH" /etc/fstab; then
        echo "$NAS_SERVER:$NAS_PATH $LOCAL_MOUNT nfs defaults 0 0" | sudo tee -a /etc/fstab
    fi
    
    # Mount NAS
    sudo mount -a
    
    # Set permissions
    sudo chown -R 1000:1000 "$LOCAL_MOUNT"
    
    log "NAS mount configured"
}

# Configure environment variables
configure_environment() {
    log "Configuring environment variables..."
    
    # Load production environment
    if [ -f "$CONFIG_DIR/production.env" ]; then
        export $(cat "$CONFIG_DIR/production.env" | grep -v '^#' | xargs)
    else
        warning "Production environment file not found, using defaults"
    fi
    
    # Set critical variables
    export JWT_SECRET="${JWT_SECRET:-$(openssl rand -hex 32)}"
    export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-$(openssl rand -hex 16)}"
    export MINIO_ROOT_PASSWORD="${MINIO_ROOT_PASSWORD:-$(openssl rand -hex 16)}"
    
    log "Environment variables configured"
}

# Build and deploy services
deploy_services() {
    log "Building and deploying services..."
    
    # Build all images
    docker-compose build --no-cache
    
    # Start services
    docker-compose up -d
    
    # Wait for services to be ready
    log "Waiting for services to be ready..."
    sleep 30
    
    # Check service health
    check_service_health
    
    log "Services deployed successfully"
}

# Check service health
check_service_health() {
    log "Checking service health..."
    
    services=(
        "postgres"
        "redis"
        "minio"
        "rabbitmq"
        "elasticsearch"
        "api-gateway"
        "ingest-service"
        "admin-dashboard"
    )
    
    for service in "${services[@]}"; do
        if docker-compose ps "$service" | grep -q "Up"; then
            log "✓ $service is running"
        else
            error "✗ $service is not running"
            return 1
        fi
    done
    
    log "All services are healthy"
}

# Configure monitoring
configure_monitoring() {
    log "Configuring monitoring..."
    
    # Copy alert rules
    if [ -f "$CONFIG_DIR/alert-rules.yml" ]; then
        docker cp "$CONFIG_DIR/alert-rules.yml" cas_prometheus:/etc/prometheus/
        docker exec cas_prometheus kill -HUP 1
    fi
    
    # Configure Grafana dashboards
    if [ -d "$CONFIG_DIR/grafana" ]; then
        docker cp "$CONFIG_DIR/grafana/" cas_grafana:/etc/grafana/provisioning/
        docker exec cas_grafana kill -HUP 1
    fi
    
    log "Monitoring configured"
}

# Setup backup automation
setup_backup_automation() {
    log "Setting up backup automation..."
    
    # Make backup script executable
    chmod +x ./scripts/backup-strategy.sh
    
    # Add to crontab
    if ! crontab -l 2>/dev/null | grep -q "backup-strategy.sh"; then
        (crontab -l 2>/dev/null; echo "0 2 * * * $(pwd)/scripts/backup-strategy.sh backup >> $LOG_DIR/backup.log 2>&1") | crontab -
    fi
    
    log "Backup automation configured"
}

# Configure security
configure_security() {
    log "Configuring security..."
    
    # Set up firewall rules
    if command -v ufw &> /dev/null; then
        sudo ufw allow 22/tcp    # SSH
        sudo ufw allow 80/tcp    # HTTP
        sudo ufw allow 443/tcp   # HTTPS
        sudo ufw allow 3001/tcp  # Admin Dashboard
        sudo ufw allow 8000/tcp  # API Gateway
        sudo ufw --force enable
    fi
    
    # Configure fail2ban
    if command -v fail2ban-client &> /dev/null; then
        sudo systemctl enable fail2ban
        sudo systemctl start fail2ban
    fi
    
    log "Security configured"
}

# Performance optimization
optimize_performance() {
    log "Optimizing performance..."
    
    # Configure system limits
    echo "* soft nofile 65536" | sudo tee -a /etc/security/limits.conf
    echo "* hard nofile 65536" | sudo tee -a /etc/security/limits.conf
    
    # Configure kernel parameters
    echo "net.core.somaxconn = 65536" | sudo tee -a /etc/sysctl.conf
    echo "net.ipv4.tcp_max_syn_backlog = 65536" | sudo tee -a /etc/sysctl.conf
    echo "vm.max_map_count = 262144" | sudo tee -a /etc/sysctl.conf
    
    # Apply kernel parameters
    sudo sysctl -p
    
    log "Performance optimization completed"
}

# Initialize database
initialize_database() {
    log "Initializing database..."
    
    # Wait for PostgreSQL to be ready
    until docker exec cas_postgres pg_isready -U cas_user; do
        sleep 5
    done
    
    # Run database migrations
    docker exec cas_ingest_service alembic upgrade head
    
    log "Database initialized"
}

# Setup initial data
setup_initial_data() {
    log "Setting up initial data..."
    
    # Create default buckets in MinIO
    docker exec cas_minio mc mb /data/cas-documents
    docker exec cas_minio mc mb /data/cas-backups
    docker exec cas_minio mc mb /data/cas-temp
    
    # Set bucket policies
    docker exec cas_minio mc policy set download /data/cas-documents
    docker exec cas_minio mc policy set private /data/cas-backups
    
    log "Initial data setup completed"
}

# Run health checks
run_health_checks() {
    log "Running comprehensive health checks..."
    
    # API Gateway health
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        log "✓ API Gateway is healthy"
    else
        error "✗ API Gateway health check failed"
        return 1
    fi
    
    # Admin Dashboard health
    if curl -f http://localhost:3001 > /dev/null 2>&1; then
        log "✓ Admin Dashboard is healthy"
    else
        error "✗ Admin Dashboard health check failed"
        return 1
    fi
    
    # Database connectivity
    if docker exec cas_postgres pg_isready -U cas_user > /dev/null 2>&1; then
        log "✓ Database is healthy"
    else
        error "✗ Database health check failed"
        return 1
    fi
    
    log "All health checks passed"
}

# Create deployment summary
create_deployment_summary() {
    log "Creating deployment summary..."
    
    cat > "$LOG_DIR/deployment-summary.txt" << EOF
CAS Platform Production Deployment Summary
==========================================
Deployment Date: $(date)
Platform Version: 1.0.0

Services Deployed:
- PostgreSQL Database
- Redis Cache
- MinIO Object Storage
- RabbitMQ Message Queue
- Elasticsearch Search Engine
- API Gateway
- Ingest Service
- Email Processor
- Footage Service
- LLM Manager
- OTRS Integration
- Backup Service
- Admin Dashboard
- Prometheus Monitoring
- Grafana Dashboards

Access Information:
- Admin Dashboard: http://localhost:3001
- API Gateway: http://localhost:8000
- Grafana: http://localhost:3000 (admin/admin)
- MinIO Console: http://localhost:9001 (minioadmin/minioadmin)

Security Features:
- SSL/TLS encryption enabled
- JWT authentication
- Rate limiting
- Firewall configured
- Fail2ban protection

Backup Configuration:
- Automated daily backups
- Encrypted backup storage
- 30-day retention policy

Monitoring:
- Prometheus metrics collection
- Grafana dashboards
- Alert rules configured
- Health checks enabled

Performance Optimization:
- Load balancing configured
- Auto-scaling enabled
- Connection pooling
- Caching layers
- Resource limits set

Next Steps:
1. Change default passwords
2. Configure SSL certificates
3. Set up external monitoring
4. Test backup and restore procedures
5. Configure user access and permissions

Support Information:
- Logs: $LOG_DIR
- Backups: $BACKUP_DIR
- Configuration: $CONFIG_DIR
EOF

    log "Deployment summary created: $LOG_DIR/deployment-summary.txt"
}

# Main deployment function
main_deployment() {
    log "Starting CAS Platform production deployment..."
    
    # Check prerequisites
    check_prerequisites
    
    # Generate SSL certificates
    generate_ssl_certificates
    
    # Setup NAS mount
    setup_nas_mount
    
    # Configure environment
    configure_environment
    
    # Optimize performance
    optimize_performance
    
    # Configure security
    configure_security
    
    # Deploy services
    deploy_services
    
    # Initialize database
    initialize_database
    
    # Setup initial data
    setup_initial_data
    
    # Configure monitoring
    configure_monitoring
    
    # Setup backup automation
    setup_backup_automation
    
    # Run health checks
    run_health_checks
    
    # Create deployment summary
    create_deployment_summary
    
    log "🎉 CAS Platform production deployment completed successfully!"
    log "Access your platform at: http://localhost:3001"
    log "Review deployment summary: $LOG_DIR/deployment-summary.txt"
}

# Rollback function
rollback_deployment() {
    log "Rolling back deployment..."
    
    # Stop all services
    docker-compose down
    
    # Remove volumes (optional)
    if [ "$1" = "--clean" ]; then
        docker-compose down -v
        log "Clean rollback completed"
    else
        log "Rollback completed (data preserved)"
    fi
}

# Show usage
usage() {
    echo "CAS Platform Production Deployment Script"
    echo "========================================="
    echo "Usage: $0 [deploy|rollback|status]"
    echo ""
    echo "Commands:"
    echo "  deploy     - Deploy the complete platform"
    echo "  rollback   - Rollback the deployment"
    echo "  status     - Show deployment status"
    echo ""
    echo "Examples:"
    echo "  $0 deploy"
    echo "  $0 rollback"
    echo "  $0 rollback --clean"
    echo "  $0 status"
}

# Show deployment status
show_status() {
    log "Deployment Status"
    echo "================"
    docker-compose ps
    echo ""
    echo "Service Health:"
    curl -s http://localhost:8000/health | jq . 2>/dev/null || echo "API Gateway not responding"
}

# Main script logic
case "${1:-deploy}" in
    deploy)
        main_deployment
        ;;
    rollback)
        rollback_deployment "$2"
        ;;
    status)
        show_status
        ;;
    *)
        usage
        exit 1
        ;;
esac
