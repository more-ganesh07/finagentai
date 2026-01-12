# src/session/login_once.py
import os
import asyncio
import time
import re
import webbrowser
import urllib.parse
from urllib.parse import unquote
from dotenv import load_dotenv

from src.session.kite_mcp_client import KiteMCPClient
from src.session.manager import SessionManager

def extract_login_url_and_session_id(text: str):
    url_match = re.search(r'https?://[^\s\)]+', text or "")
    login_url = url_match.group(0) if url_match else (text or "").strip()
    mcp_session_id = None
    try:
        parsed = urllib.parse.urlparse(login_url)
        params = urllib.parse.parse_qs(parsed.query)
        if 'redirect_params' in params:
            decoded = urllib.parse.unquote(params['redirect_params'][0])
            if 'session_id=' in decoded:
                session_part = decoded.split('|')[0]
                mcp_session_id = session_part.replace('session_id=', '')
    except Exception:
        pass
    return login_url if login_url else None, mcp_session_id

async def main():
    load_dotenv(override=True)
    user_id = os.getenv("USER_ID", "demo-user")
    mcp_mode = os.getenv("KITE_MCP_MODE", "http").strip().lower()

    print(f"🔐 Starting Zerodha MCP login for user → {user_id}")
    client = KiteMCPClient(mode=mcp_mode, user_id=user_id)
    await client.connect()

    print("🪄 Requesting login URL from MCP...")
    try:
        result = await client.call("login", {})
    except Exception as e:
        print(f"❌ Failed to start login: {e}")
        await client.close()
        return

    login_url, mcp_session_id = None, None
    if hasattr(result, "content") and isinstance(result.content, list):
        for item in result.content:
            if getattr(item, "type", None) == "text":
                login_url, mcp_session_id = extract_login_url_and_session_id(getattr(item, "text", ""))
                if login_url:
                    break

    if not login_url:
        print("⚠️ Could not extract login URL from response.")
        await client.close()
        return

    print(f"\n🔗 Open this URL and complete login:\n{login_url}\n")
    try:
        webbrowser.open(login_url)
    except Exception:
        print("⚠️ Could not open browser automatically. Copy the URL manually.")

    input("✅ After completing login in browser and seeing 'Login Successful', press Enter here to continue...")

    print("\n⏳ Waiting for MCP server to process callback...")
    time.sleep(2)

    # Validate on the same connection
    print("🔍 Validating session with MCP (same connection)...\n")
    if not client._client:
        print("⚠️ Client connection was lost. Reconnecting...")
        await client.connect()

    try:
        ok = await client.validate_session()
    except Exception as e:
        print(f"❌ Error during validation: {e}")
        print("   Attempting one reconnect...")
        try:
            await client.close()
            await client.connect()
            ok = await client.validate_session()
        except Exception:
            ok = False

    sm = SessionManager()
    if ok:
        print("✅ Session validated successfully!")
        if mcp_session_id:
            sm.persist_session(user_id, mcp_session_id, provider="kite")
            sm.mark_session_valid(user_id, provider="kite")
            print("💾 MCP session info saved to session.json")
        else:
            # Still persist cookie-like value if present on the client
            cookie = getattr(client, "session_cookie", None)
            if cookie:
                sm.persist_session(user_id, cookie, provider="kite")
                sm.mark_session_valid(user_id, provider="kite")
                print("💾 Session cookie saved to session.json")
    else:
        print("❌ Session validation failed.")
        if mcp_session_id:
            sm.persist_session(user_id, mcp_session_id, provider="kite")
            print("💾 Saved MCP session ID for reference (server likely has active session).")

    await client.close()
    print("🧹 Kite MCP client closed cleanly.")

if __name__ == "__main__":
    asyncio.run(main())
