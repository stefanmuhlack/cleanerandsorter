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
REQUEST_RBAC_DENIED = Counter('gateway_rbac_denials_total', 'RBAC denied requests', ['service', 'method', 'role'])

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# Security (optional auth for RBAC/public routes)
security = HTTPBearer(auto_error=False)

# Redis for caching and rate limiting
redis_client: Optional[redis.Redis] = None

# Import configuration loader
from config_loader import config_loader
from rbac_loader import rbac

# Load configurations from YAML
SERVICES = config_loader.get_services()
DIRECT_ROUTES = config_loader.get_direct_routes()
GATEWAY_CONFIG = config_loader.get_gateway_config()
MONITORING_CONFIG = config_loader.get_monitoring_config()

# JWT configuration from YAML
JWT_SECRET = GATEWAY_CONFIG.get('jwt_secret', "your-super-secret-jwt-key-change-in-production")
JWT_ALGORITHM = GATEWAY_CONFIG.get('jwt_algorithm', "HS256")
JWT_EXPIRATION = GATEWAY_CONFIG.get('jwt_expiration', 24 * 60 * 60)  # 24 hours

# Health check cache TTL from YAML
health_cache_ttl = GATEWAY_CONFIG.get('health_cache_ttl', 30)  # seconds

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

# Runtime config reload
def reload_runtime_config() -> Dict[str, Any]:
    global SERVICES, DIRECT_ROUTES, GATEWAY_CONFIG, MONITORING_CONFIG, JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRATION, health_cache_ttl
    config_loader.reload_config()
    SERVICES = config_loader.get_services()
    DIRECT_ROUTES = config_loader.get_direct_routes()
    GATEWAY_CONFIG = config_loader.get_gateway_config()
    MONITORING_CONFIG = config_loader.get_monitoring_config()
    JWT_SECRET = GATEWAY_CONFIG.get('jwt_secret', JWT_SECRET)
    JWT_ALGORITHM = GATEWAY_CONFIG.get('jwt_algorithm', JWT_ALGORITHM)
    JWT_EXPIRATION = GATEWAY_CONFIG.get('jwt_expiration', JWT_EXPIRATION)
    health_cache_ttl = GATEWAY_CONFIG.get('health_cache_ttl', health_cache_ttl)
    # Reload RBAC
    rbac.load()
    return {
        "services": list(SERVICES.keys()),
        "direct_routes": DIRECT_ROUTES,
        "jwt_algorithm": JWT_ALGORITHM,
        "health_cache_ttl": health_cache_ttl
    }

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
                # Try to parse degraded/warning state from response body
                status_text = "unhealthy"
                error_text: Optional[str] = None
                try:
                    data = response.json()
                    if isinstance(data, dict):
                        if data.get("status") == "degraded":
                            status_text = "warning"
                        error_text = data.get("error") or data.get("detail")
                except Exception:
                    pass
                return {
                    "status": status_text,
                    "error": error_text or f"HTTP {response.status_code}",
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

# Authentication dependencies
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Require JWT; used for admin endpoints and strict auth routes."""
    if not credentials or not credentials.credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_optional_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict[str, Any]:
    """Return user if token provided; otherwise anonymous marker for RBAC/public routes."""
    if credentials and credentials.credentials:
        try:
            payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            payload['_auth'] = True
            return payload
        except Exception:
            # Invalid token still treated as unauthenticated
            return {'user_id': 'anonymous', 'role': 'anonymous', '_auth': False}
    return {'user_id': 'anonymous', 'role': 'anonymous', '_auth': False}

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

@app.post("/admin/reload-config")
async def admin_reload_config(user: Dict[str, Any] = Depends(get_current_user)):
    """Admin-only: reload gateway YAML configs and RBAC; clear health cache."""
    if user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Forbidden")
    summary = reload_runtime_config()
    try:
        rc = await get_redis()
        await rc.delete("gateway:health_cache")
    except Exception:
        pass
    return {"reloaded": True, **summary}

@app.post("/api/admin/reload-config")
async def admin_reload_config_api(user: Dict[str, Any] = Depends(get_current_user)):
    """Admin-only: reload via /api namespace to avoid catch-all conflicts."""
    if user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Forbidden")
    summary = reload_runtime_config()
    try:
        rc = await get_redis()
        await rc.delete("gateway:health_cache")
    except Exception:
        pass
    return {"reloaded": True, **summary}

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

# Specific API routes (MUST come before any generic routing)
# These routes are configured in config/gateway-services.yml

@app.get("/api/metrics/business")
async def get_business_metrics(user: Dict[str, Any] = Depends(get_current_user)):
    """Business metrics placeholder with no mock data. Returns 204 when unavailable."""
    if user.get('role') not in ['admin', 'user']:
        raise HTTPException(status_code=403, detail="Forbidden")
    return Response(status_code=204)

@app.get("/api/audit/logs")
async def get_audit_logs(limit: int = 50, user: Dict[str, Any] = Depends(get_current_user)):
    """Audit logs placeholder with no mock data. Returns empty result until audit store is implemented."""
    if user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Forbidden")
    return {"logs": [], "total": 0, "limit": limit}

@app.get("/users/")
async def get_users(user: Dict[str, Any] = Depends(get_current_user)):
    """Users placeholder with no mock data. Returns empty result until user service is integrated."""
    if user.get('role') != 'admin':
        raise HTTPException(status_code=403, detail="Forbidden")
    return {"users": [], "total": 0}



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

# Helper function that encapsulates the actual proxy logic
async def forward_request(service: str, path: str, request: Request, user: Dict[str, Any]) -> Response:
    """Forward request to appropriate service with rate limiting and error handling."""
    # Map "frontend names" to service names
    if service in DIRECT_ROUTES:
        service = DIRECT_ROUTES[service]

    if service not in SERVICES:
        raise HTTPException(status_code=404, detail=f"Service '{service}' not found")

    service_config = SERVICES[service]
    redis_client = await get_redis()

    # Rate limit per user and service
    rate_limit_key = f"rate_limit:{service}:{user.get('user_id', 'anonymous')}"
    current_requests = await redis_client.get(rate_limit_key)
    limit, _ = service_config["rate_limit"].split("/")
    if current_requests and int(current_requests) >= int(limit):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    await redis_client.incr(rate_limit_key)
    await redis_client.expire(rate_limit_key, 60)

    # Build target URL
    target_url = f"{service_config['url']}/{path}"
    body = await request.body() if request.method in {"POST", "PUT", "PATCH"} else None

    # Transfer headers (without Host, Content-Length etc.)
    headers = {k: v for k, v in request.headers.items()
               if k.lower() not in {"host", "content-length", "transfer-encoding"}}
    headers["X-User-ID"] = user.get("user_id", "anonymous")
    headers["X-User-Role"] = user.get("role", "user")

    try:
        async with httpx.AsyncClient(timeout=service_config["timeout"]) as client:
            resp = await client.request(
                method=request.method,
                url=target_url,
                params=request.query_params,
                headers=headers,
                content=body,
            )
        return Response(
            content=resp.content,
            status_code=resp.status_code,
            headers=dict(resp.headers),
        )
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail=f"Service '{service}' timeout")
    except httpx.ConnectError:
        raise HTTPException(status_code=503, detail=f"Service '{service}' unavailable")
    except Exception as e:
        logger.error(f"Error proxying request to {service}: {e}")
        raise HTTPException(status_code=500, detail="Internal gateway error")

# Specific API routes with /api prefix (MUST come before generic catch-all route)
@app.get("/test/status")
async def get_test_status():
    """Placeholder: return no content."""
    return Response(status_code=204)

@app.api_route("/api/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit("100/minute")
async def proxy_api_route(
    request: Request,
    service: str,
    path: str,
    user: Dict[str, Any] = Depends(get_optional_user),
) -> Response:
    """Proxy requests with /api prefix to appropriate services."""
    # RBAC check
    role = user.get('role', 'user')
    path_for_rbac = path or ""
    logger.info(f"RBAC check /api: role={role} service={service} path={path_for_rbac}")
    # Temporary allowance: authenticated users can GET ingest processing resources
    if user.get('_auth', False) and service == 'ingest' and request.method.upper() == 'GET' and path_for_rbac.startswith('processing/'):
        return await forward_request(service, path, request, user)
    if role == 'admin':
        return await forward_request(service, path, request, user)
    if not rbac.is_allowed(role, service, request.method, path_for_rbac):
        REQUEST_RBAC_DENIED.labels(service=service, method=request.method, role=role).inc()
        if not user.get('_auth', False):
            raise HTTPException(status_code=401, detail="Not authenticated")
        raise HTTPException(status_code=403, detail="Forbidden by RBAC policy")
    # For /api/upload e.g., service becomes "upload" and forward_request logic is used
    return await forward_request(service, path, request, user)

# Generic service routing (with authentication)
@app.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
@limiter.limit("100/minute")
async def proxy_request(
    request: Request,
    service: str,
    path: str,
    user: Dict[str, Any] = Depends(get_optional_user)
):
    """Proxy requests to appropriate services."""
    # Check if this is a direct route mapping
    if service in DIRECT_ROUTES:
        service = DIRECT_ROUTES[service]
    
    if service not in SERVICES:
        raise HTTPException(status_code=404, detail=f"Service '{service}' not found")
    
    service_config = SERVICES[service]

    # RBAC check for generic routes
    role = user.get('role', 'user')
    path_for_rbac = path or ""
    logger.info(f"RBAC check generic: role={role} service={service} path={path_for_rbac}")
    # Temporary allowance: authenticated users can GET ingest processing resources
    if user.get('_auth', False) and service == 'ingest' and request.method.upper() == 'GET' and path_for_rbac.startswith('processing/'):
        pass
    if role == 'admin':
        pass
    if not rbac.is_allowed(role, service, request.method, path_for_rbac):
        REQUEST_RBAC_DENIED.labels(service=service, method=request.method, role=role).inc()
        if not user.get('_auth', False):
            raise HTTPException(status_code=401, detail="Not authenticated")
        raise HTTPException(status_code=403, detail="Forbidden by RBAC policy")
    
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
