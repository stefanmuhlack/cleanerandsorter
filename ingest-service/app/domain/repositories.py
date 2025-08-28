"""
Repository interfaces for the ingest service.
These define the contracts for data access operations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Protocol
from uuid import UUID

from .entities import FileEntity, SortingRule, ProcessingBatch, ProcessingStatistics


class FileRepository(Protocol):
    """Repository interface for file operations."""
    
    async def save(self, file: FileEntity) -> FileEntity:
        """Save a file entity."""
        ...
    
    async def get_by_id(self, file_id: UUID) -> Optional[FileEntity]:
        """Get a file by its ID."""
        ...
    
    async def get_by_status(self, status: str) -> List[FileEntity]:
        """Get files by processing status."""
        ...
    
    async def get_pending_files(self) -> List[FileEntity]:
        """Get all pending files."""
        ...
    
    async def update_status(self, file_id: UUID, status: str, error_message: Optional[str] = None) -> bool:
        """Update the status of a file."""
        ...
    
    async def delete(self, file_id: UUID) -> bool:
        """Delete a file entity."""
        ...
    
    async def get_statistics(self) -> ProcessingStatistics:
        """Get processing statistics."""
        ...


class SortingRuleRepository(Protocol):
    """Repository interface for sorting rule operations."""
    
    async def save(self, rule: SortingRule) -> SortingRule:
        """Save a sorting rule."""
        ...
    
    async def get_by_id(self, rule_id: UUID) -> Optional[SortingRule]:
        """Get a sorting rule by its ID."""
        ...
    
    async def get_all(self) -> List[SortingRule]:
        """Get all sorting rules."""
        ...
    
    async def get_enabled_rules(self) -> List[SortingRule]:
        """Get all enabled sorting rules."""
        ...
    
    async def update(self, rule: SortingRule) -> SortingRule:
        """Update a sorting rule."""
        ...
    
    async def delete(self, rule_id: UUID) -> bool:
        """Delete a sorting rule."""
        ...


class ProcessingBatchRepository(Protocol):
    """Repository interface for processing batch operations."""
    
    async def save(self, batch: ProcessingBatch) -> ProcessingBatch:
        """Save a processing batch."""
        ...
    
    async def get_by_id(self, batch_id: UUID) -> Optional[ProcessingBatch]:
        """Get a processing batch by its ID."""
        ...
    
    async def get_active_batches(self) -> List[ProcessingBatch]:
        """Get all active processing batches."""
        ...
    
    async def update_status(self, batch_id: UUID, status: str) -> bool:
        """Update the status of a batch."""
        ...
    
    async def get_recent_batches(self, limit: int = 10) -> List[ProcessingBatch]:
        """Get recent processing batches."""
        ...


class ObjectStorageRepository(Protocol):
    """Repository interface for object storage operations."""
    
    async def upload_file(self, file_path: str, bucket: str, key: str) -> bool:
        """Upload a file to object storage."""
        ...
    
    async def download_file(self, bucket: str, key: str, local_path: str) -> bool:
        """Download a file from object storage."""
        ...
    
    async def delete_file(self, bucket: str, key: str) -> bool:
        """Delete a file from object storage."""
        ...
    
    async def file_exists(self, bucket: str, key: str) -> bool:
        """Check if a file exists in object storage."""
        ...
    
    async def get_file_url(self, bucket: str, key: str, expires_in: int = 3600) -> str:
        """Get a presigned URL for a file."""
        ...
    
    async def list_files(self, bucket: str, prefix: str = "") -> List[str]:
        """List files in a bucket with optional prefix."""
        ...


class MessageQueueRepository(Protocol):
    """Repository interface for message queue operations."""
    
    async def publish_message(self, queue: str, message: dict) -> bool:
        """Publish a message to a queue."""
        ...
    
    async def consume_messages(self, queue: str, callback) -> None:
        """Consume messages from a queue."""
        ...
    
    async def acknowledge_message(self, delivery_tag: int) -> bool:
        """Acknowledge a processed message."""
        ...
    
    async def reject_message(self, delivery_tag: int, requeue: bool = True) -> bool:
        """Reject a message."""
        ...
    
    async def get_queue_length(self, queue: str) -> int:
        """Get the number of messages in a queue."""
        ... 