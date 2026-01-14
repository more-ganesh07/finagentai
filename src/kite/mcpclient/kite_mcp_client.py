# src/kite/mcpclient/kite_mcp_client.py
import json
import asyncio
import anyio
import contextlib
import os
import re
import time
from typing import Any, Dict, Optional

from fastmcp import Client
from fastmcp.client.transports import SSETransport
from fastmcp.exceptions import ToolError

# Flexible URL patterns
KITE_URL_REGEX = re.compile(r"https?://[^\s)]+kite\.[^\s)]+", re.IGNORECASE)
GENERIC_URL_REGEX = re.compile(r"https?://[^\s)]+", re.IGNORECASE)

class RateLimiter:
    """Simple rate limiter using token bucket algorithm."""
    
    def __init__(self, max_requests: int = 10, time_window: float = 1.0):
        """
        Args:
            max_requests: Maximum number of requests allowed in time_window
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Wait until a request can be made without exceeding rate limit."""
        while True:
            async with self._lock:
                now = time.time()
                
                # Remove requests outside the time window
                self.requests = [req_time for req_time in self.requests 
                               if now - req_time < self.time_window]
                
                # If we're under the limit, record and return
                if len(self.requests) < self.max_requests:
                    self.requests.append(now)
                    return
                
                # Calculate how long to wait until the oldest request falls out of window
                sleep_time = self.time_window - (now - self.requests[0])
            
            # Wait outside the lock to prevent deadlocks
            if sleep_time > 0:
                print(f"⏳ Rate limit reached. Waiting {sleep_time:.2f}s...")
                await asyncio.sleep(sleep_time)

