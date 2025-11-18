# src/agents/project_agent.py
from typing import List, Optional
import json
import os
import time
import hashlib

from src.tools.project_suggester import suggest_projects
from src.models.project_models import ProjectIdea

# Allowed expertise levels
_ALLOWED_LEVELS = {"beginner", "intermediate", "advanced"}

# Simple file-based cache to avoid repeated LLM calls while developing
_CACHE_DIR = "data/.cache/project_agent"
os.makedirs(_CACHE_DIR, exist_ok=True)

def _cache_key(topics: List[str], level: str, n: int) -> str:
    key = json.dumps({"topics": topics, "level": level, "n": n}, sort_keys=True)
    h = hashlib.sha1(key.encode("utf-8")).hexdigest()
    return os.path.join(_CACHE_DIR, f"projects_{h}.json")

def _read_cache(path: str) -> Optional[List[dict]]:
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return None

def _write_cache(path: str, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass

def _validate_level(level: str) -> str:
    if not level:
        return "beginner"
    level = level.lower().strip()
    if level not in _ALLOWED_LEVELS:
        raise ValueError(f"Invalid level '{level}'. Allowed: {sorted(_ALLOWED_LEVELS)}")
    return level

def _to_project_models(items: List[dict]) -> List[ProjectIdea]:
    out = []
    for obj in items:
        try:
            p = ProjectIdea(
                title=obj.get("title", "") or "Untitled Project",
                description=obj.get("description", "") or "",
                difficulty=obj.get("difficulty", "beginner"),
                estimated_hours=int(obj.get("estimated_hours")) if obj.get("estimated_hours") not in (None, "", []) else None,
                steps=obj.get("steps", []),
                required_skills=obj.get("required_skills", []),
            )
            out.append(p)
        except Exception:
            # skip malformed
            continue
    return out

def generate_project_ideas(topics: List[str], level: str = "beginner", n: int = 3, use_cache: bool = True, model: str = "llama3.2:3b") -> List[ProjectIdea]:
    """
    Generate `n` project ideas for the given topics and expertise level.

    - topics: list of topic strings (e.g. ['Pandas', 'EDA'])
    - level: 'beginner' | 'intermediate' | 'advanced'
    - n: number of projects to request
    - use_cache: whether to use local cache to avoid repeated LLM calls
    - model: model name passed to the underlying suggester (keeps backward compatibility)

    Returns a list of ProjectIdea Pydantic models.
    """
    level = _validate_level(level)
    cache_path = _cache_key(topics, level, n)

    # Try cache first
    if use_cache:
        cached = _read_cache(cache_path)
        if cached:
            return _to_project_models(cached)

    # Call the suggestor with a small retry loop
    last_exc = None
    attempts = 2
    for attempt in range(attempts):
        try:
            # suggest_projects returns List[ProjectIdea] in your earlier implementation,
            # but it may also return Pydantic models or dicts depending on implementation.
            raw = suggest_projects(topics, level=level, n=n, model=model)
            # Normalize to list of dicts
            normalized = []
            for item in raw:
                # If it's already a ProjectIdea model, use model_dump
                try:
                    if hasattr(item, "model_dump"):
                        normalized.append(item.model_dump(mode="json"))
                    elif isinstance(item, dict):
                        normalized.append(item)
                    else:
                        # fallback: try to convert via __dict__
                        normalized.append(getattr(item, "__dict__", dict(item)))
                except Exception:
                    # last-ditch attempt: convert to string
                    normalized.append({"title": str(item)})
            # write cache (best-effort)
            if use_cache:
                _write_cache(cache_path, normalized)
            # convert to ProjectIdea models and return
            return _to_project_models(normalized)
        except Exception as e:
            last_exc = e
            time.sleep(0.5 + attempt * 0.5)
    # All attempts failed: raise last exception for caller to handle
    raise RuntimeError("Failed to generate project ideas") from last_exc
