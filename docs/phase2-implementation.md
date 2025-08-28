# Phase 2 Implementation: Data Migration and Classification Pipeline

## Overview

Phase 2 implements advanced document processing capabilities including duplicate detection, LLM-powered classification, and rollback mechanisms. This phase establishes the foundation for intelligent document management with AI assistance.

## Components Implemented

### 1. Enhanced Ingest Service

#### New Features:
- **Hash-based Duplicate Detection**: SHA-256 hashing for identifying duplicate documents
- **LLM Classification**: Semantic document classification using local LLMs
- **Rollback Mechanism**: Complete undo capability for processing operations
- **Processing Snapshots**: State preservation for safe rollbacks
- **Enhanced Error Handling**: Comprehensive error recovery and logging

#### Key Files:
- `ingest-service/app/domain/services.py`: Core business logic
- `ingest-service/app/domain/entities.py`: Data structures
- `ingest-service/app/domain/repositories.py`: Repository interfaces

### 2. LLM Manager Service

#### Purpose:
- Manages local LLM models via Ollama
- Provides semantic classification for documents
- Handles model loading, caching, and fallback mechanisms

#### Features:
- Model management (pull, delete, list)
- Document classification with confidence scoring
- Fallback to rule-based classification
- Performance monitoring and metrics

#### Key Files:
- `llm-manager/main.py`: FastAPI application
- `config/llm-config.yaml`: LLM configuration
- `llm-manager/Dockerfile`: Container configuration

### 3. Email Processor Service

#### Purpose:
- Processes email attachments from IMAP accounts
- Extracts and classifies email content
- Integrates with Paperless-ngx for document storage

#### Features:
- Multi-account IMAP support (OTRS, Support, Vertrieb)
- Attachment extraction and processing
- Email body analysis and classification
- Background processing with queue management

#### Key Files:
- `email-processor/main.py`: FastAPI application
- `config/email-config.yaml`: Email configuration
- `email-processor/Dockerfile`: Container configuration

### 4. OTRS Integration Service

#### Purpose:
- Exports tickets and attachments from OTRS
- Processes ticket metadata and content
- Integrates with document processing pipeline

#### Features:
- SOAP/XML API integration with OTRS
- Ticket export with date range filtering
- Attachment download and processing
- Metadata extraction and classification

#### Key Files:
- `otrs-integration/main.py`: FastAPI application
- `config/otrs-config.yaml`: OTRS configuration
- `otrs-integration/Dockerfile`: Container configuration

### 5. Backup Service

#### Purpose:
- Automated backup of MinIO and PostgreSQL
- Backup scheduling and retention management
- Restore capabilities with verification

#### Features:
- Database backups (PostgreSQL)
- Object storage backups (MinIO)
- Full system backups
- Automated cleanup and retention
- Restore functionality

#### Key Files:
- `backup-service/main.py`: FastAPI application
- `config/backup-config.yaml`: Backup configuration
- `backup-service/Dockerfile`: Container configuration

## Infrastructure Updates

### Docker Compose Configuration

New services added to `docker-compose.yml`:
```yaml
ollama:           # LLM runtime environment
llm-manager:      # LLM management service
email-processor:  # Email processing service
otrs-integration: # OTRS integration service
backup-service:   # Backup management service
```

### Kubernetes Configuration

Updated `k8s/ingest-service-deployment.yaml`:
- Added NAS share mounts
- Enhanced environment variables
- Volume configurations for persistent storage

### Configuration Files

#### Sorting Rules (`config/sorting-rules.yaml`)
- Advanced categorization rules
- Role-based access control
- Sensitive document handling
- Processing pipeline configuration

#### LLM Configuration (`config/llm-config.yaml`)
- Model specifications
- Classification categories
- Performance settings
- Fallback configurations

#### Email Configuration (`config/email-config.yaml`)
- IMAP account settings
- Processing rules
- Notification settings
- Error handling

