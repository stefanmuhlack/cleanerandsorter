"""
MinIO object storage repository implementation.
"""

import asyncio
import logging
from typing import List, Optional
from urllib.parse import urlparse

import aiofiles
from minio import Minio
from minio.error import S3Error

from app.domain.repositories import ObjectStorageRepository

logger = logging.getLogger(__name__)


class MinioObjectStorageRepository(ObjectStorageRepository):
    """MinIO implementation of ObjectStorageRepository."""
    
    def __init__(
        self,
        endpoint: str,
        access_key: str,
        secret_key: str,
        secure: bool = False,
        region: Optional[str] = None
    ):
        self.endpoint = endpoint
        self.access_key = access_key
        self.secret_key = secret_key
        self.secure = secure
        self.region = region
        
        # Initialize MinIO client
        self.client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure,
            region=region
        )
        
        # Ensure default bucket exists
        asyncio.create_task(self._ensure_default_bucket())
    
    async def upload_file(self, file_path: str, bucket: str, key: str) -> bool:
        """Upload a file to object storage."""
        try:
            # Ensure bucket exists
            await self._ensure_bucket_exists(bucket)
            
            # Upload file
            self.client.fput_object(
                bucket_name=bucket,
                object_name=key,
                file_path=file_path
            )
            
            logger.info(f"Successfully uploaded {file_path} to {bucket}/{key}")
            return True
            
        except S3Error as e:
            logger.error(f"Failed to upload {file_path} to {bucket}/{key}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error uploading {file_path}: {e}")
            return False
    
    async def download_file(self, bucket: str, key: str, local_path: str) -> bool:
        """Download a file from object storage."""
        try:
            # Download file
            self.client.fget_object(
                bucket_name=bucket,
                object_name=key,
                file_path=local_path
            )
            
            logger.info(f"Successfully downloaded {bucket}/{key} to {local_path}")
            return True
            
        except S3Error as e:
            logger.error(f"Failed to download {bucket}/{key} to {local_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error downloading {bucket}/{key}: {e}")
            return False
    
    async def delete_file(self, bucket: str, key: str) -> bool:
        """Delete a file from object storage."""
        try:
            self.client.remove_object(bucket_name=bucket, object_name=key)
            
            logger.info(f"Successfully deleted {bucket}/{key}")
            return True
            
        except S3Error as e:
            logger.error(f"Failed to delete {bucket}/{key}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error deleting {bucket}/{key}: {e}")
            return False
    
    async def file_exists(self, bucket: str, key: str) -> bool:
        """Check if a file exists in object storage."""
        try:
            self.client.stat_object(bucket_name=bucket, object_name=key)
            return True
        except S3Error as e:
            if e.code == 'NoSuchKey':
                return False
            logger.error(f"Error checking if {bucket}/{key} exists: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error checking {bucket}/{key}: {e}")
            return False
    
    async def get_file_url(self, bucket: str, key: str, expires_in: int = 3600) -> str:
        """Get a presigned URL for a file."""
        try:
            url = self.client.presigned_get_object(
                bucket_name=bucket,
                object_name=key,
                expires=expires_in
            )
            return url
        except S3Error as e:
            logger.error(f"Failed to generate presigned URL for {bucket}/{key}: {e}")
            return ""
        except Exception as e:
            logger.error(f"Unexpected error generating presigned URL: {e}")
            return ""
    
    async def list_files(self, bucket: str, prefix: str = "") -> List[str]:
        """List files in a bucket with optional prefix."""
        try:
            objects = self.client.list_objects(
                bucket_name=bucket,
                prefix=prefix,
                recursive=True
            )
            
            file_keys = []
            for obj in objects:
                file_keys.append(obj.object_name)
            
            return file_keys
            
        except S3Error as e:
            logger.error(f"Failed to list files in {bucket} with prefix {prefix}: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error listing files: {e}")
            return []
    
    async def get_file_metadata(self, bucket: str, key: str) -> Optional[dict]:
        """Get metadata for a file."""
        try:
            stat = self.client.stat_object(bucket_name=bucket, object_name=key)
            return {
                "size": stat.size,
                "last_modified": stat.last_modified,
                "etag": stat.etag,
                "content_type": stat.content_type,
                "metadata": stat.metadata
            }
        except S3Error as e:
            logger.error(f"Failed to get metadata for {bucket}/{key}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting metadata: {e}")
            return None
    
    async def copy_file(self, source_bucket: str, source_key: str, dest_bucket: str, dest_key: str) -> bool:
        """Copy a file within object storage."""
        try:
            # Ensure destination bucket exists
            await self._ensure_bucket_exists(dest_bucket)
            
            # Copy object
            self.client.copy_object(
                bucket_name=dest_bucket,
                object_name=dest_key,
                source=f"{source_bucket}/{source_key}"
            )
            
            logger.info(f"Successfully copied {source_bucket}/{source_key} to {dest_bucket}/{dest_key}")
            return True
            
        except S3Error as e:
            logger.error(f"Failed to copy {source_bucket}/{source_key} to {dest_bucket}/{dest_key}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error copying file: {e}")
            return False
    
    async def _ensure_bucket_exists(self, bucket: str) -> None:
        """Ensure a bucket exists, create it if it doesn't."""
        try:
            if not self.client.bucket_exists(bucket):
                self.client.make_bucket(bucket)
                logger.info(f"Created bucket: {bucket}")
        except S3Error as e:
            logger.error(f"Error ensuring bucket {bucket} exists: {e}")
        except Exception as e:
            logger.error(f"Unexpected error ensuring bucket exists: {e}")
    
    async def _ensure_default_bucket(self) -> None:
        """Ensure the default documents bucket exists."""
        await self._ensure_bucket_exists("documents")
    
    async def get_bucket_size(self, bucket: str) -> int:
        """Get the total size of all files in a bucket."""
        try:
            objects = self.client.list_objects(bucket_name=bucket, recursive=True)
            total_size = sum(obj.size for obj in objects)
            return total_size
        except S3Error as e:
            logger.error(f"Failed to get size for bucket {bucket}: {e}")
            return 0
        except Exception as e:
            logger.error(f"Unexpected error getting bucket size: {e}")
            return 0
    
    async def get_bucket_file_count(self, bucket: str) -> int:
        """Get the total number of files in a bucket."""
        try:
            objects = self.client.list_objects(bucket_name=bucket, recursive=True)
            return len(list(objects))
        except S3Error as e:
            logger.error(f"Failed to get file count for bucket {bucket}: {e}")
            return 0
        except Exception as e:
            logger.error(f"Unexpected error getting bucket file count: {e}")
            return 0 