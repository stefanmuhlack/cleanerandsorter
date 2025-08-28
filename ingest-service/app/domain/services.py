"""
Domain services for the ingest service.
These contain the core business logic and orchestrate operations.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from uuid import UUID

from .entities import (
    FileEntity, SortingRule, ProcessingBatch, ProcessingStatistics,
    FileType, ProcessingStatus, FileMetadata
)
from .repositories import (
    FileRepository, SortingRuleRepository, ProcessingBatchRepository,
    ObjectStorageRepository, MessageQueueRepository
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
            file_size=stat.st_size,
            mime_type="application/octet-stream",  # Would be determined by magic
            created_date=datetime.fromtimestamp(stat.st_ctime),
            modified_date=datetime.fromtimestamp(stat.st_mtime)
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
        rules = await self.rule_repo.get_enabled_rules()
        
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
        if rule.min_file_size and file_entity.metadata.file_size < rule.min_file_size:
            return False
        if rule.max_file_size and file_entity.metadata.file_size > rule.max_file_size:
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
            year = file_entity.metadata.created_date.year if file_entity.metadata.created_date else datetime.now().year
            base_path = Path(str(base_path).replace("{year}", str(year)))
        
        if "{month}" in rule.target_path:
            month = file_entity.metadata.created_date.month if file_entity.metadata.created_date else datetime.now().month
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
        return await self.rule_repo.get_enabled_rules()


class StatisticsService:
    """Service for generating processing statistics."""
    
    def __init__(self, file_repo: FileRepository, batch_repo: ProcessingBatchRepository):
        self.file_repo = file_repo
        self.batch_repo = batch_repo
    
    async def get_processing_statistics(self) -> ProcessingStatistics:
        """Get comprehensive processing statistics."""
        return await self.file_repo.get_statistics()
    
    async def get_recent_batches(self, limit: int = 10) -> List[ProcessingBatch]:
        """Get recent processing batches."""
        return await self.batch_repo.get_recent_batches(limit)
    
    async def get_files_by_status(self, status: ProcessingStatus) -> List[FileEntity]:
        """Get files by processing status."""
        return await self.file_repo.get_by_status(status.value) 