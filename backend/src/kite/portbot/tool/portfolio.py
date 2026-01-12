# src/kite/portbot/tool/portfolio.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import os
import json
from typing import Any, Dict, Optional, List
from dotenv import load_dotenv

load_dotenv(override=True)

from src.kite.portbot.base import Agent
from src.kite.mcpclient.kite_mcp_client import KiteMCPClient


# ========================================
# DUMMY DATA FOR TESTING
# ========================================
DUMMY_HOLDINGS = [
    {
        "tradingsymbol": "INFY",
        "quantity": 2,
        "average_price": 450.0,
        "last_price": 1614.10,
        "pnl": 2328.20,  # (1614.10 - 450.0) * 2
        "source": "dummy"
    },
    {
        "tradingsymbol": "HDFCBANK",
        "quantity": 3,
        "average_price": 1006.0,
        "last_price": 939.00,
        "pnl": -201.00,  # (939.00 - 1006.0) * 3
        "source": "dummy"
    },
    {
        "tradingsymbol": "RELIANCE",
        "quantity": 5,
        "average_price": 1156.0,
        "last_price": 1475.30,
        "pnl": 1596.50,  # (1475.30 - 1156.0) * 5
        "source": "dummy"
    },
]

DUMMY_MF_HOLDINGS = [
    {
        "fund": "SBI BLUECHIP FUND - DIRECT PLAN - GROWTH",
        "quantity": 150.250,
        "average_price": 65.50,
        "last_price": 106.307,
        "source": "dummy"
    },
    {
        "fund": "ICICI PRUDENTIAL EQUITY & DEBT FUND - DIRECT - GROWTH",
        "quantity": 200.500,
        "average_price": 180.25,
        "last_price": 453.09,
        "source": "dummy"
    },
    {
        "fund": "HDFC MID-CAP OPPORTUNITIES FUND - DIRECT PLAN - GROWTH",
        "quantity": 75.125,
        "average_price": 125.80,
        "last_price": 222.322,
        "source": "dummy"
    },
]


# ========================================
# HELPER FUNCTIONS
# ========================================
def _extract_mcp_data(result: Any) -> List[Dict[str, Any]]:
    """Extract list data directly from MCP CallToolResult."""
    try:
        if hasattr(result, "content") and isinstance(result.content, list):
            for item in result.content:
                if hasattr(item, "type") and item.type == "text":
                    text = getattr(item, "text", "")
                    if text:
                        data = json.loads(text)
                        if isinstance(data, list):
                            return data
                        elif isinstance(data, dict):
                            for key in ("data", "items", "rows"):
                                if key in data and isinstance(data[key], list):
                                    return data[key]
    except Exception as e:
        print(f"Error extracting MCP data: {e}")
    return []


def _merge_unique_by_key(primary: List[Dict[str, Any]], secondary: List[Dict[str, Any]], key: str) -> List[Dict[str, Any]]:
    """Merge two lists, avoiding duplicates based on a key"""
    seen = {x.get(key) for x in primary if isinstance(x, dict)}
    merged = list(primary)
    for x in secondary:
        if not isinstance(x, dict):
            continue
        k = x.get(key)
        if k and k not in seen:
            merged.append(x)
            seen.add(k)
    return merged


def _normalize_holding(item: Dict[str, Any], source: str = "mcp") -> Dict[str, Any]:
    """Normalize holding data to consistent format"""
    symbol = item.get("tradingsymbol", "")
    qty = float(item.get("quantity", 0) or 0)
    avg = float(item.get("average_price", 0.0) or 0.0)
    ltp = float(item.get("last_price", 0.0) or 0.0)
    
    pnl = item.get("pnl")
    if pnl is None:
        pnl = (ltp - avg) * qty if qty != 0 else 0.0
    else:
        pnl = float(pnl)
    
    return {
        "symbol": symbol,
        "quantity": qty,
        "average_price": avg,
        "last_price": ltp,
        "current_value": qty * ltp,
        "investment_value": qty * avg,
        "pnl": pnl,
        "pnl_percentage": ((ltp - avg) / avg * 100.0) if avg > 0 else 0.0,
        "source": source
    }


def _normalize_position(item: Dict[str, Any], source: str = "mcp") -> Dict[str, Any]:
    """Normalize position data to consistent format"""
    symbol = item.get("tradingsymbol", "")
    qty = float(item.get("quantity", 0) or 0)
    pnl = float(item.get("pnl", 0.0) or 0.0)
    avg = float(item.get("average_price", 0.0) or 0.0)
    ltp = float(item.get("last_price", 0.0) or 0.0)
    
    return {
        "symbol": symbol,
        "quantity": qty,
        "average_price": avg,
        "last_price": ltp,
        "pnl": pnl,
        "source": source
    }


