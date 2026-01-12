from pydantic import BaseModel
from typing import Optional

class QueryRequest(BaseModel):
    user_query: str  # This will validate that `user_query` is a string

class QueryResponse(BaseModel):
    response: str  # This will define the structure of the response

class MarketChatRequest(BaseModel):
    user_query: str
    session_id: Optional[str] = None  # Optional session ID for conversation memory

 