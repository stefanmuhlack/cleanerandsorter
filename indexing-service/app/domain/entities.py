"""
Domain entities for the indexing service.
These represent the core business objects for file indexing.
"""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class IndexingStatus(str, Enum):
    """Status of file indexing."""
    PENDING = "pending"
    INDEXING = "indexing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class IndexingPriority(str, Enum):
    """Priority levels for indexing."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class IndexedFile(BaseModel):
    """Represents an indexed file in the system."""
    id: UUID = Field(default_factory=uuid4)
    file_path: Path
    filename: str
    file_size: int
    mime_type: str
    file_type: str
    content_hash: str
    extracted_text: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    indexing_status: IndexingStatus = IndexingStatus.PENDING
    priority: IndexingPriority = IndexingPriority.NORMAL
    processing_errors: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    indexed_at: Optional[datetime] = None

    class Config:
        arbitrary_types_allowed = True

    def update_status(self, status: IndexingStatus, error_message: Optional[str] = None) -> None:
        """Update the indexing status and optionally add an error message."""
        self.indexing_status = status
        self.updated_at = datetime.utcnow()
        if status == IndexingStatus.COMPLETED:
            self.indexed_at = datetime.utcnow()
        if error_message:
            self.processing_errors.append(error_message)

    def add_tag(self, tag: str) -> None:
        """Add a tag to the file."""
        if tag not in self.tags:
            self.tags.append(tag)
            self.updated_at = datetime.utcnow()

    def add_metadata(self, key: str, value: Any) -> None:
        """Add metadata to the file."""
        self.metadata[key] = value
        self.updated_at = datetime.utcnow()


class IndexingBatch(BaseModel):
    """Represents a batch of files being indexed."""
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: Optional[str] = None
    file_count: int = 0
    processed_count: int = 0
    failed_count: int = 0
    status: IndexingStatus = IndexingStatus.PENDING
    priority: IndexingPriority = IndexingPriority.NORMAL
    source_path: Path
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    processing_errors: List[str] = Field(default_factory=list)

    class Config:
        arbitrary_types_allowed = True

    def start_processing(self) -> None:
        """Mark the batch as started."""
        self.status = IndexingStatus.INDEXING
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def complete_processing(self) -> None:
        """Mark the batch as completed."""
        self.status = IndexingStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def fail_processing(self, error_message: str) -> None:
        """Mark the batch as failed."""
        self.status = IndexingStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        self.processing_errors.append(error_message)

    def increment_processed(self) -> None:
        """Increment the processed count."""
        self.processed_count += 1
        self.updated_at = datetime.utcnow()

    def increment_failed(self) -> None:
        """Increment the failed count."""
        self.failed_count += 1
        self.updated_at = datetime.utcnow()


class IndexingStatistics(BaseModel):
    """Statistics about indexing operations."""
    total_files_indexed: int = 0
    total_files_failed: int = 0
    total_batches_processed: int = 0
    average_indexing_time_seconds: float = 0.0
    files_by_type: Dict[str, int] = Field(default_factory=dict)
    files_by_status: Dict[str, int] = Field(default_factory=dict)
    top_tags: List[Dict[str, Any]] = Field(default_factory=list)
    storage_usage_bytes: int = 0
    last_indexing_run: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow) 