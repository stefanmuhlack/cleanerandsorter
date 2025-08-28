# Test Data for CAS Document Management System

This directory contains sample documents for testing the document processing pipeline.

## Directory Structure

```
test-data/
├── sample-documents/
│   ├── invoices/
│   │   ├── invoice_2024_001.pdf
│   │   ├── invoice_2024_002.pdf
│   │   └── invoice_2024_003.pdf
│   ├── contracts/
│   │   ├── contract_customer_a.pdf
│   │   ├── contract_customer_b.pdf
│   │   └── contract_customer_c.pdf
│   ├── emails/
│   │   ├── support_ticket_001.eml
│   │   ├── support_ticket_002.eml
│   │   └── sales_inquiry.eml
│   ├── footage/
│   │   ├── raw/
│   │   │   ├── project_alpha/
│   │   │   │   ├── video_001.mov
│   │   │   │   └── image_001.jpg
│   │   │   └── project_beta/
│   │   │       ├── video_002.mov
│   │   │       └── image_002.png
│   │   └── processed/
│   │       ├── project_alpha/
│   │       │   ├── video_001_compressed.mp4
│   │       │   └── image_001_thumbnail.jpg
│   │       └── project_beta/
│   │           ├── video_002_compressed.mp4
│   │           └── image_002_thumbnail.jpg
│   └── otrs-tickets/
│       ├── ticket_001/
│       │   ├── ticket_data.json
│       │   └── attachments/
│       │       ├── screenshot_001.png
│       │       └── log_file.txt
│       └── ticket_002/
│           ├── ticket_data.json
│           └── attachments/
│               ├── error_report.pdf
│               └── config_file.xml
```

## Test Scenarios

### 1. Document Classification Test
- **Invoices**: Test automatic classification as "finanzen/rechnungen"
- **Contracts**: Test classification as "projekte/vertraege"
- **Emails**: Test email processing and attachment extraction

### 2. Duplicate Detection Test
- Upload the same document multiple times
- Verify that duplicates are detected and handled appropriately

### 3. LLM Classification Test
- Test semantic classification of documents with ambiguous names
- Verify fallback to rule-based classification when LLM is unavailable

### 4. Rollback Test
- Process a batch of documents
- Test rollback functionality to undo processing

### 5. Email Processing Test
- Test IMAP connection and email fetching
- Test attachment extraction and processing

### 6. OTRS Integration Test
- Test ticket export and attachment processing
- Verify metadata extraction and classification

### 7. Footage Processing Test
- Test large file handling
- Test thumbnail generation and metadata extraction

## Usage

1. **Copy test data to NAS share**:
   ```bash
   cp -r test-data/sample-documents/* /mnt/nas/documents/
   ```

2. **Start processing**:
   ```bash
   # Via Admin Dashboard
   curl -X POST http://localhost:3001/api/processing/start \
     -H "Content-Type: application/json" \
     -d '{"source": "/mnt/nas/documents", "enable_duplicate_detection": true}'
   ```

3. **Monitor progress**:
   ```bash
   # Check processing status
   curl http://localhost:3001/api/processing/status
   
   # View logs
   docker-compose logs ingest-service
   ```

## Expected Results

### Document Classification
- Invoices should be classified as "finanzen/rechnungen"
- Contracts should be classified as "projekte/vertraege"
- Emails should be processed and attachments extracted

### Duplicate Detection
- Second upload of same document should be flagged as duplicate
- Original document should be preserved

### LLM Classification
- Documents should be semantically classified
- Fallback to rule-based classification should work

### Rollback
- Processing should be reversible
- Original file locations should be restored

### Email Processing
- Emails should be fetched from IMAP
- Attachments should be extracted and processed

### OTRS Integration
- Tickets should be exported with metadata
- Attachments should be processed

### Footage Processing
- Large files should be handled efficiently
- Thumbnails should be generated
- Metadata should be extracted

## Validation Checklist

- [ ] All documents are processed without errors
- [ ] Classification accuracy is >90%
- [ ] Duplicate detection works correctly
- [ ] Rollback functionality works
- [ ] Email processing works
- [ ] OTRS integration works
- [ ] Footage processing works
- [ ] Performance is acceptable
- [ ] Logs are properly generated
- [ ] Monitoring metrics are collected

## Troubleshooting

### Common Issues

1. **Permission Denied**: Ensure NAS mount has correct permissions
2. **LLM Timeout**: Check Ollama service is running
3. **Email Connection Failed**: Verify IMAP settings
4. **OTRS API Error**: Check OTRS credentials and API access
5. **Storage Full**: Monitor disk space and cleanup old backups

### Debug Commands

```bash
# Check service health
curl http://localhost:8001/health  # LLM Manager
curl http://localhost:8002/health  # Email Processor
curl http://localhost:8003/health  # OTRS Integration
curl http://localhost:8004/health  # Backup Service

# Check logs
docker-compose logs -f ingest-service
docker-compose logs -f llm-manager
docker-compose logs -f email-processor
docker-compose logs -f otrs-integration
docker-compose logs -f backup-service

# Check MinIO
docker-compose exec minio mc ls /backups

# Check PostgreSQL
docker-compose exec postgres psql -U cas_user -d cas_dms -c "SELECT * FROM processing_jobs LIMIT 5;"
``` 