from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
import asyncio
import aiohttp
import logging
import time
from typing import Dict, Any
from datetime import datetime
import psycopg2
from minio import Minio
import pika
from elasticsearch import Elasticsearch

logger = logging.getLogger(__name__)
router = APIRouter()

class HealthChecker:
    def __init__(self, config):
        self.config = config
        self.elasticsearch_url = config.get('elasticsearch_url', 'http://elasticsearch:9200')
        self.minio_endpoint = config.get('minio_endpoint', 'minio:9000')
        self.minio_access_key = config.get('minio_access_key', 'minioadmin')
        self.minio_secret_key = config.get('minio_secret_key', 'minioadmin')
        self.rabbitmq_url = config.get('rabbitmq_url', 'amqp://cas_user:cas_password@rabbitmq:5672/')
        self.postgres_url = config.get('postgres_url', 'postgresql://cas_user:cas_password@postgres:5432/cas_dms')

    async def check_elasticsearch(self) -> Dict[str, Any]:
        """Check Elasticsearch connectivity and cluster health"""
        try:
            start_time = time.perf_counter()
            es = Elasticsearch([self.elasticsearch_url], timeout=5)
            cluster_health = es.cluster.health()
            info = es.info()
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            
            return {
                "status": "healthy",
                "cluster_health": cluster_health,
                "version": info.get('version', {}).get('number'),
                "response_time_ms": duration_ms
            }
        except Exception as e:
            logger.warning(f"Elasticsearch health check failed: {e}")
            return {
                "status": "unavailable",
                "error": str(e)
            }

    async def check_minio(self) -> Dict[str, Any]:
        """Check MinIO connectivity and bucket access"""
        try:
            client = Minio(
                self.minio_endpoint,
                access_key=self.minio_access_key,
                secret_key=self.minio_secret_key,
                secure=False
            )
            
            # List buckets to test connectivity
            buckets = list(client.list_buckets())
            
            return {
                "status": "healthy",
                "buckets_count": len(buckets),
                "buckets": [bucket.name for bucket in buckets]
            }
        except Exception as e:
            logger.error(f"MinIO health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    async def check_rabbitmq(self) -> Dict[str, Any]:
        """Check RabbitMQ connectivity and queue status"""
        try:
            connection = pika.BlockingConnection(pika.URLParameters(self.rabbitmq_url))
            channel = connection.channel()
            
            # Get queue info
            queue_info = channel.queue_declare(queue='ingest_queue', passive=True)
            
            connection.close()
            
            return {
                "status": "healthy",
                "queue_messages": queue_info.method.message_count,
                "queue_consumers": queue_info.method.consumer_count
            }
        except Exception as e:
            logger.error(f"RabbitMQ health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    async def check_postgres(self) -> Dict[str, Any]:
        """Check PostgreSQL connectivity and database status"""
        try:
            conn = psycopg2.connect(self.postgres_url)
            cursor = conn.cursor()
            
            # Check database size
            cursor.execute("""
                SELECT pg_size_pretty(pg_database_size(current_database())) as db_size,
                       current_database() as db_name
            """)
            db_info = cursor.fetchone()
            
            # Check table counts
            cursor.execute("""
                SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del
                FROM pg_stat_user_tables
                ORDER BY n_tup_ins DESC
                LIMIT 5
            """)
            table_stats = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return {
                "status": "healthy",
                "database_size": db_info[0],
                "database_name": db_info[1],
                "table_stats": [
                    {
                        "schema": row[0],
                        "table": row[1],
                        "inserts": row[2],
                        "updates": row[3],
                        "deletes": row[4]
                    } for row in table_stats
                ]
            }
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }

    async def check_ollama(self) -> Dict[str, Any]:
        """Check Ollama LLM service connectivity"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get('http://ollama:11434/api/tags') as response:
                    if response.status == 200:
                        models = await response.json()
                        return {
                            "status": "healthy",
                            "models_count": len(models.get('models', [])),
                            "models": [model['name'] for model in models.get('models', [])]
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "error": f"HTTP {response.status}"
                        }
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e)
            }

@router.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    from app.infrastructure.config import get_config
    
    config = get_config()
    checker = HealthChecker(config)
    
    # Run all health checks concurrently
    checks = await asyncio.gather(
        checker.check_elasticsearch(),
        checker.check_minio(),
        checker.check_rabbitmq(),
        checker.check_postgres(),
        checker.check_ollama(),
        return_exceptions=True
    )
    
    es_status, minio_status, rabbitmq_status, postgres_status, ollama_status = checks
    
    # Determine overall health - only consider critical services
    critical_services = [minio_status, postgres_status]  # ES and others are optional
    all_critical_healthy = all(
        isinstance(check, dict) and check.get('status') in ['healthy', 'unavailable']
        for check in critical_services
    )
    
    response = {
        "status": "healthy" if all_critical_healthy else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "ingest-service",
        "version": "1.0.0",
        "dependencies": {
            "elasticsearch": es_status,
            "minio": minio_status,
            "rabbitmq": rabbitmq_status,
            "postgres": postgres_status,
            "ollama": ollama_status
        }
    }
    
    if not all_critical_healthy:
        response["status"] = "degraded"
        response["unhealthy_services"] = [
            service for service, status in response["dependencies"].items()
            if isinstance(status, dict) and status.get('status') not in ['healthy', 'unavailable']
        ]
    
    status_code = 200 if all_critical_healthy else 503
    return JSONResponse(content=response, status_code=status_code)

@router.get("/health/simple")
async def simple_health_check():
    """Simple health check for load balancers"""
    return {"status": "healthy", "service": "ingest-service"}

@router.get("/health/ready")
async def readiness_check():
    """Readiness check for Kubernetes"""
    from app.infrastructure.config import get_config
    
    config = get_config()
    checker = HealthChecker(config)
    
    # Check critical dependencies
    es_status, minio_status, postgres_status = await asyncio.gather(
        checker.check_elasticsearch(),
        checker.check_minio(),
        checker.check_postgres(),
        return_exceptions=True
    )
    
    critical_healthy = all(
        isinstance(check, dict) and check.get('status') == 'healthy'
        for check in [es_status, minio_status, postgres_status]
    )
    
    if critical_healthy:
        return {"status": "ready"}
    else:
        raise HTTPException(status_code=503, detail="Service not ready")
