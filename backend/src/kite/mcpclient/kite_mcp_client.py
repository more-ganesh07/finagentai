# src/kite/client/kite_mcp_client.py
import json

import asyncio
import contextlib
import os
import re
import time
import webbrowser
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
        async with self._lock:
            now = time.time()
            
            # Remove requests outside the time window
            self.requests = [req_time for req_time in self.requests 
                           if now - req_time < self.time_window]
            
            # If we're at the limit, wait
            if len(self.requests) >= self.max_requests:
                sleep_time = self.time_window - (now - self.requests[0])
                if sleep_time > 0:
                    print(f"⏳ Rate limit reached. Waiting {sleep_time:.2f}s...")
                    await asyncio.sleep(sleep_time)
                    # Recursively try again
                    return await self.acquire()
            
            # Record this request
            self.requests.append(now)


class KiteMCPClient:
    """Stable SSE-based Zerodha Kite MCP client with rate limiting and retry logic."""

    def __init__(self,
                 url: str = "https://mcp.kite.trade/sse",
                 headers: Optional[Dict[str, str]] = None,
                 max_requests_per_second: int = None,
                 max_retries: int = None):
        """
        Args:
            url: MCP server URL
            headers: Optional HTTP headers
            max_requests_per_second: Maximum requests per second (default: 10)
            max_retries: Maximum retry attempts for failed requests (default: 3)
        """
        self.transport = SSETransport(url=url, headers=headers or {})
        self._client: Optional[Client] = None
        
        # Rate limiting configuration
        # Rate limiting configuration
        # Default lowered to 1 RPS to safely handle Kite MCP limits
        max_rps = max_requests_per_second or int(os.getenv("MCP_MAX_REQUESTS_PER_SECOND", "1"))
        self.rate_limiter = RateLimiter(max_requests=max_rps, time_window=1.0)
        
        # Retry configuration
        self.max_retries = max_retries or int(os.getenv("MCP_MAX_RETRIES", "5"))
        self.retry_delay = float(os.getenv("MCP_RETRY_DELAY", "2.0"))  # Increased initial retry delay
        
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
            # Try to restore session before connecting
            self.restore_session()
            
            self._client = Client(self.transport)
            await self._client.__aenter__()

    async def close(self, exc_type=None, exc=None, tb=None):
        """Close SSE reader and client cleanly."""
        if self._client:
            reader = getattr(self.transport, "reader_task", None)
            if reader and not reader.done():
                reader.cancel()
                with contextlib.suppress(Exception):
                    await reader

            with contextlib.suppress(Exception):
                await self._client.__aexit__(exc_type, exc, tb)

        self._client = None
        # Auto-save on closure if transport has headers
        self.save_session()

    def save_session(self):
        """Save transport headers to disk for persistence."""
        try:
            if not self.transport.headers:
                return
            
            # Filter headers to avoid sensitive info if possible, 
            # but for Kite MCP we need the cookies/auth headers.
            with open(self.session_file, "w") as f:
                json.dump(self.transport.headers, f)
            print(f"💾 Kite session saved to {self.session_file}")
        except Exception as e:
            print(f"⚠️ Error saving session: {e}")

    def restore_session(self) -> bool:
        """Load headers from disk and inject into transport."""
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, "r") as f:
                    headers = json.load(f)
                    if headers:
                        self.transport.headers.update(headers)
                        print("📂 Kite session restored from disk.")
                        return True
        except Exception as e:
            print(f"⚠️ Error restoring session: {e}")
        return False

    def clear_session(self):
        """Wipe session from disk and memory."""
        try:
            # 1. Clear memory
            self.transport.headers = {}
            if self._client:
                # Only attempt to access session if client exists
                try:
                    if hasattr(self._client, "session"):
                        self._client.session = None
                except Exception:
                    # Ignore errors if client is disconnected/inaccessible
                    pass
            
            # 2. Clear disk
            if os.path.exists(self.session_file):
                os.remove(self.session_file)
                print(f"🧹 Session file deleted: {self.session_file}")
                
            print("✨ Kite session cleared successfully. Ready for fresh login.")
        except Exception as e:
            print(f"⚠️ Error clearing session: {e}")

    # --------------------------
    # Tool call with rate limiting and retry
    # --------------------------
    async def call(self, tool_name: str, args: Optional[Dict[str, Any]] = None, silent: bool = False):
        """
        Call MCP tool with rate limiting and automatic retry on failure.
        
        Args:
            tool_name: Name of the tool to call
            args: Tool arguments
            silent: If True, suppress error printing (useful for validation checks)
            
        Returns:
            Tool result
            
        Raises:
            ToolError: If all retry attempts fail
        """
        if not self._client:
            await self.connect()

        last_error = None
        
        for attempt in range(self.max_retries + 1):
            try:
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
                
                # Check if it's a connection error
                elif "broken" in error_msg or "connection" in error_msg:
                    if attempt < self.max_retries:
                        wait_time = self.retry_delay * (2 ** attempt)
                        if not silent:
                            print(f"⚠️ Connection error. Retrying in {wait_time:.1f}s... (attempt {attempt + 1}/{self.max_retries})")
                        
                        # Try to reconnect
                        try:
                            await self.close()
                            await self.connect()
                        except Exception:
                            pass
                        
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        if not silent:
                            print(f"❌ Connection error after {self.max_retries} retries: {e}")
                        raise
                
                # For other errors, don't retry
                else:
                    if not silent:
                        print(f"❌ Tool error: {e}")
                    raise
        
        # If we get here, all retries failed
        if last_error:
            raise last_error

    async def validate_session(self) -> bool:
        """
        Check if the current session is valid by calling a lightweight tool.
        """
        try:
            # get_profile is a lightweight call to check session validity
            res = await self.call("get_profile", {}, silent=True)
            # If it doesn't raise an exception, the session is likely valid
            # Also check for specific error messages in the result content
            raw_text = self._collect_text_chunks(res)
            if "please log in" in raw_text.lower():
                return False
            return True
        except Exception:
            return False

    # --------------------------
    # Collect text chunks (needed for URL parsing)
    # --------------------------
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

    # --------------------------
    # Flexible login URL extraction
    # --------------------------
    @staticmethod
    def extract_login_url(login_result: Any) -> Optional[str]:

        # (1) From text content
        raw_text = KiteMCPClient._collect_text_chunks(login_result)
        if raw_text:
            m = KITE_URL_REGEX.search(raw_text)
            if m:
                return m.group(0)

            m2 = GENERIC_URL_REGEX.search(raw_text)
            if m2:
                return m2.group(0)

        # (2) Try JSON payloads (structured_content, data)
        for attr in ("structured_content", "data"):
            payload = getattr(login_result, attr, None)
            if not payload:
                continue

            if isinstance(payload, dict):
                for key in ("login_url", "url", "href"):
                    v = payload.get(key)
                    if isinstance(v, str) and v.startswith("http"):
                        return v

                for v in payload.values():
                    if isinstance(v, str):
                        m = KITE_URL_REGEX.search(v) or GENERIC_URL_REGEX.search(v)
                        if m:
                            return m.group(0)

            if isinstance(payload, list):
                for item in payload:
                    if isinstance(item, str):
                        m = KITE_URL_REGEX.search(item) or GENERIC_URL_REGEX.search(item)
                        if m:
                            return m.group(0)
                    if isinstance(item, dict):
                        for v in item.values():
                            if isinstance(v, str):
                                m = KITE_URL_REGEX.search(v) or GENERIC_URL_REGEX.search(v)
                                if m:
                                    return m.group(0)

        return None

    # --------------------------
    # Login helper
    # --------------------------
    async def run_login_flow(self) -> str:
        login_res = await self.call("login", {})
        login_url = self.extract_login_url(login_res)

        if not login_url:
            raw = self._collect_text_chunks(login_res)
            print("⚠️ Could not extract login URL.")
            if raw:
                print("MCP login output:")
                print(raw)
            raise RuntimeError("Could not extract login URL from MCP login tool.")

        print(f"\n🔗 OPEN THIS LOGIN URL:\n{login_url}\n")
        try:
            webbrowser.open(login_url)
        except Exception:
            print("⚠️ Could not open browser automatically.")

        input("⏳ Login in browser → then press ENTER here... ")

        return login_url






