# API Gateway Configuration Guide

## Overview

The API Gateway now supports **declarative configuration** through YAML files, allowing you to manage services, routes, and settings without modifying code. This makes the system more maintainable and configurable.

## Configuration Files

### Main Configuration File: `config/gateway-services.yml`

This file contains all service definitions, routing rules, and gateway settings.

## Configuration Structure

### Services Configuration

```yaml
services:
  ingest:
    url: "http://cas_ingest:8000"
    health_check: "/health"
    timeout: 30
    rate_limit: "100/minute"
    description: "Document ingestion and processing service"
```

**Service Properties:**
- `url`: Service endpoint URL
- `health_check`: Health check endpoint path
- `timeout`: Request timeout in seconds
- `rate_limit`: Rate limiting rules (e.g., "100/minute")
- `description`: Human-readable service description

### Direct Route Mappings

```yaml
direct_routes:
  upload: "ingest"
  processing: "ingest"
  health: "ingest"
  metrics: "ingest"
```

Maps frontend route names to actual service names for compatibility.

### API-Specific Routes

```yaml
api_routes:
  metrics:
    business:
      path: "/api/metrics/business"
      method: "GET"
      authentication: false
      description: "Business metrics aggregation endpoint"
      mock_data: true
```

**Route Properties:**
- `path`: API endpoint path
- `method`: HTTP method (GET, POST, etc.)
- `authentication`: Whether authentication is required
- `description`: Route description
- `mock_data`: Whether to return mock data

### Gateway Configuration

```yaml
gateway:
  jwt_secret: "your-super-secret-jwt-key-change-in-production"
  jwt_algorithm: "HS256"
  jwt_expiration: 86400  # 24 hours in seconds
  health_cache_ttl: 30  # seconds
  rate_limit_default: "100/minute"
  cors_origins: ["*"]
  trusted_hosts: ["*"]
```

### Monitoring Configuration

```yaml
monitoring:
  prometheus_enabled: true
  request_logging: true
  health_check_interval: 30  # seconds
  service_timeout_default: 30  # seconds
```

## Adding New Services

To add a new service:

1. **Edit `config/gateway-services.yml`**
2. **Add service definition:**
   ```yaml
   services:
     new_service:
       url: "http://cas_new_service:8000"
       health_check: "/health"
       timeout: 30
       rate_limit: "50/minute"
       description: "New service description"
   ```

3. **Add route mappings if needed:**
   ```yaml
   direct_routes:
     new_route: "new_service"
   ```

4. **Restart the API Gateway:**
   ```bash
   docker-compose restart api-gateway
   ```

## Adding New API Routes

To add a new API route:

1. **Edit `config/gateway-services.yml`**
2. **Add route definition:**
   ```yaml
   api_routes:
     new_category:
       new_endpoint:
         path: "/api/new/endpoint"
         method: "GET"
         authentication: false
         description: "New API endpoint"
         mock_data: true
   ```

3. **Restart the API Gateway:**
   ```bash
   docker-compose restart api-gateway
   ```

## Configuration Validation

The API Gateway validates configuration on startup:

- ✅ **Service URLs**: Must be valid URLs
- ✅ **Rate Limits**: Must follow "number/period" format
- ✅ **Timeouts**: Must be positive integers
- ✅ **JWT Settings**: Must be valid JWT configuration

## Fallback Configuration

If the YAML file is not found or invalid, the API Gateway uses built-in default configuration to ensure system stability.

## Hot Reloading

Currently, configuration changes require a restart of the API Gateway. Future versions may support hot reloading.

## Best Practices

### 1. **Consistent Naming**
- Use descriptive service names
- Follow consistent URL patterns
- Use clear route descriptions

### 2. **Security**
- Change default JWT secrets in production
- Use appropriate rate limits
- Configure CORS origins properly

### 3. **Monitoring**
- Enable Prometheus metrics
- Set appropriate health check intervals
- Configure request logging

### 4. **Performance**
- Set appropriate timeouts
- Configure rate limits based on service capacity
- Use health check caching

## Troubleshooting

### Configuration Not Loading
- Check file path: `config/gateway-services.yml`
- Verify YAML syntax
- Check file permissions

### Routes Not Working
- Verify route definitions in YAML
- Check service health status
- Review API Gateway logs

### Authentication Issues
- Verify JWT configuration
- Check authentication settings in routes
- Review token expiration settings

## Example Complete Configuration

```yaml
# API Gateway Services Configuration
services:
  ingest:
    url: "http://cas_ingest:8000"
    health_check: "/health"
    timeout: 30
    rate_limit: "100/minute"
    description: "Document ingestion and processing service"
    
  email:
    url: "http://cas_email_processor:8000"
    health_check: "/health"
    timeout: 15
    rate_limit: "50/minute"
    description: "Email processing and notification service"

direct_routes:
  upload: "ingest"
  processing: "ingest"
  health: "ingest"
  metrics: "ingest"

api_routes:
  metrics:
    business:
      path: "/api/metrics/business"
      method: "GET"
      authentication: false
      description: "Business metrics aggregation endpoint"
      mock_data: true
      
  audit:
    logs:
      path: "/api/audit/logs"
      method: "GET"
      authentication: false
      description: "Audit logs endpoint"
      mock_data: true

gateway:
  jwt_secret: "your-super-secret-jwt-key-change-in-production"
  jwt_algorithm: "HS256"
  jwt_expiration: 86400
  health_cache_ttl: 30
  rate_limit_default: "100/minute"
  cors_origins: ["*"]
  trusted_hosts: ["*"]
  
monitoring:
  prometheus_enabled: true
  request_logging: true
  health_check_interval: 30
  service_timeout_default: 30
```

## Migration from Code-Based Configuration

If you're migrating from the old code-based configuration:

1. **Export current settings** from `main.py`
2. **Create YAML configuration** using the structure above
3. **Test configuration** with a subset of services
4. **Gradually migrate** all services
5. **Remove hardcoded configurations** from `main.py`

This approach ensures a smooth transition without service disruption.
