# src/session/use_session.py
from typing import AsyncGenerator, Dict, Any, Optional
from contextlib import asynccontextmanager

from src.session.manager import SessionManager
from src.session.kite_mcp_client import KiteMCPClient

class RequiresLoginError(Exception):
    """Raised when a valid Zerodha session is not available."""
    pass

async def get_kite_client(user_id: str) -> KiteMCPClient:
    """
    Load saved session, bind to KiteMCPClient, connect & validate.
    Raises RequiresLoginError if missing/invalid.
    """
    sm = SessionManager()
    sess: Optional[Dict[str, Any]] = sm.get_active_session(user_id, provider="kite")

    # Missing session file / cookie
    if not sess or not isinstance(sess.get("cookie"), str) or not sess["cookie"]:
        raise RequiresLoginError(
            "Zerodha login required.\n"
            "Start the MCP server, then run:\n"
            "  python -m src.session.login_once"
        )

    # Bind saved session into the client and connect
    client = KiteMCPClient(user_id=user_id).restore_session(sess)
    await client.connect()

    # Validate by calling a lightweight tool (get_profile)
    ok = await client.validate_session()
    if not ok:
        sm.mark_session_invalid(user_id, provider="kite")
        raise RequiresLoginError(
            "Saved Zerodha session appears invalid/expired.\n"
            "Please re-run:\n"
            "  python -m src.session.login_once"
        )

    sm.mark_session_valid(user_id, provider="kite")
    return client

@asynccontextmanager
async def kite_client_ctx(user_id: str) -> AsyncGenerator[KiteMCPClient, None]:
    """
    Context manager that yields a connected, validated KiteMCPClient
    and ensures it closes cleanly afterwards.
    """
    client = await get_kite_client(user_id)
    try:
        yield client
    finally:
        await client.close()
