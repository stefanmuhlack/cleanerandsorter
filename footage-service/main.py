#!/usr/bin/env python3
"""
Footage and Media Management Service
Handles creative files (images, videos, designs) with thumbnail generation and metadata extraction
"""

import asyncio
import os
import json
import logging
import tempfile
import shutil
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
import hashlib
import mimetypes

import httpx
from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends, UploadFile, File
from fastapi.security import HTTPBearer
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
import yaml
from loguru import logger
from PIL import Image, ImageOps
import cv2
import exifread
from moviepy.editor import VideoFileClip
import httpx

# Import LLM Manager for classification
try:
    from llm_manager import LLMClassifier
except ImportError:
    LLMClassifier = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Footage and Media Management Service",
    description="Comprehensive media file management with thumbnail generation and metadata extraction",
    version="1.0.0"
)

# Security
security = HTTPBearer()

# Configuration
class FootageConfig:
    def __init__(self):
        self.footage_path = os.getenv("FOOTAGE_PATH", "/mnt/nas/footage")
        self.thumbnails_path = os.getenv("THUMBNAILS_PATH", "/mnt/nas/thumbnails")
        self.temp_path = os.getenv("TEMP_PATH", "/tmp/footage")
        self.max_file_size = int(os.getenv("FOOTAGE_MAX_SIZE", "1073741824"))  # 1GB
        self.thumbnail_size = (300, 300)
        self.enable_llm_classification = os.getenv("FOOTAGE_ENABLE_LLM", "true").lower() == "true"
        self.allowed_image_types = ["jpg", "jpeg", "png", "gif", "bmp", "tiff", "webp"]
        self.allowed_video_types = ["mp4", "avi", "mov", "mkv", "wmv", "flv", "webm"]
        self.allowed_design_types = ["psd", "ai", "eps", "svg", "pdf", "indd"]

config = FootageConfig()

# Pydantic Models
class MediaFile(BaseModel):
    id: str
    filename: str
    original_path: str
    file_type: str
    mime_type: str
    size: int
    hash: str
    customer: Optional[str] = None
    project: Optional[str] = None
    category: str = "unknown"
    tags: List[str] = []
    metadata: Dict[str, Any] = {}
    thumbnail_path: Optional[str] = None
    created_at: str
    updated_at: str

class MediaUploadRequest(BaseModel):
    customer: Optional[str] = None
    project: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = []
    generate_thumbnail: bool = True
    extract_metadata: bool = True
    enable_classification: bool = True

class MediaSearchRequest(BaseModel):
    customer: Optional[str] = None
    project: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = []
    file_type: Optional[str] = None
    date_from: Optional[str] = None
    date_to: Optional[str] = None
    size_min: Optional[int] = None
    size_max: Optional[int] = None

class ThumbnailRequest(BaseModel):
    file_id: str
    size: Optional[tuple] = (300, 300)
    quality: int = 85


class ImportFromShareRequest(BaseModel):
    storage_manager_url: str
    share: Dict[str, Any]
    paths: List[str]
    customer: Optional[str] = None
    project: Optional[str] = None
    category: Optional[str] = None
    generate_thumbnail: bool = True
    extract_metadata: bool = True
    enable_classification: bool = False

# LLM Classifier
llm_classifier = None
if config.enable_llm_classification and LLMClassifier:
    try:
        llm_classifier = LLMClassifier()
        logger.info("LLM Classifier initialized for footage management")
    except Exception as e:
        logger.warning(f"Failed to initialize LLM Classifier: {e}")

