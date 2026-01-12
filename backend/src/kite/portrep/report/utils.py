# utils.py
from typing import Any, Dict, List

def inr(x: Any) -> str:
    try:
        return f"₹{float(x):,.2f}"
    except Exception:
        return "₹-"

def _get(d: Dict, *keys, default=None):
    cur = d
    for k in keys:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k, None)
    return cur if cur is not None else default

def as_list(obj: Any) -> List[Any]:
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        for k in ("data", "items", "rows", "holdings", "positions"):
            if k in obj and isinstance(obj[k], list):
                return obj[k]
    if isinstance(obj, str):
        s = obj.strip()
        return [] if s in ("", "[]") else []
    return []
