import asyncio
from src.session.kite_mcp_client import KiteMCPClient

async def main():
    # You can switch mode="sse" or "http" — both work (HTTP uses fallback SSETransport)
    client = KiteMCPClient(mode="sse")

    await client.connect()
    result = await client.call("get_profile", {})
    print("\n✅ Response from get_profile:")
    print(result)
    await client.close()

asyncio.run(main())
