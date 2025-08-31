import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import jsonschema


router = APIRouter()


CONFIG_PATH = Path("config/ingest-config.yaml")


class IngestConfigPayload(BaseModel):
    yaml_text: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class ThresholdPayload(BaseModel):
    confidence_threshold: float


def _read_ingest_config() -> Dict[str, Any]:
    if not CONFIG_PATH.exists():
        raise HTTPException(status_code=404, detail="ingest-config.yaml not found")
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read config: {e}")


def _write_ingest_config(cfg: Dict[str, Any]) -> None:
    try:
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            yaml.safe_dump(cfg, f, sort_keys=False, allow_unicode=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to write config: {e}")


@router.get('/config/ingest')
def get_ingest_config():
    cfg = _read_ingest_config()
    try:
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            raw = f.read()
    except Exception:
        raw = yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True)
    threshold = cfg.get('classification', {}).get('confidence_threshold', 0.8)
    return {"config": cfg, "yaml": raw, "confidence_threshold": threshold}


@router.put('/config/ingest')
def update_ingest_config(payload: IngestConfigPayload):
    if not payload.yaml_text and not payload.config:
        raise HTTPException(status_code=400, detail="Provide yaml_text or config")
    new_cfg: Dict[str, Any] = {}
    try:
        if payload.yaml_text:
            new_cfg = yaml.safe_load(payload.yaml_text) or {}
        else:
            new_cfg = dict(payload.config or {})
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid YAML: {e}")
    # Basic validation
    # Validate storage shares for multiple NAS paths
    shares = new_cfg.get('shares')
    if shares is None or not isinstance(shares, list) or len(shares) == 0:
        raise HTTPException(status_code=400, detail="Missing 'shares' list in config")
    # Optionally validate central_base
    if 'central_base' not in new_cfg and 'central_base_directory' not in new_cfg and 'central_base' not in new_cfg:
        # keep backward-compat but encourage central_base
        new_cfg['central_base'] = new_cfg.get('central_base_directory', '/data/sorted')
    # Optional schema validation for folder rules if present
    rules = new_cfg.get('folder_rules')
    schema_path = Path('config/folder-rules.schema.json')
    if rules and schema_path.exists():
        try:
            import json
            with open(schema_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            jsonschema.validate(instance=rules, schema=schema)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"folder_rules validation failed: {e}")

    # Write
    _write_ingest_config(new_cfg)
    return {"updated": True}


@router.put('/config/ingest/confidence-threshold')
def update_confidence_threshold(payload: ThresholdPayload):
    cfg = _read_ingest_config()
    cfg.setdefault('classification', {})['confidence_threshold'] = float(payload.confidence_threshold)
    _write_ingest_config(cfg)
    return {"updated": True, "confidence_threshold": cfg['classification']['confidence_threshold']}


