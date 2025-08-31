import os
import json
import shelve
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import yaml
from prometheus_client import Counter


router = APIRouter()
CLASS_AUTO = Counter('ingest_classification_auto_total', 'Auto-classified files', ['category'])
CLASS_MANUAL = Counter('ingest_classification_manual_total', 'Manually confirmed classifications', ['category'])
CLASS_CONFIDENCE = Counter('ingest_classification_confidence_total', 'Confidence bucket counts', ['bucket'])


def _load_config() -> Dict[str, Any]:
    cfg_path = Path("config/ingest-config.yaml")
    if not cfg_path.exists():
        return {}
    with open(cfg_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def _review_db_path() -> str:
    data_dir = 'data'
    os.makedirs(data_dir, exist_ok=True)
    return os.path.join(data_dir, 'review_store')


class ReviewItem(BaseModel):
    id: str
    original_path: str
    filename: str
    size: int
    mtime: float
    suggested_category: str
    confidence: float
    customer: Optional[str] = None
    project: Optional[str] = None
    tags: List[str] = []
    metadata: Dict[str, Any] = {}


class PendingResponse(BaseModel):
    items: List[ReviewItem]
    total: int


@router.get('/classification/pending', response_model=PendingResponse)
def list_pending(customer: Optional[str] = None, project: Optional[str] = None, min_confidence: float = 0.0, max_confidence: float = 1.0):
    db = shelve.open(_review_db_path())
    try:
        items: List[ReviewItem] = []
        for key in db.keys():
            rec = db[key]
            try:
                if customer and rec.get('customer') != customer:
                    continue
                if project and rec.get('project') != project:
                    continue
                conf = float(rec.get('confidence', 0.0))
                if conf < min_confidence or conf > max_confidence:
                    continue
                items.append(ReviewItem(**rec))
            except Exception:
                continue
        items.sort(key=lambda r: r.mtime, reverse=True)
        return PendingResponse(items=items, total=len(items))
    finally:
        db.close()


class ConfirmRequest(BaseModel):
    id: str
    category: str


@router.post('/classification/confirm')
def confirm_review(req: ConfirmRequest):
    db = shelve.open(_review_db_path())
    rec: Optional[Dict[str, Any]] = None
    try:
        if req.id not in db:
            raise HTTPException(status_code=404, detail="Review not found")
        rec = db[req.id]
    finally:
        db.close()
    if not rec:
        raise HTTPException(status_code=404, detail="Review not found")

    # Determine destination using config and chosen category
    cfg = _load_config()
    central_base = cfg.get('central_base', '/data/sorted')
    internal_roots = set(cfg.get('internal_roots', ['ORGA','INFRA','SALES','HR']))

    original_path = rec['original_path']
    filename = rec['filename']
    path_lower = original_path.lower()

    import re
    m = re.search(r"(\d{4,6})_([\w\- ]+)", os.path.dirname(original_path))
    if m:
        customer_root = m.group(0)
    else:
        customer_root = next((r for r in internal_roots if r.lower() in path_lower), 'ALLGEMEIN')

    subfolder = {
        'finanzen': 'Archiv',
        'projekte': 'Projekte',
        'personal': 'Archiv',
        'footage': 'Projekte',
        'unsorted': 'Allgemein'
    }.get(req.category.lower(), 'Allgemein')

    # Year/month
    from datetime import datetime
    st = Path(original_path).stat() if Path(original_path).exists() else None
    mtime = (st.st_mtime if st else rec.get('mtime') or 0)
    year = datetime.fromtimestamp(mtime).year if mtime else datetime.now().year
    sorting = cfg.get('sorting', {})
    enable_year = sorting.get('enable_year_subfolders', True)
    year_under = set(sorting.get('year_folders_under', ['Projekte','Archiv']))
    target_dir = os.path.join(central_base, customer_root, subfolder, str(year)) if enable_year and subfolder in year_under else os.path.join(central_base, customer_root, subfolder)
    os.makedirs(target_dir, exist_ok=True)
    dest = Path(target_dir) / filename
    counter = 1
    while dest.exists():
        dest = Path(target_dir) / f"{dest.stem}_{counter}{dest.suffix}"
        counter += 1

    # Move file
    try:
        Path(original_path).replace(dest)
    except Exception:
        import shutil
        shutil.move(original_path, str(dest))

    # Append feedback
    feedback_dir = 'data'
    os.makedirs(feedback_dir, exist_ok=True)
    with open(os.path.join(feedback_dir, 'classification_feedback.jsonl'), 'a', encoding='utf-8') as f:
        fb = {
            'id': req.id,
            'chosen_category': req.category,
            'suggested_category': rec.get('suggested_category'),
            'confidence': rec.get('confidence'),
            'customer': rec.get('customer'),
            'project': rec.get('project'),
            'filename': filename,
            'moved_to': str(dest)
        }
        f.write(json.dumps(fb, ensure_ascii=False) + "\n")

    # Remove from store
    db2 = shelve.open(_review_db_path())
    try:
        if req.id in db2:
            del db2[req.id]
            db2.sync()
    finally:
        db2.close()

    return {"confirmed": True, "destination": str(dest)}


@router.get('/classification/download')
def download_review_file(id: str):
    db = shelve.open(_review_db_path())
    try:
        if id not in db:
            raise HTTPException(status_code=404, detail="Review not found")
        rec = db[id]
        p = Path(rec['original_path'])
        if not p.exists():
            raise HTTPException(status_code=404, detail="File not found")
        from fastapi.responses import FileResponse
        return FileResponse(path=str(p), filename=p.name)
    finally:
        db.close()


