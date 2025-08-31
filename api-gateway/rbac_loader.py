import yaml
from typing import Dict, Any

class RBAC:
    def __init__(self, path: str = "config/gateway-rbac.yml"):
        self.path = path
        self.model: Dict[str, Any] = {"roles": {}, "permissions": {}}
        self.load()

    def load(self) -> None:
        try:
            with open(self.path, 'r', encoding='utf-8') as f:
                self.model = yaml.safe_load(f) or {"roles": {}, "permissions": {}}
        except Exception:
            self.model = {"roles": {}, "permissions": {}}

    def is_allowed(self, role: str, service: str, method: str, path: str) -> bool:
        # Admin has full access by default
        if role == 'admin':
            return True
        perms = self.model.get("permissions", {}).get(service, {})
        method_perms = perms.get(method.upper()) or {}
        allowed_roles = set(method_perms.get("roles", []))
        if role not in allowed_roles:
            return False
        # naive path match: exact, prefix with wildcard support "**" and trailing "*"
        allowed_paths = method_perms.get("paths", [])
        for pattern in allowed_paths:
            if self._match(pattern, path):
                return True
        return False

    def _match(self, pattern: str, path: str) -> bool:
        # strip leading slashes for uniformity
        pattern = pattern.lstrip('/')
        path = path.lstrip('/')
        if pattern == path:
            return True
        if pattern.endswith('/**'):
            return path.startswith(pattern[:-3])
        if pattern.endswith('/*'):
            base = pattern[:-2]
            return path.startswith(base) and '/' not in path[len(base)+1:]
        return False

rbac = RBAC()
