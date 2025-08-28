"""
Domain services for the indexing service.
These contain the core business logic for file indexing operations.
"""

import asyncio
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from uuid import UUID

import magic
from PIL import Image
import pytesseract
import fitz  # PyMuPDF

from .entities import (
    IndexedFile, IndexingBatch, IndexingStatistics,
    IndexingStatus, IndexingPriority
)
from .repositories import (
    IndexedFileRepository, IndexingBatchRepository,
    ElasticsearchRepository, MessageQueueRepository
)


logger = logging.getLogger(__name__)


class FileIndexingService:
    """Service for indexing files into Elasticsearch."""
    
    def __init__(
        self,
        file_repo: IndexedFileRepository,
        batch_repo: IndexingBatchRepository,
        elasticsearch_repo: ElasticsearchRepository,
        message_repo: MessageQueueRepository
    ):
        self.file_repo = file_repo
        self.batch_repo = batch_repo
        self.elasticsearch_repo = elasticsearch_repo
        self.message_repo = message_repo
    
    async def index_file(self, file_path: Path, priority: IndexingPriority = IndexingPriority.NORMAL) -> IndexedFile:
        """Index a single file."""
        try:
            # Create indexed file entity
            indexed_file = await self._create_indexed_file_entity(file_path, priority)
            
            # Extract file metadata
            indexed_file.metadata = await self._extract_file_metadata(file_path)
            
            # Determine file type
            indexed_file.file_type = self._determine_file_type(indexed_file.metadata.get('mime_type', ''))
            
            # Extract text content if supported
            if self._supports_text_extraction(indexed_file.file_type):
                indexed_file.extracted_text = await self._extract_text_content(file_path, indexed_file.file_type)
            
            # Generate content hash
            indexed_file.content_hash = await self._generate_content_hash(file_path)
            
            # Save to database
            indexed_file = await self.file_repo.save(indexed_file)
            
            # Index in Elasticsearch
            success = await self.elasticsearch_repo.index_file(indexed_file)
            if success:
                indexed_file.update_status(IndexingStatus.COMPLETED)
            else:
                indexed_file.update_status(IndexingStatus.FAILED, "Failed to index in Elasticsearch")
            
            # Update database
            await self.file_repo.save(indexed_file)
            
            # Publish indexing completion message
            await self._publish_indexing_completion_message(indexed_file)
            
            return indexed_file
            
        except Exception as e:
            logger.error("Failed to index file", file_path=str(file_path), error=str(e))
            if 'indexed_file' in locals():
                indexed_file.update_status(IndexingStatus.FAILED, str(e))
                await self.file_repo.save(indexed_file)
            raise
    
    async def index_batch(self, file_paths: List[Path], batch_name: str, priority: IndexingPriority = IndexingPriority.NORMAL) -> IndexingBatch:
        """Index a batch of files."""
        try:
            # Create batch entity
            batch = IndexingBatch(
                name=batch_name,
                file_count=len(file_paths),
                source_path=Path("/data/sorted"),
                priority=priority
            )
            batch = await self.batch_repo.save(batch)
            
            # Start processing
            batch.start_processing()
            await self.batch_repo.save(batch)
            
            # Process files concurrently
            tasks = []
            for file_path in file_paths:
                task = self._index_file_with_batch_tracking(file_path, batch, priority)
                tasks.append(task)
            
            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Update batch statistics
            for result in results:
                if isinstance(result, Exception):
                    batch.increment_failed()
                else:
                    batch.increment_processed()
            
            # Complete batch
            if batch.failed_count == 0:
                batch.complete_processing()
            else:
                batch.fail_processing(f"Failed to index {batch.failed_count} files")
            
            await self.batch_repo.save(batch)
            
            # Publish batch completion message
            await self._publish_batch_completion_message(batch)
            
            return batch
            
        except Exception as e:
            logger.error("Failed to process indexing batch", batch_name=batch_name, error=str(e))
            if 'batch' in locals():
                batch.fail_processing(str(e))
                await self.batch_repo.save(batch)
            raise
    
    async def reindex_file(self, file_id: UUID) -> IndexedFile:
        """Reindex an existing file."""
        indexed_file = await self.file_repo.get_by_id(file_id)
        if not indexed_file:
            raise ValueError(f"File with ID {file_id} not found")
        
        # Reset status
        indexed_file.update_status(IndexingStatus.PENDING)
        await self.file_repo.save(indexed_file)
        
        # Reindex
        return await self.index_file(Path(indexed_file.file_path), indexed_file.priority)
    
    async def search_files(self, query: str, filters: Optional[Dict[str, Any]] = None, limit: int = 50) -> List[IndexedFile]:
        """Search for files using Elasticsearch."""
        search_results = await self.elasticsearch_repo.search_files(query, filters, limit)
        
        # Convert to domain entities
        files = []
        for result in search_results:
            file_id = UUID(result['_id'])
            indexed_file = await self.file_repo.get_by_id(file_id)
            if indexed_file:
                files.append(indexed_file)
        
        return files
    
    async def get_indexing_statistics(self) -> IndexingStatistics:
        """Get comprehensive indexing statistics."""
        return await self.file_repo.get_statistics()
    
    async def _create_indexed_file_entity(self, file_path: Path, priority: IndexingPriority) -> IndexedFile:
        """Create an indexed file entity from a file path."""
        return IndexedFile(
            file_path=file_path,
            filename=file_path.name,
            file_size=file_path.stat().st_size,
            priority=priority
        )
    
    async def _extract_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from a file."""
        metadata = {}
        
        try:
            # Basic file info
            stat = file_path.stat()
            metadata.update({
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'accessed': datetime.fromtimestamp(stat.st_atime).isoformat(),
            })
            
            # MIME type
            mime_type = magic.from_file(str(file_path), mime=True)
            metadata['mime_type'] = mime_type
            
            # File extension
            metadata['extension'] = file_path.suffix.lower()
            
        except Exception as e:
            logger.warning("Failed to extract metadata", file_path=str(file_path), error=str(e))
        
        return metadata
    
    def _determine_file_type(self, mime_type: str) -> str:
        """Determine file type from MIME type."""
        if mime_type.startswith('image/'):
            return 'image'
        elif mime_type == 'application/pdf':
            return 'pdf'
        elif mime_type.startswith('text/'):
            return 'text'
        elif mime_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
            return 'document'
        elif mime_type in ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']:
            return 'spreadsheet'
        elif mime_type in ['application/vnd.ms-powerpoint', 'application/vnd.openxmlformats-officedocument.presentationml.presentation']:
            return 'presentation'
        else:
            return 'unknown'
    
    def _supports_text_extraction(self, file_type: str) -> bool:
        """Check if file type supports text extraction."""
        return file_type in ['pdf', 'text', 'image']
    
    async def _extract_text_content(self, file_path: Path, file_type: str) -> Optional[str]:
        """Extract text content from file."""
        try:
            if file_type == 'pdf':
                return await self._extract_pdf_text(file_path)
            elif file_type == 'text':
                return await self._extract_text_file_content(file_path)
            elif file_type == 'image':
                return await self._extract_image_text(file_path)
            else:
                return None
        except Exception as e:
            logger.warning("Failed to extract text content", file_path=str(file_path), error=str(e))
            return None
    
    async def _extract_pdf_text(self, file_path: Path) -> str:
        """Extract text from PDF file."""
        text = ""
        try:
            doc = fitz.open(str(file_path))
            for page in doc:
                text += page.get_text()
            doc.close()
        except Exception as e:
            logger.error("Failed to extract PDF text", file_path=str(file_path), error=str(e))
        return text
    
    async def _extract_text_file_content(self, file_path: Path) -> str:
        """Extract content from text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()
    
    async def _extract_image_text(self, file_path: Path) -> str:
        """Extract text from image using OCR."""
        try:
            image = Image.open(file_path)
            text = pytesseract.image_to_string(image, lang='eng+deu')
            return text
        except Exception as e:
            logger.error("Failed to extract image text", file_path=str(file_path), error=str(e))
            return ""
    
    async def _generate_content_hash(self, file_path: Path) -> str:
        """Generate content hash for file."""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
        except Exception as e:
            logger.error("Failed to generate content hash", file_path=str(file_path), error=str(e))
        return hash_md5.hexdigest()
    
    async def _index_file_with_batch_tracking(self, file_path: Path, batch: IndexingBatch, priority: IndexingPriority) -> IndexedFile:
        """Index a file and track progress in batch."""
        try:
            return await self.index_file(file_path, priority)
        except Exception as e:
            logger.error("Failed to index file in batch", file_path=str(file_path), batch_id=str(batch.id), error=str(e))
            raise
    
    async def _publish_indexing_completion_message(self, indexed_file: IndexedFile) -> None:
        """Publish message when file indexing is completed."""
        message = {
            'event_type': 'file_indexed',
            'file_id': str(indexed_file.id),
            'file_path': str(indexed_file.file_path),
            'status': indexed_file.indexing_status.value,
            'timestamp': datetime.utcnow().isoformat()
        }
        await self.message_repo.publish_message("indexing_events", message)
    
    async def _publish_batch_completion_message(self, batch: IndexingBatch) -> None:
        """Publish message when batch indexing is completed."""
        message = {
            'event_type': 'batch_indexed',
            'batch_id': str(batch.id),
            'batch_name': batch.name,
            'status': batch.status.value,
            'processed_count': batch.processed_count,
            'failed_count': batch.failed_count,
            'timestamp': datetime.utcnow().isoformat()
        }
        await self.message_repo.publish_message("indexing_events", message)


class IndexingBatchService:
    """Service for managing indexing batches."""
    
    def __init__(self, batch_repo: IndexingBatchRepository):
        self.batch_repo = batch_repo
    
    async def create_batch(self, name: str, description: Optional[str] = None, priority: IndexingPriority = IndexingPriority.NORMAL) -> IndexingBatch:
        """Create a new indexing batch."""
        batch = IndexingBatch(
            name=name,
            description=description,
            priority=priority,
            source_path=Path("/data/sorted")
        )
        return await self.batch_repo.save(batch)
    
    async def get_batch(self, batch_id: UUID) -> Optional[IndexingBatch]:
        """Get a batch by ID."""
        return await self.batch_repo.get_by_id(batch_id)
    
    async def get_recent_batches(self, limit: int = 10) -> List[IndexingBatch]:
        """Get recent indexing batches."""
        return await self.batch_repo.get_recent_batches(limit)
    
    async def get_batches_by_status(self, status: IndexingStatus) -> List[IndexingBatch]:
        """Get batches by status."""
        return await self.batch_repo.get_by_status(status.value)
    
    async def delete_batch(self, batch_id: UUID) -> bool:
        """Delete an indexing batch."""
        return await self.batch_repo.delete(batch_id) 