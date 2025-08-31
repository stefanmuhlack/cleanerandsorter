import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import yaml


router = APIRouter()


def _load_config() -> Dict[str, Any]:
    cfg_path = Path("config/ingest-config.yaml")
    if not cfg_path.exists():
        raise HTTPException(status_code=500, detail="ingest-config.yaml not found")
    with open(cfg_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


class DuplicateItem(BaseModel):
    customer_root: str
    filename: str
    path: str
    size: int
    mtime: float


class DuplicatesResponse(BaseModel):
    items: List[DuplicateItem]
    total: int


@router.get('/duplicates', response_model=DuplicatesResponse)
def list_duplicates(customer: Optional[str] = None, limit: int = 50, offset: int = 0):
    cfg = _load_config()
    base = Path(cfg.get('central_base', '/data/sorted'))
    if not base.exists():
        return DuplicatesResponse(items=[], total=0)

    items: List[DuplicateItem] = []
    for entry in base.iterdir():
        if not entry.is_dir():
            continue
        customer_root = entry.name
        if customer and customer_root != customer:
            continue
        dup_dir = entry / '_duplicates'
        if not dup_dir.exists() or not dup_dir.is_dir():
            continue
        for p in dup_dir.rglob('*'):
            if p.is_file():
                try:
                    st = p.stat()
                    items.append(DuplicateItem(
                        customer_root=customer_root,
                        filename=p.name,
                        path=str(p),
                        size=st.st_size,
                        mtime=st.st_mtime,
                    ))
                except Exception:
                    continue

    total = len(items)
    # Sort by mtime desc by default
    items.sort(key=lambda x: x.mtime, reverse=True)
    items_page = items[offset:offset+limit]
    return DuplicatesResponse(items=items_page, total=total)


class PromoteRequest(BaseModel):
    path: str


@router.post('/duplicates/promote')
def promote_duplicate(req: PromoteRequest):
    p = Path(req.path)
    if not p.exists() or not p.is_file():
        raise HTTPException(status_code=404, detail="Duplicate file not found")
    # Compute hash and locate primary via crawler index if available
    try:
        import hashlib
        h = hashlib.sha256()
        with open(p, 'rb') as f:
            for chunk in iter(lambda: f.read(1024*1024), b""):
                h.update(chunk)
        file_hash = h.hexdigest()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Hashing failed: {e}")

    # Read crawler shelve index
    import shelve
    cfg = _load_config()
    index_dir = cfg.get('index_store_path', 'data')
    shelve_path = os.path.join(index_dir, 'crawler_hash_index')
    primary_path: Optional[str] = None
    try:
        db = shelve.open(shelve_path)
        try:
            info = db.get(file_hash)
            if info and 'path' in info:
                primary_path = info['path']
        finally:
            db.close()
    except Exception:
        primary_path = None

    if not primary_path:
        raise HTTPException(status_code=404, detail="Primary file not found in index")

    primary = Path(primary_path)
    if not primary.exists():
        # If primary is missing, just move duplicate to primary location
        primary.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(p), str(primary))
        return {"promoted": True, "replaced_missing_primary": True}

    # Swap: move current primary to _duplicates, move selected duplicate into primary path
    target_dup_dir = primary.parents[1] / '_duplicates' if len(primary.parents) >= 2 else primary.parent / '_duplicates'
    target_dup_dir.mkdir(parents=True, exist_ok=True)
    moved_primary = target_dup_dir / primary.name
    counter = 1
    while moved_primary.exists():
        moved_primary = target_dup_dir / f"{moved_primary.stem}_{counter}{moved_primary.suffix}"
        counter += 1
    try:
        primary.replace(moved_primary)
    except Exception:
        shutil.move(str(primary), str(moved_primary))

    # Move selected duplicate into original primary location
    primary.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(p), str(primary))
    return {"promoted": True, "previous_primary": str(moved_primary)}


class MoveRequest(BaseModel):
    path: str
    target_dir: str


@router.post('/duplicates/move')
def move_duplicate(req: MoveRequest):
    p = Path(req.path)
    if not p.exists() or not p.is_file():
        raise HTTPException(status_code=404, detail="Duplicate file not found")
    dest_dir = Path(req.target_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / p.name
    counter = 1
    while dest.exists():
        dest = dest_dir / f"{dest.stem}_{counter}{dest.suffix}"
        counter += 1
    shutil.move(str(p), str(dest))
    return {"moved": True, "destination": str(dest)}


class DeleteRequest(BaseModel):
    paths: List[str]


@router.post('/duplicates/delete')
def delete_duplicates(req: DeleteRequest):
    deleted = 0
    failed: List[Dict[str, Any]] = []
    for pth in req.paths:
        try:
            p = Path(pth)
            if p.exists() and p.is_file():
                p.unlink()
                deleted += 1
            else:
                failed.append({"path": pth, "error": "not_found"})
        except Exception as e:
            failed.append({"path": pth, "error": str(e)})
    return {"deleted": deleted, "failed": failed}


