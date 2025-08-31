"""
Ingest Service - Real endpoints wired to domain services and repositories.
"""
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Request, UploadFile, File, Depends
from fastapi.responses import Response, JSONResponse
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import logging
import os
from pathlib import Path
from uuid import UUID

from app.application.health import router as health_router
from app.application.crawler import router as crawler_router
from app.application.config_api import router as config_router
from app.application.duplicates import router as duplicates_router
from app.application.review import router as review_router
from app.infrastructure.config import Settings
from app.infrastructure.database import create_database_session
from app.infrastructure.repositories.postgres_repository import (
    PostgresFileRepository,
    PostgresSortingRuleRepository,
    PostgresProcessingBatchRepository,
)
from app.infrastructure.repositories.minio_repository import MinioObjectStorageRepository
from app.infrastructure.repositories.rabbitmq_repository import RabbitMQMessageRepository
from app.domain.services import FileProcessingService, StatisticsService
from app.domain.entities import ProcessingStatus
from app.domain.services.rollback_service import RollbackService, RollbackOperation

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Ingest Service",
    description="Document ingestion and processing service",
    version="1.0.0"
)

# Mount advanced health router (includes /health, /health/simple, /health/ready)
app.include_router(health_router)
app.include_router(crawler_router)
app.include_router(config_router)
app.include_router(duplicates_router)
app.include_router(review_router)

# App state for services
class AppState:
    settings: Settings
    session_factory = None
    file_repo: Optional[PostgresFileRepository] = None
    rule_repo: Optional[PostgresSortingRuleRepository] = None
    batch_repo: Optional[PostgresProcessingBatchRepository] = None
    storage_repo: Optional[MinioObjectStorageRepository] = None
    message_repo: Optional[RabbitMQMessageRepository] = None
    file_processing_service: Optional[FileProcessingService] = None
    statistics_service: Optional[StatisticsService] = None


state = AppState()


@app.on_event("startup")
async def on_startup() -> None:
    """Initialize repositories and services."""
    state.settings = Settings()
    state.session_factory = await create_database_session(state.settings)
    state.file_repo = PostgresFileRepository(state.session_factory)
    state.rule_repo = PostgresSortingRuleRepository(state.session_factory)
    state.batch_repo = PostgresProcessingBatchRepository(state.session_factory)
    state.storage_repo = MinioObjectStorageRepository(
        endpoint=state.settings.minio_endpoint,
        access_key=state.settings.minio_access_key,
        secret_key=state.settings.minio_secret_key,
        secure=state.settings.minio_secure,
        region=state.settings.minio_region,
    )
    state.message_repo = RabbitMQMessageRepository(state.settings.rabbitmq_url)
    state.file_processing_service = FileProcessingService(
        file_repo=state.file_repo,
        rule_repo=state.rule_repo,
        batch_repo=state.batch_repo,
        storage_repo=state.storage_repo,
        message_repo=state.message_repo,
    )
    state.statistics_service = StatisticsService(
        file_repo=state.file_repo,
        batch_repo=state.batch_repo,
    )
    state.rollback_service = RollbackService(
        file_repo=state.file_repo,
        batch_repo=state.batch_repo,
        storage_repo=state.storage_repo,
        message_repo=state.message_repo,
    )
    # Ensure source directory exists
    os.makedirs(state.settings.source_directory, exist_ok=True)


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/processing/start")
async def start_processing(request: Request):
    """Start file processing. Accepts either single file_path or batch config with 'files'."""
    data = await request.json()
    try:
        # Single file
        if "file_path" in data:
            file_path = data.get("file_path")
            if not file_path:
                raise HTTPException(status_code=400, detail="No file path provided")
            file_entity = await state.file_processing_service.process_file(Path(file_path))
            return {"status": "success", "file": file_entity.dict()}
        # Batch
        files = data.get("files", [])
        if not isinstance(files, list):
            raise HTTPException(status_code=400, detail="'files' must be a list of paths")
        batch = await state.file_processing_service.process_batch([Path(p) for p in files])
        return {"status": "success", "batch": batch.dict()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"start_processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/processing/jobs")
async def get_processing_jobs(status: Optional[str] = None):
    """List files by status or pending if none provided."""
    try:
        if status:
            files = await state.file_repo.get_by_status(status)
        else:
            files = await state.file_repo.get_pending_files()
        return {"jobs": [f.dict() for f in files]}
    except Exception as e:
        logger.error(f"get_processing_jobs error: {e}")
        return {"jobs": []}


