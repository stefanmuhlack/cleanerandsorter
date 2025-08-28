"""
SQLAlchemy database models for the ingest service.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class FileModel(Base):
    """Database model for files."""
    __tablename__ = "files"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True)
    original_path = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    file_type = Column(String, nullable=False)
    status = Column(String, nullable=False, default="pending")
    file_metadata = Column(JSON, nullable=True)
    sorting_rule_id = Column(PostgresUUID(as_uuid=True), ForeignKey("sorting_rules.id"), nullable=True)
    target_path = Column(String, nullable=True)
    bucket_name = Column(String, nullable=True)
    object_key = Column(String, nullable=True)
    processing_errors = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sorting_rule = relationship("SortingRuleModel", back_populates="files")


class SortingRuleModel(Base):
    """Database model for sorting rules."""
    __tablename__ = "sorting_rules"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True)
    name = Column(String, nullable=False)
    keywords = Column(JSON, nullable=False)
    target_path = Column(String, nullable=False)
    priority = Column(Integer, default=100)
    enabled = Column(Boolean, default=True)
    file_types = Column(JSON, nullable=True)
    min_file_size = Column(Integer, nullable=True)
    max_file_size = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    files = relationship("FileModel", back_populates="sorting_rule")


class ProcessingBatchModel(Base):
    """Database model for processing batches."""
    __tablename__ = "processing_batches"
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True)
    status = Column(String, nullable=False, default="pending")
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    total_files = Column(Integer, default=0)
    processed_files = Column(Integer, default=0)
    failed_files = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow) 