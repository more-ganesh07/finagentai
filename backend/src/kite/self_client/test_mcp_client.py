import asyncio
from src.kite.client.kite_mcp_client import KiteMCPClient

async def main():
    async with KiteMCPClient() as mcp:
        print("✅ Connected to Hosted Kite MCP.", flush=True)

        # 🔹 Login
        try:
            res = await mcp.call("login", {})
            print("🪪 login =>", res, flush=True)
        except Exception as e:
            print("login error:", e, flush=True)

        # 🔹 Profile
        try:
            prof = await mcp.call("get_profile", {})
            print("👤 get_profile =>", prof, flush=True)
        except Exception as e:
            print("get_profile error:", e, flush=True)

        # 🔹 Quotes
        try:
            quotes = await mcp.call("get_quotes", {"instruments": ["NSE:INFY", "NSE:TCS"]})
            print("📈 get_quotes =>", quotes, flush=True)
        except Exception as e:
            print("get_quotes error:", e, flush=True)

if __name__ == "__main__":
    print("🚀 Starting Hosted Kite MCP Client Test...\n", flush=True)
    asyncio.run(main())
