"""
Repository interfaces for the ingest service.
These define the contracts for data access operations.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from .entities import (
    FileEntity, SortingRule, ProcessingBatch, ProcessingStatistics,
    FileType, ProcessingStatus, FileMetadata, Document, ProcessingResult,
    EmailData, TicketData, BackupInfo, ProcessingJob, RollbackInfo
)

class FileRepository(ABC):
    """Abstract base class for file repository operations."""
    
    @abstractmethod
    async def save(self, file: FileEntity) -> FileEntity:
        """Save a file entity."""
        pass
    
    @abstractmethod
    async def get_by_id(self, file_id: str) -> Optional[FileEntity]:
        """Get a file by ID."""
        pass
    
    @abstractmethod
    async def get_by_status(self, status: ProcessingStatus) -> List[FileEntity]:
        """Get files by processing status."""
        pass
    
    @abstractmethod
    async def update_status(self, file_id: str, status: ProcessingStatus) -> bool:
        """Update file processing status."""
        pass
    
    @abstractmethod
    async def delete(self, file_id: str) -> bool:
        """Delete a file entity."""
        pass

class SortingRuleRepository(ABC):
    """Abstract base class for sorting rule repository operations."""
    
    @abstractmethod
    async def save(self, rule: SortingRule) -> SortingRule:
        """Save a sorting rule."""
        pass
    
    @abstractmethod
    async def get_by_id(self, rule_id: str) -> Optional[SortingRule]:
        """Get a sorting rule by ID."""
        pass
    
    @abstractmethod
    async def get_all(self) -> List[SortingRule]:
        """Get all sorting rules."""
        pass
    
    @abstractmethod
    async def get_enabled(self) -> List[SortingRule]:
        """Get all enabled sorting rules."""
        pass
    
    @abstractmethod
    async def delete(self, rule_id: str) -> bool:
        """Delete a sorting rule."""
        pass

class ProcessingBatchRepository(ABC):
    """Abstract base class for processing batch repository operations."""
    
    @abstractmethod
    async def save(self, batch: ProcessingBatch) -> ProcessingBatch:
        """Save a processing batch."""
        pass
    
    @abstractmethod
    async def get_by_id(self, batch_id: str) -> Optional[ProcessingBatch]:
        """Get a processing batch by ID."""
        pass
    
    @abstractmethod
    async def get_by_status(self, status: ProcessingStatus) -> List[ProcessingBatch]:
        """Get processing batches by status."""
        pass
    
    @abstractmethod
    async def update_status(self, batch_id: str, status: ProcessingStatus) -> bool:
        """Update processing batch status."""
        pass

class ObjectStorageRepository(ABC):
    """Abstract base class for object storage operations."""
    
    @abstractmethod
    async def upload_file(self, file_path: str, bucket: str, key: str) -> bool:
        """Upload a file to object storage."""
        pass
    
    @abstractmethod
    async def download_file(self, bucket: str, key: str, local_path: str) -> bool:
        """Download a file from object storage."""
        pass
    
    @abstractmethod
    async def delete_file(self, bucket: str, key: str) -> bool:
        """Delete a file from object storage."""
        pass
    
    @abstractmethod
    async def file_exists(self, bucket: str, key: str) -> bool:
        """Check if a file exists in object storage."""
        pass

class MessageQueueRepository(ABC):
    """Abstract base class for message queue operations."""
    
    @abstractmethod
    async def publish_message(self, queue: str, message: Dict[str, Any]) -> bool:
        """Publish a message to a queue."""
        pass
    
    @abstractmethod
    async def consume_message(self, queue: str) -> Optional[Dict[str, Any]]:
        """Consume a message from a queue."""
        pass
    
    @abstractmethod
    async def acknowledge_message(self, queue: str, message_id: str) -> bool:
        """Acknowledge a processed message."""
        pass

# New repository interfaces for enhanced features

class DocumentRepository(ABC):
    """Abstract base class for document repository operations."""
    
    @abstractmethod
    async def save(self, document: Document) -> Document:
        """Save a document."""
        pass
    
    @abstractmethod
    async def get_by_id(self, document_id: str) -> Optional[Document]:
        """Get a document by ID."""
        pass
    
    @abstractmethod
    async def find_by_hash(self, file_hash: str) -> Optional[Document]:
        """Find a document by file hash."""
        pass
    
    @abstractmethod
    async def get_by_category(self, category: str) -> List[Document]:
        """Get documents by category."""
        pass
    
    @abstractmethod
    async def get_by_customer(self, customer: str) -> List[Document]:
        """Get documents by customer."""
        pass
    
    @abstractmethod
    async def get_by_project(self, project: str) -> List[Document]:
        """Get documents by project."""
        pass
    
    @abstractmethod
    async def search(self, query: str) -> List[Document]:
        """Search documents by text query."""
        pass
    
    @abstractmethod
    async def update(self, document: Document) -> Document:
        """Update a document."""
        pass
    
    @abstractmethod
    async def delete(self, document_id: str) -> bool:
        """Delete a document."""
        pass

class StorageRepository(ABC):
    """Abstract base class for file system storage operations."""
    
    @abstractmethod
    async def move_file(self, source_path: str, target_path: str) -> bool:
        """Move a file from source to target path."""
        pass
    
    @abstractmethod
    async def copy_file(self, source_path: str, target_path: str) -> bool:
        """Copy a file from source to target path."""
        pass
    
    @abstractmethod
    async def delete_file(self, file_path: str) -> bool:
        """Delete a file."""
        pass
    
    @abstractmethod
    async def file_exists(self, file_path: str) -> bool:
        """Check if a file exists."""
        pass
    
    @abstractmethod
    async def get_file_size(self, file_path: str) -> int:
        """Get file size in bytes."""
        pass
    
    @abstractmethod
    async def create_directory(self, directory_path: str) -> bool:
        """Create a directory."""
        pass
    
    @abstractmethod
    async def list_files(self, directory_path: str, pattern: str = "*") -> List[str]:
        """List files in a directory matching a pattern."""
        pass

class EmailRepository(ABC):
    """Abstract base class for email processing operations."""
    
    @abstractmethod
    async def fetch_emails(self, account_name: str) -> List[EmailData]:
        """Fetch emails from an IMAP account."""
        pass
    
    @abstractmethod
    async def download_attachments(self, email: EmailData, target_dir: str) -> List[str]:
        """Download email attachments to target directory."""
        pass
    
    @abstractmethod
    async def mark_as_read(self, email_id: str, account_name: str) -> bool:
        """Mark an email as read."""
        pass
    
    @abstractmethod
    async def move_email(self, email_id: str, account_name: str, folder: str) -> bool:
        """Move an email to a different folder."""
        pass

class TicketRepository(ABC):
    """Abstract base class for OTRS ticket operations."""
    
    @abstractmethod
    async def get_tickets(self, filters: Dict[str, Any] = None) -> List[TicketData]:
        """Get tickets from OTRS system."""
        pass
    
    @abstractmethod
    async def get_ticket_attachments(self, ticket_id: str) -> List[Dict[str, Any]]:
        """Get attachments for a specific ticket."""
        pass
    
    @abstractmethod
    async def download_attachment(self, ticket_id: str, attachment_id: str, target_path: str) -> bool:
        """Download a ticket attachment."""
        pass
    
    @abstractmethod
    async def update_ticket_status(self, ticket_id: str, status: str) -> bool:
        """Update ticket status."""
        pass

class BackupRepository(ABC):
    """Abstract base class for backup operations."""
    
    @abstractmethod
    async def create_backup(self, file_path: str, backup_dir: str) -> BackupInfo:
        """Create a backup of a file."""
        pass
    
    @abstractmethod
    async def restore_backup(self, backup_info: BackupInfo, target_path: str) -> bool:
        """Restore a file from backup."""
        pass
    
    @abstractmethod
    async def list_backups(self, backup_dir: str) -> List[BackupInfo]:
        """List all backups in a directory."""
        pass
    
    @abstractmethod
    async def cleanup_old_backups(self, backup_dir: str, retention_days: int) -> int:
        """Clean up old backups based on retention policy."""
        pass

class ProcessingJobRepository(ABC):
    """Abstract base class for processing job operations."""
    
    @abstractmethod
    async def save(self, job: ProcessingJob) -> ProcessingJob:
        """Save a processing job."""
        pass
    
    @abstractmethod
    async def get_by_id(self, job_id: str) -> Optional[ProcessingJob]:
        """Get a processing job by ID."""
        pass
    
    @abstractmethod
    async def get_by_status(self, status: str) -> List[ProcessingJob]:
        """Get processing jobs by status."""
        pass
    
    @abstractmethod
    async def update_status(self, job_id: str, status: str) -> bool:
        """Update processing job status."""
        pass
    
    @abstractmethod
    async def add_processed_file(self, job_id: str, file_path: str) -> bool:
        """Add a processed file to a job."""
        pass
    
    @abstractmethod
    async def add_failed_file(self, job_id: str, file_path: str) -> bool:
        """Add a failed file to a job."""
        pass

class RollbackRepository(ABC):
    """Abstract base class for rollback operations."""
    
    @abstractmethod
    async def save_rollback_info(self, rollback_info: RollbackInfo) -> RollbackInfo:
        """Save rollback information."""
        pass
    
    @abstractmethod
    async def get_rollback_info(self, job_id: str) -> Optional[RollbackInfo]:
        """Get rollback information for a job."""
        pass
    
    @abstractmethod
    async def execute_rollback(self, job_id: str) -> bool:
        """Execute a rollback for a job."""
        pass
    
    @abstractmethod
    async def list_available_rollbacks(self) -> List[RollbackInfo]:
        """List all available rollbacks."""
        pass 