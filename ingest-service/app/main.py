"""
Ingest Service - Clean Mock Implementation
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
import logging
import structlog

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = structlog.get_logger()

# Create FastAPI app
app = FastAPI(
    title="Ingest Service",
    description="Document ingestion and processing service",
    version="1.0.0"
)

# Health endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "ingest-service"}

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Processing endpoints - COMPLETELY CLEAN MOCK IMPLEMENTATIONS (NO SERVICE DEPENDENCIES)
@app.post("/processing/start")
async def start_processing(request: Request):
    """Start file processing - COMPLETE MOCK."""
    try:
        data = await request.json()
        
        # Support both old format (file_path) and new format (ProcessingConfig)
        if "file_path" in data:
            # Old format - single file processing
            file_path = data.get("file_path")
            if not file_path:
                raise HTTPException(status_code=400, detail="No file path provided")
            
            return {"status": "success", "file_id": "mock-file-id-123"}
        else:
            # New format - batch processing with configuration
            config = data
            
            # Return success with mock data
            return {
                "status": "success",
                "message": "Batch processing started",
                "job_id": "mock-job-456",
                "config": config
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/processing/jobs")
async def get_processing_jobs():
    """Get all processing jobs - COMPLETE MOCK."""
    return {
        "jobs": [
            {
                "id": "1",
                "filename": "invoice_2024_001.pdf",
                "status": "completed",
                "progress": 100,
                "startTime": "2024-01-15T10:30:00Z",
                "endTime": "2024-01-15T10:32:15Z",
                "targetPath": "/finanzen/rechnungen/2024/",
                "classification": "finanzen/rechnungen",
                "isDuplicate": False
            },
            {
                "id": "2",
                "filename": "contract_customer_a.pdf",
                "status": "processing",
                "progress": 65,
                "startTime": "2024-01-15T10:35:00Z",
                "targetPath": "/projekte/vertraege/",
                "classification": "projekte/vertraege"
            },
            {
                "id": "3",
                "filename": "employee_data.xlsx",
                "status": "pending",
                "progress": 0,
                "startTime": "2024-01-15T10:40:00Z",
                "targetPath": "/personal/",
                "classification": "personal"
            }
        ]
    }


@app.get("/processing/stats")
async def get_processing_stats():
    """Get processing statistics - COMPLETE MOCK."""
    return {
        "total_files_processed": 245,
        "successful_files": 238,
        "failed_files": 3,
        "skipped_files": 4,
        "files_by_status": {
            "completed": 238,
            "failed": 3,
            "pending": 2,
            "processing": 2
        },
        "files_by_type": {
            "pdf": 120,
            "docx": 45,
            "xlsx": 30,
            "image": 50
        }
    }


@app.post("/processing/stop")
async def stop_processing():
    """Stop all processing jobs - COMPLETE MOCK."""
    return {"status": "success", "message": "Processing stopped"}


@app.post("/processing/rollback/{job_id}")
async def rollback_job(job_id: str):
    """Rollback a specific job - COMPLETE MOCK."""
    return {"status": "success", "message": f"Job {job_id} rolled back"}


# Additional API endpoints - COMPLETE MOCKS
@app.post("/api/files/process")
async def process_file(file_path: str):
    """Process a single file - COMPLETE MOCK."""
    return {"status": "success", "file_id": "mock-file-id"}


@app.post("/api/files/process-batch")
async def process_batch(file_paths: list[str]):
    """Process a batch of files - COMPLETE MOCK."""
    return {"status": "success", "batch_id": "mock-batch-id"}


@app.get("/api/files/{file_id}")
async def get_file(file_id: str):
    """Get file information - COMPLETE MOCK."""
    return {
        "id": file_id,
        "filename": "mock-file.pdf",
        "status": "completed",
        "file_type": "pdf"
    }


@app.get("/api/files")
async def list_files(status: str = None):
    """List files with optional status filter - COMPLETE MOCK."""
    return {
        "files": [
            {
                "id": "1",
                "filename": "invoice_2024_001.pdf",
                "status": "completed",
                "file_type": "pdf"
            },
            {
                "id": "2",
                "filename": "contract_customer_a.pdf",
                "status": "processing",
                "file_type": "pdf"
            }
        ]
    }


# Upload endpoint
@app.post("/upload")
async def upload_files():
    """Upload files - COMPLETE MOCK."""
    return {"status": "success", "message": "Files uploaded successfully"}


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 