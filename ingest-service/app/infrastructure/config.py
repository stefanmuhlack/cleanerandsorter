"""
Configuration settings for the ingest service.
"""

import os
from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Database settings
    database_url: str = "postgresql+asyncpg://cas_user:cas_password@postgres:5432/cas_dms"
    
    # MinIO settings
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False
    minio_region: Optional[str] = None
    
    # RabbitMQ settings
    rabbitmq_url: str = "amqp://cas_user:cas_password@rabbitmq:5672/"
    
    # Elasticsearch settings
    elasticsearch_url: str = "http://elasticsearch:9200"
    
    # Application settings
    log_level: str = "INFO"
    debug: bool = False
    
    # File processing settings
    source_directory: str = "/data/source"
    sorted_directory: str = "/data/sorted"
    max_file_size: int = 100 * 1024 * 1024  # 100MB
    supported_extensions: list = [
        ".pdf", ".doc", ".docx", ".xls", ".xlsx", 
        ".ppt", ".pptx", ".txt", ".jpg", ".jpeg", 
        ".png", ".gif", ".bmp", ".tiff"
    ]
    
    # Processing settings
    batch_size: int = 10
    processing_timeout: int = 300  # 5 minutes
    
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = False 