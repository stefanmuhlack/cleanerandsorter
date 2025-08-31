from fastapi import FastAPI, Body
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

app = FastAPI(title="CAS Storage Manager", version="1.0.0")


@app.get("/health")
async def health() -> Dict[str, Any]:
    return {
        "status": "healthy",
        "service": "storage-manager"
    }


class Credentials(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None


class Share(BaseModel):
    url: str
    base_path: Optional[str] = None
    credentials: Optional[Credentials] = None
    policy: Optional[Dict[str, Any]] = None


class DetectRequest(Share):
    pass


@app.post("/detect")
async def detect(req: DetectRequest) -> Dict[str, Any]:
    url = req.url.lower().strip()
    stype = "unknown"
    if url.startswith("file://"):
        stype = "local"
    elif url.startswith("smb://") or url.startswith("cifs://"):
        stype = "smb"
    elif url.startswith("dav://") or url.startswith("davs://") or url.startswith("webdav://"):
        stype = "webdav"
    elif "sharepoint" in url or url.endswith("sharepoint.com"):
        stype = "sharepoint"
    return {"type": stype, "supported": stype != "unknown"}


class TestRequest(BaseModel):
    url: str
    credentials: Optional[Credentials] = None


@app.post("/test")
async def test_share(req: TestRequest) -> Dict[str, Any]:
    # Minimal stub: respond OK; deeper connectivity checks can be added per adapter
    return {"ok": True}


class ListRequest(BaseModel):
    share: Share
    path: Optional[str] = None


@app.post("/list")
async def list_path(req: ListRequest) -> List[Dict[str, Any]]:
    # Minimal stub: return empty listing to keep UI functional when no adapter configured
    return []


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

#!/usr/bin/env python3
"""
Storage Manager Service
Auto-detects and connects to heterogeneous file shares: SMB/CIFS, NFS/local, WebDAV (Nextcloud/OwnCloud), SharePoint Online.
Provides a unified API for testing connectivity, listing directories, and basic download streaming.
"""

import os
import io
import logging
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Storage Manager",
    description="Unified access to heterogeneous file shares with autodetection",
    version="1.0.0",
)


