#!/bin/bash

# Sprint 5: Dokumentation und Schulung
# ====================================
# Ziel: Systemverständnis und Bedienbarkeit erhöhen

set -e

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

# Step 1: Create Technical Documentation
create_technical_documentation() {
    log "Step 1: Create Technical Documentation"
    
    # Create docs directory
    mkdir -p docs
    
    # System Architecture Documentation
    cat > docs/system-architecture.md << EOF
# CAS Platform - System Architecture

## Overview
The CAS Platform is a comprehensive document management and processing system built with microservices architecture.

## Architecture Components

### Core Services
- **API Gateway**: Central entry point with authentication and routing
- **Ingest Service**: Document processing and classification
- **Email Processor**: Email attachment processing
- **OTRS Integration**: Ticket system integration
- **LLM Manager**: AI-powered document classification
- **Backup Service**: Automated backup management

### Infrastructure
- **PostgreSQL**: Primary database
- **Redis**: Caching and session management
- **MinIO**: Object storage
- **RabbitMQ**: Message queuing
- **Elasticsearch**: Search and indexing

### Frontend
- **Admin Dashboard**: React-based management interface
- **Monitoring**: Grafana dashboards and Prometheus metrics

## Data Flow
1. Documents uploaded via Admin Dashboard or Email
2. Ingest Service processes and classifies documents
3. LLM Manager provides AI-powered classification
4. Documents stored in MinIO with metadata in PostgreSQL
5. Search available via Elasticsearch
6. Automated backups ensure data integrity

## Security
- JWT-based authentication
- Role-based access control
- SSL/TLS encryption
- Rate limiting and monitoring
- Audit logging

## Monitoring
- Prometheus metrics collection
- Grafana dashboards
- Alert management
- Health checks for all services
EOF

    # API Documentation
    cat > docs/api-reference.md << EOF
# CAS Platform - API Reference

## Base URL
\`http://localhost:8000\`

## Authentication
All API requests require JWT authentication:
\`\`\`
Authorization: Bearer <jwt_token>
\`\`\`

## Endpoints

### Health Checks
- \`GET /health\` - System health status
- \`GET /api/health\` - Ingest service health

### Document Management
- \`POST /api/ingest/start\` - Start document ingestion
- \`POST /api/ingest/file\` - Process single file
- \`GET /api/documents\` - List documents
- \`GET /api/documents/{id}\` - Get document details

### Classification
- \`POST /api/classify\` - Classify document
- \`GET /api/categories\` - List categories

### Backup
- \`POST /api/backup\` - Create backup
- \`GET /api/backups\` - List backups
- \`POST /api/backup/restore\` - Restore backup

### Rollback
- \`POST /api/rollback/snapshot\` - Create snapshot
- \`POST /api/rollback/execute\` - Execute rollback

## Response Format
\`\`\`json
{
  "success": true,
  "data": {},
  "message": "Operation completed"
}
\`\`\`

## Error Handling
\`\`\`json
{
  "success": false,
  "error": "Error description",
  "code": "ERROR_CODE"
}
\`\`\`
EOF

    # Configuration Reference
    cat > docs/configuration-reference.md << EOF
# CAS Platform - Configuration Reference

## Environment Variables

### Security
- \`JWT_SECRET\`: JWT signing secret
- \`JWT_EXPIRATION\`: Token expiration time

### Database
- \`POSTGRES_DB\`: Database name
- \`POSTGRES_USER\`: Database user
- \`POSTGRES_PASSWORD\`: Database password

### Storage
- \`MINIO_ROOT_USER\`: MinIO admin user
- \`MINIO_ROOT_PASSWORD\`: MinIO admin password

### Email
- \`SUPPORT_EMAIL_PASSWORD\`: Support email password
- \`SALES_EMAIL_PASSWORD\`: Sales email password
- \`OTRS_EMAIL_PASSWORD\`: OTRS email password

### OTRS
- \`OTRS_API_PASSWORD\`: OTRS API password
- \`OTRS_API_KEY\`: OTRS API key

## Configuration Files

### Email Configuration (\`config/email-config.yaml\`)
- IMAP account settings
- Processing rules
- File type handling
- Notification settings

### OTRS Configuration (\`config/otrs-config.yaml\`)
- API settings
- Ticket processing rules
- Attachment handling
- Export/Import settings

### Security Configuration (\`config/security-config.yaml\`)
- SSL/TLS settings
- Authentication policies
- Authorization rules
- Network security

### Monitoring Configuration (\`prometheus.yml\`)
- Metrics collection
- Alert rules
- Service discovery
EOF

    log "✓ Technical documentation created"
}

# Step 2: Create User Guides
create_user_guides() {
    log "Step 2: Create User Guides"
    
    # Admin User Guide
    cat > docs/admin-user-guide.md << EOF
# CAS Platform - Admin User Guide

## Getting Started

### Accessing the Dashboard
1. Open browser and navigate to \`http://localhost:3001\`
2. Login with admin credentials
3. Dashboard overview shows system status

### Dashboard Navigation
- **Dashboard**: System overview and statistics
- **File Processing**: Upload and manage documents
- **Sorting Rules**: Configure document classification rules
- **Statistics**: View processing statistics
- **Email Integration**: Monitor email processing
- **Footage Management**: Manage video/media files
- **Monitoring**: System health and performance
- **Settings**: System configuration

## Document Management

### Uploading Documents
1. Navigate to "File Processing"
2. Click "Upload Files"
3. Select files or drag-and-drop
4. Configure processing options:
   - Generate thumbnails
   - Extract metadata
   - Enable classification
5. Click "Upload"

### Managing Documents
1. Use search to find documents
2. View document details and metadata
3. Download or delete documents
4. Update classification manually

## System Administration

### Monitoring System Health
1. Navigate to "Monitoring"
2. View service status
3. Check performance metrics
4. Review alerts and notifications

### Backup Management
1. Navigate to "Settings" > "Backup"
2. View backup history
3. Create manual backups
4. Restore from backup if needed

### User Management
1. Navigate to "Settings" > "Users"
2. Add new users
3. Assign roles and permissions
4. Manage user access

## Troubleshooting

### Common Issues
- **Service not responding**: Check service health in Monitoring
- **Upload failures**: Verify file size and type restrictions
- **Classification errors**: Check LLM service status
- **Email processing issues**: Verify email configuration

### Logs and Debugging
- View service logs in Monitoring
- Check error messages in Admin Dashboard
- Use API endpoints for detailed debugging
EOF

    # End User Guide
    cat > docs/end-user-guide.md << EOF
# CAS Platform - End User Guide

## Introduction
The CAS Platform helps you manage and organize documents efficiently using AI-powered classification.

## Basic Operations

### Finding Documents
1. Use the search function to find documents
2. Filter by date, type, or classification
3. View document previews and metadata

### Understanding Classifications
- Documents are automatically classified by AI
- Categories include: Invoices, Contracts, Reports, etc.
- You can manually adjust classifications if needed

### Working with Email Attachments
- Email attachments are automatically processed
- Check "Email Integration" for processing status
- Attachments are classified and stored automatically

## Best Practices

### File Naming
- Use descriptive file names
- Include dates in filenames when relevant
- Avoid special characters in filenames

### File Organization
- Let the system automatically organize files
- Use tags and categories for better organization
- Regular cleanup of old files

### Security
- Don't share sensitive documents
- Report any security concerns to administrators
- Log out when finished using the system

## Getting Help
- Contact your system administrator for technical issues
- Check the FAQ section for common questions
- Use the help documentation for detailed instructions
EOF

    # Training Materials
    cat > docs/training-materials.md << EOF
# CAS Platform - Training Materials

## Training Sessions

### Session 1: System Overview (30 minutes)
**Objectives:**
- Understand system purpose and capabilities
- Learn basic navigation
- Know where to find help

**Topics:**
- System introduction and benefits
- Dashboard overview
- Basic navigation
- Help resources

### Session 2: Document Management (45 minutes)
**Objectives:**
- Upload and manage documents
- Search and find documents
- Understand classification

**Topics:**
- Document upload process
- Search and filtering
- Classification system
- Document organization

### Session 3: Email Integration (30 minutes)
**Objectives:**
- Understand email processing
- Monitor email status
- Handle email attachments

**Topics:**
- Email processing workflow
- Monitoring email status
- Attachment management
- Troubleshooting email issues

### Session 4: Advanced Features (45 minutes)
**Objectives:**
- Use advanced search features
- Manage user permissions
- Monitor system health

**Topics:**
- Advanced search and filtering
- User management
- System monitoring
- Backup and restore

## Hands-on Exercises

### Exercise 1: Document Upload
1. Upload a sample document
2. Verify classification
3. Search for the document
4. Download the document

### Exercise 2: Email Processing
1. Send test email with attachment
2. Monitor processing status
3. Verify attachment classification
4. Access processed attachment

### Exercise 3: System Monitoring
1. Check system health
2. View performance metrics
3. Review recent alerts
4. Generate system report

## Assessment Questions

### Basic Level
1. How do you upload a document?
2. How do you search for documents?
3. What is automatic classification?

### Intermediate Level
1. How do you monitor email processing?
2. How do you manage user permissions?
3. How do you check system health?

### Advanced Level
1. How do you configure classification rules?
2. How do you perform system backup?
3. How do you troubleshoot service issues?

## Certification
Complete all training sessions and pass assessment to receive CAS Platform certification.
EOF

    log "✓ User guides created"
}

# Step 3: Create Admin Handbook
create_admin_handbook() {
    log "Step 3: Create Admin Handbook"
    
    cat > docs/admin-handbook.md << EOF
# CAS Platform - Administrator Handbook

## System Administration

### Daily Operations
1. **Morning Checks**
   - Review system health dashboard
   - Check for overnight alerts
   - Verify backup completion
   - Review email processing status

2. **Monitoring Tasks**
   - Monitor service performance
   - Check disk space usage
   - Review error logs
   - Monitor user activity

3. **Weekly Tasks**
   - Review system statistics
   - Check backup integrity
   - Update security patches
   - Review user access logs

### Backup Procedures

#### Manual Backup
\`\`\`bash
# Create manual backup
curl -X POST http://localhost:8004/backup \\
  -H "Content-Type: application/json" \\
  -d '{"type": "full", "description": "Manual backup"}'
\`\`\`

#### Restore Procedure
\`\`\`bash
# List available backups
curl http://localhost:8004/backups

# Restore from backup
curl -X POST http://localhost:8004/restore \\
  -H "Content-Type: application/json" \\
  -d '{"backup_id": "backup-id-here"}'
\`\`\`

### Rollback Procedures

#### Create Snapshot
\`\`\`bash
curl -X POST http://localhost:8000/api/rollback/snapshot \\
  -H "Content-Type: application/json" \\
  -d '{"description": "Before system update"}'
\`\`\`

#### Execute Rollback
\`\`\`bash
curl -X POST http://localhost:8000/api/rollback/execute \\
  -H "Content-Type: application/json" \\
  -d '{"snapshot_id": "snapshot-id-here"}'
\`\`\`

### User Management

#### Adding Users
1. Navigate to Admin Dashboard > Settings > Users
2. Click "Add User"
3. Enter user details and assign role
4. Set initial password
5. Configure permissions

#### Role Management
- **Admin**: Full system access
- **Manager**: Document management and monitoring
- **User**: Document upload and search
- **Viewer**: Read-only access

### Troubleshooting

#### Service Issues
1. Check service status: \`docker-compose ps\`
2. View service logs: \`docker logs <service-name>\`
3. Restart service: \`docker-compose restart <service>\`
4. Check resource usage: \`docker stats\`

#### Performance Issues
1. Monitor CPU and memory usage
2. Check disk space
3. Review database performance
4. Analyze slow queries

#### Security Incidents
1. Review access logs
2. Check for unauthorized access
3. Verify user permissions
4. Update security settings

### Maintenance

#### Regular Maintenance
- **Daily**: Health checks and monitoring
- **Weekly**: Backup verification and log review
- **Monthly**: Security updates and performance tuning
- **Quarterly**: System updates and capacity planning

#### Emergency Procedures
1. **System Down**: Check service status and restart
2. **Data Loss**: Restore from latest backup
3. **Security Breach**: Isolate system and investigate
4. **Performance Issues**: Scale resources or optimize

### Configuration Management

#### Environment Variables
- Keep sensitive data in environment variables
- Use strong passwords and keys
- Rotate credentials regularly
- Document all configuration changes

#### Configuration Files
- Version control all configuration files
- Test changes in staging environment
- Document configuration changes
- Maintain backup of configurations

### Monitoring and Alerts

#### Key Metrics
- Service response times
- Error rates
- Resource usage
- User activity

#### Alert Management
- Configure appropriate alert thresholds
- Set up notification channels
- Review and acknowledge alerts
- Escalate critical issues

### Disaster Recovery

#### Recovery Procedures
1. **System Recovery**: Restore from backup
2. **Data Recovery**: Use point-in-time recovery
3. **Service Recovery**: Restart failed services
4. **Network Recovery**: Check connectivity and DNS

#### Business Continuity
- Maintain off-site backups
- Document recovery procedures
- Test recovery procedures regularly
- Train staff on emergency procedures
EOF

    log "✓ Admin handbook created"
}

# Step 4: Create Sprint 5 report
create_sprint5_report() {
    log "Step 4: Create Sprint 5 report"
    
    cat > "sprint5-report.txt" << EOF
Sprint 5: Dokumentation und Schulung
====================================
Report Date: $(date)
Status: COMPLETED

Documentation Created:

1. Technical Documentation:
   - System Architecture: docs/system-architecture.md
   - API Reference: docs/api-reference.md
   - Configuration Reference: docs/configuration-reference.md

2. User Guides:
   - Admin User Guide: docs/admin-user-guide.md
   - End User Guide: docs/end-user-guide.md
   - Training Materials: docs/training-materials.md

3. Administrator Handbook:
   - Admin Handbook: docs/admin-handbook.md

Documentation Coverage:
- System architecture and components
- API endpoints and usage
- Configuration management
- User operations and workflows
- Administrative procedures
- Troubleshooting guides
- Training materials and exercises

Training Program:
- 4 training sessions (2.5 hours total)
- Hands-on exercises
- Assessment questions
- Certification process

Abnahme Criteria:
✅ Comprehensive technical documentation
✅ User-friendly guides created
✅ Administrator handbook complete
✅ Training materials prepared
✅ System handover ready

Next Steps:
1. Conduct training sessions
2. User acceptance testing
3. System handover to operations team
4. Ongoing support and maintenance

Production Readiness:
- Documentation: COMPLETE
- Training: READY
- Handover: PREPARED
- Support: AVAILABLE

EOF

    log "✓ Sprint 5 report created: sprint5-report.txt"
}

# Main Sprint 5 execution
main_sprint5() {
    log "🚀 Starting Sprint 5: Dokumentation und Schulung"
    
    create_technical_documentation
    create_user_guides
    create_admin_handbook
    create_sprint5_report
    
    log "🎉 Sprint 5 completed successfully!"
    log "📊 Review sprint5-report.txt for detailed results"
    log "📚 Documentation available in docs/ directory"
}

# Show usage
usage() {
    echo "Sprint 5: Dokumentation und Schulung"
    echo "===================================="
    echo "Usage: $0 [run|list]"
    echo ""
    echo "Commands:"
    echo "  run      - Execute complete Sprint 5"
    echo "  list     - List created documentation"
    echo ""
    echo "Examples:"
    echo "  $0 run"
    echo "  $0 list"
}

# List documentation
list_documentation() {
    log "Created Documentation"
    echo "===================="
    echo "Technical Documentation:"
    echo "  - docs/system-architecture.md"
    echo "  - docs/api-reference.md"
    echo "  - docs/configuration-reference.md"
    echo ""
    echo "User Guides:"
    echo "  - docs/admin-user-guide.md"
    echo "  - docs/end-user-guide.md"
    echo "  - docs/training-materials.md"
    echo ""
    echo "Administrator Handbook:"
    echo "  - docs/admin-handbook.md"
    echo ""
    echo "Reports:"
    echo "  - sprint5-report.txt"
}

# Main script logic
case "${1:-run}" in
    run)
        main_sprint5
        ;;
    list)
        list_documentation
        ;;
    *)
        usage
        exit 1
        ;;
esac
