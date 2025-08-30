#!/bin/bash

# CAS Platform Backup Strategy
# ============================
# Automated backup script with encryption and retention

set -e

# Configuration
BACKUP_DIR="/backups"
RETENTION_DAYS=30
ENCRYPTION_KEY="${BACKUP_ENCRYPTION_KEY:-default-key-change-in-production}"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_NAME="cas-backup-${DATE}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Create backup directory
create_backup_dir() {
    log "Creating backup directory: ${BACKUP_DIR}/${BACKUP_NAME}"
    mkdir -p "${BACKUP_DIR}/${BACKUP_NAME}"
}

# Database backup
backup_database() {
    log "Starting PostgreSQL backup..."
    
    if docker exec cas_postgres pg_dump -U cas_user -d cas_dms > "${BACKUP_DIR}/${BACKUP_NAME}/database.sql"; then
        log "Database backup completed successfully"
    else
        error "Database backup failed"
        return 1
    fi
}

# MinIO backup
backup_minio() {
    log "Starting MinIO backup..."
    
    # Create MinIO backup using mc client
    if docker exec cas_minio mc mirror /data "${BACKUP_DIR}/${BACKUP_NAME}/minio"; then
        log "MinIO backup completed successfully"
    else
        error "MinIO backup failed"
        return 1
    fi
}

# Configuration backup
backup_config() {
    log "Starting configuration backup..."
    
    # Backup all configuration files
    tar -czf "${BACKUP_DIR}/${BACKUP_NAME}/config.tar.gz" \
        -C . config/ \
        --exclude='*.tmp' \
        --exclude='*.log'
    
    log "Configuration backup completed successfully"
}

# Logs backup
backup_logs() {
    log "Starting logs backup..."
    
    # Backup application logs
    find . -name "*.log" -type f -mtime -7 -exec tar -czf "${BACKUP_DIR}/${BACKUP_NAME}/logs.tar.gz" {} +
    
    log "Logs backup completed successfully"
}

# Encrypt backup
encrypt_backup() {
    log "Encrypting backup..."
    
    # Create encrypted archive
    tar -czf - -C "${BACKUP_DIR}" "${BACKUP_NAME}" | \
    openssl enc -aes-256-cbc -salt -k "${ENCRYPTION_KEY}" > \
    "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz.enc"
    
    # Remove unencrypted backup
    rm -rf "${BACKUP_DIR}/${BACKUP_NAME}"
    
    log "Backup encrypted successfully"
}

# Verify backup
verify_backup() {
    log "Verifying backup integrity..."
    
    # Test decryption
    if openssl enc -d -aes-256-cbc -k "${ENCRYPTION_KEY}" -in "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz.enc" | tar -tz > /dev/null; then
        log "Backup verification successful"
    else
        error "Backup verification failed"
        return 1
    fi
}

# Cleanup old backups
cleanup_old_backups() {
    log "Cleaning up backups older than ${RETENTION_DAYS} days..."
    
    find "${BACKUP_DIR}" -name "cas-backup-*.tar.gz.enc" -type f -mtime +${RETENTION_DAYS} -delete
    
    log "Cleanup completed"
}

# Create backup manifest
create_manifest() {
    log "Creating backup manifest..."
    
    cat > "${BACKUP_DIR}/${BACKUP_NAME}.manifest" << EOF
CAS Platform Backup Manifest
============================
Backup Date: $(date)
Backup Name: ${BACKUP_NAME}
Retention Days: ${RETENTION_DAYS}
Encryption: AES-256-CBC

Contents:
- Database: PostgreSQL dump
- Storage: MinIO object storage
- Configuration: All config files
- Logs: Application logs (last 7 days)

Verification:
- Database: $(wc -l < "${BACKUP_DIR}/${BACKUP_NAME}/database.sql" 2>/dev/null || echo "N/A") lines
- MinIO: $(find "${BACKUP_DIR}/${BACKUP_NAME}/minio" -type f | wc -l 2>/dev/null || echo "N/A") files
- Config: $(tar -tzf "${BACKUP_DIR}/${BACKUP_NAME}/config.tar.gz" 2>/dev/null | wc -l || echo "N/A") files
- Logs: $(tar -tzf "${BACKUP_DIR}/${BACKUP_NAME}/logs.tar.gz" 2>/dev/null | wc -l || echo "N/A") files

Backup Size: $(du -sh "${BACKUP_DIR}/${BACKUP_NAME}.tar.gz.enc" 2>/dev/null | cut -f1 || echo "N/A")
EOF

    log "Manifest created successfully"
}