class ShareCredentials(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    domain: Optional[str] = None
    client_id: Optional[str] = None  # SharePoint
    client_secret: Optional[str] = None  # SharePoint
    tenant: Optional[str] = None  # SharePoint tenant or authority


class ShareConfig(BaseModel):
    url: str = Field(..., description="Share endpoint. Examples: smb://server/share, nfs:///mnt/media, davs://host/remote.php/webdav, https://tenant.sharepoint.com/sites/site")
    base_path: Optional[str] = Field(None, description="Base path within the share")
    credentials: Optional[ShareCredentials] = None
    policy: Optional[Dict[str, bool]] = Field(default_factory=lambda: {"read": True, "write": False, "delete": False})


class ListRequest(BaseModel):
    share: ShareConfig
    path: Optional[str] = None


class DownloadRequest(BaseModel):
    share: ShareConfig
    path: str


def detect_scheme(url: str) -> str:
    lower = url.lower()
    if lower.startswith("smb://") or lower.startswith("cifs://"):
        return "smb"
    if lower.startswith("nfs://") or lower.startswith("file://") or lower.startswith("/"):
        return "local"
    if lower.startswith("dav://") or lower.startswith("davs://") or "/webdav" in lower:
        return "webdav"
    if "sharepoint.com" in lower:
        return "sharepoint"
    return "unknown"


# Adapters
class LocalAdapter:
    @staticmethod
    def test(share: ShareConfig) -> Dict[str, Any]:
        path = share.url.replace("file://", "") if share.url.startswith("file://") else share.url
        ok = os.path.isdir(path)
        return {"ok": ok, "path": path}

    @staticmethod
    def list_dir(share: ShareConfig, path: Optional[str]) -> List[Dict[str, Any]]:
        base = share.url.replace("file://", "") if share.url.startswith("file://") else share.url
        full = os.path.join(base, path or "")
        if not os.path.isdir(full):
            raise HTTPException(status_code=404, detail="Directory not found")
        entries = []
        for name in sorted(os.listdir(full)):
            p = os.path.join(full, name)
            try:
                stat = os.stat(p)
                entries.append({
                    "name": name,
                    "path": os.path.relpath(p, base).replace("\\", "/"),
                    "is_dir": os.path.isdir(p),
                    "size": stat.st_size,
                })
            except Exception:
                continue
        return entries

    @staticmethod
    def open_file(share: ShareConfig, path: str) -> io.BufferedReader:
        base = share.url.replace("file://", "") if share.url.startswith("file://") else share.url
        full = os.path.join(base, path)
        if not os.path.isfile(full):
            raise HTTPException(status_code=404, detail="File not found")
        return open(full, "rb")


try:
    from smb.SMBConnection import SMBConnection  # pysmb
except Exception:
    SMBConnection = None


class SMBAdapter:
    @staticmethod
    def _connect(share: ShareConfig) -> SMBConnection:
        if SMBConnection is None:
            raise HTTPException(status_code=501, detail="SMB support not available (pysmb not installed)")
        if not share.credentials or not share.credentials.username or not share.credentials.password:
            raise HTTPException(status_code=400, detail="Missing SMB credentials")
        # Parse smb://server/share
        rest = share.url[6:] if share.url.lower().startswith("smb://") else share.url
        parts = rest.split("/")
        server_name = parts[0]
        service_name = parts[1] if len(parts) > 1 else ""
        conn = SMBConnection(share.credentials.username, share.credentials.password, "client", server_name, domain=share.credentials.domain or "", use_ntlm_v2=True)
        if not conn.connect(server_name, 445, timeout=5):
            raise HTTPException(status_code=502, detail="SMB connection failed")
        return conn, service_name

    @classmethod
    def test(cls, share: ShareConfig) -> Dict[str, Any]:
        conn, service = cls._connect(share)
        try:
            shares = conn.listShares()
            return {"ok": True, "shares": [s.name for s in shares]}
        finally:
            try:
                conn.close()
            except Exception:
                pass

    @classmethod
    def list_dir(cls, share: ShareConfig, path: Optional[str]) -> List[Dict[str, Any]]:
        conn, service = cls._connect(share)
        try:
            folder = (path or "").replace("\\", "/").strip("/")
            files = conn.listPath(service, f"/{folder}")
            items = []
            for f in files:
                if f.filename in (".", ".."):
                    continue
                items.append({
                    "name": f.filename,
                    "path": f"{folder}/{f.filename}".lstrip("/"),
                    "is_dir": f.isDirectory,
                    "size": f.file_size,
                })
            return items
        finally:
            try:
                conn.close()
            except Exception:
                pass


try:
    from webdav3.client import Client as WebDavClient
except Exception:
    WebDavClient = None


class WebDavAdapter:
    @staticmethod
    def _client(share: ShareConfig) -> WebDavClient:
        if WebDavClient is None:
            raise HTTPException(status_code=501, detail="WebDAV support not available")
        options = {
            'webdav_hostname': share.url,
        }
        if share.credentials and share.credentials.username:
            options['webdav_login'] = share.credentials.username
            options['webdav_password'] = share.credentials.password or ""
        return WebDavClient(options)

    @classmethod
    def test(cls, share: ShareConfig) -> Dict[str, Any]:
        client = cls._client(share)
        root = share.base_path or "/"
        try:
            entries = client.list(root)
            return {"ok": True, "entries": entries}
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"WebDAV error: {e}")

    @classmethod
    def list_dir(cls, share: ShareConfig, path: Optional[str]) -> List[Dict[str, Any]]:
        client = cls._client(share)
        folder = path or share.base_path or "/"
        try:
            # webdavclient3 returns list of names
            names = client.list(folder)
            items = []
            for name in names:
                if not name or name in ("/", folder):
                    continue
                # Heuristic: directories often end with '/'
                is_dir = name.endswith('/')
                items.append({
                    "name": name.rstrip('/').split('/')[-1],
                    "path": f"{folder.rstrip('/')}/{name}".replace('//', '/'),
                    "is_dir": is_dir,
                    "size": 0,
                })
            return items
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"WebDAV error: {e}")


try:
    from office365.sharepoint.client_context import ClientContext
    from office365.runtime.auth.user_credential import UserCredential
except Exception:
    ClientContext = None
    UserCredential = None


class SharePointAdapter:
    @staticmethod
    def _ctx(share: ShareConfig):
        if ClientContext is None:
            raise HTTPException(status_code=501, detail="SharePoint support not available")
        if not share.credentials or not share.credentials.username or not share.credentials.password:
            raise HTTPException(status_code=400, detail="Missing SharePoint credentials")
        ctx = ClientContext(share.url).with_credentials(UserCredential(share.credentials.username, share.credentials.password))
        return ctx

    @classmethod
    def test(cls, share: ShareConfig) -> Dict[str, Any]:
        ctx = cls._ctx(share)
        try:
            web = ctx.web.get().execute_query()
            return {"ok": True, "title": web.properties.get('Title', '')}
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"SharePoint error: {e}")

    @classmethod
    def list_dir(cls, share: ShareConfig, path: Optional[str]) -> List[Dict[str, Any]]:
        ctx = cls._ctx(share)
        folder_path = path or share.base_path or "/Shared Documents"
        try:
            folder = ctx.web.get_folder_by_server_relative_url(folder_path)
            files = folder.files.get().execute_query()
            folders = folder.folders.get().execute_query()
            items: List[Dict[str, Any]] = []
            for d in folders:
                items.append({"name": d.properties.get('Name', ''), "path": f"{folder_path}/{d.properties.get('Name', '')}", "is_dir": True, "size": 0})
            for f in files:
                items.append({"name": f.properties.get('Name', ''), "path": f"{folder_path}/{f.properties.get('Name', '')}", "is_dir": False, "size": f.properties.get('Length', 0)})
            return items
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"SharePoint error: {e}")


