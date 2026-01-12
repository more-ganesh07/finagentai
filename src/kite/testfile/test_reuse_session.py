import asyncio
from src.session.kite_mcp_client import KiteMCPClient

async def main():
    # No login step — directly reuse saved session
    client = KiteMCPClient(mode="sse", user_id="demo-user")
    await client.connect()

    print("🔍 Testing reused session...")
    ok = await client.validate_session()
    if ok:
        print("✅ Session still valid — you’re logged in!")
        result = await client.call("get_profile", {})
        print("\n📄 Profile Response:")
        print(result)
    else:
        print("❌ Session invalid. You may need to log in again.")

    await client.close()

asyncio.run(main())
