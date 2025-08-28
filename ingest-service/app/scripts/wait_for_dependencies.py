#!/usr/bin/env python3
"""
Script to wait for external dependencies to become available.
"""

import asyncio
import os
import sys
import logging
import asyncpg
import aiohttp
from minio import Minio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def wait_for_postgres() -> bool:
    host = os.getenv("POSTGRES_HOST", "postgres")
    port = int(os.getenv("POSTGRES_PORT", "5432"))
    user = os.getenv("POSTGRES_USER", "cas_user")
    password = os.getenv("POSTGRES_PASSWORD", "cas_password")
    database = os.getenv("POSTGRES_DB", "cas_dms")
    logger.info(f"Waiting for PostgreSQL at {host}:{port}...")
    for attempt in range(30):
        try:
            conn = await asyncpg.connect(host=host, port=port, user=user, password=password, database=database)
            await conn.close()
            logger.info("PostgreSQL is ready")
            return True
        except Exception as e:
            logger.info(f"PostgreSQL not ready, attempt {attempt + 1}/30: {e}")
            await asyncio.sleep(2)
    logger.error("PostgreSQL connection timeout")
    return False

async def wait_for_minio() -> bool:
    endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
    access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    secret_key = os.getenv("MINIO_SECRET_KEY", "minioadmin")
    logger.info(f"Waiting for MinIO at {endpoint}...")
    for attempt in range(30):
        try:
            client = Minio(endpoint=endpoint, access_key=access_key, secret_key=secret_key, secure=False)
            client.list_buckets()
            logger.info("MinIO is ready")
            return True
        except Exception as e:
            logger.info(f"MinIO not ready, attempt {attempt + 1}/30: {e}")
            await asyncio.sleep(2)
    logger.error("MinIO connection timeout")
    return False

async def wait_for_rabbitmq() -> bool:
    host = os.getenv("RABBITMQ_HOST", "rabbitmq")
    port = int(os.getenv("RABBITMQ_PORT", "5672"))
    user = os.getenv("RABBITMQ_USER", "cas_user")
    password = os.getenv("RABBITMQ_PASSWORD", "cas_password")
    logger.info(f"Waiting for RabbitMQ at {host}:{port}...")
    for attempt in range(30):
        try:
            # Try to connect to RabbitMQ management API
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://{host}:15672/api/overview", 
                                     auth=aiohttp.BasicAuth(user, password)) as response:
                    if response.status == 200:
                        logger.info("RabbitMQ is ready")
                        return True
        except Exception as e:
            logger.info(f"RabbitMQ not ready, attempt {attempt + 1}/30: {e}")
            await asyncio.sleep(2)
    logger.error("RabbitMQ connection timeout")
    return False

async def wait_for_elasticsearch() -> bool:
    url = os.getenv("ELASTICSEARCH_URL", "http://elasticsearch:9200")
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
    """Wait for all dependencies to become available."""
    logger.info("Waiting for dependencies...")
    
    # Wait for all services
    postgres_ready = await wait_for_postgres()
    minio_ready = await wait_for_minio()
    rabbitmq_ready = await wait_for_rabbitmq()
    elasticsearch_ready = await wait_for_elasticsearch()
    
    if all([postgres_ready, minio_ready, rabbitmq_ready, elasticsearch_ready]):
        logger.info("All dependencies are ready!")
        return True
    else:
        logger.error("Some dependencies failed to start")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1) 