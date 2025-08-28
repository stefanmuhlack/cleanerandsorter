"""
Application controllers for the ingest service.
These handle HTTP requests and delegate to domain services.
"""

import logging
from pathlib import Path
from typing import List, Optional
from uuid import UUID

from app.domain.entities import FileEntity, SortingRule, ProcessingBatch, ProcessingStatistics
from app.domain.services import FileProcessingService, SortingRuleService, StatisticsService

logger = logging.getLogger(__name__)


class FileController:
    """Controller for file processing operations."""
    
    async def process_file(
        self,
        file_path: Path,
        service: FileProcessingService
    ) -> FileEntity:
        """Process a single file."""
        logger.info("Processing file", file_path=str(file_path))
        return await service.process_file(file_path)
    
    async def process_batch(
        self,
        file_paths: List[Path],
        service: FileProcessingService
    ) -> ProcessingBatch:
        """Process a batch of files."""
        logger.info("Processing batch", file_count=len(file_paths))
        return await service.process_batch(file_paths)
    
    async def get_file(
        self,
        file_id: str,
        service: FileProcessingService
    ) -> Optional[FileEntity]:
        """Get file information by ID."""
        try:
            file_uuid = UUID(file_id)
            return await service.file_repo.get_by_id(file_uuid)
        except ValueError:
            logger.error("Invalid file ID format", file_id=file_id)
            return None
    
    async def list_files(
        self,
        status: Optional[str],
        service: FileProcessingService
    ) -> List[FileEntity]:
        """List files with optional status filter."""
        if status:
            return await service.file_repo.get_by_status(status)
        else:
            return await service.file_repo.get_pending_files()


class SortingRuleController:
    """Controller for sorting rule operations."""
    
    async def create_rule(
        self,
        rule_data: dict,
        service: SortingRuleService
    ) -> SortingRule:
        """Create a new sorting rule."""
        logger.info("Creating sorting rule", rule_name=rule_data.get("name"))
        return await service.create_rule(rule_data)
    
    async def get_rule(
        self,
        rule_id: str,
        service: SortingRuleService
    ) -> Optional[SortingRule]:
        """Get a sorting rule by ID."""
        try:
            rule_uuid = UUID(rule_id)
            return await service.rule_repo.get_by_id(rule_uuid)
        except ValueError:
            logger.error("Invalid rule ID format", rule_id=rule_id)
            return None
    
    async def list_rules(self, service: SortingRuleService) -> List[SortingRule]:
        """List all sorting rules."""
        return await service.get_all_rules()
    
    async def update_rule(
        self,
        rule_id: str,
        rule_data: dict,
        service: SortingRuleService
    ) -> SortingRule:
        """Update a sorting rule."""
        try:
            rule_uuid = UUID(rule_id)
            logger.info("Updating sorting rule", rule_id=rule_id)
            return await service.update_rule(rule_uuid, rule_data)
        except ValueError:
            logger.error("Invalid rule ID format", rule_id=rule_id)
            raise ValueError("Invalid rule ID format")
    
    async def delete_rule(
        self,
        rule_id: str,
        service: SortingRuleService
    ) -> bool:
        """Delete a sorting rule."""
        try:
            rule_uuid = UUID(rule_id)
            logger.info("Deleting sorting rule", rule_id=rule_id)
            return await service.delete_rule(rule_uuid)
        except ValueError:
            logger.error("Invalid rule ID format", rule_id=rule_id)
            return False


class StatisticsController:
    """Controller for statistics operations."""
    
    async def get_statistics(
        self,
        service: StatisticsService
    ) -> ProcessingStatistics:
        """Get processing statistics."""
        return await service.get_processing_statistics()
    
    async def get_recent_batches(
        self,
        limit: int,
        service: StatisticsService
    ) -> List[ProcessingBatch]:
        """Get recent processing batches."""
        return await service.get_recent_batches(limit) 