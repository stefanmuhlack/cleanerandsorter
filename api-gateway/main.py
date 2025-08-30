"""
API Gateway for CAS Platform
Central entry point for all services with authentication, rate limiting, and monitoring.
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
import httpx
import jwt
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import redis.asyncio as redis
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('gateway_requests_total', 'Total requests through gateway', ['service', 'method', 'status'])
REQUEST_LATENCY = Histogram('gateway_request_duration_seconds', 'Request latency through gateway', ['service'])

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# Security
security = HTTPBearer()

# Redis for caching and rate limiting
redis_client: Optional[redis.Redis] = None

# Service configurations
SERVICES = {
    'ingest': {
        'url': 'http://ingest-service:8000',
        'health_check': '/api/health',
        'timeout': 30,
        'rate_limit': '100/minute'
    },
    'email': {
        'url': 'http://email-processor:8000',
        'health_check': '/health',
        'timeout': 15,
        'rate_limit': '50/minute'
    },
    'footage': {
        'url': 'http://footage-service:8000',
        'health_check': '/health',
        'timeout': 20,
        'rate_limit': '30/minute'
    },
    'llm': {
        'url': 'http://llm-manager:8000',
        'health_check': '/health',
        'timeout': 60,
        'rate_limit': '20/minute'
    },
    'otrs': {
        'url': 'http://otrs-integration:8000',
        'health_check': '/health',
        'timeout': 10,
        'rate_limit': '100/minute'
    },
    'backup': {
        'url': 'http://backup-service:8000',
        'health_check': '/health',
        'timeout': 30,
        'rate_limit': '10/minute'
    }
}

# JWT configuration
JWT_SECRET = "your-super-secret-jwt-key-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = 24 * 60 * 60  # 24 hours

app = FastAPI(
    title="CAS API Gateway",
    description="Central API Gateway for CAS Document Management Platform",
    version="1.0.0"
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Health check cache
health_cache: Dict[str, Dict[str, Any]] = {}
health_cache_ttl = 30  # seconds


async def get_redis() -> redis.Redis:
    """Get Redis client."""
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url("redis://redis:6379", decode_responses=True)
    return redis_client


async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Verify JWT token and return user information."""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def check_service_health(service_name: str, service_config: Dict[str, Any]) -> Dict[str, Any]:
    """Check health of a specific service."""
    try:
        async with httpx.AsyncClient(timeout=service_config['timeout']) as client:
            response = await client.get(f"{service_config['url']}{service_config['health_check']}")
            return {
                'status': 'healthy' if response.status_code == 200 else 'unhealthy',
                'response_time': response.elapsed.total_seconds(),
                'status_code': response.status_code,
                'last_check': datetime.utcnow().isoformat()
            }
    except Exception as e:
        logger.error(f"Health check failed for {service_name}: {e}")
        return {
            'status': 'unhealthy',
            'error': str(e),
            'last_check': datetime.utcnow().isoformat()
        }


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("API Gateway starting up...")
    await get_redis()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global redis_client
    if redis_client:
        await redis_client.close()
    logger.info("API Gateway shutting down...")


@app.middleware("http")
async def gateway_middleware(request: Request, call_next):
    """Main gateway middleware for monitoring and routing."""
    start_time = time.time()
    
    # Extract service from path
    path_parts = request.url.path.strip('/').split('/')
    service_name = path_parts[0] if path_parts else None
    
    # Process request
    response = await call_next(request)
    
    # Calculate duration
    duration = time.time() - start_time
    
    # Record metrics
    if service_name and service_name in SERVICES:
        REQUEST_COUNT.labels(
            service=service_name,
            method=request.method,
            status=response.status_code
        ).inc()
        REQUEST_LATENCY.labels(service=service_name).observe(duration)
    
    # Add response headers
    response.headers["X-Gateway-Processing-Time"] = str(duration)
    response.headers["X-Gateway-Service"] = service_name or "unknown"
    
    return response


@app.get("/health")
async def gateway_health():
    """Gateway health check endpoint."""
    return {
        "status": "healthy",
        "service": "api-gateway",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@app.get("/health/all")
async def all_services_health():
    """Check health of all services."""
    health_results = {}
    
    # Check cache first
    redis_client = await get_redis()
    cached_health = await redis_client.get("gateway:health_cache")
    
    if cached_health:
        import json
        health_results = json.loads(cached_health)
        cache_age = datetime.utcnow() - datetime.fromisoformat(health_results.get('cache_time', '1970-01-01T00:00:00'))
        
        if cache_age.total_seconds() < health_cache_ttl:
            return health_results
    
    # Perform fresh health checks
    health_tasks = []
    for service_name, service_config in SERVICES.items():
        task = check_service_health(service_name, service_config)
        health_tasks.append((service_name, task))
    
    # Execute health checks concurrently
    for service_name, task in health_tasks:
        health_results[service_name] = await task
    
    # Add cache timestamp
    health_results['cache_time'] = datetime.utcnow().isoformat()
    
    # Cache results
    await redis_client.setex(
        "gateway:health_cache",
        health_cache_ttl,
        json.dumps(health_results)
    )
    
    return health_results


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@app.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit("100/minute")
async def proxy_request(
    request: Request,
    service: str,
    path: str,
    user: Dict[str, Any] = Depends(verify_token)
):
    """Proxy requests to appropriate services."""
    if service not in SERVICES:
        raise HTTPException(status_code=404, detail=f"Service '{service}' not found")
    
    service_config = SERVICES[service]
    
    # Check rate limiting per service
    rate_limit_key = f"rate_limit:{service}:{user.get('user_id', 'anonymous')}"
    redis_client = await get_redis()
    
    current_requests = await redis_client.get(rate_limit_key)
    if current_requests and int(current_requests) >= int(service_config['rate_limit'].split('/')[0]):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    # Increment rate limit counter
    await redis_client.incr(rate_limit_key)
    await redis_client.expire(rate_limit_key, 60)  # Reset after 1 minute
    
    # Prepare request to service
    target_url = f"{service_config['url']}/{path}"
    
    # Get request body
    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        body = await request.body()
    
    # Get headers (filter out some headers)
    headers = dict(request.headers)
    headers_to_remove = ['host', 'content-length', 'transfer-encoding']
    for header in headers_to_remove:
        headers.pop(header.lower(), None)
    
    # Add user context
    headers['X-User-ID'] = user.get('user_id', 'anonymous')
    headers['X-User-Role'] = user.get('role', 'user')
    
    try:
        async with httpx.AsyncClient(timeout=service_config['timeout']) as client:
            response = await client.request(
                method=request.method,
                url=target_url,
                params=request.query_params,
                headers=headers,
                content=body
            )
            
            # Return response
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
            
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail=f"Service '{service}' timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail=f"Service '{service}' unavailable")
    except Exception as e:
        logger.error(f"Error proxying request to {service}: {e}")
        raise HTTPException(status_code=500, detail="Internal gateway error")


@app.post("/auth/login")
async def login(username: str, password: str):
    """Authenticate user and return JWT token."""
    # In production, validate against database
    if username == "admin" and password == "admin123":
        payload = {
            'user_id': 'admin',
            'username': username,
            'role': 'admin',
            'exp': datetime.utcnow() + timedelta(seconds=JWT_EXPIRATION)
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return {"access_token": token, "token_type": "bearer"}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")


@app.get("/services")
async def list_services():
    """List all available services."""
    return {
        "services": list(SERVICES.keys()),
        "service_configs": {
            name: {
                "url": config["url"],
                "timeout": config["timeout"],
                "rate_limit": config["rate_limit"]
            }
            for name, config in SERVICES.items()
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