@app.get("/processing/stats")
async def get_processing_stats():
    """Get processing statistics from repository; returns empty totals when no data."""
    stats = await state.statistics_service.get_processing_statistics()
    return stats.dict()


@app.post("/processing/stop")
async def stop_processing():
    """No background workers in this service; return acknowledged to keep contract stable."""
    return {"status": "acknowledged"}


@app.post("/processing/rollback/{job_id}")
async def rollback_job(job_id: str):
    """Rollback via snapshot if available, else best-effort reset."""
    try:
        # Try rollback service if snapshots exist (ID used as snapshot id for simplicity)
        result = await state.rollback_service.rollback_to_snapshot(job_id)
        if result.success:
            updated = await state.file_repo.get_by_id(job_id)
            return {"status": "success", "file": updated.dict() if updated else {"id": job_id}, "rollback": {
                "files_restored": result.files_restored,
                "files_failed": result.files_failed
            }}
        # Fallback: best-effort
        file_entity = await state.file_repo.get_by_id(job_id)
        if not file_entity:
            raise HTTPException(status_code=404, detail="File not found")
        if file_entity.bucket_name and file_entity.object_key:
            try:
                await state.storage_repo.delete_file(file_entity.bucket_name, file_entity.object_key)
            except Exception as e:
                logger.warning(f"Failed to delete object during rollback: {e}")
        await state.file_repo.update_status(job_id, ProcessingStatus.PENDING)
        updated = await state.file_repo.get_by_id(job_id)
        return {"status": "success", "file": updated.dict() if updated else {"id": job_id}, "rollback": {
            "files_restored": 1,
            "files_failed": 0
        }}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"rollback_job error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/snapshots")
async def list_snapshots(limit: int = 50):
    """List rollback snapshots if any; returns []."""
    snaps = await state.rollback_service.list_snapshots(limit=limit)
    # Convert dataclasses to primitives
    xs = []
    for s in snaps:
        xs.append({
            "id": s.id,
            "operation_type": s.operation_type.value,
            "timestamp": s.timestamp.isoformat(),
            "description": s.description,
            "file_ids": s.file_ids,
            "batch_id": s.batch_id
        })
    return {"snapshots": xs}

@app.post("/snapshots/{snapshot_id}/rollback")
async def rollback_snapshot(snapshot_id: str):
    """Rollback to a specific snapshot; returns result."""
    result = await state.rollback_service.rollback_to_snapshot(snapshot_id)
    return {
        "success": result.success,
        "message": result.message,
        "files_restored": result.files_restored,
        "files_failed": result.files_failed,
        "errors": result.errors,
        "duration_seconds": result.duration_seconds
    }


@app.post("/api/files/process")
async def process_file_api(file_path: str):
    """Process a single file and return stored entity."""
    try:
        file_entity = await state.file_processing_service.process_file(Path(file_path))
        return {"status": "success", "file": file_entity.dict()}
    except Exception as e:
        logger.error(f"process_file_api error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/files/process-batch")
async def process_batch_api(file_paths: List[str]):
    """Process a batch of files and return batch information."""
    try:
        batch = await state.file_processing_service.process_batch([Path(p) for p in file_paths])
        return {"status": "success", "batch": batch.dict()}
    except Exception as e:
        logger.error(f"process_batch_api error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/files/{file_id}")
async def get_file(file_id: str):
    """Get file information by ID; returns 404 if not found."""
    file_entity = await state.file_repo.get_by_id(file_id)
    if not file_entity:
        raise HTTPException(status_code=404, detail="File not found")
    return file_entity.dict()


@app.get("/api/files")
async def list_files(status: Optional[str] = None):
    """List files with optional status filter; returns [] when empty."""
    try:
        if status:
            files = await state.file_repo.get_by_status(status)
        else:
            files = await state.file_repo.get_pending_files()
        return {"files": [f.dict() for f in files]}
    except Exception as e:
        logger.error(f"list_files error: {e}")
        return {"files": []}


@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(default=[])):
    """Save uploaded files to source directory and return their temporary paths."""
    saved: List[str] = []
    for uf in files:
        try:
            dest_path = os.path.join(state.settings.source_directory, uf.filename)
            # Ensure directory exists
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            with open(dest_path, 'wb') as out:
                content = await uf.read()
                out.write(content)
            saved.append(dest_path)
        except Exception as e:
            logger.error(f"upload error for {uf.filename}: {e}")
    return {"files": saved}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 