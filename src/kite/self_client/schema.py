from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class SessionRecord(BaseModel):
    user_id: str
    provider: str = "kite"
    cookie: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_validated_at: Optional[datetime] = None
    status: str = "ACTIVE"   # ACTIVE | INVALID | EXPIRED
    meta: Dict[str, Any] = {}