#### OTRS Configuration (`config/otrs-config.yaml`)
- API credentials
- Export settings
- Processing parameters
- Integration rules

#### Backup Configuration (`config/backup-config.yaml`)
- Retention policies
- Schedule settings
- Storage configuration
- Security settings

## Monitoring and Observability

### Grafana Dashboard

Comprehensive monitoring dashboard (`config/grafana/provisioning/dashboards/cas-monitoring-dashboard.json`):
- System health overview
- Processing metrics
- LLM performance
- Storage usage
- Error rates
- Alert status

### Prometheus Configuration

Updated `prometheus.yml` with new service targets:
- All microservices
- Database and storage metrics
- LLM performance metrics
- Custom business metrics

### Alert Rules

Comprehensive alerting (`alert_rules.yml`):
- Service health monitoring
- Performance thresholds
- Error rate alerts
- Resource usage warnings
- Security alerts

## Testing Framework

### Test Data Structure

Organized test data in `test-data/sample-documents/`:
- Invoices and contracts
- Email samples
- Footage files
- OTRS ticket data
- Various document types

### Test Scenarios

1. **Document Classification Test**
   - Automatic categorization
   - LLM vs rule-based classification
   - Accuracy validation

2. **Duplicate Detection Test**
   - Hash-based detection
   - Duplicate handling
   - Performance validation

3. **Rollback Test**
   - Processing undo
   - State restoration
   - Data integrity verification

4. **Email Processing Test**
   - IMAP connectivity
   - Attachment extraction
   - Classification accuracy

5. **OTRS Integration Test**
   - API connectivity
   - Ticket export
   - Attachment processing

6. **Backup Test**
   - Automated backups
   - Restore functionality
   - Retention policies

## API Endpoints

### LLM Manager (`http://localhost:8001`)
```
GET  /health                    # Health check
GET  /models                    # List available models
POST /models/pull               # Pull new model
DELETE /models/{model_name}     # Delete model
POST /classify                  # Classify document
```

### Email Processor (`http://localhost:8002`)
```
GET  /health                    # Health check
GET  /accounts                  # List email accounts
POST /process/{account}         # Process emails
```

### OTRS Integration (`http://localhost:8003`)
```
GET  /health                    # Health check
GET  /tickets                   # List tickets
GET  /tickets/{ticket_id}       # Get ticket details
POST /export                    # Export tickets
GET  /attachments/{ticket_id}   # Get attachments
```

### Backup Service (`http://localhost:8004`)
```
GET  /health                    # Health check
POST /backup                    # Create backup
GET  /backups                   # List backups
GET  /backups/{backup_id}       # Get backup details
DELETE /backups/{backup_id}     # Delete backup
POST /backups/{backup_id}/restore # Restore backup
POST /cleanup                   # Cleanup old backups
```

## Performance Characteristics

### Processing Capacity
- **Document Processing**: 100+ documents/minute
- **LLM Classification**: 10-30 seconds per document
- **Duplicate Detection**: Near-instantaneous
- **Email Processing**: 50+ emails/minute
- **Backup Operations**: 1-10 GB/hour

### Resource Requirements
- **CPU**: 2-4 cores per service
- **Memory**: 1-2 GB per service
- **Storage**: 10-50 GB for models and data
- **Network**: 100 Mbps for processing

### Scalability
- Horizontal scaling via Docker Compose
- Queue-based processing with RabbitMQ
- Stateless service design
- Load balancing ready

## Security Considerations

### Data Protection
- Encrypted storage for sensitive documents
- Role-based access control
- Audit logging for all operations
- Secure API authentication

### Network Security
- Internal service communication
- HTTPS for external APIs
- Firewall rules for service isolation
- VPN access for remote management

### Backup Security
- Encrypted backup storage
- Secure backup transfer
- Access control for restore operations
- Backup integrity verification

## Deployment Instructions

