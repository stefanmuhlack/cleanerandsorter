"""
Main FastAPI application for the ingest service.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

import structlog
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from starlette.requests import Request

from app.application.controllers import (
    FileController,
    SortingRuleController,
    StatisticsController
)
from app.application.health import router as health_router
from app.infrastructure.config import Settings
from app.infrastructure.database import create_database_session
from app.infrastructure.repositories.minio_repository import MinioObjectStorageRepository
from app.infrastructure.repositories.postgres_repository import (
    PostgresFileRepository,
    PostgresSortingRuleRepository,
    PostgresProcessingBatchRepository
)
from app.infrastructure.repositories.rabbitmq_repository import RabbitMQMessageRepository
from app.domain.services import (
    FileProcessingService,
    SortingRuleService,
    StatisticsService
)

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency')

# Global variables for dependency injection
settings: Settings = None
file_processing_service: FileProcessingService = None
sorting_rule_service: SortingRuleService = None
statistics_service: StatisticsService = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global settings, file_processing_service, sorting_rule_service, statistics_service
    
    # Load settings
    settings = Settings()
    
    # Initialize database
    await create_database_session(settings)
    
    # Initialize repositories
    session_factory = create_database_session(settings)
    file_repo = PostgresFileRepository(session_factory)
    rule_repo = PostgresSortingRuleRepository(session_factory)
    batch_repo = PostgresProcessingBatchRepository(session_factory)
    
    storage_repo = MinioObjectStorageRepository(
        endpoint=settings.minio_endpoint,
        access_key=settings.minio_access_key,
        secret_key=settings.minio_secret_key,
        secure=settings.minio_secure
    )
    
    message_repo = RabbitMQMessageRepository(settings.rabbitmq_url)
    await message_repo.connect()
    
    # Initialize services
    file_processing_service = FileProcessingService(
        file_repo=file_repo,
        rule_repo=rule_repo,
        batch_repo=batch_repo,
        storage_repo=storage_repo,
        message_repo=message_repo
    )
    
    sorting_rule_service = SortingRuleService(rule_repo=rule_repo)
    
    statistics_service = StatisticsService(
        file_repo=file_repo,
        batch_repo=batch_repo
    )
    
    logger.info("Application started successfully")
    
    yield
    
    # Cleanup
    await message_repo.disconnect()
    logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="CAS Ingest Service",
    description="Document processing and sorting service",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency injection
def get_file_processing_service() -> FileProcessingService:
    if file_processing_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return file_processing_service


def get_sorting_rule_service() -> SortingRuleService:
    if sorting_rule_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return sorting_rule_service


def get_statistics_service() -> StatisticsService:
    if statistics_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return statistics_service


# Middleware for metrics and logging
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Middleware for collecting metrics and logging."""
    import time
    
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration = time.time() - start_time
    
    # Record metrics
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_LATENCY.observe(duration)
    
    # Log request
    logger.info(
        "HTTP request",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration=duration
    )
    
    return response


# Include health check routes
app.include_router(health_router, prefix="/api", tags=["health"])


# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return JSONResponse(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


# Initialize controllers
file_controller = FileController()
sorting_rule_controller = SortingRuleController()
statistics_controller = StatisticsController()


# File processing routes
@app.post("/api/files/process")
async def process_file(
    file_path: str,
    service: FileProcessingService = Depends(get_file_processing_service)
):
    """Process a single file."""
    try:
        file_entity = await file_controller.process_file(
            Path(file_path),
            service
        )
        return {"status": "success", "file_id": str(file_entity.id)}
    except Exception as e:
        logger.error("Error processing file", file_path=file_path, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/files/process-batch")
async def process_batch(
    file_paths: list[str],
    service: FileProcessingService = Depends(get_file_processing_service)
):
    """Process a batch of files."""
    try:
        batch = await file_controller.process_batch(
            [Path(p) for p in file_paths],
            service
        )
        return {"status": "success", "batch_id": str(batch.id)}
    except Exception as e:
        logger.error("Error processing batch", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/files/{file_id}")
async def get_file(
    file_id: str,
    service: FileProcessingService = Depends(get_file_processing_service)
):
    """Get file information."""
    try:
        file_entity = await file_controller.get_file(file_id, service)
        if file_entity:
            return file_entity.dict()
        raise HTTPException(status_code=404, detail="File not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting file", file_id=file_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/files")
async def list_files(
    status: str = None,
    service: FileProcessingService = Depends(get_file_processing_service)
):
    """List files with optional status filter."""
    try:
        files = await file_controller.list_files(status, service)
        return {"files": [f.dict() for f in files]}
    except Exception as e:
        logger.error("Error listing files", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Sorting rule routes
@app.post("/api/rules")
async def create_rule(
    rule_data: dict,
    service: SortingRuleService = Depends(get_sorting_rule_service)
):
    """Create a new sorting rule."""
    try:
        rule = await sorting_rule_controller.create_rule(rule_data, service)
        return rule.dict()
    except Exception as e:
        logger.error("Error creating rule", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rules")
async def list_rules(
    service: SortingRuleService = Depends(get_sorting_rule_service)
):
    """List all sorting rules."""
    try:
        rules = await sorting_rule_controller.list_rules(service)
        return {"rules": [r.dict() for r in rules]}
    except Exception as e:
        logger.error("Error listing rules", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/rules/{rule_id}")
async def get_rule(
    rule_id: str,
    service: SortingRuleService = Depends(get_sorting_rule_service)
):
    """Get a specific sorting rule."""
    try:
        rule = await sorting_rule_controller.get_rule(rule_id, service)
        if rule:
            return rule.dict()
        raise HTTPException(status_code=404, detail="Rule not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting rule", rule_id=rule_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/rules/{rule_id}")
async def update_rule(
    rule_id: str,
    rule_data: dict,
    service: SortingRuleService = Depends(get_sorting_rule_service)
):
    """Update a sorting rule."""
    try:
        rule = await sorting_rule_controller.update_rule(rule_id, rule_data, service)
        return rule.dict()
    except Exception as e:
        logger.error("Error updating rule", rule_id=rule_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/rules/{rule_id}")
async def delete_rule(
    rule_id: str,
    service: SortingRuleService = Depends(get_sorting_rule_service)
):
    """Delete a sorting rule."""
    try:
        success = await sorting_rule_controller.delete_rule(rule_id, service)
        if success:
            return {"status": "success"}
        raise HTTPException(status_code=404, detail="Rule not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting rule", rule_id=rule_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# Statistics routes
@app.get("/api/statistics")
async def get_statistics(
    service: StatisticsService = Depends(get_statistics_service)
):
    """Get processing statistics."""
    try:
        stats = await statistics_controller.get_statistics(service)
        return stats.dict()
    except Exception as e:
        logger.error("Error getting statistics", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/statistics/batches")
async def get_recent_batches(
    limit: int = 10,
    service: StatisticsService = Depends(get_statistics_service)
):
    """Get recent processing batches."""
    try:
        batches = await statistics_controller.get_recent_batches(limit, service)
        return {"batches": [b.dict() for b in batches]}
    except Exception as e:
        logger.error("Error getting recent batches", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 