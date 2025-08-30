"""
Domain entities for the ingest service.
These represent the core business objects and rules.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class FileType(Enum):
    """File type enumeration."""
    DOCUMENT = "document"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    ARCHIVE = "archive"
    SPREADSHEET = "spreadsheet"
    PRESENTATION = "presentation"
    UNKNOWN = "unknown"

class ProcessingStatus(Enum):
    """Processing status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DUPLICATE = "duplicate"

@dataclass
class FileMetadata:
    """File metadata information."""
    size: int
    mime_type: str
    created_at: datetime
    modified_at: datetime
    checksum: str
    tags: List[str] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    def dict(self):
        """Convert to dictionary."""
        return {
            "size": self.size,
            "mime_type": self.mime_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "modified_at": self.modified_at.isoformat() if self.modified_at else None,
            "checksum": self.checksum,
            "tags": self.tags,
            "custom_fields": self.custom_fields
        }

@dataclass
class FileEntity:
    """File entity for processing."""
    id: Optional[UUID] = None
    filename: str = ""
    original_path: str = ""
    target_path: str = ""
    file_type: FileType = FileType.UNKNOWN
    status: ProcessingStatus = ProcessingStatus.PENDING
    metadata: FileMetadata = field(default_factory=FileMetadata)
    sorting_rule: Optional['SortingRule'] = None
    bucket_name: Optional[str] = None
    object_key: Optional[str] = None
    processing_errors: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def dict(self):
        """Convert to dictionary."""
        return {
            "id": str(self.id) if self.id else None,
            "filename": self.filename,
            "original_path": self.original_path,
            "target_path": self.target_path,
            "file_type": self.file_type.value if self.file_type else None,
            "status": self.status.value if self.status else None,
            "metadata": self.metadata.dict() if self.metadata else None,
            "sorting_rule": self.sorting_rule.dict() if self.sorting_rule else None,
            "bucket_name": self.bucket_name,
            "object_key": self.object_key,
            "processing_errors": self.processing_errors,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def assign_sorting_rule(self, rule: 'SortingRule'):
        """Assign a sorting rule to this file."""
        self.sorting_rule = rule
    
    def set_target_path(self, target_path: str):
        """Set the target path for this file."""
        self.target_path = target_path
    
    def set_storage_location(self, bucket: str, key: str):
        """Set the storage location for this file."""
        self.bucket_name = bucket
        self.object_key = key
    
    def update_status(self, status: ProcessingStatus, error_message: str = None):
        """Update the processing status."""
        self.status = status
        if error_message:
            if not hasattr(self, 'processing_errors'):
                self.processing_errors = []
            self.processing_errors.append(error_message)

@dataclass
class SortingRule:
    """Sorting rule configuration."""
    id: Optional[UUID] = None
    name: str = ""
    description: str = ""
    priority: int = 50
    enabled: bool = True
    keywords: List[str] = field(default_factory=list)
    file_types: List[str] = field(default_factory=list)
    target_path: str = ""
    min_size: Optional[int] = None
    max_size: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def dict(self):
        """Convert to dictionary."""
        return {
            "id": str(self.id) if self.id else None,
            "name": self.name,
            "description": self.description,
            "priority": self.priority,
            "enabled": self.enabled,
            "keywords": self.keywords,
            "file_types": self.file_types,
            "target_path": self.target_path,
            "min_size": self.min_size,
            "max_size": self.max_size,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

@dataclass
class ProcessingBatch:
    """Processing batch information."""
    id: Optional[UUID] = None
    name: str = ""
    description: str = ""
    files: List[FileEntity] = field(default_factory=list)
    status: ProcessingStatus = ProcessingStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    
    def dict(self):
        """Convert to dictionary."""
        return {
            "id": str(self.id) if self.id else None,
            "name": self.name,
            "description": self.description,
            "files": [f.dict() for f in self.files],
            "status": self.status.value if self.status else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
    
    def add_file(self, file_entity: FileEntity):
        """Add a file to this batch."""
        self.files.append(file_entity)

@dataclass
class ProcessingStatistics:
    """Processing statistics."""
    total_files_processed: int = 0
    successful_files: int = 0
    failed_files: int = 0
    skipped_files: int = 0
    files_by_status: Dict[str, int] = field(default_factory=dict)
    files_by_type: Dict[str, int] = field(default_factory=dict)
    
    def dict(self):
        """Convert to dictionary."""
        return {
            "total_files_processed": self.total_files_processed,
            "successful_files": self.successful_files,
            "failed_files": self.failed_files,
            "skipped_files": self.skipped_files,
            "files_by_status": self.files_by_status,
            "files_by_type": self.files_by_type
        }

# New entities for enhanced document processing

@dataclass
class Document:
    """Document entity with enhanced metadata."""
    id: Optional[str] = None
    filename: str = ""
    original_path: str = ""
    target_path: str = ""
    file_hash: str = ""
    category: str = ""
    customer: Optional[str] = None
    project: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class ProcessingResult:
    """Result of document processing."""
    success: bool
    document_id: Optional[str] = None
    target_path: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ClassificationResult:
    """Result of document classification."""
    category: str
    confidence: float
    customer: Optional[str] = None
    project: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class EmailData:
    """Email data for processing attachments."""
    id: str = ""
    sender: str = ""
    recipient: str = ""
    subject: str = ""
    body: str = ""
    received_at: datetime = field(default_factory=datetime.now)
    attachments: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class TicketData:
    """OTRS ticket data."""
    ticket_id: str = ""
    customer: str = ""
    subject: str = ""
    status: str = ""
    priority: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    attachments: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class BackupInfo:
    """Backup information."""
    id: str = ""
    original_path: str = ""
    backup_path: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    size: int = 0
    checksum: str = ""

@dataclass
class ProcessingJob:
    """Processing job information."""
    id: str = ""
    name: str = ""
    description: str = ""
    source_path: str = ""
    target_path: str = ""
    status: str = "pending"
    files_to_process: List[str] = field(default_factory=list)
    processed_files: List[str] = field(default_factory=list)
    failed_files: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class RollbackInfo:
    """Rollback information."""
    job_id: str = ""
    snapshot_id: str = ""
    original_files: List[str] = field(default_factory=list)
    moved_files: List[str] = field(default_factory=list)
    database_entries: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    executed_at: Optional[datetime] = None 