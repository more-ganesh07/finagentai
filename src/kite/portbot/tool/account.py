# src/kite/portbot/tool/account.py
import json
from typing import Any, Dict, List

from src.kite.portbot.base import Agent
from src.kite.mcpclient.kite_mcp_client import KiteMCPClient


# ========================================
# HELPER FUNCTION
# ========================================
def _extract_mcp_data(result: Any) -> Dict[str, Any]:
    """
    Extract dict data directly from MCP CallToolResult.
    Handles the specific structure returned by KiteMCPClient.
    """
    try:
        if hasattr(result, "content") and isinstance(result.content, list):
            for item in result.content:
                if hasattr(item, "type") and item.type == "text":
                    text = getattr(item, "text", "")
                    if text:
                        data = json.loads(text)
                        if isinstance(data, dict):
                            return data
    except Exception as e:
        print(f"Error extracting MCP data: {e}")
    
    return {}


class AccountAgent(Agent):
    """
    Account agent for retrieving user profile and margin information.
    Returns structured JSON data for easy UI consumption.
    """
    name = "account"
    description = "Retrieves user profile and account margin information"

    tools = [
        {
            "name": "get_profile",
            "description": "Fetch user profile information",
            "parameters": {}
        },
        {
            "name": "get_margins",
            "description": "Get account margin details for equity and commodity",
            "parameters": {}
        },
    ]

    def __init__(self, kite_client: KiteMCPClient, shared_state=None):
        super().__init__(shared_state)
        self.kite_client = kite_client

    async def run(self, tool_name: str, **kwargs: Any) -> Dict[str, Any]:
        """Execute the specified tool"""
        if tool_name == "get_profile":
            return await self._get_profile()
        elif tool_name == "get_margins":
            return await self._get_margins()
        raise ValueError(f"Unknown tool: {tool_name}")

    async def _get_profile(self) -> Dict[str, Any]:
        """
        Fetch user profile information.
        
        Returns:
            {
                "status": "success" | "error",
                "data": {
                    "user_id": str,
                    "user_name": str,
                    "email": str,
                    "broker": str,
                    "user_type": str,
                    "products": list,
                    "exchanges": list
                },
                "summary": {
                    "display_name": str,
                    "account_id": str
                }
            }
        """
        try:
            result = await self.kite_client.call("get_profile", {})
            obj = _extract_mcp_data(result)

            if not isinstance(obj, dict):
                return {
                    "status": "error",
                    "message": "Invalid profile data format",
                    "data": None,
                    "summary": None
                }

            # Extract and normalize profile data
            profile_data = {
                "user_id": obj.get("user_id", ""),
                "user_name": obj.get("user_name") or obj.get("user_shortname", ""),
                "email": obj.get("email", ""),
                "broker": obj.get("broker", ""),
                "user_type": obj.get("user_type", ""),
                "products": obj.get("products", []),
                "exchanges": obj.get("exchanges", [])
            }

            # Create summary with all profile parameters for UI display
            summary = {
                "user_id": profile_data["user_id"],
                "user_name": profile_data["user_name"],
                "email": profile_data["email"],
                "broker": profile_data["broker"],
                "user_type": profile_data["user_type"],
                "products": profile_data["products"],
                "exchanges": profile_data["exchanges"]
            }

            return {
                "status": "success",
                "data": profile_data,
                "summary": summary
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to fetch profile: {str(e)}",
                "data": None,
                "summary": None
            }

    async def _get_margins(self) -> Dict[str, Any]:
        """
        Fetch account margin information.
        
        Returns:
            {
                "status": "success" | "error",
                "data": {
                    "equity": {
                        "net": float,
                        "available_cash": float,
                        "available_margin": float,
                        "utilised": float
                    },
                    "commodity": {
                        "net": float,
                        "available_cash": float,
                        "available_margin": float,
                        "utilised": float
                    }
                },
                "summary": {
                    "total_equity_margin": float,
                    "total_commodity_margin": float,
                    "total_available": float
                }
            }
        """
        try:
            result = await self.kite_client.call("get_margins", {})
            obj = _extract_mcp_data(result)

            if not isinstance(obj, dict):
                return {
                    "status": "error",
                    "message": "Invalid margin data format",
                    "data": None,
                    "summary": None
                }

            # Helper to safely extract nested values
            def safe_float(d: dict, *keys, default=0.0) -> float:
                """Safely extract nested float value from dict"""
                current = d
                for key in keys:
                    if not isinstance(current, dict):
                        return default
                    current = current.get(key, default)
                try:
                    return float(current)
                except (ValueError, TypeError):
                    return default

            # Extract equity margins
            equity = obj.get("equity", {}) or {}
            equity_data = {
                "net": safe_float(equity, "net"),
                "available_cash": safe_float(equity, "available", "cash"),
                "available_margin": safe_float(equity, "available", "live_balance"),
                "utilised": safe_float(equity, "utilised", "debits")
            }

            # Extract commodity margins
            commodity = obj.get("commodity", {}) or {}
            commodity_data = {
                "net": safe_float(commodity, "net"),
                "available_cash": safe_float(commodity, "available", "cash"),
                "available_margin": safe_float(commodity, "available", "live_balance"),
                "utilised": safe_float(commodity, "utilised", "debits")
            }

            # Create summary with all margin details (excluding source)
            summary = {
                "equity": {
                    "net": equity_data["net"],
                    "available_cash": equity_data["available_cash"],
                    "available_margin": equity_data["available_margin"],
                    "utilised": equity_data["utilised"]
                },
                "commodity": {
                    "net": commodity_data["net"],
                    "available_cash": commodity_data["available_cash"],
                    "available_margin": commodity_data["available_margin"],
                    "utilised": commodity_data["utilised"]
                },
                "total_available": equity_data["net"] + commodity_data["net"]
            }

            return {
                "status": "success",
                "data": {
                    "equity": equity_data,
                    "commodity": commodity_data
                },
                "summary": summary
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to fetch margins: {str(e)}",
                "data": None,
                "summary": None
            }
