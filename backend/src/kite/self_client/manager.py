# src/session/manager.py
from typing import Optional, Dict, Any
from src.session.schema import SessionRecord
from src.session.store import SessionStore

class SessionManager:
    """High-level API used by chatbot/report."""
    def __init__(self, store: Optional[SessionStore] = None):
        self.store = store or SessionStore()

    def get_active_session(self, user_id: str, provider: str = "kite") -> Optional[Dict[str, Any]]:
        return self.store.load(user_id=user_id, provider=provider)

    def persist_session(self, user_id: str, cookie: str, provider: str = "kite", meta=None) -> None:
        rec = SessionRecord(user_id=user_id, provider=provider, cookie=str(cookie), meta=meta or {})
        self.store.save(rec)

    def mark_session_valid(self, user_id: str, provider: str = "kite") -> None:
        self.store.touch_validated(user_id=user_id, provider=provider)

    def mark_session_invalid(self, user_id: str, provider: str = "kite") -> None:
        self.store.mark_invalid(user_id=user_id, provider=provider)

    def clear_session(self, user_id: str, provider: str = "kite") -> None:
        self.store.delete(user_id=user_id, provider=provider)