class KiteMCPClient:
    """Stable SSE-based Zerodha Kite MCP client with rate limiting and retry logic."""

    def __init__(self,
                 url: Optional[str] = None,
                 headers: Optional[Dict[str, str]] = None,
                 max_requests_per_second: int = None,
                 max_retries: int = None):
        """
        Args:
            url: MCP server URL
            headers: Optional HTTP headers
            max_requests_per_second: Maximum requests per second (default: 1)
            max_retries: Maximum retry attempts for failed requests (default: 5)
        """
        # Priority: explicit arg > KITE_MCP_SSE_URL > MCP_SSE_URL > default
        self.url = url or os.getenv("KITE_MCP_SSE_URL") or os.getenv("MCP_SSE_URL") or "https://mcp.kite.trade/sse"
        
        # Source of truth for headers
        self.headers = headers or {}
        if "User-Agent" not in self.headers:
            self.headers["User-Agent"] = "KiteInfi-Backend/1.0"
            
        self.transport: Optional[SSETransport] = None
        self._client: Optional[Client] = None
        
        # Rate limiting configuration
        max_rps = max_requests_per_second or int(os.getenv("MCP_MAX_REQUESTS_PER_SECOND", "1"))
        self.rate_limiter = RateLimiter(max_requests=max_rps, time_window=1.0)
        
        # Retry configuration
        self.max_retries = max_retries or int(os.getenv("MCP_MAX_RETRIES", "5"))
        self.retry_delay = float(os.getenv("MCP_RETRY_DELAY", "2.0"))
        
        # Persistence configuration
        self.session_file = os.path.join(os.getcwd(), ".kite_session.json")

    # --------------------------
    # Context Manager lifecycle
    # --------------------------
    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.close(exc_type, exc, tb)

    # --------------------------
    # Connect / Close
    # --------------------------
    async def connect(self):
        if self._client is None:
            # Refresh headers from disk if available
            self.restore_session()
            
            # Always create a fresh transport and client
            self.transport = SSETransport(url=self.url, headers=self.headers)
            self._client = Client(self.transport)
            await self._client.__aenter__()
            print(f"🔌 Connected to Kite MCP: {self.url}")

    async def close(self, exc_type=None, exc=None, tb=None):
        """Close SSE reader and client cleanly."""
        # Auto-save before closure
        self.save_session()
        
        if self._client:
            if self.transport:
                reader = getattr(self.transport, "reader_task", None)
                if reader and not reader.done():
                    reader.cancel()
                    with contextlib.suppress(Exception):
                        await reader

            with contextlib.suppress(Exception):
                await self._client.__aexit__(exc_type, exc, tb)

        self._client = None
        self.transport = None

    def save_session(self):
        """Save headers to disk for persistence."""
        try:
            if not self.headers:
                return
            
            with open(self.session_file, "w") as f:
                json.dump(self.headers, f)
            print(f"💾 Kite session saved to {self.session_file}")
        except Exception as e:
            print(f"⚠️ Error saving session: {e}")

    def restore_session(self) -> bool:
        """Load headers from disk."""
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, "r") as f:
                    saved_headers = json.load(f)
                    if saved_headers:
                        self.headers.update(saved_headers)
                        print("📂 Kite session restored from disk.")
                        return True
        except Exception as e:
            print(f"⚠️ Error restoring session: {e}")
        return False

    def clear_session(self):
        """Wipe session from disk and memory."""
        try:
            # 1. Clear memory source of truth
            self.headers = {"User-Agent": "KiteInfi-Backend/1.0"}
            
            # 2. Invalidate current client AND transport to force full reconnect
            self._client = None
            self.transport = None
            
            # 3. Clear disk
            if os.path.exists(self.session_file):
                os.remove(self.session_file)
                print(f"🧹 Session file deleted: {self.session_file}")
                
            print("✨ Kite session cleared successfully. Ready for fresh login.")
        except Exception as e:
            print(f"⚠️ Error clearing session: {e}")

    async def force_reconnect(self):
        """Force a complete teardown and reconnection to MCP server."""
        try:
            # Clean up existing client if any
            if self._client:
                with contextlib.suppress(Exception):
                    await self._client.__aexit__(None, None, None)
            
            # Reset both client and transport to ensure fresh connection
            self._client = None
            self.transport = None
            
            # Small delay to allow cleanup
            await asyncio.sleep(0.1)
            
            # Reconnect with fresh transport
            await self.connect()
            print("🔄 Force reconnection completed successfully.")
        except Exception as e:
            print(f"⚠️ Force reconnection failed: {e}")
            raise

    # --------------------------
    # Tool call with rate limiting and retry
    # --------------------------
    async def call(self, tool_name: str, args: Optional[Dict[str, Any]] = None, silent: bool = False):
        """
        Call MCP tool with rate limiting and automatic retry on failure.
        """
        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
                if not self._client:
                    await self.connect()
                
                # Apply rate limiting before each request
                await self.rate_limiter.acquire()
                
                # Make the actual call
                result = await self._client.call_tool(tool_name, args or {})
                
                # Success - return immediately
                return result
                
            except Exception as e:
                last_error = e
                error_msg = str(e).lower()
                
                # Check if it's a rate limit error
                if "429" in error_msg or "too many requests" in error_msg:
                    if attempt < self.max_retries:
                        # Exponential backoff for rate limit errors
                        wait_time = self.retry_delay * (2 ** attempt)
                        if not silent:
                            print(f"⚠️ Rate limit hit (429). Retrying in {wait_time:.1f}s... (attempt {attempt + 1}/{self.max_retries})")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        if not silent:
                            print(f"❌ Rate limit error after {self.max_retries} retries: {e}")
                        raise ToolError(f"Rate limit exceeded after {self.max_retries} retries. Please try again later.")
                
                # Check if it's a connection/protocol error
                elif any(word in error_msg for word in ["broken", "connection", "closed", "resource", "anyio"]) or \
                     type(e).__name__ in ["ClosedResourceError", "RemoteProtocolError", "EndOfStream", "ConnectionResetError"] or \
                     isinstance(e, anyio.ClosedResourceError):
                         
                    if attempt < self.max_retries:
                        wait_time = self.retry_delay * (2 ** attempt)
                        if not silent:
                            print(f"⚠️ Connection failure ({type(e).__name__}). Retrying in {wait_time:.1f}s... (attempt {attempt + 1}/{self.max_retries})")
                        
                        # FORCE a complete teardown and re-initialization with fresh transport
                        try:
                            await self.force_reconnect()
                        except Exception as reconnect_err:
                            if not silent:
                                print(f"⚠️ Reconnection attempt failed: {reconnect_err}")
                        
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        if not silent:
                            print(f"❌ Connection failure after {self.max_retries} retries: {e}")
                        raise
                
                # For other errors, don't retry
                else:
                    if not silent:
                        print(f"❌ Tool error call '{tool_name}': {type(e).__name__}: {e}")
                    raise
        
        if last_error:
            raise last_error

    async def validate_session(self) -> bool:
        """
        Check if the current session is valid by calling a lightweight tool.
        """
        try:
            res = await self.call("get_profile", {}, silent=True)
            raw_text = self._collect_text_chunks(res)
            if "please log in" in raw_text.lower():
                return False
            return True
        except Exception:
            return False

    @staticmethod
    def _collect_text_chunks(result: Any) -> str:
        texts = []
        contents = getattr(result, "content", None)
        if isinstance(contents, list):
            for item in contents:
                if getattr(item, "type", "") == "text":
                    t = getattr(item, "text", "")
                    if t:
                        texts.append(t)
        return "\n".join(texts).strip()

    @staticmethod
    def extract_login_url(login_result: Any) -> Optional[str]:
        # (1) From text content
        raw_text = KiteMCPClient._collect_text_chunks(login_result)
        if raw_text:
            m = KITE_URL_REGEX.search(raw_text) or GENERIC_URL_REGEX.search(raw_text)
            if m:
                return m.group(0)

        # (2) Try JSON payloads
        for attr in ("structured_content", "data"):
            payload = getattr(login_result, attr, None)
            if not payload: continue
            if isinstance(payload, dict):
                for key in ("login_url", "url", "href"):
                    v = payload.get(key)
                    if isinstance(v, str) and v.startswith("http"):
                        return v
        return None
