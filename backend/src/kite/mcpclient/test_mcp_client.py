import asyncio, re, time, webbrowser
from typing import Optional
from src.kite.client.kite_mcp_client import KiteMCPClient

LOGIN_URL_RE = re.compile(r"https?://kite\.zerodha\.com/connect/login\?[^ \n]+")

def extract_login_url(login_result) -> Optional[str]:
    contents = getattr(login_result, "content", None) or []
    for item in contents:
        text = getattr(item, "text", None)
        if not text:
            continue
        m = LOGIN_URL_RE.search(text)
        if m:
            return m.group(0)
    return None

async def ensure_logged_in(mcp: KiteMCPClient, max_attempts=2, poll_secs=60, interval=2):
    """
    Try up to `max_attempts` login cycles. Each cycle:
      - call login(), open URL, prompt user to finish
      - poll get_profile for `poll_secs`
    """
    for attempt in range(1, max_attempts + 1):
        print(f"\n🔑 Login attempt {attempt}/{max_attempts}")
        login_res = await mcp.call("login", {})
        url = extract_login_url(login_res)
        if not url:
            raise RuntimeError("Could not find login URL in login() response.")

        print("\n⚠️  WARNING: AI systems are unpredictable and non-deterministic.")
        print("   By continuing, you agree to interact with your Zerodha account via AI at your own risk.\n")
        print(f"🔗 Login URL: {url}\n")

        try:
            webbrowser.open(url)
            print("🌐 Opened login URL in your default browser.")
        except Exception:
            print("ℹ️ If it didn't open, copy & paste the URL into your browser.")

        input("⏳ Finish the browser login (click Allow/Continue). Then press ENTER here... ")

        deadline = time.time() + poll_secs
        last_err = None
        while time.time() < deadline:
            try:
                prof = await mcp.call("get_profile", {})
                print("👤 get_profile =>", prof)
                return True
            except Exception as e:
                last_err = e
                await asyncio.sleep(interval)

        print(f"⌛ Session not active yet (last error: {last_err}). Retrying a fresh login link...")

    return False

async def main():
    async with KiteMCPClient() as mcp:
        mode, url = mcp.connection_info()
        print(f"✅ Connected to Hosted Kite MCP in {mode} mode @ {url}")

        ok = await ensure_logged_in(mcp, max_attempts=3, poll_secs=90, interval=3)
        if not ok:
            print("\n❌ Still missing session. Likely causes:")
            print("   • Didn’t click Allow/Continue on the consent screen")
            print("   • Link expired (took too long) — re-run and login promptly")
            print("   • Adblocker or strict privacy blocked the redirect back to mcp.kite.trade")
            print("   • Logged into multiple Zerodha accounts at once")
            return

        # Optional: quotes now that session works
        try:
            quotes = await mcp.call("get_quotes", {"instruments": ["NSE:INFY", "NSE:TCS"]})
            print("📈 get_quotes =>", quotes)
        except Exception as e:
            print("get_quotes error:", e)

if __name__ == "__main__":
    print("🚀 Hosted Kite MCP test (HTTP preferred, SSE fallback)\n")
    asyncio.run(main())
