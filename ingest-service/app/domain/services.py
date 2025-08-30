"""
Domain services for the ingest service.
These contain the core business logic and orchestrate operations.
"""

import asyncio
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
from uuid import UUID
import hashlib
import yaml
import json
from dataclasses import dataclass, asdict
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

from .entities import (
    FileEntity, SortingRule, ProcessingBatch, ProcessingStatistics,
    FileType, ProcessingStatus, FileMetadata, Document, ProcessingResult, ClassificationResult
)
from .repositories import (
    FileRepository, SortingRuleRepository, ProcessingBatchRepository,
    ObjectStorageRepository, MessageQueueRepository, DocumentRepository, StorageRepository
)


logger = logging.getLogger(__name__)


class FileProcessingService:
    """Service for processing and sorting files."""
    
    def __init__(
        self,
        file_repo: FileRepository,
        rule_repo: SortingRuleRepository,
        batch_repo: ProcessingBatchRepository,
        storage_repo: ObjectStorageRepository,
        message_repo: MessageQueueRepository
    ):
        self.file_repo = file_repo
        self.rule_repo = rule_repo
        self.batch_repo = batch_repo
        self.storage_repo = storage_repo
        self.message_repo = message_repo
    
    async def process_file(self, file_path: Path) -> FileEntity:
        """Process a single file through the entire pipeline."""
        try:
            # Create file entity
            file_entity = await self._create_file_entity(file_path)
            
            # Extract metadata
            file_entity.metadata = await self._extract_metadata(file_path)
            
            # Determine file type
            file_entity.file_type = self._determine_file_type(file_entity.metadata.mime_type)
            
            # Find matching sorting rule
            rule = await self._find_matching_rule(file_entity)
            if rule:
                file_entity.assign_sorting_rule(rule)
                target_path = self._generate_target_path(rule, file_entity)
                file_entity.set_target_path(target_path)
            
            # Save file entity
            file_entity = await self.file_repo.save(file_entity)
            
            # Upload to object storage
            if file_entity.target_path:
                bucket = "documents"
                key = str(file_entity.target_path)
                success = await self.storage_repo.upload_file(str(file_path), bucket, key)
                if success:
                    file_entity.set_storage_location(bucket, key)
                    file_entity.update_status(ProcessingStatus.COMPLETED)
                else:
                    file_entity.update_status(ProcessingStatus.FAILED, "Failed to upload to storage")
            
            # Update file entity
            await self.file_repo.save(file_entity)
            
            # Publish message for indexing
            await self._publish_indexing_message(file_entity)
            
            return file_entity
            
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            if 'file_entity' in locals():
                file_entity.update_status(ProcessingStatus.FAILED, str(e))
                await self.file_repo.save(file_entity)
            raise
    
    async def process_batch(self, file_paths: List[Path]) -> ProcessingBatch:
        """Process a batch of files."""
        batch = ProcessingBatch()
        
        for file_path in file_paths:
            try:
                file_entity = await self.process_file(file_path)
                batch.add_file(file_entity)
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {e}")
                # Create failed file entity
                failed_file = await self._create_file_entity(file_path)
                failed_file.update_status(ProcessingStatus.FAILED, str(e))
                batch.add_file(failed_file)
        
        batch = await self.batch_repo.save(batch)
        return batch
    
    async def _create_file_entity(self, file_path: Path) -> FileEntity:
        """Create a file entity from a file path."""
        return FileEntity(
            original_path=file_path,
            filename=file_path.name,
            file_type=FileType.UNKNOWN
        )
    
    async def _extract_metadata(self, file_path: Path) -> FileMetadata:
        """Extract metadata from a file."""
        # This would integrate with actual metadata extraction libraries
        stat = file_path.stat()
        return FileMetadata(
            size=stat.st_size,
            mime_type="application/octet-stream",  # Would be determined by magic
            created_at=datetime.fromtimestamp(stat.st_ctime),
            modified_at=datetime.fromtimestamp(stat.st_mtime),
            checksum="",  # Would be calculated
            tags=[],
            custom_fields={}
        )
    
    def _determine_file_type(self, mime_type: str) -> FileType:
        """Determine file type from MIME type."""
        mime_to_type = {
            "application/pdf": FileType.PDF,
            "image/": FileType.IMAGE,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": FileType.DOCUMENT,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": FileType.SPREADSHEET,
            "application/vnd.openxmlformats-officedocument.presentationml.presentation": FileType.PRESENTATION,
            "application/zip": FileType.ARCHIVE,
        }
        
        for mime_pattern, file_type in mime_to_type.items():
            if mime_type.startswith(mime_pattern):
                return file_type
        
        return FileType.UNKNOWN
    
    async def _find_matching_rule(self, file_entity: FileEntity) -> Optional[SortingRule]:
        """Find a matching sorting rule for the file."""
        rules = await self.rule_repo.get_enabled()
        
        # Sort by priority (lower number = higher priority)
        rules.sort(key=lambda r: r.priority)
        
        for rule in rules:
            if self._rule_matches_file(rule, file_entity):
                return rule
        
        return None
    
    def _rule_matches_file(self, rule: SortingRule, file_entity: FileEntity) -> bool:
        """Check if a rule matches a file."""
        # Check file type
        if rule.file_types and file_entity.file_type not in rule.file_types:
            return False
        
        # Check file size
        if rule.min_size and file_entity.metadata.size < rule.min_size:
            return False
        if rule.max_size and file_entity.metadata.size > rule.max_size:
            return False
        
        # Check keywords in filename
        filename_lower = file_entity.filename.lower()
        for keyword in rule.keywords:
            if keyword.lower() in filename_lower:
                return True
        
        return False
    
    def _generate_target_path(self, rule: SortingRule, file_entity: FileEntity) -> Path:
        """Generate target path based on rule and file metadata."""
        # Simple path generation - could be more sophisticated
        base_path = Path(rule.target_path)
        
        # Add year/month if specified in target path
        if "{year}" in rule.target_path:
            year = file_entity.metadata.created_at.year if file_entity.metadata.created_at else datetime.now().year
            base_path = Path(str(base_path).replace("{year}", str(year)))
        
        if "{month}" in rule.target_path:
            month = file_entity.metadata.created_at.month if file_entity.metadata.created_at else datetime.now().month
            base_path = Path(str(base_path).replace("{month}", f"{month:02d}"))
        
        return base_path / file_entity.filename
    
    async def _publish_indexing_message(self, file_entity: FileEntity) -> None:
        """Publish a message to trigger indexing."""
        message = {
            "file_id": str(file_entity.id),
            "bucket": file_entity.bucket_name,
            "key": file_entity.object_key,
            "file_type": file_entity.file_type.value,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.message_repo.publish_message("indexing", message)


class SortingRuleService:
    """Service for managing sorting rules."""
    
    def __init__(self, rule_repo: SortingRuleRepository):
        self.rule_repo = rule_repo
    
    async def create_rule(self, rule_data: Dict[str, Any]) -> SortingRule:
        """Create a new sorting rule."""
        rule = SortingRule(**rule_data)
        return await self.rule_repo.save(rule)
    
    async def update_rule(self, rule_id: UUID, rule_data: Dict[str, Any]) -> SortingRule:
        """Update an existing sorting rule."""
        rule = await self.rule_repo.get_by_id(rule_id)
        if not rule:
            raise ValueError(f"Rule with ID {rule_id} not found")
        
        # Update fields
        for key, value in rule_data.items():
            if hasattr(rule, key):
                setattr(rule, key, value)
        
        rule.updated_at = datetime.utcnow()
        return await self.rule_repo.update(rule)
    
    async def delete_rule(self, rule_id: UUID) -> bool:
        """Delete a sorting rule."""
        return await self.rule_repo.delete(rule_id)
    
    async def get_all_rules(self) -> List[SortingRule]:
        """Get all sorting rules."""
        return await self.rule_repo.get_all()
    
    async def get_enabled_rules(self) -> List[SortingRule]:
        """Get all enabled sorting rules."""
        return await self.rule_repo.get_enabled()


class StatisticsService:
    """Service for generating processing statistics."""
    
    def __init__(self, file_repo: FileRepository, batch_repo: ProcessingBatchRepository):
        self.file_repo = file_repo
        self.batch_repo = batch_repo
    
    async def get_processing_statistics(self) -> ProcessingStatistics:
        """Get comprehensive processing statistics."""
        try:
            return await self.file_repo.get_statistics()
        except Exception as e:
            logger.error(f"Error getting processing statistics: {e}")
            # Return empty statistics on error
            return ProcessingStatistics()
    
    async def get_recent_batches(self, limit: int = 10) -> List[ProcessingBatch]:
        """Get recent processing batches."""
        try:
            return await self.batch_repo.get_recent_batches(limit)
        except Exception as e:
            logger.error(f"Error getting recent batches: {e}")
            return []
    
    async def get_files_by_status(self, status: ProcessingStatus) -> List[FileEntity]:
        """Get files by processing status."""
        try:
            return await self.file_repo.get_by_status(status.value)
        except Exception as e:
            logger.error(f"Error getting files by status: {e}")
            return [] 


@dataclass
class DuplicateDetectionResult:
    is_duplicate: bool
    existing_document_id: Optional[str] = None
    similarity_score: float = 0.0
    hash_value: str = ""

@dataclass
class LLMClassificationResult:
    category: str
    confidence: float
    customer: Optional[str] = None
    project: Optional[str] = None
    tags: List[str] = None
    metadata: Dict = None

@dataclass
class ProcessingSnapshot:
    job_id: str
    timestamp: datetime
    processed_files: List[str]
    assigned_metadata: Dict
    target_paths: List[str]
    database_entries: List[str]

class DocumentProcessingService:
    """Enhanced document processing service with duplicate detection and LLM classification"""
    
    def __init__(
        self,
        document_repo: DocumentRepository,
        storage_repo: StorageRepository,
        message_queue_repo: MessageQueueRepository,
        config_path: str = "/app/config/sorting-rules.yaml"
    ):
        self.document_repo = document_repo
        self.storage_repo = storage_repo
        self.message_queue_repo = message_queue_repo
        self.config = self._load_config(config_path)
        self.snapshots: Dict[str, ProcessingSnapshot] = {}
        
    def _load_config(self, config_path: str) -> Dict:
        """Load sorting rules configuration"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config from {config_path}: {e}")
            return {}
    
    def calculate_file_hash(self, file_path: str, algorithm: str = "sha256") -> str:
        """Calculate file hash for duplicate detection"""
        hash_func = hashlib.new(algorithm)
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_func.update(chunk)
            return hash_func.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate hash for {file_path}: {e}")
            return ""
    
    def detect_duplicates(self, file_path: str) -> DuplicateDetectionResult:
        """Detect duplicate files using hash-based comparison"""
        if not self.config.get('processing', {}).get('duplicate_detection', {}).get('enabled', True):
            return DuplicateDetectionResult(is_duplicate=False)
        
        file_hash = self.calculate_file_hash(file_path)
        if not file_hash:
            return DuplicateDetectionResult(is_duplicate=False)
        
        # Check if hash exists in database
        existing_doc = self.document_repo.find_by_hash(file_hash)
        if existing_doc:
            return DuplicateDetectionResult(
                is_duplicate=True,
                existing_document_id=existing_doc.id,
                similarity_score=1.0,
                hash_value=file_hash
            )
        
        return DuplicateDetectionResult(
            is_duplicate=False,
            hash_value=file_hash
        )
    
    def classify_with_llm(self, file_path: str, file_content: Optional[str] = None) -> LLMClassificationResult:
        """Classify document using LLM"""
        if not self.config.get('processing', {}).get('llm_classification', {}).get('enabled', True):
            return LLMClassificationResult(category="unsorted", confidence=0.0)
        
        llm_config = self.config.get('processing', {}).get('llm_classification', {})
        model = llm_config.get('model', 'mistral-7b')
        temperature = llm_config.get('temperature', 0.1)
        max_tokens = llm_config.get('max_tokens', 100)
        
        # Prepare content for classification
        content = file_content or self._extract_text_content(file_path)
        if not content:
            return LLMClassificationResult(category="unsorted", confidence=0.0)
        
        try:
            # Call LLM service (Ollama or Hugging Face)
            classification = self._call_llm_service(content, model, temperature, max_tokens)
            return classification
        except Exception as e:
            logger.error(f"LLM classification failed for {file_path}: {e}")
            return LLMClassificationResult(category="unsorted", confidence=0.0)
    
    def _call_llm_service(self, content: str, model: str, temperature: float, max_tokens: int) -> LLMClassificationResult:
        """Call LLM service for classification"""
        # Try Ollama first
        try:
            response = requests.post(
                "http://ollama:11434/api/generate",
                json={
                    "model": model,
                    "prompt": f"""Classify this document into one of these categories: finanzen, projekte, personal, footage, unsorted.
                    Also extract customer name and project name if mentioned.
                    Document content: {content[:1000]}
                    
                    Respond in JSON format:
                    {{
                        "category": "category_name",
                        "confidence": 0.95,
                        "customer": "customer_name",
                        "project": "project_name",
                        "tags": ["tag1", "tag2"]
                    }}""",
                    "temperature": temperature,
                    "max_tokens": max_tokens
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get('response', '{}')
                try:
                    classification = json.loads(response_text)
                    return LLMClassificationResult(
                        category=classification.get('category', 'unsorted'),
                        confidence=classification.get('confidence', 0.0),
                        customer=classification.get('customer'),
                        project=classification.get('project'),
                        tags=classification.get('tags', [])
                    )
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON response from LLM: {response_text}")
            
        except Exception as e:
            logger.warning(f"Ollama service unavailable: {e}")
        
        # Fallback to rule-based classification
        return self._rule_based_classification(content)
    
    def _rule_based_classification(self, content: str) -> LLMClassificationResult:
        """Fallback rule-based classification"""
        content_lower = content.lower()
        
        # Check categories
        categories = self.config.get('categories', {})
        for category_name, category_config in categories.items():
            keywords = []
            for subcategory in category_config.get('subcategories', {}).values():
                keywords.extend(subcategory.get('keywords', []))
            
            if any(keyword in content_lower for keyword in keywords):
                return LLMClassificationResult(
                    category=category_name,
                    confidence=0.7,
                    tags=[category_name]
                )
        
        return LLMClassificationResult(category="unsorted", confidence=0.0)
    
    def _extract_text_content(self, file_path: str) -> Optional[str]:
        """Extract text content from file for classification"""
        try:
            # Simple text extraction - in production, use proper OCR/text extraction
            if file_path.lower().endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return f.read()
            # Add more file type handlers here
            return None
        except Exception as e:
            logger.error(f"Failed to extract text from {file_path}: {e}")
            return None
    
    def create_processing_snapshot(self, job_id: str, files: List[str]) -> ProcessingSnapshot:
        """Create a snapshot before processing for rollback capability"""
        snapshot = ProcessingSnapshot(
            job_id=job_id,
            timestamp=datetime.now(),
            processed_files=files.copy(),
            assigned_metadata={},
            target_paths=[],
            database_entries=[]
        )
        self.snapshots[job_id] = snapshot
        return snapshot
    
    def rollback_processing(self, job_id: str) -> bool:
        """Rollback processing for a specific job"""
        if job_id not in self.snapshots:
            logger.error(f"No snapshot found for job {job_id}")
            return False
        
        snapshot = self.snapshots[job_id]
        logger.info(f"Rolling back job {job_id} with {len(snapshot.processed_files)} files")
        
        try:
            # Rollback file movements
            for file_path in snapshot.processed_files:
                if os.path.exists(file_path):
                    # Move back to original location
                    original_path = self._get_original_path(file_path)
                    if original_path and original_path != file_path:
                        shutil.move(file_path, original_path)
            
            # Rollback database entries
            for entry_id in snapshot.database_entries:
                self.document_repo.delete(entry_id)
            
            # Remove snapshot
            del self.snapshots[job_id]
            
            logger.info(f"Successfully rolled back job {job_id}")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed for job {job_id}: {e}")
            return False
    
    def _get_original_path(self, current_path: str) -> Optional[str]:
        """Get original path from backup or metadata"""
        # Implementation depends on backup strategy
        # For now, return None (no rollback)
        return None
    
    def process_document(self, file_path: str, job_id: str = None) -> ProcessingResult:
        """Process a single document with enhanced features"""
        if not os.path.exists(file_path):
            return ProcessingResult(success=False, error="File not found")
        
        try:
            # Create snapshot for rollback
            if job_id:
                self.create_processing_snapshot(job_id, [file_path])
            
            # Detect duplicates
            duplicate_result = self.detect_duplicates(file_path)
            if duplicate_result.is_duplicate:
                logger.info(f"Duplicate detected for {file_path}")
                return ProcessingResult(
                    success=True,
                    message=f"Duplicate of document {duplicate_result.existing_document_id}",
                    metadata={"duplicate": True, "existing_id": duplicate_result.existing_document_id}
                )
            
            # Classify with LLM
            classification = self.classify_with_llm(file_path)
            
            # Determine target path based on classification
            target_path = self._determine_target_path(file_path, classification)
            
            # Create backup if enabled
            if self.config.get('processing', {}).get('backup', {}).get('enabled', True):
                backup_path = self._create_backup(file_path)
            
            # Move file to target location
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            shutil.move(file_path, target_path)
            
            # Store document metadata
            document = Document(
                id=None,  # Will be set by repository
                filename=os.path.basename(file_path),
                original_path=file_path,
                target_path=target_path,
                file_hash=duplicate_result.hash_value,
                category=classification.category,
                customer=classification.customer,
                project=classification.project,
                tags=classification.tags or [],
                metadata=classification.metadata or {},
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            stored_doc = self.document_repo.save(document)
            
            # Update snapshot
            if job_id and job_id in self.snapshots:
                self.snapshots[job_id].assigned_metadata[file_path] = asdict(classification)
                self.snapshots[job_id].target_paths.append(target_path)
                self.snapshots[job_id].database_entries.append(stored_doc.id)
            
            return ProcessingResult(
                success=True,
                document_id=stored_doc.id,
                target_path=target_path,
                metadata={
                    "category": classification.category,
                    "confidence": classification.confidence,
                    "customer": classification.customer,
                    "project": classification.project,
                    "tags": classification.tags
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")
            return ProcessingResult(success=False, error=str(e))
    
    def _determine_target_path(self, file_path: str, classification: LLMClassificationResult) -> str:
        """Determine target path based on classification and rules"""
        categories = self.config.get('categories', {})
        category_config = categories.get(classification.category, {})
        
        # Get base path from category
        base_path = category_config.get('path', '/unsorted')
        
        # Add customer and project if available
        if classification.customer:
            base_path = base_path.replace('{customer}', classification.customer)
        if classification.project:
            base_path = base_path.replace('{project}', classification.project)
        
        # Add year
        current_year = datetime.now().year
        base_path = base_path.replace('{year}', str(current_year))
        
        # Add filename
        filename = os.path.basename(file_path)
        target_path = os.path.join(base_path, filename)
        
        return target_path
    
    def _create_backup(self, file_path: str) -> str:
        """Create backup of file before processing"""
        backup_config = self.config.get('processing', {}).get('backup', {})
        backup_dir = backup_config.get('path', '/backups')
        retention_days = backup_config.get('retention_days', 30)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"{timestamp}_{os.path.basename(file_path)}"
        backup_path = os.path.join(backup_dir, backup_filename)
        
        os.makedirs(backup_dir, exist_ok=True)
        shutil.copy2(file_path, backup_path)
        
        return backup_path
    
    def process_batch(self, file_paths: List[str], job_id: str = None) -> List[ProcessingResult]:
        """Process multiple documents in parallel"""
        results = []
        
        # Create snapshot for batch
        if job_id:
            self.create_processing_snapshot(job_id, file_paths)
        
        # Process files in parallel
        with ThreadPoolExecutor(max_workers=4) as executor:
            future_to_file = {
                executor.submit(self.process_document, file_path, job_id): file_path 
                for file_path in file_paths
            }
            
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Failed to process {file_path}: {e}")
                    results.append(ProcessingResult(success=False, error=str(e)))
        
        return results

class EmailProcessingService:
    """Service for processing email attachments"""
    
    def __init__(self, document_service: DocumentProcessingService):
        self.document_service = document_service
        self.config = document_service.config
    
    def process_email_attachments(self, email_data: Dict) -> List[ProcessingResult]:
        """Process email attachments according to rules"""
        results = []
        attachment_rules = self.config.get('email', {}).get('attachment_rules', [])
        
        for attachment in email_data.get('attachments', []):
            # Apply rules
            for rule in attachment_rules:
                if self._matches_rule(attachment, email_data, rule):
                    result = self._apply_rule(attachment, rule)
                    results.append(result)
                    break
            else:
                # No rule matched, use default processing
                result = self.document_service.process_document(attachment['path'])
                results.append(result)
        
        return results
    
    def _matches_rule(self, attachment: Dict, email_data: Dict, rule: Dict) -> bool:
        """Check if attachment matches a rule"""
        condition = rule.get('condition', '')
        
        if 'sender_contains:' in condition:
            keyword = condition.split('sender_contains:')[1]
            return keyword in email_data.get('sender', '')
        
        if 'subject_contains:' in condition:
            keyword = condition.split('subject_contains:')[1]
            return keyword in email_data.get('subject', '')
        
        if 'file_type:' in condition:
            file_type = condition.split('file_type:')[1]
            return attachment.get('type', '').lower() == file_type.lower()
        
        return False
    
    def _apply_rule(self, attachment: Dict, rule: Dict) -> ProcessingResult:
        """Apply rule to attachment"""
        action = rule.get('action', '')
        target_path = rule.get('target_path', '/unsorted')
        
        if action == 'classify_as_ticket':
            # Extract ticket ID from email subject or body
            ticket_id = self._extract_ticket_id(attachment)
            target_path = target_path.replace('{ticket_id}', ticket_id)
        
        elif action == 'classify_as_invoice':
            current_year = datetime.now().year
            target_path = target_path.replace('{year}', str(current_year))
        
        # Move file to target path
        source_path = attachment['path']
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        shutil.move(source_path, target_path)
        
        return ProcessingResult(
            success=True,
            target_path=target_path,
            metadata={"rule_applied": rule.get('condition', '')}
        )
    
    def _extract_ticket_id(self, attachment: Dict) -> str:
        """Extract ticket ID from attachment or email data"""
        # Implementation depends on OTRS format
        return "TICKET-001"  # Placeholder 