def _normalize_mf_holding(item: Dict[str, Any], source: str = "mcp") -> Dict[str, Any]:
    """Normalize mutual fund holding data to consistent format"""
    scheme = item.get("fund", "")
    units = float(item.get("quantity", 0.0) or 0.0)
    avg_nav = float(item.get("average_price", 0.0) or 0.0)
    current_nav = float(item.get("last_price", 0.0) or 0.0)
    
    current_value = units * current_nav
    investment_value = units * avg_nav
    pnl = current_value - investment_value
    pnl_percentage = (pnl / investment_value * 100.0) if investment_value > 0 else 0.0
    
    return {
        "scheme_name": scheme,
        "units": units,
        "average_nav": avg_nav,
        "current_nav": current_nav,
        "investment_value": investment_value,
        "current_value": current_value,
        "pnl": pnl,
        "pnl_percentage": pnl_percentage,
        "source": source
    }


# ========================================
# PORTFOLIO AGENT
# ========================================
class PortfolioAgent(Agent):
    """Portfolio agent for managing holdings, positions, and mutual funds."""
    name = "portfolio"
    description = "Manages portfolio data including holdings, positions, and mutual funds"

    tools = [
        {"name": "get_holdings", "description": "Retrieve all stock holdings with quantities and P&L", "parameters": {}},
        {"name": "get_positions", "description": "Get current open positions for the day", "parameters": {}},
        {"name": "get_mf_holdings", "description": "Fetch mutual fund holdings with current value and returns", "parameters": {}},
    ]

    def __init__(self, kite_client: KiteMCPClient, shared_state: Optional[Dict[str, Any]] = None):
        super().__init__(shared_state)
        self.kite_client = kite_client
        
        # MCP data flags (1 = use MCP data, 0 = ignore MCP data)
        self.use_mcp_holdings = os.getenv("MCP_HOLDINGS", "1").strip() == "1"
        self.use_mcp_positions = os.getenv("MCP_POSITIONS", "1").strip() == "1"
        self.use_mcp_mf = os.getenv("MCP_MF", "1").strip() == "1"
        
        # Dummy data flags (1 = use dummy data, 0 = ignore dummy data)
        self.use_dummy_holdings = os.getenv("DUMMY_HOLDINGS", "0").strip() == "1"
        self.use_dummy_positions = os.getenv("DUMMY_POSITIONS", "0").strip() == "1"
        self.use_dummy_mf = os.getenv("DUMMY_MF", "0").strip() == "1"

    async def run(self, tool_name: str, **kwargs: Any) -> Dict[str, Any]:
        if tool_name == "get_holdings":
            return await self._get_holdings()
        elif tool_name == "get_positions":
            return await self._get_positions()
        elif tool_name == "get_mf_holdings":
            return await self._get_mf_holdings()
        raise ValueError(f"Unknown tool: {tool_name}")

    async def _get_holdings(self) -> Dict[str, Any]:
        try:
            normalized_mcp = []
            
            # Fetch and normalize MCP data only if flag is enabled
            if self.use_mcp_holdings:
                res = await self.kite_client.call("get_holdings", {})
                mcp_data = _extract_mcp_data(res)
                normalized_mcp = [_normalize_holding(item, "mcp") for item in mcp_data if isinstance(item, dict)]
            
            # Start with MCP data (if enabled)
            all_holdings = normalized_mcp
            
            # Merge dummy data if flag is enabled
            if self.use_dummy_holdings:
                dummy_normalized = [_normalize_holding(item, "dummy") for item in DUMMY_HOLDINGS]
                all_holdings = _merge_unique_by_key(all_holdings, dummy_normalized, "symbol")
            
            # Round all values
            for h in all_holdings:
                for key in ["quantity", "average_price", "last_price", "current_value", "investment_value", "pnl", "pnl_percentage"]:
                    h[key] = round(h[key], 2)
            
            # Calculate totals
            total_investment = sum(h["investment_value"] for h in all_holdings)
            total_current_value = sum(h["current_value"] for h in all_holdings)
            total_pnl = sum(h["pnl"] for h in all_holdings)
            total_pnl_percentage = ((total_current_value - total_investment) / total_investment * 100.0) if total_investment > 0 else 0.0
            
            # Create summary with ALL data (excluding source) + totals
            summary = {
                "holdings": [{k: v for k, v in h.items() if k != "source"} for h in all_holdings],
                "totals": {
                    "total_holdings": len(all_holdings),
                    "total_investment": round(total_investment, 2),
                    "total_current_value": round(total_current_value, 2),
                    "total_pnl": round(total_pnl, 2),
                    "total_pnl_percentage": round(total_pnl_percentage, 2)
                }
            }
            
            return {"status": "success", "data": all_holdings, "summary": summary}
        except Exception as e:
            return {"status": "error", "message": f"Failed to fetch holdings: {str(e)}", "data": [], "summary": None}

    async def _get_positions(self) -> Dict[str, Any]:
        try:
            normalized_mcp = []
            
            # Fetch and normalize MCP data only if flag is enabled
            if self.use_mcp_positions:
                res = await self.kite_client.call("get_positions", {})
                mcp_data = _extract_mcp_data(res)
                normalized_mcp = [_normalize_position(item, "mcp") for item in mcp_data if isinstance(item, dict)]
            
            # Start with MCP data (if enabled)
            all_positions = normalized_mcp
            
            # Merge dummy data if flag is enabled (currently no dummy positions data)
            if self.use_dummy_positions:
                # dummy_normalized = [_normalize_position(item, "dummy") for item in DUMMY_POSITIONS]
                # all_positions = _merge_unique_by_key(all_positions, dummy_normalized, "symbol")
                pass
            
            # Round all values
            for p in all_positions:
                for key in ["quantity", "average_price", "last_price", "pnl"]:
                    p[key] = round(p[key], 2)
            
            total_pnl = sum(p["pnl"] for p in all_positions)
            
            # Create summary with ALL data (excluding source) + totals
            summary = {
                "positions": [{k: v for k, v in p.items() if k != "source"} for p in all_positions],
                "totals": {
                    "total_positions": len(all_positions),
                    "total_pnl": round(total_pnl, 2)
                }
            }
            
            return {"status": "success", "data": all_positions, "summary": summary}
        except Exception as e:
            return {"status": "error", "message": f"Failed to fetch positions: {str(e)}", "data": [], "summary": None}

    async def _get_mf_holdings(self) -> Dict[str, Any]:
        try:
            normalized_mcp = []
            
            # Fetch and normalize MCP data only if flag is enabled
            if self.use_mcp_mf:
                res = await self.kite_client.call("get_mf_holdings", {})
                mcp_data = _extract_mcp_data(res)
                normalized_mcp = [_normalize_mf_holding(item, "mcp") for item in mcp_data if isinstance(item, dict)]
            
            # Start with MCP data (if enabled)
            all_mf_holdings = normalized_mcp
            
            # Merge dummy data if flag is enabled
            if self.use_dummy_mf:
                dummy_normalized = [_normalize_mf_holding(item, "dummy") for item in DUMMY_MF_HOLDINGS]
                all_mf_holdings = _merge_unique_by_key(all_mf_holdings, dummy_normalized, "scheme_name")
            
            # Round all values
            for mf in all_mf_holdings:
                mf["units"] = round(mf["units"], 3)
                mf["average_nav"] = round(mf["average_nav"], 4)
                mf["current_nav"] = round(mf["current_nav"], 4)
                mf["investment_value"] = round(mf["investment_value"], 2)
                mf["current_value"] = round(mf["current_value"], 2)
                mf["pnl"] = round(mf["pnl"], 2)
                mf["pnl_percentage"] = round(mf["pnl_percentage"], 2)
            
            total_investment = sum(mf["investment_value"] for mf in all_mf_holdings)
            total_current_value = sum(mf["current_value"] for mf in all_mf_holdings)
            total_pnl = sum(mf["pnl"] for mf in all_mf_holdings)
            total_pnl_percentage = ((total_current_value - total_investment) / total_investment * 100.0) if total_investment > 0 else 0.0
            
            # Create summary with ALL data (excluding source) + totals
            summary = {
                "mutual_funds": [{k: v for k, v in mf.items() if k != "source"} for mf in all_mf_holdings],
                "totals": {
                    "total_schemes": len(all_mf_holdings),
                    "total_investment": round(total_investment, 2),
                    "total_current_value": round(total_current_value, 2),
                    "total_pnl": round(total_pnl, 2),
                    "total_pnl_percentage": round(total_pnl_percentage, 2)
                }
            }
            
            return {"status": "success", "data": all_mf_holdings, "summary": summary}
        except Exception as e:
            return {"status": "error", "message": f"Failed to fetch MF holdings: {str(e)}", "data": [], "summary": None}