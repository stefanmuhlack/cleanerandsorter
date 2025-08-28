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
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

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

@dataclass
class ProcessingStatistics:
    """Processing statistics."""
    total_files: int = 0
    processed_files: int = 0
    failed_files: int = 0
    duplicate_files: int = 0
    total_size: int = 0
    processing_time: float = 0.0
    average_processing_time: float = 0.0

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