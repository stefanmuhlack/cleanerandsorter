"""
Rollback service for managing file processing operations and snapshots.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

from app.domain.entities import FileEntity, ProcessingBatch
from app.domain.repositories import (
    FileRepository,
    ProcessingBatchRepository,
    ObjectStorageRepository,
    MessageRepository
)

logger = logging.getLogger(__name__)


class RollbackOperation(Enum):
    """Types of rollback operations."""
    FILE_PROCESSING = "file_processing"
    BATCH_PROCESSING = "batch_processing"
    METADATA_UPDATE = "metadata_update"
    CLASSIFICATION = "classification"
    STORAGE_MOVE = "storage_move"


@dataclass
class Snapshot:
    """Snapshot of system state before an operation."""
    id: str
    operation_type: RollbackOperation
    timestamp: datetime
    description: str
    file_ids: List[str]
    batch_id: Optional[str]
    metadata: Dict[str, Any]
    original_paths: Dict[str, str]
    target_paths: Dict[str, str]
    database_state: Dict[str, Any]
    storage_state: Dict[str, Any]


@dataclass
class RollbackResult:
    """Result of a rollback operation."""
    success: bool
    message: str
    files_restored: int
    files_failed: int
    errors: List[str]
    duration_seconds: float


class RollbackService:
    """
    Service for managing rollback operations and snapshots.
    
    This service provides comprehensive rollback capabilities for file processing
    operations, including:
    - Creating snapshots before operations
    - Rolling back file processing operations
    - Restoring database states
    - Managing file movements and storage operations
    """
    
    def __init__(
        self,
        file_repo: FileRepository,
        batch_repo: ProcessingBatchRepository,
        storage_repo: ObjectStorageRepository,
        message_repo: MessageRepository,
        snapshot_retention_days: int = 30
    ):
        self.file_repo = file_repo
        self.batch_repo = batch_repo
        self.storage_repo = storage_repo
        self.message_repo = message_repo
        self.snapshot_retention_days = snapshot_retention_days
        self._snapshots: Dict[str, Snapshot] = {}
    
    async def create_snapshot(
        self,
        operation_type: RollbackOperation,
        description: str,
        file_ids: List[str],
        batch_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a snapshot before performing an operation.
        
        Args:
            operation_type: Type of operation being performed
            description: Human-readable description of the operation
            file_ids: List of file IDs involved in the operation
            batch_id: Optional batch ID if this is part of a batch operation
            metadata: Additional metadata about the operation
            
        Returns:
            Snapshot ID for later rollback
        """
        snapshot_id = f"snapshot_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{operation_type.value}"
        
        # Capture current state
        original_paths = {}
        target_paths = {}
        database_state = {}
        storage_state = {}
        
        # Get file information
        for file_id in file_ids:
            file_entity = await self.file_repo.get_by_id(file_id)
            if file_entity:
                original_paths[file_id] = file_entity.original_path
                target_paths[file_id] = file_entity.target_path
                
                # Capture database state
                database_state[file_id] = {
                    'status': file_entity.status,
                    'metadata': file_entity.metadata,
                    'tags': file_entity.tags,
                    'classification': file_entity.classification,
                    'created_at': file_entity.created_at.isoformat(),
                    'updated_at': file_entity.updated_at.isoformat()
                }
        
        # Capture batch state if applicable
        if batch_id:
            batch = await self.batch_repo.get_by_id(batch_id)
            if batch:
                database_state['batch'] = {
                    'status': batch.status,
                    'processed_files': batch.processed_files,
                    'failed_files': batch.failed_files,
                    'started_at': batch.started_at.isoformat(),
                    'completed_at': batch.completed_at.isoformat() if batch.completed_at else None
                }
        
        # Capture storage state
        storage_state = await self._capture_storage_state(file_ids)
        
        # Create snapshot
        snapshot = Snapshot(
            id=snapshot_id,
            operation_type=operation_type,
            timestamp=datetime.utcnow(),
            description=description,
            file_ids=file_ids,
            batch_id=batch_id,
            metadata=metadata or {},
            original_paths=original_paths,
            target_paths=target_paths,
            database_state=database_state,
            storage_state=storage_state
        )
        
        # Store snapshot
        self._snapshots[snapshot_id] = snapshot
        
        # Persist snapshot to storage
        await self._persist_snapshot(snapshot)
        
        logger.info(f"Created snapshot {snapshot_id} for {operation_type.value} operation")
        return snapshot_id
    
    async def rollback_to_snapshot(self, snapshot_id: str) -> RollbackResult:
        """
        Rollback to a specific snapshot.
        
        Args:
            snapshot_id: ID of the snapshot to rollback to
            
        Returns:
            RollbackResult with operation details
        """
        start_time = datetime.utcnow()
        
        if snapshot_id not in self._snapshots:
            # Try to load from storage
            snapshot = await self._load_snapshot(snapshot_id)
            if not snapshot:
                return RollbackResult(
                    success=False,
                    message=f"Snapshot {snapshot_id} not found",
                    files_restored=0,
                    files_failed=0,
                    errors=[f"Snapshot {snapshot_id} not found"],
                    duration_seconds=(datetime.utcnow() - start_time).total_seconds()
                )
            self._snapshots[snapshot_id] = snapshot
        
        snapshot = self._snapshots[snapshot_id]
        errors = []
        files_restored = 0
        files_failed = 0
        
        try:
            # Rollback based on operation type
            if snapshot.operation_type == RollbackOperation.FILE_PROCESSING:
                result = await self._rollback_file_processing(snapshot)
                files_restored = result['files_restored']
                files_failed = result['files_failed']
                errors.extend(result['errors'])
                
            elif snapshot.operation_type == RollbackOperation.BATCH_PROCESSING:
                result = await self._rollback_batch_processing(snapshot)
                files_restored = result['files_restored']
                files_failed = result['files_failed']
                errors.extend(result['errors'])
                
            elif snapshot.operation_type == RollbackOperation.METADATA_UPDATE:
                result = await self._rollback_metadata_update(snapshot)
                files_restored = result['files_restored']
                files_failed = result['files_failed']
                errors.extend(result['errors'])
                
            elif snapshot.operation_type == RollbackOperation.CLASSIFICATION:
                result = await self._rollback_classification(snapshot)
                files_restored = result['files_restored']
                files_failed = result['files_failed']
                errors.extend(result['errors'])
                
            elif snapshot.operation_type == RollbackOperation.STORAGE_MOVE:
                result = await self._rollback_storage_move(snapshot)
                files_restored = result['files_restored']
                files_failed = result['files_failed']
                errors.extend(result['errors'])
            
            # Send rollback notification
            await self._send_rollback_notification(snapshot, files_restored, files_failed)
            
            success = files_failed == 0
            message = f"Rollback completed: {files_restored} files restored, {files_failed} failed"
            
        except Exception as e:
            logger.error(f"Rollback failed for snapshot {snapshot_id}: {e}")
            errors.append(str(e))
            success = False
            message = f"Rollback failed: {e}"
        
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        return RollbackResult(
            success=success,
            message=message,
            files_restored=files_restored,
            files_failed=files_failed,
            errors=errors,
            duration_seconds=duration
        )
    
    async def list_snapshots(
        self,
        operation_type: Optional[RollbackOperation] = None,
        since: Optional[datetime] = None,
        limit: int = 50
    ) -> List[Snapshot]:
        """
        List available snapshots with optional filtering.
        
        Args:
            operation_type: Filter by operation type
            since: Filter snapshots created since this time
            limit: Maximum number of snapshots to return
            
        Returns:
            List of snapshots matching the criteria
        """
        snapshots = list(self._snapshots.values())
        
        # Apply filters
        if operation_type:
            snapshots = [s for s in snapshots if s.operation_type == operation_type]
        
        if since:
            snapshots = [s for s in snapshots if s.timestamp >= since]
        
        # Sort by timestamp (newest first)
        snapshots.sort(key=lambda s: s.timestamp, reverse=True)
        
        return snapshots[:limit]
    
    async def cleanup_old_snapshots(self) -> int:
        """
        Clean up snapshots older than the retention period.
        
        Returns:
            Number of snapshots cleaned up
        """
        cutoff_date = datetime.utcnow() - timedelta(days=self.snapshot_retention_days)
        old_snapshots = [
            snapshot_id for snapshot_id, snapshot in self._snapshots.items()
            if snapshot.timestamp < cutoff_date
        ]
        
        for snapshot_id in old_snapshots:
            await self._delete_snapshot(snapshot_id)
            del self._snapshots[snapshot_id]
        
        logger.info(f"Cleaned up {len(old_snapshots)} old snapshots")
        return len(old_snapshots)
    
    async def _capture_storage_state(self, file_ids: List[str]) -> Dict[str, Any]:
        """Capture the current state of files in storage."""
        storage_state = {}
        
        for file_id in file_ids:
            try:
                # Check if file exists in storage
                exists = await self.storage_repo.file_exists(file_id)
                if exists:
                    metadata = await self.storage_repo.get_file_metadata(file_id)
                    storage_state[file_id] = {
                        'exists': True,
                        'metadata': metadata
                    }
                else:
                    storage_state[file_id] = {'exists': False}
            except Exception as e:
                logger.warning(f"Failed to capture storage state for file {file_id}: {e}")
                storage_state[file_id] = {'error': str(e)}
        
        return storage_state
    
    async def _persist_snapshot(self, snapshot: Snapshot) -> None:
        """Persist snapshot to storage."""
        try:
            snapshot_data = asdict(snapshot)
            snapshot_data['timestamp'] = snapshot.timestamp.isoformat()
            
            # Store in object storage
            await self.storage_repo.store_snapshot(
                snapshot.id,
                json.dumps(snapshot_data, indent=2)
            )
        except Exception as e:
            logger.error(f"Failed to persist snapshot {snapshot.id}: {e}")
    
    async def _load_snapshot(self, snapshot_id: str) -> Optional[Snapshot]:
        """Load snapshot from storage."""
        try:
            snapshot_data = await self.storage_repo.get_snapshot(snapshot_id)
            if snapshot_data:
                data = json.loads(snapshot_data)
                data['timestamp'] = datetime.fromisoformat(data['timestamp'])
                data['operation_type'] = RollbackOperation(data['operation_type'])
                return Snapshot(**data)
        except Exception as e:
            logger.error(f"Failed to load snapshot {snapshot_id}: {e}")
        
        return None
    
    async def _delete_snapshot(self, snapshot_id: str) -> None:
        """Delete snapshot from storage."""
        try:
            await self.storage_repo.delete_snapshot(snapshot_id)
        except Exception as e:
            logger.error(f"Failed to delete snapshot {snapshot_id}: {e}")
    
    async def _rollback_file_processing(self, snapshot: Snapshot) -> Dict[str, Any]:
        """Rollback file processing operation."""
        files_restored = 0
        files_failed = 0
        errors = []
        
        for file_id in snapshot.file_ids:
            try:
                # Restore database state
                if file_id in snapshot.database_state:
                    file_state = snapshot.database_state[file_id]
                    await self.file_repo.update_status(file_id, file_state['status'])
                    await self.file_repo.update_metadata(file_id, file_state['metadata'])
                    await self.file_repo.update_tags(file_id, file_state['tags'])
                    await self.file_repo.update_classification(file_id, file_state['classification'])
                
                # Restore file location if it was moved
                if file_id in snapshot.original_paths and file_id in snapshot.target_paths:
                    original_path = snapshot.original_paths[file_id]
                    target_path = snapshot.target_paths[file_id]
                    
                    if original_path != target_path:
                        # Move file back to original location
                        await self.storage_repo.move_file(file_id, target_path, original_path)
                
                files_restored += 1
                
            except Exception as e:
                logger.error(f"Failed to rollback file {file_id}: {e}")
                errors.append(f"File {file_id}: {e}")
                files_failed += 1
        
        return {
            'files_restored': files_restored,
            'files_failed': files_failed,
            'errors': errors
        }
    
    async def _rollback_batch_processing(self, snapshot: Snapshot) -> Dict[str, Any]:
        """Rollback batch processing operation."""
        # First rollback individual files
        file_result = await self._rollback_file_processing(snapshot)
        
        # Then restore batch state
        if snapshot.batch_id and 'batch' in snapshot.database_state:
            try:
                batch_state = snapshot.database_state['batch']
                await self.batch_repo.update_status(snapshot.batch_id, batch_state['status'])
                await self.batch_repo.update_processed_files(snapshot.batch_id, batch_state['processed_files'])
                await self.batch_repo.update_failed_files(snapshot.batch_id, batch_state['failed_files'])
            except Exception as e:
                logger.error(f"Failed to rollback batch {snapshot.batch_id}: {e}")
                file_result['errors'].append(f"Batch {snapshot.batch_id}: {e}")
        
        return file_result
    
    async def _rollback_metadata_update(self, snapshot: Snapshot) -> Dict[str, Any]:
        """Rollback metadata update operation."""
        files_restored = 0
        files_failed = 0
        errors = []
        
        for file_id in snapshot.file_ids:
            try:
                if file_id in snapshot.database_state:
                    file_state = snapshot.database_state[file_id]
                    await self.file_repo.update_metadata(file_id, file_state['metadata'])
                    await self.file_repo.update_tags(file_id, file_state['tags'])
                    await self.file_repo.update_classification(file_id, file_state['classification'])
                
                files_restored += 1
                
            except Exception as e:
                logger.error(f"Failed to rollback metadata for file {file_id}: {e}")
                errors.append(f"File {file_id}: {e}")
                files_failed += 1
        
        return {
            'files_restored': files_restored,
            'files_failed': files_failed,
            'errors': errors
        }
    
    async def _rollback_classification(self, snapshot: Snapshot) -> Dict[str, Any]:
        """Rollback classification operation."""
        files_restored = 0
        files_failed = 0
        errors = []
        
        for file_id in snapshot.file_ids:
            try:
                if file_id in snapshot.database_state:
                    file_state = snapshot.database_state[file_id]
                    await self.file_repo.update_classification(file_id, file_state['classification'])
                
                files_restored += 1
                
            except Exception as e:
                logger.error(f"Failed to rollback classification for file {file_id}: {e}")
                errors.append(f"File {file_id}: {e}")
                files_failed += 1
        
        return {
            'files_restored': files_restored,
            'files_failed': files_failed,
            'errors': errors
        }
    
    async def _rollback_storage_move(self, snapshot: Snapshot) -> Dict[str, Any]:
        """Rollback storage move operation."""
        files_restored = 0
        files_failed = 0
        errors = []
        
        for file_id in snapshot.file_ids:
            try:
                if file_id in snapshot.original_paths and file_id in snapshot.target_paths:
                    original_path = snapshot.original_paths[file_id]
                    target_path = snapshot.target_paths[file_id]
                    
                    if original_path != target_path:
                        # Move file back to original location
                        await self.storage_repo.move_file(file_id, target_path, original_path)
                
                files_restored += 1
                
            except Exception as e:
                logger.error(f"Failed to rollback storage move for file {file_id}: {e}")
                errors.append(f"File {file_id}: {e}")
                files_failed += 1
        
        return {
            'files_restored': files_restored,
            'files_failed': files_failed,
            'errors': errors
        }
    
    async def _send_rollback_notification(
        self,
        snapshot: Snapshot,
        files_restored: int,
        files_failed: int
    ) -> None:
        """Send notification about rollback operation."""
        try:
            notification = {
                'type': 'rollback_completed',
                'snapshot_id': snapshot.id,
                'operation_type': snapshot.operation_type.value,
                'description': snapshot.description,
                'files_restored': files_restored,
                'files_failed': files_failed,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            await self.message_repo.publish_message('rollback_notifications', notification)
            
        except Exception as e:
            logger.error(f"Failed to send rollback notification: {e}")
