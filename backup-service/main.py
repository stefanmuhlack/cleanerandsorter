import os
import asyncio
import yaml
import tempfile
import shutil
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import httpx
import json
from loguru import logger
import schedule
import threading
import time

# Configure logging
logger.add("/app/logs/backup-service.log", rotation="1 day", retention="7 days")

app = FastAPI(title="Backup Service", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
POSTGRES_URL = os.getenv("POSTGRES_URL", "postgresql://cas_user:cas_password@postgres:5432/cas_dms")
BACKUP_RETENTION_DAYS = int(os.getenv("BACKUP_RETENTION_DAYS", "30"))

class BackupInfo(BaseModel):
    id: str
    type: str
    size: int
    created_at: str
    status: str
    path: str
    metadata: Dict[str, Any] = {}

class BackupRequest(BaseModel):
    type: str  # "database", "minio", "full"
    description: Optional[str] = None
    retention_days: Optional[int] = None

class BackupResult(BaseModel):
    success: bool
    message: str
    backup_id: Optional[str] = None
    size: Optional[int] = None
    duration: Optional[float] = None

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check if backup directory is accessible
        backup_dir = Path("/app/backups")
        if not backup_dir.exists():
            backup_dir.mkdir(parents=True, exist_ok=True)
        
        return {"status": "healthy", "service": "backup-service"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.post("/backup")
async def create_backup(request: BackupRequest, background_tasks: BackgroundTasks):
    """Create a new backup"""
    try:
        # Start background backup
        background_tasks.add_task(perform_backup, request)
        
        return {"message": f"Started {request.type} backup", "status": "backing_up"}
        
    except Exception as e:
        logger.error(f"Failed to start backup: {e}")
        raise HTTPException(status_code=500, detail="Failed to start backup")

@app.get("/backups")
async def list_backups():
    """List all available backups"""
    try:
        backup_dir = Path("/app/backups")
        if not backup_dir.exists():
            return {"backups": []}
        
        backups = []
        for backup_file in backup_dir.glob("*"):
            if backup_file.is_file():
                stat = backup_file.stat()
                backups.append(BackupInfo(
                    id=backup_file.stem,
                    type=backup_file.suffix[1:] if backup_file.suffix else "unknown",
                    size=stat.st_size,
                    created_at=datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    status="completed",
                    path=str(backup_file)
                ))
        
        # Sort by creation date (newest first)
        backups.sort(key=lambda x: x.created_at, reverse=True)
        
        return {"backups": backups}
        
    except Exception as e:
        logger.error(f"Failed to list backups: {e}")
        raise HTTPException(status_code=500, detail="Failed to list backups")

@app.get("/backups/{backup_id}")
async def get_backup(backup_id: str):
    """Get backup details"""
    try:
        backup_dir = Path("/app/backups")
        backup_file = backup_dir / f"{backup_id}"
        
        if not backup_file.exists():
            raise HTTPException(status_code=404, detail="Backup not found")
        
        stat = backup_file.stat()
        
        return BackupInfo(
            id=backup_id,
            type=backup_file.suffix[1:] if backup_file.suffix else "unknown",
            size=stat.st_size,
            created_at=datetime.fromtimestamp(stat.st_ctime).isoformat(),
            status="completed",
            path=str(backup_file)
        )
        
    except Exception as e:
        logger.error(f"Failed to get backup {backup_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get backup")

@app.delete("/backups/{backup_id}")
async def delete_backup(backup_id: str):
    """Delete a backup"""
    try:
        backup_dir = Path("/app/backups")
        backup_file = backup_dir / f"{backup_id}"
        
        if not backup_file.exists():
            raise HTTPException(status_code=404, detail="Backup not found")
        
        backup_file.unlink()
        
        return {"message": f"Backup {backup_id} deleted successfully"}
        
    except Exception as e:
        logger.error(f"Failed to delete backup {backup_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete backup")

@app.post("/backups/{backup_id}/restore")
async def restore_backup(backup_id: str, background_tasks: BackgroundTasks):
    """Restore a backup"""
    try:
        # Start background restore
        background_tasks.add_task(perform_restore, backup_id)
        
        return {"message": f"Started restore of backup {backup_id}", "status": "restoring"}
        
    except Exception as e:
        logger.error(f"Failed to start restore: {e}")
        raise HTTPException(status_code=500, detail="Failed to start restore")

@app.post("/cleanup")
async def cleanup_old_backups():
    """Clean up old backups based on retention policy"""
    try:
        deleted_count = await cleanup_backups()
        return {"message": f"Cleaned up {deleted_count} old backups"}
        
    except Exception as e:
        logger.error(f"Failed to cleanup backups: {e}")
        raise HTTPException(status_code=500, detail="Failed to cleanup backups")

async def perform_backup(request: BackupRequest):
    """Perform the actual backup"""
    try:
        start_time = time.time()
        backup_id = f"{request.type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"Starting {request.type} backup: {backup_id}")
        
        if request.type == "database":
            await backup_database(backup_id)
        elif request.type == "minio":
            await backup_minio(backup_id)
        elif request.type == "full":
            await backup_full(backup_id)
        else:
            raise ValueError(f"Unknown backup type: {request.type}")
        
        duration = time.time() - start_time
        logger.info(f"Completed {request.type} backup {backup_id} in {duration:.2f} seconds")
        
    except Exception as e:
        logger.error(f"Backup failed: {e}")

async def backup_database(backup_id: str):
    """Backup PostgreSQL database"""
    try:
        backup_dir = Path("/app/backups")
        backup_file = backup_dir / f"{backup_id}.sql"
        
        # Extract database connection info from URL
        # postgresql://user:password@host:port/database
        db_url = POSTGRES_URL.replace("postgresql://", "")
        user_pass, host_port_db = db_url.split("@")
        user, password = user_pass.split(":")
        host_port, database = host_port_db.split("/")
        host, port = host_port.split(":")
        
        # Create pg_dump command
        cmd = [
            "pg_dump",
            f"--host={host}",
            f"--port={port}",
            f"--username={user}",
            f"--dbname={database}",
            "--format=custom",
            f"--file={backup_file}"
        ]
        
        # Set password environment variable
        env = os.environ.copy()
        env["PGPASSWORD"] = password
        
        # Execute backup
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Database backup failed: {result.stderr}")
        
        logger.info(f"Database backup completed: {backup_file}")
        
    except Exception as e:
        logger.error(f"Database backup failed: {e}")
        raise

async def backup_minio(backup_id: str):
    """Backup MinIO data"""
    try:
        backup_dir = Path("/app/backups")
        backup_file = backup_dir / f"{backup_id}.tar.gz"
        
        # Use mc (MinIO Client) to backup
        cmd = [
            "mc", "mirror",
            "--recursive",
            f"http://{MINIO_ACCESS_KEY}:{MINIO_SECRET_KEY}@{MINIO_ENDPOINT}",
            str(backup_file)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"MinIO backup failed: {result.stderr}")
        
        logger.info(f"MinIO backup completed: {backup_file}")
        
    except Exception as e:
        logger.error(f"MinIO backup failed: {e}")
        raise

async def backup_full(backup_id: str):
    """Perform full system backup"""
    try:
        backup_dir = Path("/app/backups")
        backup_file = backup_dir / f"{backup_id}.tar.gz"
        
        # Create temporary directory for backup
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Backup database
            db_backup = temp_path / "database.sql"
            await backup_database_to_file(db_backup)
            
            # Backup MinIO data
            minio_backup = temp_path / "minio"
            minio_backup.mkdir()
            await backup_minio_to_dir(minio_backup)
            
            # Create tar.gz archive
            cmd = [
                "tar", "-czf", str(backup_file),
                "-C", str(temp_path), "."
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"Full backup failed: {result.stderr}")
        
        logger.info(f"Full backup completed: {backup_file}")
        
    except Exception as e:
        logger.error(f"Full backup failed: {e}")
        raise

async def backup_database_to_file(backup_file: Path):
    """Backup database to specific file"""
    try:
        # Extract database connection info
        db_url = POSTGRES_URL.replace("postgresql://", "")
        user_pass, host_port_db = db_url.split("@")
        user, password = user_pass.split(":")
        host_port, database = host_port_db.split("/")
        host, port = host_port.split(":")
        
        cmd = [
            "pg_dump",
            f"--host={host}",
            f"--port={port}",
            f"--username={user}",
            f"--dbname={database}",
            "--format=custom",
            f"--file={backup_file}"
        ]
        
        env = os.environ.copy()
        env["PGPASSWORD"] = password
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Database backup failed: {result.stderr}")
        
    except Exception as e:
        logger.error(f"Database backup to file failed: {e}")
        raise

async def backup_minio_to_dir(backup_dir: Path):
    """Backup MinIO to specific directory"""
    try:
        cmd = [
            "mc", "mirror",
            "--recursive",
            f"http://{MINIO_ACCESS_KEY}:{MINIO_SECRET_KEY}@{MINIO_ENDPOINT}",
            str(backup_dir)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"MinIO backup failed: {result.stderr}")
        
    except Exception as e:
        logger.error(f"MinIO backup to directory failed: {e}")
        raise

async def perform_restore(backup_id: str):
    """Restore a backup"""
    try:
        backup_dir = Path("/app/backups")
        backup_file = backup_dir / f"{backup_id}"
        
        if not backup_file.exists():
            raise Exception(f"Backup file not found: {backup_file}")
        
        logger.info(f"Starting restore of backup: {backup_id}")
        
        # Determine backup type and restore accordingly
        if backup_file.suffix == ".sql":
            await restore_database(backup_file)
        elif backup_file.suffix == ".tar.gz":
            await restore_full(backup_file)
        else:
            raise Exception(f"Unknown backup format: {backup_file.suffix}")
        
        logger.info(f"Restore completed: {backup_id}")
        
    except Exception as e:
        logger.error(f"Restore failed: {e}")
        raise

async def restore_database(backup_file: Path):
    """Restore database from backup"""
    try:
        # Extract database connection info
        db_url = POSTGRES_URL.replace("postgresql://", "")
        user_pass, host_port_db = db_url.split("@")
        user, password = user_pass.split(":")
        host_port, database = host_port_db.split("/")
        host, port = host_port.split(":")
        
        cmd = [
            "pg_restore",
            f"--host={host}",
            f"--port={port}",
            f"--username={user}",
            f"--dbname={database}",
            "--clean",
            "--if-exists",
            str(backup_file)
        ]
        
        env = os.environ.copy()
        env["PGPASSWORD"] = password
        
        result = subprocess.run(cmd, env=env, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"Database restore failed: {result.stderr}")
        
    except Exception as e:
        logger.error(f"Database restore failed: {e}")
        raise

async def restore_full(backup_file: Path):
    """Restore full system backup"""
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Extract backup
            cmd = ["tar", "-xzf", str(backup_file), "-C", str(temp_path)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"Backup extraction failed: {result.stderr}")
            
            # Restore database if present
            db_backup = temp_path / "database.sql"
            if db_backup.exists():
                await restore_database(db_backup)
            
            # Restore MinIO if present
            minio_backup = temp_path / "minio"
            if minio_backup.exists():
                await restore_minio(minio_backup)
        
    except Exception as e:
        logger.error(f"Full restore failed: {e}")
        raise

async def restore_minio(backup_dir: Path):
    """Restore MinIO from backup"""
    try:
        cmd = [
            "mc", "mirror",
            "--recursive",
            str(backup_dir),
            f"http://{MINIO_ACCESS_KEY}:{MINIO_SECRET_KEY}@{MINIO_ENDPOINT}"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise Exception(f"MinIO restore failed: {result.stderr}")
        
    except Exception as e:
        logger.error(f"MinIO restore failed: {e}")
        raise

async def cleanup_backups() -> int:
    """Clean up old backups based on retention policy"""
    try:
        backup_dir = Path("/app/backups")
        if not backup_dir.exists():
            return 0
        
        cutoff_date = datetime.now() - timedelta(days=BACKUP_RETENTION_DAYS)
        deleted_count = 0
        
        for backup_file in backup_dir.glob("*"):
            if backup_file.is_file():
                stat = backup_file.stat()
                file_date = datetime.fromtimestamp(stat.st_ctime)
                
                if file_date < cutoff_date:
                    backup_file.unlink()
                    deleted_count += 1
                    logger.info(f"Deleted old backup: {backup_file.name}")
        
        return deleted_count
        
    except Exception as e:
        logger.error(f"Backup cleanup failed: {e}")
        raise

def schedule_backups():
    """Schedule automatic backups"""
    try:
        config = load_backup_config()
        
        # Schedule daily database backup
        schedule.every().day.at("02:00").do(lambda: asyncio.run(perform_backup(BackupRequest(type="database"))))
        
        # Schedule weekly full backup
        schedule.every().sunday.at("03:00").do(lambda: asyncio.run(perform_backup(BackupRequest(type="full"))))
        
        # Schedule daily cleanup
        schedule.every().day.at("04:00").do(lambda: asyncio.run(cleanup_backups()))
        
        logger.info("Backup schedule configured")
        
        # Run scheduler
        while True:
            schedule.run_pending()
            time.sleep(60)
            
    except Exception as e:
        logger.error(f"Backup scheduler failed: {e}")

def load_backup_config() -> Dict[str, Any]:
    """Load backup configuration"""
    config_path = "/app/config/backup-config.yaml"
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    else:
        return {
            "retention_days": BACKUP_RETENTION_DAYS,
            "schedule": {
                "database": "daily",
                "full": "weekly"
            }
        }

# Start backup scheduler in background thread
scheduler_thread = threading.Thread(target=schedule_backups, daemon=True)
scheduler_thread.start()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 