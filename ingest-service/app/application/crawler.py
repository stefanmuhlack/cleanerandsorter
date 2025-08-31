import asyncio
import os
import re
import shutil
import shelve
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

import yaml
from fastapi import APIRouter, HTTPException
from prometheus_client import Counter


router = APIRouter()


class CrawlerState:
    def __init__(self) -> None:
        self.running: bool = False
        self.stop_requested: bool = False
        self.started_at: Optional[str] = None
        self.finished_at: Optional[str] = None
        self.stats: Dict[str, Any] = {
            "processed": 0,
            "moved": 0,
            "duplicates": 0,
            "errors": 0,
            "by_customer": {},
        }
        self.hash_index: Dict[str, Dict[str, Any]] = {}

    def reset(self) -> None:
        self.running = False
        self.stop_requested = False
        self.started_at = None
        self.finished_at = None
        self.stats = {"processed": 0, "moved": 0, "duplicates": 0, "errors": 0, "by_customer": {}}
        self.hash_index = {}


state = CrawlerState()

CRAWLER_PROCESSED = Counter('ingest_crawler_processed_total', 'Files processed by crawler')
CRAWLER_DUPLICATES = Counter('ingest_crawler_duplicates_total', 'Duplicates found by crawler')


def load_ingest_config() -> Dict[str, Any]:
    cfg_path = Path("config/ingest-config.yaml")
    if not cfg_path.exists():
        raise HTTPException(status_code=500, detail="ingest-config.yaml not found")
    with open(cfg_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def determine_customer_root(file_path: str, internal_roots: List[str]) -> str:
    m = re.search(r"(\d{4,6})_([\w\- ]+)", os.path.dirname(file_path))
    if m:
        return m.group(0)
    lower = file_path.lower()
    for r in internal_roots:
        if r.lower() in lower:
            return r
    return "ALLGEMEIN"


def determine_subfolder(file_path: str) -> str:
    lower = file_path.lower()
    filename = os.path.basename(file_path).lower()
    candidates = {
        'Projekte': ['projekt', 'projects', 'proj_'],
        'Portale': ['portal', 'website', 'site'],
        'Kampagnen': ['kampagne', 'campaign'],
        'Angebote': ['angebot', 'offer', 'quote'],
        'Archiv': ['archiv', 'archive']
    }
    for key, keys in candidates.items():
        if any(k in lower or k in filename for k in keys):
            return key
    return 'Allgemein'


def target_dir_for(central_base: str, customer_root: str, subfolder: str, enable_year: bool, year_folders_under: List[str], mtime: float) -> str:
    year = datetime.fromtimestamp(mtime).year
    if enable_year and subfolder in set(year_folders_under or []):
        return os.path.join(central_base, customer_root, subfolder, str(year))
    return os.path.join(central_base, customer_root, subfolder)


def file_hash_sha256(path: Path) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


async def _crawl_once(config: Dict[str, Any]) -> None:
    central_base = config.get('central_base', '/data/sorted')
    internal_roots = config.get('internal_roots', ['ORGA', 'INFRA', 'SALES', 'HR'])
    shares = config.get('shares', [])
    sorting = config.get('sorting', {})
    enable_year = sorting.get('enable_year_subfolders', True)
    year_under = sorting.get('year_folders_under', ['Projekte', 'Archiv'])

    os.makedirs(central_base, exist_ok=True)
    # Persistent hash index (simple shelve-based KV store)
    index_dir = config.get('index_store_path', 'data')
    os.makedirs(index_dir, exist_ok=True)
    shelve_path = os.path.join(index_dir, 'crawler_hash_index')
    db = shelve.open(shelve_path)
    try:
        # Load existing hashes into memory for quick checks
        try:
            for key in db.keys():
                state.hash_index[key] = db[key]
        except Exception:
            pass

    for root in shares:
        if state.stop_requested:
            break
        for dirpath, _, filenames in os.walk(root):
            if state.stop_requested:
                break
            for name in filenames:
                if state.stop_requested:
                    break
                try:
                    src = Path(dirpath) / name
                    if not src.is_file():
                        continue
                    st = src.stat()
                    h = file_hash_sha256(src)
                    state.stats['processed'] += 1
                    CRAWLER_PROCESSED.inc()

                    customer_root = determine_customer_root(str(src), internal_roots)
                    subfolder = determine_subfolder(str(src))
                    dst_dir = target_dir_for(central_base, customer_root, subfolder, enable_year, year_under, st.st_mtime)
                    os.makedirs(dst_dir, exist_ok=True)
                    dst = Path(dst_dir) / name

                    by_cust = state.stats['by_customer']
                    if customer_root not in by_cust:
                        by_cust[customer_root] = {"processed": 0, "duplicates": 0, "by_subfolder": {}}
                    by_cust[customer_root]["processed"] += 1
                    by_sub = by_cust[customer_root]["by_subfolder"]
                    if subfolder not in by_sub:
                        by_sub[subfolder] = {"processed": 0, "duplicates": 0}
                    by_sub[subfolder]["processed"] += 1

                    # No previous file with same hash
                    if h not in state.hash_index:
                        shutil.move(str(src), str(dst))
                        state.hash_index[h] = {
                            "path": str(dst),
                            "mtime": st.st_mtime,
                            "size": st.st_size,
                            "customer": customer_root,
                        }
                        try:
                            db[h] = state.hash_index[h]
                            db.sync()
                        except Exception:
                            pass
                        state.stats['moved'] += 1
                        continue

                    # Duplicate: decide which to keep
                    prev = state.hash_index[h]
                    keep_new = (st.st_mtime > prev['mtime']) or (st.st_mtime == prev['mtime'] and st.st_size > prev['size'])
                    if keep_new:
                        # Move previous to _duplicates
                        prev_path = Path(prev['path'])
                        base = prev_path.parents[1] if len(prev_path.parents) >= 2 else Path(central_base)
                        dup_dir = base / "_duplicates"
                        os.makedirs(dup_dir, exist_ok=True)
                        new_prev = dup_dir / prev_path.name
                        counter = 1
                        while new_prev.exists():
                            new_prev = dup_dir / f"{new_prev.stem}_{counter}{new_prev.suffix}"
                            counter += 1
                        try:
                            prev_path.replace(new_prev)
                        except Exception:
                            shutil.move(str(prev_path), str(new_prev))
                        # Move new file to destination
                        shutil.move(str(src), str(dst))
                        state.hash_index[h] = {"path": str(dst), "mtime": st.st_mtime, "size": st.st_size, "customer": customer_root}
                        try:
                            db[h] = state.hash_index[h]
                            db.sync()
                        except Exception:
                            pass
                    else:
                        # Move new duplicate to _duplicates of its (or detected) customer
                        dup_dir = Path(central_base) / customer_root / "_duplicates"
                        os.makedirs(dup_dir, exist_ok=True)
                        target = dup_dir / name
                        counter = 1
                        while target.exists():
                            target = dup_dir / f"{target.stem}_{counter}{target.suffix}"
                            counter += 1
                        shutil.move(str(src), str(target))
    finally:
        try:
            db.close()
        except Exception:
            pass
                    state.stats['duplicates'] += 1
                    CRAWLER_DUPLICATES.inc()
                    by_cust[customer_root]['duplicates'] = by_cust[customer_root].get('duplicates', 0) + 1
                    by_cust[customer_root]['by_subfolder'][subfolder]['duplicates'] = by_cust[customer_root]['by_subfolder'][subfolder].get('duplicates', 0) + 1

                except Exception as e:
                    state.stats['errors'] += 1
                    # Continue crawling on error
                    continue


@router.post('/crawler/start')
async def start_crawler():
    if state.running:
        raise HTTPException(status_code=409, detail="Crawler already running")
    try:
        cfg = load_ingest_config()
    except HTTPException:
        raise
    state.reset()
    state.running = True
    state.started_at = datetime.utcnow().isoformat()
    loop = asyncio.get_event_loop()

    async def runner():
        try:
            await _crawl_once(cfg)
        finally:
            state.running = False
            state.finished_at = datetime.utcnow().isoformat()
            state.stop_requested = False

    loop.create_task(runner())
    return {"status": "started", "started_at": state.started_at}


@router.post('/crawler/stop')
async def stop_crawler():
    if not state.running:
        return {"status": "idle"}
    state.stop_requested = True
    return {"status": "stopping"}


@router.get('/crawler/status')
async def crawler_status():
    return {
        "running": state.running,
        "stop_requested": state.stop_requested,
        "started_at": state.started_at,
        "finished_at": state.finished_at,
        "stats": state.stats,
    }


@router.get('/crawler/stats')
async def crawler_stats():
    return state.stats