### 1. Prerequisites
```bash
# Ensure Docker and Docker Compose are installed
docker --version
docker-compose --version

# Ensure sufficient disk space (50+ GB recommended)
df -h

# Ensure ports are available
netstat -tulpn | grep -E ':(3001|8001|8002|8003|8004|8010|11434)'
```

### 2. Environment Setup
```bash
# Copy configuration files
cp config/*.yaml /etc/cas/

# Set environment variables
export CAS_ENVIRONMENT=production
export CAS_LOG_LEVEL=INFO

# Create necessary directories
mkdir -p /var/cas/{backups,logs,data}
```

### 3. Service Deployment
```bash
# Start all services
docker-compose up -d

# Verify service health
docker-compose ps
curl http://localhost:8001/health  # LLM Manager
curl http://localhost:8002/health  # Email Processor
curl http://localhost:8003/health  # OTRS Integration
curl http://localhost:8004/health  # Backup Service
```

### 4. Initial Configuration
```bash
# Load LLM models
curl -X POST http://localhost:8001/models/pull \
  -H "Content-Type: application/json" \
  -d '{"model": "mistral:7b"}'

# Configure email accounts
# Edit config/email-config.yaml

# Configure OTRS integration
# Edit config/otrs-config.yaml

# Test backup functionality
curl -X POST http://localhost:8004/backup \
  -H "Content-Type: application/json" \
  -d '{"type": "database"}'
```

### 5. Monitoring Setup
```bash
# Access Grafana dashboard
# http://localhost:3000 (admin/admin)

# Access Prometheus
# http://localhost:9090

# Access Admin Dashboard
# http://localhost:3001
```

## Troubleshooting

### Common Issues

1. **LLM Service Not Responding**
   ```bash
   # Check Ollama service
   docker-compose logs ollama
   
   # Check model availability
   curl http://localhost:11434/api/tags
   ```

2. **Email Processing Failures**
   ```bash
   # Check IMAP connectivity
   docker-compose logs email-processor
   
   # Verify email configuration
   cat config/email-config.yaml
   ```

3. **OTRS Integration Errors**
   ```bash
   # Check API connectivity
   docker-compose logs otrs-integration
   
   # Verify OTRS credentials
   cat config/otrs-config.yaml
   ```

4. **Backup Failures**
   ```bash
   # Check backup service logs
   docker-compose logs backup-service
   
   # Verify storage permissions
   ls -la /var/cas/backups/
   ```

### Debug Commands

```bash
# Service health checks
for service in llm-manager email-processor otrs-integration backup-service; do
  echo "Checking $service..."
  curl -s http://localhost:$(docker-compose port $service 8000 | cut -d: -f2)/health
done

# Log analysis
docker-compose logs --tail=100 ingest-service | grep ERROR
docker-compose logs --tail=100 llm-manager | grep ERROR

# Resource usage
docker stats --no-stream

# Storage usage
du -sh /var/cas/*
```

## Next Steps (Phase 3)

Phase 2 establishes the foundation for advanced document processing. Phase 3 will focus on:

1. **Email and OTRS Integration Enhancement**
   - Advanced email filtering rules
   - Automated ticket processing
   - Integration with TLD management

2. **Footage and Media Processing**
   - Video and image processing
   - Thumbnail generation
   - Metadata extraction

3. **Advanced Analytics**
   - Processing analytics
   - Performance optimization
   - Machine learning improvements

4. **Production Hardening**
   - Security enhancements
   - Performance tuning
   - Disaster recovery planning

## Support and Maintenance

### Regular Maintenance Tasks
- Monitor backup success rates
- Review and update LLM models
- Clean up old processing data
- Update security configurations
- Review and optimize performance

### Monitoring Alerts
- Set up email notifications for critical alerts
- Configure escalation procedures
- Regular review of alert thresholds
- Performance trend analysis

### Documentation Updates
- Keep configuration documentation current
- Update troubleshooting guides
- Maintain API documentation
- Record lessons learned 