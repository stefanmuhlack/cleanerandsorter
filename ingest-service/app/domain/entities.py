"""
Domain entities for the ingest service.
These represent the core business objects and rules.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class FileType(str, Enum):
    """Supported file types for processing."""
    PDF = "pdf"
    IMAGE = "image"
    DOCUMENT = "document"
    SPREADSHEET = "spreadsheet"
    PRESENTATION = "presentation"
    ARCHIVE = "archive"
    UNKNOWN = "unknown"


class ProcessingStatus(str, Enum):
    """Status of file processing."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class FileMetadata(BaseModel):
    """Metadata extracted from a file."""
    file_size: int
    mime_type: str
    created_date: Optional[datetime] = None
    modified_date: Optional[datetime] = None
    exif_data: Optional[Dict[str, Any]] = None
    ocr_text: Optional[str] = None
    extracted_text: Optional[str] = None
    language: Optional[str] = None
    confidence: Optional[float] = None


class SortingRule(BaseModel):
    """Rule for sorting files into categories."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    keywords: List[str]
    target_path: str
    priority: int = 100
    enabled: bool = True
    file_types: Optional[List[FileType]] = None
    min_file_size: Optional[int] = None
    max_file_size: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class FileEntity(BaseModel):
    """Core file entity representing a document in the system."""
    id: UUID = Field(default_factory=uuid4)
    original_path: Path
    filename: str
    file_type: FileType
    status: ProcessingStatus = ProcessingStatus.PENDING
    metadata: Optional[FileMetadata] = None
    sorting_rule: Optional[SortingRule] = None
    target_path: Optional[Path] = None
    bucket_name: Optional[str] = None
    object_key: Optional[str] = None
    processing_errors: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        arbitrary_types_allowed = True

    def update_status(self, status: ProcessingStatus, error_message: Optional[str] = None) -> None:
        """Update the processing status and optionally add an error message."""
        self.status = status
        self.updated_at = datetime.utcnow()
        if error_message:
            self.processing_errors.append(error_message)

    def assign_sorting_rule(self, rule: SortingRule) -> None:
        """Assign a sorting rule to this file."""
        self.sorting_rule = rule
        self.updated_at = datetime.utcnow()

    def set_target_path(self, path: Path) -> None:
        """Set the target path for the file."""
        self.target_path = path
        self.updated_at = datetime.utcnow()

    def set_storage_location(self, bucket: str, key: str) -> None:
        """Set the storage location in object storage."""
        self.bucket_name = bucket
        self.object_key = key
        self.updated_at = datetime.utcnow()


class ProcessingBatch(BaseModel):
    """Represents a batch of files being processed."""
    id: UUID = Field(default_factory=uuid4)
    files: List[FileEntity] = Field(default_factory=list)
    status: ProcessingStatus = ProcessingStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_files: int = 0
    processed_files: int = 0
    failed_files: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)

    def add_file(self, file: FileEntity) -> None:
        """Add a file to the batch."""
        self.files.append(file)
        self.total_files = len(self.files)

    def start_processing(self) -> None:
        """Mark the batch as started."""
        self.status = ProcessingStatus.PROCESSING
        self.started_at = datetime.utcnow()

    def complete_processing(self) -> None:
        """Mark the batch as completed."""
        self.status = ProcessingStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.processed_files = len([f for f in self.files if f.status == ProcessingStatus.COMPLETED])
        self.failed_files = len([f for f in self.files if f.status == ProcessingStatus.FAILED])

    def fail_processing(self, error_message: str) -> None:
        """Mark the batch as failed."""
        self.status = ProcessingStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.failed_files = self.total_files


class ProcessingStatistics(BaseModel):
    """Statistics about file processing."""
    total_files_processed: int = 0
    successful_files: int = 0
    failed_files: int = 0
    skipped_files: int = 0
    total_processing_time: float = 0.0
    average_processing_time: float = 0.0
    files_by_type: Dict[FileType, int] = Field(default_factory=dict)
    files_by_status: Dict[ProcessingStatus, int] = Field(default_factory=dict)
    last_processed_at: Optional[datetime] = None 