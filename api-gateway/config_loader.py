"""
Configuration Loader for API Gateway
Loads service configurations from YAML files for declarative configuration management.
"""

import yaml
import os
from typing import Dict, Any, Optional
from pathlib import Path

class GatewayConfigLoader:
    """Loads and manages API Gateway configuration from YAML files."""
    
    def __init__(self, config_path: str = "config/gateway-services.yml"):
        self.config_path = config_path
        self.config: Optional[Dict[str, Any]] = None
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        try:
            # Try to load from the specified path
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as file:
                    self.config = yaml.safe_load(file)
            else:
                # Fallback to default configuration
                self.config = self._get_default_config()
                print(f"Warning: Config file {self.config_path} not found, using default configuration")
                
        except Exception as e:
            print(f"Error loading configuration: {e}")
            self.config = self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Return default configuration if YAML file is not available."""
        return {
            'services': {
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
            },
            'direct_routes': {
                'upload': 'ingest',
                'processing': 'ingest',
                'health': 'ingest',
                'metrics': 'ingest'
            },
            'api_routes': {
                'metrics': {
                    'business': {
                        'path': '/api/metrics/business',
                        'method': 'GET',
                        'authentication': False,
                        'mock_data': True
                    }
                },
                'audit': {
                    'logs': {
                        'path': '/api/audit/logs',
                        'method': 'GET',
                        'authentication': False,
                        'mock_data': True
                    }
                },
                'users': {
                    'list': {
                        'path': '/users/',
                        'method': 'GET',
                        'authentication': False,
                        'mock_data': True
                    }
                }
            },
            'gateway': {
                'jwt_secret': 'your-super-secret-jwt-key-change-in-production',
                'jwt_algorithm': 'HS256',
                'jwt_expiration': 86400,
                'health_cache_ttl': 30,
                'rate_limit_default': '100/minute',
                'cors_origins': ['*'],
                'trusted_hosts': ['*']
            },
            'monitoring': {
                'prometheus_enabled': True,
                'request_logging': True,
                'health_check_interval': 30,
                'service_timeout_default': 30
            }
        }
    
    def get_services(self) -> Dict[str, Any]:
        """Get services configuration."""
        return self.config.get('services', {})
    
    def get_direct_routes(self) -> Dict[str, str]:
        """Get direct route mappings."""
        return self.config.get('direct_routes', {})
    
    def get_api_routes(self) -> Dict[str, Any]:
        """Get API-specific routes configuration."""
        return self.config.get('api_routes', {})
    
    def get_gateway_config(self) -> Dict[str, Any]:
        """Get gateway configuration."""
        return self.config.get('gateway', {})
    
    def get_monitoring_config(self) -> Dict[str, Any]:
        """Get monitoring configuration."""
        return self.config.get('monitoring', {})
    
    def reload_config(self) -> None:
        """Reload configuration from file."""
        self._load_config()
    
    def get_api_route_config(self, path: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific API route."""
        api_routes = self.get_api_routes()
        
        # Search through the nested structure
        for category, routes in api_routes.items():
            for route_name, route_config in routes.items():
                if route_config.get('path') == path:
                    return route_config
        
        return None
    
    def is_api_route(self, path: str) -> bool:
        """Check if a path is configured as an API route."""
        return self.get_api_route_config(path) is not None
    
    def get_mock_data_config(self, path: str) -> Optional[Dict[str, Any]]:
        """Get mock data configuration for a route."""
        route_config = self.get_api_route_config(path)
        if route_config and route_config.get('mock_data'):
            return route_config
        return None

# Global configuration loader instance
config_loader = GatewayConfigLoader()
