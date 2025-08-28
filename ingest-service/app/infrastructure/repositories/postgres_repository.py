"""
PostgreSQL repository implementations for the ingest service.
"""

import json
import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

import asyncpg
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.domain.entities import (
    FileEntity, SortingRule, ProcessingBatch, ProcessingStatistics,
    ProcessingStatus, FileType
)
from app.domain.repositories import (
    FileRepository, SortingRuleRepository, ProcessingBatchRepository
)
from app.infrastructure.models import (
    FileModel, SortingRuleModel, ProcessingBatchModel
)

logger = logging.getLogger(__name__)


class PostgresFileRepository(FileRepository):
    """PostgreSQL implementation of FileRepository."""
    
    def __init__(self, session_factory: sessionmaker):
        self.session_factory = session_factory
    
    async def save(self, file: FileEntity) -> FileEntity:
        """Save a file entity."""
        async with self.session_factory() as session:
            # Convert entity to model
            file_model = FileModel(
                id=file.id,
                original_path=str(file.original_path),
                filename=file.filename,
                file_type=file.file_type.value,
                status=file.status.value,
                                   file_metadata=file.metadata.dict() if file.metadata else None,
                sorting_rule_id=file.sorting_rule.id if file.sorting_rule else None,
                target_path=str(file.target_path) if file.target_path else None,
                bucket_name=file.bucket_name,
                object_key=file.object_key,
                processing_errors=file.processing_errors,
                created_at=file.created_at,
                updated_at=file.updated_at
            )
            
            session.add(file_model)
            await session.commit()
            await session.refresh(file_model)
            
            return self._model_to_entity(file_model)
    
    async def get_by_id(self, file_id: UUID) -> Optional[FileEntity]:
        """Get a file by its ID."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(FileModel).where(FileModel.id == file_id)
            )
            file_model = result.scalar_one_or_none()
            
            if file_model:
                return self._model_to_entity(file_model)
            return None
    
    async def get_by_status(self, status: str) -> List[FileEntity]:
        """Get files by processing status."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(FileModel).where(FileModel.status == status)
            )
            file_models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in file_models]
    
    async def get_pending_files(self) -> List[FileEntity]:
        """Get all pending files."""
        return await self.get_by_status(ProcessingStatus.PENDING.value)
    
    async def update_status(self, file_id: UUID, status: str, error_message: Optional[str] = None) -> bool:
        """Update the status of a file."""
        async with self.session_factory() as session:
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow()
            }
            
            if error_message:
                # Get current errors and append new one
                result = await session.execute(
                    select(FileModel.processing_errors).where(FileModel.id == file_id)
                )
                current_errors = result.scalar_one_or_none()
                if current_errors:
                    current_errors.append(error_message)
                    update_data["processing_errors"] = current_errors
                else:
                    update_data["processing_errors"] = [error_message]
            
            result = await session.execute(
                update(FileModel)
                .where(FileModel.id == file_id)
                .values(**update_data)
            )
            
            await session.commit()
            return result.rowcount > 0
    
    async def delete(self, file_id: UUID) -> bool:
        """Delete a file entity."""
        async with self.session_factory() as session:
            result = await session.execute(
                delete(FileModel).where(FileModel.id == file_id)
            )
            await session.commit()
            return result.rowcount > 0
    
    async def get_statistics(self) -> ProcessingStatistics:
        """Get processing statistics."""
        async with self.session_factory() as session:
            # Get total files
            total_result = await session.execute(select(FileModel.id))
            total_files = len(total_result.scalars().all())
            
            # Get files by status
            status_result = await session.execute(
                select(FileModel.status, FileModel.id)
            )
            status_counts = {}
            for status, _ in status_result:
                status_counts[status] = status_counts.get(status, 0) + 1
            
            # Get files by type
            type_result = await session.execute(
                select(FileModel.file_type, FileModel.id)
            )
            type_counts = {}
            for file_type, _ in type_result:
                type_counts[file_type] = type_counts.get(file_type, 0) + 1
            
            return ProcessingStatistics(
                total_files_processed=total_files,
                successful_files=status_counts.get(ProcessingStatus.COMPLETED.value, 0),
                failed_files=status_counts.get(ProcessingStatus.FAILED.value, 0),
                skipped_files=status_counts.get(ProcessingStatus.SKIPPED.value, 0),
                files_by_status=status_counts,
                files_by_type=type_counts
            )
    
    def _model_to_entity(self, model: FileModel) -> FileEntity:
        """Convert database model to domain entity."""
        from app.domain.entities import FileMetadata
        
        metadata = None
        if model.file_metadata:
            metadata = FileMetadata(**model.file_metadata)
        
        return FileEntity(
            id=model.id,
            original_path=model.original_path,
            filename=model.filename,
            file_type=FileType(model.file_type),
            status=ProcessingStatus(model.status),
            metadata=metadata,
            sorting_rule=None,  # Would need to be loaded separately
            target_path=model.target_path,
            bucket_name=model.bucket_name,
            object_key=model.object_key,
            processing_errors=model.processing_errors or [],
            created_at=model.created_at,
            updated_at=model.updated_at
        )