# Main backup function
main_backup() {
    log "Starting CAS Platform backup process..."
    
    # Check if containers are running
    if ! docker ps | grep -q cas_postgres; then
        error "PostgreSQL container is not running"
        exit 1
    fi
    
    if ! docker ps | grep -q cas_minio; then
        error "MinIO container is not running"
        exit 1
    fi
    
    # Execute backup steps
    create_backup_dir
    backup_database
    backup_minio
    backup_config
    backup_logs
    encrypt_backup
    verify_backup
    create_manifest
    cleanup_old_backups
    
    log "Backup process completed successfully!"
    log "Backup file: ${BACKUP_DIR}/${BACKUP_NAME}.tar.gz.enc"
}

# Restore function
restore_backup() {
    local backup_file="$1"
    
    if [ -z "$backup_file" ]; then
        error "Please specify backup file to restore"
        echo "Usage: $0 restore <backup-file>"
        exit 1
    fi
    
    if [ ! -f "$backup_file" ]; then
        error "Backup file not found: $backup_file"
        exit 1
    fi
    
    log "Starting restore from: $backup_file"
    
    # Create restore directory
    local restore_dir="/tmp/cas-restore-${DATE}"
    mkdir -p "$restore_dir"
    
    # Decrypt and extract backup
    log "Decrypting backup..."
    openssl enc -d -aes-256-cbc -k "${ENCRYPTION_KEY}" -in "$backup_file" | \
    tar -xzf - -C "$restore_dir"
    
    # Restore database
    log "Restoring database..."
    docker exec -i cas_postgres psql -U cas_user -d cas_dms < "$restore_dir"/*/database.sql
    
    # Restore MinIO (if needed)
    log "Restoring MinIO data..."
    docker exec cas_minio mc mirror "$restore_dir"/*/minio /data
    
    # Cleanup
    rm -rf "$restore_dir"
    
    log "Restore completed successfully!"
}

# Show usage
usage() {
    echo "CAS Platform Backup Script"
    echo "=========================="
    echo "Usage: $0 [backup|restore <file>|status]"
    echo ""
    echo "Commands:"
    echo "  backup    - Create a new backup"
    echo "  restore   - Restore from backup file"
    echo "  status    - Show backup status"
    echo ""
    echo "Examples:"
    echo "  $0 backup"
    echo "  $0 restore /backups/cas-backup-20241201_120000.tar.gz.enc"
    echo "  $0 status"
}

# Show backup status
show_status() {
    log "Backup Status"
    echo "============="
    echo "Backup Directory: ${BACKUP_DIR}"
    echo "Retention Days: ${RETENTION_DAYS}"
    echo ""
    echo "Recent Backups:"
    ls -la "${BACKUP_DIR}"/*.tar.gz.enc 2>/dev/null | tail -10 || echo "No backups found"
    echo ""
    echo "Disk Usage:"
    du -sh "${BACKUP_DIR}" 2>/dev/null || echo "Backup directory not found"
}

# Main script logic
case "${1:-backup}" in
    backup)
        main_backup
        ;;
    restore)
        restore_backup "$2"
        ;;
    status)
        show_status
        ;;
    *)
        usage
        exit 1
        ;;
esac
