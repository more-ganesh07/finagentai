# data_fetch.py
import sys
from pathlib import Path
from typing import Any, Dict

root = Path(__file__).resolve().parents[1]
if str(root) not in sys.path:
    sys.path.append(str(root))

from portbot.master_agent import MasterAgent  # noqa: E402
from portbot.session_config import SESSION_PATH  # noqa: E402


async def fetch_eod_payload() -> Dict[str, Any]:
    """
    Use persisted session cookie at src/portbot/session.json.
    Load cookie BEFORE validating, then reconnect with fresh headers.
    If still invalid, invoke LoginAgent.login to refresh cookies, then retry.
    """
    async with MasterAgent(validate_on_enter=False) as master:
        kite = master.kite_client

        # 1) Load cookie FIRST (from shared path)
        if SESSION_PATH.exists():
            print(f"🔁 Loading cookie from {SESSION_PATH}")
            kite.load_session(str(SESSION_PATH))

        # 2) Reconnect so new headers apply
        await kite.close()
        await kite.connect()

        # 3) Validate with loaded cookie
        ok = await kite.validate_session()
        if not ok:
            print("❌ Session invalid — invoking LoginAgent.login to refresh cookies...")
            res = await master.execute("login", "login")
            if res.get("status") != "success":
                print(f"❌ LoginAgent.login failed: {res.get('message')}")
                return {}

            # 4) Reload cookie just saved by login agent
            if not SESSION_PATH.exists():
                print(f"❌ Expected session file not found at {SESSION_PATH}")
                return {}
            kite.load_session(str(SESSION_PATH))

            # 5) Reconnect again to apply headers, validate again
            await kite.close()
            await kite.connect()
            ok = await kite.validate_session()
            if not ok:
                print("❌ Still invalid after LoginAgent — aborting.")
                return {}

        print("✅ Session validated. Fetching data from MCP...")

        profile   = await master.execute("account",   "get_profile")
        margins   = await master.execute("account",   "get_margins")
        holdings  = await master.execute("portfolio", "get_holdings")
        positions = await master.execute("portfolio", "get_positions")
        mfs       = await master.execute("portfolio", "get_mf_holdings")

    return {
        "profile":   profile,
        "margins":   margins,
        "holdings":  holdings,
        "positions": positions,
        "mfs":       mfs,
    }



def extract_recipient_email(profile_res: Dict[str, Any], fallback_email: str = "") -> str:
    data = profile_res.get("data") or {}
    for k in ("email", "user_email", "mail"):
        v = data.get(k)
        if isinstance(v, str) and "@" in v:
            return v
    msg = profile_res.get("message", "") or ""
    for token in msg.replace("•", " ").replace("|", " ").split():
        if "@" in token and "." in token:
            return token.strip().strip(",")
    return fallback_email or ""