class FootageManager:
    def __init__(self):
        self.footage_path = Path(config.footage_path)
        self.thumbnails_path = Path(config.thumbnails_path)
        self.temp_path = Path(config.temp_path)
        
        # Create directories
        self.footage_path.mkdir(parents=True, exist_ok=True)
        self.thumbnails_path.mkdir(parents=True, exist_ok=True)
        self.temp_path.mkdir(parents=True, exist_ok=True)
        
        self.media_files: Dict[str, MediaFile] = {}
        self.hash_index: Dict[str, str] = {}
        self.load_existing_files()
    
    def load_existing_files(self):
        """Load existing media files from storage"""
        try:
            # Scan footage directory for existing files
            for file_path in self.footage_path.rglob("*"):
                if file_path.is_file():
                    file_id = self.generate_file_id(file_path)
                    if file_id not in self.media_files:
                        # Create MediaFile object for existing file
                        media_file = self.create_media_file_from_path(file_path)
                        if media_file:
                            self.media_files[file_id] = media_file
                            try:
                                file_hash = self.calculate_file_hash(file_path)
                                if file_hash:
                                    self.hash_index[file_hash] = file_id
                            except Exception:
                                pass
            
            logger.info(f"Loaded {len(self.media_files)} existing media files")
            
        except Exception as e:
            logger.error(f"Error loading existing files: {e}")
    
    def generate_file_id(self, file_path: Path) -> str:
        """Generate unique file ID based on path and content"""
        content = f"{file_path.absolute()}_{file_path.stat().st_mtime}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def create_media_file_from_path(self, file_path: Path) -> Optional[MediaFile]:
        """Create MediaFile object from existing file path"""
        try:
            file_type = self.get_file_type(file_path)
            if not file_type:
                return None
            
            file_id = self.generate_file_id(file_path)
            stat = file_path.stat()
            
            return MediaFile(
                id=file_id,
                filename=file_path.name,
                original_path=str(file_path),
                file_type=file_type,
                mime_type=mimetypes.guess_type(file_path)[0] or "application/octet-stream",
                size=stat.st_size,
                hash=self.calculate_file_hash(file_path),
                created_at=datetime.fromtimestamp(stat.st_ctime).isoformat(),
                updated_at=datetime.fromtimestamp(stat.st_mtime).isoformat()
            )
            
        except Exception as e:
            logger.error(f"Error creating media file from path {file_path}: {e}")
            return None
    
    def get_file_type(self, file_path: Path) -> Optional[str]:
        """Determine file type based on extension"""
        ext = file_path.suffix.lower().lstrip('.')
        
        if ext in config.allowed_image_types:
            return "image"
        elif ext in config.allowed_video_types:
            return "video"
        elif ext in config.allowed_design_types:
            return "design"
        else:
            return None
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _process_saved_path(self, file_path: Path, original_filename: str, request: MediaUploadRequest) -> MediaFile:
        """Process a file that is already saved to disk (dedup, metadata, thumbnail, classification)."""
        try:
            # Deduplication check by hash
            file_hash = self.calculate_file_hash(file_path)
            if file_hash and file_hash in self.hash_index:
                existing_id = self.hash_index[file_hash]
                existing = self.media_files.get(existing_id)
                if existing:
                    # Move duplicate to _duplicates preserving customer root
                    try:
                        base_dir = Path(existing.original_path).parents[2] if len(Path(existing.original_path).parents) >= 3 else self.footage_path
                        dup_dir = base_dir / "_duplicates"
                        dup_dir.mkdir(parents=True, exist_ok=True)
                        target = dup_dir / original_filename
                        # Prevent overwrite by suffixing
                        counter = 1
                        while target.exists():
                            target = dup_dir / f"{target.stem}_{counter}{target.suffix}"
                            counter += 1
                        file_path.replace(target)
                    except Exception as e:
                        logger.warning(f"Failed to move duplicate to _duplicates: {e}")
                    # Return existing without creating new record
                    return existing

            file_type = self.get_file_type(file_path)
            if not file_type:
                raise HTTPException(status_code=400, detail="Unsupported file type")

            file_id = self.generate_file_id(file_path)
            stat = file_path.stat()

            media_file = MediaFile(
                id=file_id,
                filename=original_filename,
                original_path=str(file_path),
                file_type=file_type,
                mime_type=mimetypes.guess_type(file_path)[0] or "application/octet-stream",
                size=stat.st_size,
                hash=file_hash,
                customer=request.customer,
                project=request.project,
                category=request.category or "unknown",
                tags=request.tags or [],
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat()
            )

            # Extract metadata if requested
            if request.extract_metadata:
                media_file.metadata = self.extract_metadata_sync(file_path, file_type)

            # Generate thumbnail if requested
            if request.generate_thumbnail and file_type in ["image", "video"]:
                thumbnail_path = self.generate_thumbnail_sync(file_path, file_id, file_type)
                if thumbnail_path:
                    media_file.thumbnail_path = thumbnail_path

            # Optional classification
            # (left async path for future; here we keep sync pipeline robust)

            # Save indices
            self.media_files[file_id] = media_file
            if file_hash:
                self.hash_index[file_hash] = file_id
            return media_file
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error processing saved file: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")

    async def process_uploaded_file(self, file: UploadFile, request: MediaUploadRequest) -> MediaFile:
        """Process uploaded file and create MediaFile object"""
        try:
            # Validate file type
            file_ext = Path(file.filename).suffix.lower().lstrip('.')
            file_type = self.get_file_type(Path(file.filename))
            
            if not file_type:
                raise HTTPException(status_code=400, detail="Unsupported file type")
            
            # Create customer/project directory structure
            customer_dir = self.footage_path / (request.customer or "unknown")
            project_dir = customer_dir / (request.project or "general")
            project_dir.mkdir(parents=True, exist_ok=True)
            
            # Save file
            file_path = project_dir / file.filename
            with open(file_path, "wb") as f:
                content = await file.read()
                f.write(content)
            return self._process_saved_path(file_path, file.filename, request)
            
        except Exception as e:
            logger.error(f"Error processing uploaded file: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")

    def extract_metadata_sync(self, file_path: Path, file_type: str) -> Dict[str, Any]:
        # Wrapper around async methods for reuse in sync pipeline
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self.extract_metadata(file_path, file_type))
        finally:
            loop.close()

    def generate_thumbnail_sync(self, file_path: Path, file_id: str, file_type: str) -> Optional[str]:
        import asyncio
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            return loop.run_until_complete(self.generate_thumbnail(file_path, file_id, file_type))
        finally:
            loop.close()
    
    async def extract_metadata(self, file_path: Path, file_type: str) -> Dict[str, Any]:
        """Extract metadata from media file"""
        metadata = {}
        
        try:
            if file_type == "image":
                metadata = await self.extract_image_metadata(file_path)
            elif file_type == "video":
                metadata = await self.extract_video_metadata(file_path)
            elif file_type == "design":
                metadata = await self.extract_design_metadata(file_path)
                
        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {e}")
        
        return metadata
    
    async def extract_image_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from image file"""
        metadata = {}
        
        try:
            # Use PIL for basic image info
            with Image.open(file_path) as img:
                metadata.update({
                    "width": img.width,
                    "height": img.height,
                    "mode": img.mode,
                    "format": img.format
                })
            
            # Use exifread for EXIF data
            with open(file_path, 'rb') as f:
                tags = exifread.process_file(f)
                if tags:
                    exif_data = {}
                    for tag, value in tags.items():
                        exif_data[tag] = str(value)
                    metadata["exif"] = exif_data
                    
        except Exception as e:
            logger.error(f"Error extracting image metadata: {e}")
        
        return metadata
    
    async def extract_video_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from video file"""
        metadata = {}
        
        try:
            # Use OpenCV for video info
            cap = cv2.VideoCapture(str(file_path))
            if cap.isOpened():
                metadata.update({
                    "width": int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                    "height": int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                    "fps": cap.get(cv2.CAP_PROP_FPS),
                    "frame_count": int(cap.get(cv2.CAP_PROP_FRAME_COUNT)),
                    "duration": cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS) if cap.get(cv2.CAP_PROP_FPS) > 0 else 0
                })
                cap.release()
            
            # Use moviepy for additional info
            try:
                clip = VideoFileClip(str(file_path))
                metadata.update({
                    "duration_moviepy": clip.duration,
                    "audio": clip.audio is not None
                })
                clip.close()
            except Exception as e:
                logger.warning(f"MoviePy metadata extraction failed: {e}")
                
        except Exception as e:
            logger.error(f"Error extracting video metadata: {e}")
        
        return metadata
    
    async def extract_design_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from design file"""
        metadata = {
            "file_size": file_path.stat().st_size,
            "file_type": file_path.suffix.lower().lstrip('.'),
            "last_modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
        }
        
        return metadata
    
    async def generate_thumbnail(self, file_path: Path, file_id: str, file_type: str) -> Optional[str]:
        """Generate thumbnail for media file"""
        try:
            thumbnail_dir = self.thumbnails_path / file_id[:2]
            thumbnail_dir.mkdir(parents=True, exist_ok=True)
            
            thumbnail_path = thumbnail_dir / f"{file_id}.jpg"
            
            if file_type == "image":
                await self.generate_image_thumbnail(file_path, thumbnail_path)
            elif file_type == "video":
                await self.generate_video_thumbnail(file_path, thumbnail_path)
            else:
                return None
            
            return str(thumbnail_path)
            
        except Exception as e:
            logger.error(f"Error generating thumbnail for {file_path}: {e}")
            return None
    
    async def generate_image_thumbnail(self, image_path: Path, thumbnail_path: Path):
        """Generate thumbnail from image"""
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            
            # Create thumbnail
            img.thumbnail(config.thumbnail_size, Image.Resampling.LANCZOS)
            
            # Save thumbnail
            img.save(thumbnail_path, 'JPEG', quality=85, optimize=True)
    
    async def generate_video_thumbnail(self, video_path: Path, thumbnail_path: Path):
        """Generate thumbnail from video"""
        cap = cv2.VideoCapture(str(video_path))
        if cap.isOpened():
            # Get frame at 25% of video duration
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_number = int(total_frames * 0.25)
            
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = cap.read()
            
            if ret:
                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Create PIL image
                img = Image.fromarray(frame_rgb)
                img.thumbnail(config.thumbnail_size, Image.Resampling.LANCZOS)
                
                # Save thumbnail
                img.save(thumbnail_path, 'JPEG', quality=85, optimize=True)
            
            cap.release()
    
    async def classify_media_file(self, media_file: MediaFile) -> Optional[Dict[str, Any]]:
        """Classify media file using LLM"""
        if not llm_classifier:
            return None
        
        try:
            # Prepare content for classification
            content = f"""
            Filename: {media_file.filename}
            File Type: {media_file.file_type}
            Size: {media_file.size} bytes
            Customer: {media_file.customer or 'unknown'}
            Project: {media_file.project or 'unknown'}
            Metadata: {json.dumps(media_file.metadata, indent=2)}
            """
            
            # Get classification
            classification = await llm_classifier.classify_document(content)
            
            return {
                "category": classification.get("category", "unknown"),
                "tags": classification.get("tags", []),
                "confidence": classification.get("confidence", 0.0)
            }
            
        except Exception as e:
            logger.error(f"Error classifying media file: {e}")
            return None
    
    def search_media_files(self, search_request: MediaSearchRequest) -> List[MediaFile]:
        """Search media files based on criteria"""
        results = []
        
        for media_file in self.media_files.values():
            # Apply filters
            if search_request.customer and media_file.customer != search_request.customer:
                continue
            
            if search_request.project and media_file.project != search_request.project:
                continue
            
            if search_request.category and media_file.category != search_request.category:
                continue
            
            if search_request.file_type and media_file.file_type != search_request.file_type:
                continue
            
            if search_request.tags:
                if not any(tag in media_file.tags for tag in search_request.tags):
                    continue
            
            if search_request.size_min and media_file.size < search_request.size_min:
                continue
            
            if search_request.size_max and media_file.size > search_request.size_max:
                continue
            
            if search_request.date_from:
                date_from = datetime.fromisoformat(search_request.date_from)
                file_date = datetime.fromisoformat(media_file.created_at)
                if file_date < date_from:
                    continue
            
            if search_request.date_to:
                date_to = datetime.fromisoformat(search_request.date_to)
                file_date = datetime.fromisoformat(media_file.created_at)
                if file_date > date_to:
                    continue
            
            results.append(media_file)
        
        return results

# Global footage manager instance
footage_manager = FootageManager()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        return {
            "status": "healthy",
            "service": "footage-service",
            "media_files": len(footage_manager.media_files),
            "llm_classifier": "available" if llm_classifier else "unavailable"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")

@app.post("/upload", response_model=MediaFile)
async def upload_media_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    request: MediaUploadRequest = Depends()
):
    """Upload media file"""
    try:
        # Validate file size
        if file.size and file.size > config.max_file_size:
            raise HTTPException(status_code=413, detail="File too large")
        
        # Process file
        media_file = await footage_manager.process_uploaded_file(file, request)
        
        return media_file
        
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


class BatchUploadResponse(BaseModel):
    items: List[MediaFile] = []
    errors: List[Dict[str, Any]] = []


@app.post("/upload/batch", response_model=BatchUploadResponse)
async def upload_media_files_batch(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    request: MediaUploadRequest = Depends(),
):
    """Batch upload multiple media files with per-file processing and dedup handling."""
    results: List[MediaFile] = []
    errors: List[Dict[str, Any]] = []
    for f in files:
        try:
            media_file = await footage_manager.process_uploaded_file(f, request)
            results.append(media_file)
        except HTTPException as he:
            errors.append({"filename": f.filename, "error": he.detail})
        except Exception as e:
            errors.append({"filename": f.filename, "error": str(e)})
    return BatchUploadResponse(items=results, errors=errors)

class PagedFilesResponse(BaseModel):
    items: List[MediaFile]
    total: int


@app.get("/files", response_model=PagedFilesResponse)
async def list_media_files(
    customer: Optional[str] = None,
    project: Optional[str] = None,
    category: Optional[str] = None,
    file_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    sort_by: Optional[str] = None,
    sort_dir: Optional[str] = "desc"
):
    """List media files with optional filtering"""
    try:
        files = list(footage_manager.media_files.values())
        
        # Apply filters
        if customer:
            files = [f for f in files if f.customer == customer]
        if project:
            files = [f for f in files if f.project == project]
        if category:
            files = [f for f in files if f.category == category]
        if file_type:
            files = [f for f in files if f.file_type == file_type]

        total = len(files)

        # Sorting
        key_map = {
            'created_at': lambda f: f.created_at,
            'updated_at': lambda f: f.updated_at,
            'size': lambda f: f.size,
            'filename': lambda f: f.filename.lower(),
        }
        if sort_by in key_map:
            files.sort(key=key_map[sort_by], reverse=(sort_dir or 'desc').lower() == 'desc')
        
        # Apply pagination
        items = files[offset:offset + limit]
        
        return PagedFilesResponse(items=items, total=total)
        
    except Exception as e:
        logger.error(f"Error listing files: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list files: {str(e)}")

@app.post("/search", response_model=List[MediaFile])
async def search_media_files(request: MediaSearchRequest):
    """Search media files"""
    try:
        results = footage_manager.search_media_files(request)
        return results
        
    except Exception as e:
        logger.error(f"Error searching files: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/files/{file_id}", response_model=MediaFile)
async def get_media_file(file_id: str):
    """Get specific media file"""
    if file_id not in footage_manager.media_files:
        raise HTTPException(status_code=404, detail="File not found")
    
    return footage_manager.media_files[file_id]

@app.get("/files/{file_id}/download")
async def download_media_file(file_id: str):
    """Download media file"""
    if file_id not in footage_manager.media_files:
        raise HTTPException(status_code=404, detail="File not found")
    
    media_file = footage_manager.media_files[file_id]
    file_path = Path(media_file.original_path)
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found on disk")
    
    return FileResponse(
        path=file_path,
        filename=media_file.filename,
        media_type=media_file.mime_type
    )

@app.get("/files/{file_id}/thumbnail")
async def get_media_thumbnail(file_id: str, size: str = "300x300"):
    """Get media file thumbnail"""
    if file_id not in footage_manager.media_files:
        raise HTTPException(status_code=404, detail="File not found")
    
    media_file = footage_manager.media_files[file_id]
    
    if not media_file.thumbnail_path:
        raise HTTPException(status_code=404, detail="Thumbnail not available")
    
    thumbnail_path = Path(media_file.thumbnail_path)
    
    if not thumbnail_path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail not found on disk")
    
    return FileResponse(
        path=thumbnail_path,
        media_type="image/jpeg"
    )

@app.delete("/files/{file_id}")
async def delete_media_file(file_id: str):
    """Delete media file"""
    if file_id not in footage_manager.media_files:
        raise HTTPException(status_code=404, detail="File not found")
    
    try:
        media_file = footage_manager.media_files[file_id]
        
        # Delete original file
        file_path = Path(media_file.original_path)
        if file_path.exists():
            file_path.unlink()
        
        # Delete thumbnail
        if media_file.thumbnail_path:
            thumbnail_path = Path(media_file.thumbnail_path)
            if thumbnail_path.exists():
                thumbnail_path.unlink()
        
        # Remove from storage
        del footage_manager.media_files[file_id]
        
        return {"message": "File deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting file {file_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete file: {str(e)}")

@app.get("/statistics")
async def get_statistics():
    """Get media file statistics"""
    try:
        files = list(footage_manager.media_files.values())
        
        stats = {
            "total_files": len(files),
            "total_size": sum(f.size for f in files),
            "by_type": {},
            "by_customer": {},
            "by_category": {},
            "recent_uploads": len([f for f in files if datetime.fromisoformat(f.created_at) > datetime.now() - timedelta(days=7)])
        }
        
        # Count by type
        for file_type in ["image", "video", "design"]:
            stats["by_type"][file_type] = len([f for f in files if f.file_type == file_type])
        
        # Count by customer
        customers = set(f.customer for f in files if f.customer)
        for customer in customers:
            stats["by_customer"][customer] = len([f for f in files if f.customer == customer])
        
        # Count by category
        categories = set(f.category for f in files)
        for category in categories:
            stats["by_category"][category] = len([f for f in files if f.category == category])
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@app.post("/import-from-share")
async def import_from_share(req: ImportFromShareRequest):
    """Import selected files from heterogeneous shares via storage-manager.
    For each path, stream download from storage-manager and process into local repository with dedup.
    """
    try:
        imported: List[Dict[str, Any]] = []
        errors: List[Dict[str, Any]] = []
        customer_dir = footage_manager.footage_path / (req.customer or "unknown")
        project_dir = customer_dir / (req.project or "general")
        project_dir.mkdir(parents=True, exist_ok=True)
        async with httpx.AsyncClient(timeout=None) as client:
            for p in req.paths:
                try:
                    # Request storage-manager download
                    resp = await client.post(f"{req.storage_manager_url.rstrip('/')}/download", json={"share": req.share, "path": p})
                    if resp.status_code != 200:
                        errors.append({"path": p, "error": f"HTTP {resp.status_code}"})
                        continue
                    # Determine filename
                    name = os.path.basename(p) or f"import_{hashlib.md5(p.encode()).hexdigest()}"
                    dest = project_dir / name
                    with open(dest, 'wb') as out:
                        async for chunk in resp.aiter_bytes(chunk_size=1024*1024):
                            out.write(chunk)
                    # Process saved file (dedup aware)
                    media = footage_manager._process_saved_path(dest, name, MediaUploadRequest(
                        customer=req.customer,
                        project=req.project,
                        category=req.category,
                        generate_thumbnail=req.generate_thumbnail,
                        extract_metadata=req.extract_metadata,
                        enable_classification=req.enable_classification,
                    ))
                    imported.append(media.dict())
                except HTTPException as he:
                    # If duplicate, we keep as error with existing id
                    errors.append({"path": p, "error": he.detail})
                    try:
                        if dest and dest.exists():
                            dest.unlink()
                    except Exception:
                        pass
                except Exception as e:
                    errors.append({"path": p, "error": str(e)})
        return {"imported": imported, "errors": errors}
    except Exception as e:
        logger.error(f"Import from share error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 