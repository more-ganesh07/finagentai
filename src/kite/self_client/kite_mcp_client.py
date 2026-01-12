# C:\Users\Ganesh.More\Desktop\GaneshMore\KiteInfi\src\kite\client\kite_mcp_client.py
import asyncio
import os
import time
from typing import Any, Optional
from dotenv import load_dotenv
from fastmcp import Client
from fastmcp.client.transports import SSETransport


class KiteMCPClient:
    """
    Minimal async client for the hosted Kite MCP server (SSE mode).
    Connects to https://mcp.kite.trade/sse by default.

    🔹 No API keys or credentials required
    🔹 Uses SSE transport (event streaming)
    🔹 Safe for use in agents (e.g., async with KiteMCPClient())
    """

    def __init__(self, url: Optional[str] = None) -> None:
        load_dotenv(override=True)
        self.url = url or os.getenv("KITE_MCP_SSE_URL", "https://mcp.kite.trade/sse")
        self.transport: Optional[SSETransport] = None
        self._client: Optional[Client] = None

    # ---------------- Context Manager ----------------
    async def __aenter__(self) -> "KiteMCPClient":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close()

    # ---------------- Lifecycle ----------------
    async def connect(self) -> None:
        if self._client:
            return

        # Hosted version: no headers, no API keys
        self.transport = SSETransport(url=self.url)
        self._client = Client(self.transport)

        await self._client.__aenter__()
        print(f"⚡ Connected to hosted Kite MCP server (SSE) @ {self.url}")

    async def close(self) -> None:
        if not self._client:
            return

        try:
            await self._client.__aexit__(None, None, None)
            print("🧹 Closed Kite MCP client connection.")
        except Exception as e:
            print(f"⚠️ Error closing client: {e}")
        finally:
            self._client = None

    # ---------------- Tool Call ----------------
    async def call(self, tool_name: str, args: Optional[dict] = None) -> Any:
        if not self._client:
            raise RuntimeError("Client not connected. Use 'async with KiteMCPClient()'.")

        trace_on = os.getenv("AGENT_TRACE", "1").lower() not in ("0", "false")
        arg_str = (
            ", ".join(
                f"{k}={repr(v)[:80]}..." if len(repr(v)) > 80 else f"{k}={repr(v)}"
                for k, v in (args or {}).items()
            )
            if args
            else ""
        )

        if trace_on:
            print(f"🔧 [MCP] call_tool('{tool_name}'{', ' + arg_str if arg_str else ''})")

        t0 = time.perf_counter()
        try:
            result = await self._client.call_tool(tool_name, args or {})
            if trace_on:
                dt = (time.perf_counter() - t0) * 1000.0
                print(f"✅ [MCP] {tool_name} completed in {dt:.0f} ms")
            return result
        except Exception as e:
            dt = (time.perf_counter() - t0) * 1000.0
            print(f"❌ [MCP] {tool_name} failed after {dt:.0f} ms — {e}")
            raise
