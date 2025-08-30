"""
API Gateway for CAS Platform
Central entry point for all services with authentication, rate limiting, and monitoring.
"""

import asyncio
import json
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
        'url': 'http://cas_ingest:8000',
        'health_check': '/health',
        'timeout': 30,
        'rate_limit': '100/minute'
    },
    'email': {
        'url': 'http://cas_email_processor:8000',
        'health_check': '/health',
        'timeout': 15,
        'rate_limit': '50/minute'
    },
    'footage': {
        'url': 'http://cas_footage_service:8000',
        'health_check': '/health',
        'timeout': 20,
        'rate_limit': '30/minute'
    },
    'llm': {
        'url': 'http://cas_llm_manager:8000',
        'health_check': '/health',
        'timeout': 60,
        'rate_limit': '20/minute'
    },
    'otrs': {
        'url': 'http://cas_otrs_integration:8000',
        'health_check': '/health',
        'timeout': 10,
        'rate_limit': '100/minute'
    },
    'backup': {
        'url': 'http://cas_backup_service:8000',
        'health_check': '/health',
        'timeout': 30,
        'rate_limit': '10/minute'
    },
    'tld': {
        'url': 'http://cas_tld_manager:8000',
        'health_check': '/health',
        'timeout': 15,
        'rate_limit': '50/minute'
    }
}

# Direct route mappings for frontend compatibility
DIRECT_ROUTES = {
    'upload': 'ingest',
    'processing': 'ingest',
    'health': 'ingest',
    'metrics': 'ingest'
}

# JWT configuration
JWT_SECRET = "your-super-secret-jwt-key-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = 24 * 60 * 60  # 24 hours

# Health check cache TTL
health_cache_ttl = 30  # seconds

# Create FastAPI app
app = FastAPI(
    title="CAS API Gateway",
    description="Central API Gateway for CAS Platform",
    version="1.0.0"
)

# Add middleware
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

# Add rate limiting exception handler
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Redis connection
async def get_redis():
    global redis_client
    if redis_client is None:
        redis_client = redis.Redis(host='cas_redis', port=6379, db=0, decode_responses=True)
    return redis_client

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize Redis connection on startup."""
    await get_redis()
    logger.info("API Gateway started successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    global redis_client
    if redis_client:
        await redis_client.close()
    logger.info("API Gateway shutting down...")

# Health check functions
async def check_service_health(service_name: str, service_config: Dict[str, Any]) -> Dict[str, Any]:
    """Check health of a specific service."""
    start_time = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{service_config['url']}{service_config['health_check']}")
            
            duration = time.time() - start_time
            
            if response.status_code == 200:
                return {
                    "status": "healthy",
                    "response_time": round(duration, 3),
                    "status_code": response.status_code,
                    "last_check": datetime.utcnow().isoformat()
                }
            else:
                return {
                    "status": "unhealthy",
                    "error": f"HTTP {response.status_code}",
                    "response_time": round(duration, 3),
                    "status_code": response.status_code,
                    "last_check": datetime.utcnow().isoformat()
                }
                
    except httpx.TimeoutException:
        return {
            "status": "unhealthy",
            "error": "Timeout",
            "response_time": round(time.time() - start_time, 3),
            "last_check": datetime.utcnow().isoformat()
        }
    except httpx.ConnectError:
        return {
            "status": "unhealthy",
            "error": "Connection refused",
            "response_time": round(time.time() - start_time, 3),
            "last_check": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "response_time": round(time.time() - start_time, 3),
            "last_check": datetime.utcnow().isoformat()
        }

# Authentication middleware
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Validate JWT token and return user information."""
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Gateway middleware
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

# Health endpoints
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

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

# Specific API routes (must come before generic service routing)
@app.get("/api/metrics/business")
async def get_business_metrics():
    """Get business metrics - MOCK IMPLEMENTATION."""
    return {
        "total_revenue": 1250000,
        "monthly_growth": 12.5,
        "active_users": 1250,
        "conversion_rate": 3.2,
        "average_order_value": 450,
        "customer_satisfaction": 4.8,
        "top_products": [
            {"name": "Premium Package", "sales": 45000},
            {"name": "Standard Package", "sales": 32000},
            {"name": "Basic Package", "sales": 28000}
        ],
        "revenue_by_month": [
            {"month": "Jan", "revenue": 95000},
            {"month": "Feb", "revenue": 105000},
            {"month": "Mar", "revenue": 115000},
            {"month": "Apr", "revenue": 125000}
        ]
    }

@app.get("/api/audit/logs")
async def get_audit_logs(limit: int = 50):
    """Get audit logs - MOCK IMPLEMENTATION."""
    return {
        "logs": [
            {
                "id": "1",
                "timestamp": "2024-01-15T10:30:00Z",
                "user": "admin",
                "action": "file_upload",
                "details": "Uploaded invoice_2024_001.pdf",
                "ip_address": "192.168.1.100",
                "status": "success"
            },
            {
                "id": "2",
                "timestamp": "2024-01-15T10:25:00Z",
                "user": "user123",
                "action": "login",
                "details": "User logged in successfully",
                "ip_address": "192.168.1.101",
                "status": "success"
            },
            {
                "id": "3",
                "timestamp": "2024-01-15T10:20:00Z",
                "user": "admin",
                "action": "system_config",
                "details": "Updated processing configuration",
                "ip_address": "192.168.1.100",
                "status": "success"
            }
        ],
        "total": 3,
        "limit": limit
    }

@app.get("/users/")
async def get_users():
    """Get users - MOCK IMPLEMENTATION."""
    return {
        "users": [
            {
                "id": "1",
                "username": "admin",
                "email": "admin@company.com",
                "role": "admin",
                "status": "active",
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "id": "2",
                "username": "user123",
                "email": "user123@company.com",
                "role": "user",
                "status": "active",
                "created_at": "2024-01-02T00:00:00Z"
            }
        ],
        "total": 2
    }

# Generic service routing (with authentication)
@app.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit("100/minute")
async def proxy_request(
    request: Request,
    service: str,
    path: str,
    user: Dict[str, Any] = Depends(get_current_user)
):
    """Proxy requests to appropriate services."""
    # Check if this is a direct route mapping
    if service in DIRECT_ROUTES:
        service = DIRECT_ROUTES[service]
    
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

# Authentication endpoints
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

# Service information
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
