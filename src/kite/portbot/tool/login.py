

# # src/kite/portbot/tool/login.py

# import webbrowser
# from typing import Any, Dict, Optional

# from src.kite.portbot.base import Agent
# from src.kite.mcpclient.kite_mcp_client import KiteMCPClient


# class LoginAgent(Agent):
#     name = "login"
#     description = "Handles Kite authentication via MCP login tool."

#     tools = [
#         {
#             "name": "login",
#             "description": "Login to Zerodha Kite (interactive browser login).",
#             "parameters": {}
#         }
#     ]

#     def __init__(self, kite_client: KiteMCPClient, shared_state: Optional[Dict[str, Any]] = None):
#         super().__init__(shared_state)
#         self.kite_client = kite_client

#     async def run(self, tool_name: str = "login", **kwargs: Any) -> Dict[str, Any]:
#         if tool_name != "login":
#             raise ValueError(f"Unknown tool: {tool_name}")
        
#         # In web mode, we usually just want the URL or to check the session
#         # For backward compatibility with CLI, we still expose _login
#         return await self._login()

#     async def get_login_url(self) -> Optional[str]:
#         """
#         Fetches the Zerodha login URL without opening a browser or waiting.
#         """
#         try:
#             login_res = await self.kite_client.call("login", {})
#             return self.kite_client.extract_login_url(login_res)
#         except Exception as e:
#             print(f"⚠️ Error fetching login URL: {e}")
#             return None

#     async def finalize_session(self) -> Dict[str, Any]:
#         """
#         Checks the current MCP client for a live session and updates shared state.
#         This is called after the user completes the browser login.
#         """
#         # Try to validate the session first
#         is_valid = False
#         try:
#             validate = getattr(self.kite_client, "validate_session", None)
#             if callable(validate):
#                 val = validate()
#                 is_valid = await val if hasattr(val, "__await__") else bool(val)
#         except Exception:
#             is_valid = False

#         # Best-effort fetch of session object
#         session_obj = {}
#         try:
#             # Check internal client state
#             if self.kite_client and self.kite_client._client:
#                 session_obj = getattr(self.kite_client._client, "session", {})
#         except Exception:
#             pass

#         if is_valid or session_obj:
#             self.shared_state["session"] = session_obj
#             # Immediately persist to disk after successful login/confirmation
#             if hasattr(self.kite_client, "save_session"):
#                 self.kite_client.save_session()
                
#             return {
#                 "status": "success",
#                 "message": "Session confirmed and persisted to disk.",
#                 "session": session_obj
#             }
        
#         return {
#             "status": "error",
#             "message": "No active session found. Please complete login in the browser first."
#         }

#     async def _login(self) -> Dict[str, Any]:
#         print("🔐 Initiating Kite login flow…")

#         login_url = await self.get_login_url()
#         if not login_url:
#             return {
#                 "status": "error",
#                 "message": "Could not extract login URL from MCP login()"
#             }

#         print(f"\n🔗 Login URL:\n{login_url}\n")
#         try:
#             webbrowser.open(login_url)
#             print("🌐 Login URL opened in browser.")
#         except Exception:
#             print("⚠️ Could not open browser automatically.")

#         input("\n⏳ Complete login in browser → then press ENTER here… ")

#         return await self.finalize_session()





# src/kite/portbot/tool/login.py
# src/kite/portbot/tool/login.py
# src/kite/portbot/tool/login.py

import webbrowser
import asyncio
from typing import Any, Dict, Optional

from src.kite.portbot.base import Agent
from src.kite.mcpclient.kite_mcp_client import KiteMCPClient


class LoginAgent(Agent):
    name = "login"
    description = "Handles Kite authentication via MCP login tool."

    tools = [
        {
            "name": "login",
            "description": "Login to Zerodha Kite (interactive browser login).",
            "parameters": {}
        }
    ]

    def __init__(self, kite_client: KiteMCPClient, shared_state: Optional[Dict[str, Any]] = None):
        super().__init__(shared_state)
        self.kite_client = kite_client

    async def run(self, tool_name: str = "login", **kwargs: Any) -> Dict[str, Any]:
        if tool_name != "login":
            raise ValueError(f"Unknown tool: {tool_name}")
        
        # In web mode, we usually just want the URL or to check the session
        # For backward compatibility with CLI, we still expose _login
        return await self._login()

    async def get_login_url(self) -> Optional[str]:
        """
        Fetches the Zerodha login URL without opening a browser or waiting.
        """
        try:
            login_res = await self.kite_client.call("login", {})
            return self.kite_client.extract_login_url(login_res)
        except Exception as e:
            print(f"⚠️ Error fetching login URL: {e}")
            return None

    async def finalize_session(self) -> Dict[str, Any]:
        """
        Checks the current MCP client for a live session and updates shared state.
        This is called after the user completes the browser login.
        """
        # Try to validate the session first
        is_valid = False
        try:
            validate = getattr(self.kite_client, "validate_session", None)
            if callable(validate):
                val = validate()
                is_valid = await val if hasattr(val, "__await__") else bool(val)
        except Exception:
            is_valid = False

        # Best-effort fetch of session object
        session_obj = {}
        try:
            # Check internal client state
            if self.kite_client and self.kite_client._client:
                session_obj = getattr(self.kite_client._client, "session", {})
        except Exception:
            pass

        if is_valid or session_obj:
            self.shared_state["session"] = session_obj
            # Immediately persist to disk after successful login/confirmation
            if hasattr(self.kite_client, "save_session"):
                self.kite_client.save_session()
                
            return {
                "status": "success",
                "message": "Session confirmed and persisted to disk.",
                "session": session_obj
            }
        
        return {
            "status": "error",
            "message": "No active session found. Please complete login in the browser first."
        }

    async def _login(self) -> Dict[str, Any]:
        print("🔐 Initiating Kite login flow…")

        login_url = await self.get_login_url()
        if not login_url:
            return {
                "status": "error",
                "message": "Could not extract login URL from MCP login()"
            }

        print(f"\n🔗 Login URL:\n{login_url}\n")
        try:
            webbrowser.open(login_url)
            print("🌐 Login URL opened in browser.")
        except Exception:
            print("⚠️ Could not open browser automatically.")

        # Auto-detect login completion instead of waiting for ENTER
        print("\n⏳ Waiting for login completion...")
        
        timeout = 300  # 5 minutes
        check_interval = 0.1  # Check every 100ms
        elapsed = 0
        
        while elapsed < timeout:
            await asyncio.sleep(check_interval)
            elapsed += check_interval
            
            # Check if session is active
            try:
                is_valid = False
                validate = getattr(self.kite_client, "validate_session", None)
                if callable(validate):
                    val = validate()
                    is_valid = await val if hasattr(val, "__await__") else bool(val)
                
                if not is_valid and self.kite_client and self.kite_client._client:
                    session_obj = getattr(self.kite_client._client, "session", {})
                    is_valid = bool(session_obj and session_obj.get("access_token"))
                
                if is_valid:
                    print("✅ Login detected successfully!")
                    break
                    
            except Exception:
                pass
            
            # Progress indicator every 10 seconds
            if int(elapsed) % 10 == 0:
                print(f"⏱️  Still waiting... ({int(elapsed)}s elapsed)")
        
        if elapsed >= timeout:
            print(f"⏰ Timeout reached after {timeout}s")
            return {
                "status": "timeout",
                "message": "Login timeout. Please try again."
            }

        return await self.finalize_session()