class PostgresSortingRuleRepository(SortingRuleRepository):
    """PostgreSQL implementation of SortingRuleRepository."""
    
    def __init__(self, session_factory: sessionmaker):
        self.session_factory = session_factory
    
    async def save(self, rule: SortingRule) -> SortingRule:
        """Save a sorting rule."""
        async with self.session_factory() as session:
            rule_model = SortingRuleModel(
                id=rule.id,
                name=rule.name,
                keywords=rule.keywords,
                target_path=rule.target_path,
                priority=rule.priority,
                enabled=rule.enabled,
                file_types=[ft.value for ft in rule.file_types] if rule.file_types else None,
                min_file_size=rule.min_file_size,
                max_file_size=rule.max_file_size,
                created_at=rule.created_at,
                updated_at=rule.updated_at
            )
            
            session.add(rule_model)
            await session.commit()
            await session.refresh(rule_model)
            
            return self._model_to_entity(rule_model)
    
    async def get_by_id(self, rule_id: UUID) -> Optional[SortingRule]:
        """Get a sorting rule by its ID."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(SortingRuleModel).where(SortingRuleModel.id == rule_id)
            )
            rule_model = result.scalar_one_or_none()
            
            if rule_model:
                return self._model_to_entity(rule_model)
            return None
    
    async def get_all(self) -> List[SortingRule]:
        """Get all sorting rules."""
        async with self.session_factory() as session:
            result = await session.execute(select(SortingRuleModel))
            rule_models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in rule_models]
    
    async def get_enabled_rules(self) -> List[SortingRule]:
        """Get all enabled sorting rules."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(SortingRuleModel).where(SortingRuleModel.enabled == True)
            )
            rule_models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in rule_models]
    
    async def update(self, rule: SortingRule) -> SortingRule:
        """Update a sorting rule."""
        async with self.session_factory() as session:
            result = await session.execute(
                update(SortingRuleModel)
                .where(SortingRuleModel.id == rule.id)
                .values(
                    name=rule.name,
                    keywords=rule.keywords,
                    target_path=rule.target_path,
                    priority=rule.priority,
                    enabled=rule.enabled,
                    file_types=[ft.value for ft in rule.file_types] if rule.file_types else None,
                    min_file_size=rule.min_file_size,
                    max_file_size=rule.max_file_size,
                    updated_at=rule.updated_at
                )
            )
            
            await session.commit()
            
            # Get updated rule
            return await self.get_by_id(rule.id)
    
    async def delete(self, rule_id: UUID) -> bool:
        """Delete a sorting rule."""
        async with self.session_factory() as session:
            result = await session.execute(
                delete(SortingRuleModel).where(SortingRuleModel.id == rule_id)
            )
            await session.commit()
            return result.rowcount > 0
    
    def _model_to_entity(self, model: SortingRuleModel) -> SortingRule:
        """Convert database model to domain entity."""
        file_types = None
        if model.file_types:
            file_types = [FileType(ft) for ft in model.file_types]
        
        return SortingRule(
            id=model.id,
            name=model.name,
            keywords=model.keywords,
            target_path=model.target_path,
            priority=model.priority,
            enabled=model.enabled,
            file_types=file_types,
            min_file_size=model.min_file_size,
            max_file_size=model.max_file_size,
            created_at=model.created_at,
            updated_at=model.updated_at
        )


class PostgresProcessingBatchRepository(ProcessingBatchRepository):
    """PostgreSQL implementation of ProcessingBatchRepository."""
    
    def __init__(self, session_factory: sessionmaker):
        self.session_factory = session_factory
    
    async def save(self, batch: ProcessingBatch) -> ProcessingBatch:
        """Save a processing batch."""
        async with self.session_factory() as session:
            batch_model = ProcessingBatchModel(
                id=batch.id,
                status=batch.status.value,
                started_at=batch.started_at,
                completed_at=batch.completed_at,
                total_files=batch.total_files,
                processed_files=batch.processed_files,
                failed_files=batch.failed_files,
                created_at=batch.created_at
            )
            
            session.add(batch_model)
            await session.commit()
            await session.refresh(batch_model)
            
            return self._model_to_entity(batch_model)
    
    async def get_by_id(self, batch_id: UUID) -> Optional[ProcessingBatch]:
        """Get a processing batch by its ID."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(ProcessingBatchModel).where(ProcessingBatchModel.id == batch_id)
            )
            batch_model = result.scalar_one_or_none()
            
            if batch_model:
                return self._model_to_entity(batch_model)
            return None
    
    async def get_active_batches(self) -> List[ProcessingBatch]:
        """Get all active processing batches."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(ProcessingBatchModel).where(
                    ProcessingBatchModel.status.in_([
                        ProcessingStatus.PENDING.value,
                        ProcessingStatus.PROCESSING.value
                    ])
                )
            )
            batch_models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in batch_models]
    
    async def update_status(self, batch_id: UUID, status: str) -> bool:
        """Update the status of a batch."""
        async with self.session_factory() as session:
            result = await session.execute(
                update(ProcessingBatchModel)
                .where(ProcessingBatchModel.id == batch_id)
                .values(status=status)
            )
            
            await session.commit()
            return result.rowcount > 0
    
    async def get_recent_batches(self, limit: int = 10) -> List[ProcessingBatch]:
        """Get recent processing batches."""
        async with self.session_factory() as session:
            result = await session.execute(
                select(ProcessingBatchModel)
                .order_by(ProcessingBatchModel.created_at.desc())
                .limit(limit)
            )
            batch_models = result.scalars().all()
            
            return [self._model_to_entity(model) for model in batch_models]
    
    def _model_to_entity(self, model: ProcessingBatchModel) -> ProcessingBatch:
        """Convert database model to domain entity."""
        return ProcessingBatch(
            id=model.id,
            files=[],  # Would need to be loaded separately
            status=ProcessingStatus(model.status),
            started_at=model.started_at,
            completed_at=model.completed_at,
            total_files=model.total_files,
            processed_files=model.processed_files,
            failed_files=model.failed_files,
            created_at=model.created_at
        ) 