def get_adapter(kind: str):
    if kind == 'local':
        return LocalAdapter
    if kind == 'smb':
        return SMBAdapter
    if kind == 'webdav':
        return WebDavAdapter
    if kind == 'sharepoint':
        return SharePointAdapter
    raise HTTPException(status_code=400, detail="Unknown share type")


def enforce_policy(share: ShareConfig, op: str) -> None:
    pol = (share.policy or {"read": True}).copy()
    allowed = pol.get(op, False)
    if not allowed:
        raise HTTPException(status_code=403, detail=f"Operation '{op}' not allowed by policy")


@app.get("/health")
def health():
    return {"status": "healthy", "service": "storage-manager"}


@app.post("/detect")
def detect(share: ShareConfig):
    kind = detect_scheme(share.url)
    if kind == 'unknown':
        return {"type": kind, "supported": False}
    return {"type": kind, "supported": True}


@app.post("/test")
def test(share: ShareConfig):
    kind = detect_scheme(share.url)
    adapter = get_adapter(kind)
    enforce_policy(share, 'read')
    return adapter.test(share)


@app.post("/list")
def list_dir(req: ListRequest):
    kind = detect_scheme(req.share.url)
    adapter = get_adapter(kind)
    enforce_policy(req.share, 'read')
    return adapter.list_dir(req.share, req.path)


@app.post("/download")
def download(req: DownloadRequest):
    kind = detect_scheme(req.share.url)
    adapter = get_adapter(kind)
    enforce_policy(req.share, 'read')
    if kind == 'local':
        fileobj = adapter.open_file(req.share, req.path)
        def iterfile():
            with fileobj as f:
                while True:
                    chunk = f.read(1024 * 1024)
                    if not chunk:
                        break
                    yield chunk
        return StreamingResponse(iterfile(), media_type="application/octet-stream")
    if kind == 'smb':
        if SMBConnection is None:
            raise HTTPException(status_code=501, detail="SMB not available")
        conn, service = SMBAdapter._connect(req.share)
        folder = os.path.dirname("/" + req.path.strip("/")) or "/"
        filename = os.path.basename(req.path)
        temp = io.BytesIO()
        try:
            conn.retrieveFile(service, f"{folder}/{filename}", temp)
            temp.seek(0)
            return StreamingResponse(iter(lambda: temp.read(1024 * 1024), b""), media_type="application/octet-stream")
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"SMB download error: {e}")
        finally:
            try:
                conn.close()
            except Exception:
                pass
    if kind == 'webdav':
        if WebDavClient is None:
            raise HTTPException(status_code=501, detail="WebDAV not available")
        client = WebDavAdapter._client(req.share)
        remote = req.path or req.share.base_path or "/"
        try:
            import tempfile
            tmp = tempfile.NamedTemporaryFile(delete=False)
            tmp.close()
            client.download(remote, tmp.name)
            def iterfile():
                with open(tmp.name, 'rb') as f:
                    while True:
                        chunk = f.read(1024 * 1024)
                        if not chunk:
                            break
                        yield chunk
            return StreamingResponse(iterfile(), media_type="application/octet-stream")
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"WebDAV download error: {e}")
    if kind == 'sharepoint':
        if ClientContext is None:
            raise HTTPException(status_code=501, detail="SharePoint support not available")
        enforce_policy(req.share, 'read')
        ctx = SharePointAdapter._ctx(req.share)
        server_relative_url = req.path or req.share.base_path or "/Shared Documents"
        try:
            import tempfile
            tmp = tempfile.NamedTemporaryFile(delete=False)
            tmp.close()
            file = ctx.web.get_file_by_server_relative_url(server_relative_url)
            with open(tmp.name, 'wb') as local_file:
                file.download(local_file).execute_query()
            def iterfile():
                with open(tmp.name, 'rb') as f:
                    while True:
                        chunk = f.read(1024 * 1024)
                        if not chunk:
                            break
                        yield chunk
            return StreamingResponse(iterfile(), media_type="application/octet-stream")
        except Exception as e:
            raise HTTPException(status_code=502, detail=f"SharePoint download error: {e}")
    raise HTTPException(status_code=400, detail="Unsupported backend")


