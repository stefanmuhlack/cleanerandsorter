#!/usr/bin/env python3
"""
Script to wait for dependencies to be ready before starting the application.
"""

import asyncio
import logging
import os
import sys
from typing import Optional

import aiohttp
import asyncpg
from minio import Minio
from minio.error import S3Error

logger = logging.getLogger(__name__)


async def wait_for_postgres() -> bool:
    """Wait for PostgreSQL to be ready."""
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = int(os.getenv("POSTGRES_PORT", "5432"))
    user = os.getenv("POSTGRES_USER", "cas_user")
    password = os.getenv("POSTGRES_PASSWORD", "cas_password")
    database = os.getenv("POSTGRES_DB", "cas_dms")
    
    logger.info(f"Waiting for PostgreSQL at {host}:{port}...")
    
    for attempt in range(30):
        try:
            conn = await asyncpg.connect(
                host=host,
                port=port,
                user=user,
                password=password,
                database=database
            )
            await conn.close()
            logger.info("PostgreSQL is ready")
            return True
        except Exception as e:
            logger.info(f"PostgreSQL not ready, attempt {attempt + 1}/30: {e}")
            await asyncio.sleep(2)
    
    logger.error("PostgreSQL connection timeout")
    return False


async def wait_for_minio() -> bool:
    """Wait for MinIO to be ready."""
    endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    secure = os.getenv("MINIO_SECURE", "false").lower() == "true"
    
    logger.info(f"Waiting for MinIO at {endpoint}...")
    
    for attempt in range(30):
        try:
            client = Minio(
                endpoint=endpoint,
                access_key=access_key,
                secret_key=secret_key,
                secure=secure
            )
            
            # Try to list buckets
            client.list_buckets()
            logger.info("MinIO is ready")
            return True
        except Exception as e:
            logger.info(f"MinIO not ready, attempt {attempt + 1}/30: {e}")
            await asyncio.sleep(2)
    
    logger.error("MinIO connection timeout")
    return False


async def wait_for_rabbitmq() -> bool:
    """Wait for RabbitMQ to be ready."""
    host = os.getenv("RABBITMQ_HOST", "localhost")
    port = int(os.getenv("RABBITMQ_PORT", "5672"))
    user = os.getenv("RABBITMQ_USER", "cas_user")
    password = os.getenv("RABBITMQ_PASSWORD", "cas_password")
    
    logger.info(f"Waiting for RabbitMQ at {host}:{port}...")
    
    for attempt in range(30):
        try:
            # Try to connect to RabbitMQ management API
            management_port = 15672
            url = f"http://{host}:{management_port}/api/overview"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, auth=aiohttp.BasicAuth(user, password)) as response:
                    if response.status == 200:
                        logger.info("RabbitMQ is ready")
                        return True
        except Exception as e:
            logger.info(f"RabbitMQ not ready, attempt {attempt + 1}/30: {e}")
            await asyncio.sleep(2)
    
    logger.error("RabbitMQ connection timeout")
    return False


async def wait_for_elasticsearch() -> bool:
    """Wait for Elasticsearch to be ready."""
    url = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
    
    logger.info(f"Waiting for Elasticsearch at {url}...")
    
    for attempt in range(30):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{url}/_cluster/health") as response:
                    if response.status == 200:
                        logger.info("Elasticsearch is ready")
                        return True
        except Exception as e:
            logger.info(f"Elasticsearch not ready, attempt {attempt + 1}/30: {e}")
            await asyncio.sleep(2)
    
    logger.error("Elasticsearch connection timeout")
    return False


async def main():
    """Wait for all dependencies to be ready."""
    logger.info("Waiting for dependencies...")
    
    # Wait for all dependencies
    results = await asyncio.gather(
        wait_for_postgres(),
        wait_for_minio(),
        wait_for_rabbitmq(),
        wait_for_elasticsearch(),
        return_exceptions=True
    )
    
    # Check results
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Dependency {i} failed: {result}")
            sys.exit(1)
        elif not result:
            logger.error(f"Dependency {i} timeout")
            sys.exit(1)
    
    logger.info("All dependencies are ready")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main()) 