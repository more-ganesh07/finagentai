# src/session/store.py
import os
import json
from contextlib import contextmanager
from typing import Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv
from src.session.schema import SessionRecord

class SessionStore:
    """
    Centralized file-based session store.
    ✅ Single JSON file from .env (SESSION_FILE_PATH)
    """
    def __init__(self, file_path: Optional[str] = None):
        load_dotenv(override=True)
        self.session_file = file_path or os.getenv(
            "SESSION_FILE_PATH",
            os.path.join(".", "data", "sessions", "session.json")
        )
        os.makedirs(os.path.dirname(self.session_file), exist_ok=True)

    # ---------- public API ----------
    def save(self, record: SessionRecord) -> None:
        payload: Dict[str, Any] = record.model_dump()
        payload["created_at"] = record.created_at.isoformat() + "Z"
        if record.last_validated_at:
            payload["last_validated_at"] = record.last_validated_at.isoformat() + "Z"
        with self._atomic_write(self.session_file) as f:
            json.dump(payload, f, indent=2)

    def load(self, user_id: str, provider: str = "kite") -> Optional[dict]:
        if not os.path.exists(self.session_file):
            return None
        try:
            with open(self.session_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def delete(self, user_id: str, provider: str = "kite") -> None:
        try:
            if os.path.exists(self.session_file):
                os.remove(self.session_file)
        except Exception:
            pass

    def touch_validated(self, user_id: str, provider: str = "kite") -> None:
        data = self.load(user_id, provider)
        if not data:
            return
        data["last_validated_at"] = datetime.utcnow().isoformat() + "Z"
        data["status"] = "ACTIVE"
        with self._atomic_write(self.session_file) as f:
            json.dump(data, f, indent=2)

    def mark_invalid(self, user_id: str, provider: str = "kite") -> None:
        data = self.load(user_id, provider)
        if not data:
            return
        data["status"] = "INVALID"
        with self._atomic_write(self.session_file) as f:
            json.dump(data, f, indent=2)

    # ---------- internals ----------
    @contextmanager
    def _atomic_write(self, path: str):
        tmp = f"{path}.tmp"
        f = open(tmp, "w", encoding="utf-8")
        try:
            yield f
            f.flush()
            os.fsync(f.fileno())
            f.close()
            os.replace(tmp, path)
        except Exception:
            try: f.close()
            except Exception: pass
            try:
                if os.path.exists(tmp):
                    os.remove(tmp)
            except Exception:
                pass
            raise
