# src/kite/portbot/tool/orders.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import os
import json
from typing import Any, Dict, Optional, List
from datetime import datetime
from dotenv import load_dotenv

load_dotenv(override=True)

from src.kite.portbot.base import Agent
from src.kite.mcpclient.kite_mcp_client import KiteMCPClient


# ========================================
# DUMMY DATA FOR TESTING
# ========================================
DUMMY_ORDERS = [
    {
        "order_id": "240101000001234",
        "exchange": "NSE",
        "tradingsymbol": "INFY",
        "transaction_type": "BUY",
        "product": "CNC",
        "quantity": 10,
        "filled_quantity": 10,
        "average_price": 1520.0,
        "status": "COMPLETE",
        "order_timestamp": "2025-01-09T10:21:15+05:30",
        "source": "dummy"
    },
    {
        "order_id": "240101000001235",
        "exchange": "NSE",
        "tradingsymbol": "RELIANCE",
        "transaction_type": "SELL",
        "product": "MIS",
        "quantity": 5,
        "filled_quantity": 0,
        "average_price": 0.0,
        "status": "REJECTED",
        "rejection_reason": "Insufficient margin (dummy)",
        "order_timestamp": "2025-01-09T11:03:02+05:30",
        "source": "dummy"
    },
    {
        "order_id": "240101000001236",
        "exchange": "NSE",
        "tradingsymbol": "TCS",
        "transaction_type": "BUY",
        "product": "CNC",
        "quantity": 2,
        "filled_quantity": 2,
        "average_price": 3550.0,
        "status": "COMPLETE",
        "order_timestamp": "2025-01-09T14:30:45+05:30",
        "source": "dummy"
    },
]

DUMMY_TRADES = [
    {
        "trade_id": "T24010100004567",
        "order_id": "240101000001234",
        "exchange": "NSE",
        "tradingsymbol": "INFY",
        "quantity": 10,
        "price": 1520.0,
        "trade_timestamp": "2025-01-09T10:21:20+05:30",
        "product": "CNC",
        "transaction_type": "BUY",
        "source": "dummy"
    },
    {
        "trade_id": "T24010100004568",
        "order_id": "240101000001236",
        "exchange": "NSE",
        "tradingsymbol": "TCS",
        "quantity": 2,
        "price": 3550.0,
        "trade_timestamp": "2025-01-09T14:30:50+05:30",
        "product": "CNC",
        "transaction_type": "BUY",
        "source": "dummy"
    },
]

DUMMY_ORDER_HISTORY = {
    "240101000001234": [
        {"status": "PUT ORDER REQ RECEIVED", "timestamp": "2025-01-09T10:21:10+05:30"},
        {"status": "OPEN", "timestamp": "2025-01-09T10:21:12+05:30"},
        {"status": "COMPLETE", "timestamp": "2025-01-09T10:21:20+05:30"},
    ],

    "240101000001235": [
        {"status": "PUT ORDER REQ RECEIVED", "timestamp": "2025-01-09T11:03:01+05:30"},
        {
            "status": "REJECTED",
            "timestamp": "2025-01-09T11:03:02+05:30",
            "message": "Order rejected: Insufficient margin available to execute the trade."
        },
    ],

    "240101000001236": [
        {"status": "PUT ORDER REQ RECEIVED", "timestamp": "2025-01-09T14:30:40+05:30"},
        {
            "status": "REJECTED",
            "timestamp": "2025-01-09T14:30:42+05:30",
            "message": "Order rejected: Price outside the exchange's circuit limit range."
        },
    ],
}



# ========================================
# HELPER FUNCTIONS
# ========================================
def _extract_mcp_data(result: Any) -> List[Dict[str, Any]]:
    """
    Extract list data directly from MCP CallToolResult.
    Handles the specific structure returned by KiteMCPClient.
    """
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


def _normalize_order(item: Dict[str, Any], source: str = "mcp") -> Dict[str, Any]:
    """Normalize order data to consistent format"""
    return {
        "order_id": item.get("order_id", ""),
        "symbol": item.get("tradingsymbol", ""),
        "exchange": item.get("exchange", ""),
        "transaction_type": item.get("transaction_type", ""),
        "product": item.get("product", ""),
        "quantity": int(item.get("quantity", 0) or 0),
        "filled_quantity": int(item.get("filled_quantity", 0) or 0),
        "pending_quantity": int(item.get("quantity", 0) or 0) - int(item.get("filled_quantity", 0) or 0),
        "average_price": round(float(item.get("average_price", 0.0) or 0.0), 2),
        "status": item.get("status", ""),
        "order_timestamp": item.get("order_timestamp", ""),
        "rejection_reason": item.get("rejection_reason", ""),
        "source": source
    }


def _normalize_trade(item: Dict[str, Any], source: str = "mcp") -> Dict[str, Any]:
    """Normalize trade data to consistent format"""
    return {
        "trade_id": item.get("trade_id", ""),
        "order_id": item.get("order_id", ""),
        "symbol": item.get("tradingsymbol", ""),
        "exchange": item.get("exchange", ""),
        "transaction_type": item.get("transaction_type", ""),
        "product": item.get("product", ""),
        "quantity": int(item.get("quantity", 0) or 0),
        "price": round(float(item.get("price", 0.0) or 0.0), 2),
        "trade_timestamp": item.get("trade_timestamp", ""),
        "source": source
    }


def _normalize_history_event(item: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize order history event to consistent format"""
    return {
        "timestamp": item.get("timestamp", ""),
        "status": item.get("status", ""),
        "message": item.get("message", "") or item.get("text", "")
    }


# ========================================
# ORDERS AGENT
# ========================================
class OrdersAgent(Agent):
    """
    Orders agent for managing order and trade queries.
    Returns structured JSON data for easy UI consumption.
    """
    name = "orders"
    description = "Read-only order/trade queries with dummy data support"

    tools = [
        {
            "name": "get_orders",
            "description": "List all orders with status breakdown",
            "parameters": {}
        },
        {
            "name": "get_trades",
            "description": "List all executed trades",
            "parameters": {}
        },
        {
            "name": "get_order_history",
            "description": "Get timeline/history for a specific order, or analyze failed/rejected orders if no order_id provided",
            "parameters": {"order_id": "str (optional)"}
        },
    ]

    def __init__(self, kite_client: KiteMCPClient, shared_state=None):
        super().__init__(shared_state)
        self.kite_client = kite_client

        # Separate dummy flags for each data type
        self.use_dummy_orders = os.getenv("DUMMY_ORDERS", "0").strip() == "1"
        self.use_dummy_trades = os.getenv("DUMMY_TRADES", "0").strip() == "1"
        self.use_dummy_order_history = os.getenv("DUMMY_ORDER_HISTORY", "0").strip() == "1"

    async def run(self, tool_name: str, **kwargs):
        """Execute the specified tool"""
        if tool_name == "get_orders":
            return await self._get_orders()
        elif tool_name == "get_trades":
            return await self._get_trades()
        elif tool_name == "get_order_history":
            return await self._get_order_history(**kwargs)
        raise ValueError(f"Unknown tool: {tool_name}")

    async def _get_orders(self) -> Dict[str, Any]:
        """
        Fetch all orders.
        
        Returns:
            {
                "status": "success" | "error",
                "data": [
                    {
                        "order_id": str,
                        "symbol": str,
                        "exchange": str,
                        "transaction_type": str,
                        "product": str,
                        "quantity": int,
                        "filled_quantity": int,
                        "pending_quantity": int,
                        "average_price": float,
                        "status": str,
                        "order_timestamp": str,
                        "rejection_reason": str,
                        "source": "mcp" | "dummy"
                    }
                ],
                "summary": {
                    "total_orders": int,
                    "complete": int,
                    "rejected": int,
                    "open": int,
                    "cancelled": int
                }
            }
        """
        try:
            # Fetch MCP data
            res = await self.kite_client.call("get_orders", {})
            mcp_data = _extract_mcp_data(res)
            
            # Normalize MCP data
            normalized_mcp = [_normalize_order(item, "mcp") for item in mcp_data if isinstance(item, dict)]
            
            # Merge with dummy data if enabled
            if self.use_dummy_orders:
                dummy_normalized = [_normalize_order(item, "dummy") for item in DUMMY_ORDERS]
                all_orders = _merge_unique_by_key(normalized_mcp, dummy_normalized, "order_id")
            else:
                all_orders = normalized_mcp
            
            # Calculate status counts
            status_counts = {"complete": 0, "rejected": 0, "open": 0, "cancelled": 0}
            for order in all_orders:
                status = (order.get("status") or "").upper()
                if "COMPLE" in status:
                    status_counts["complete"] += 1
                elif "REJECT" in status:
                    status_counts["rejected"] += 1
                elif "CANCEL" in status:
                    status_counts["cancelled"] += 1
                elif "OPEN" in status:
                    status_counts["open"] += 1
            
            # Create summary with ALL orders data (excluding source) + status breakdown
            summary = {
                "orders": [{k: v for k, v in o.items() if k != "source"} for o in all_orders],
                "status_breakdown": {
                    "total_orders": len(all_orders),
                    "complete": status_counts["complete"],
                    "rejected": status_counts["rejected"],
                    "open": status_counts["open"],
                    "cancelled": status_counts["cancelled"]
                }
            }
            
            return {
                "status": "success",
                "data": all_orders,
                "summary": summary
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to fetch orders: {str(e)}",
                "data": [],
                "summary": None
            }

    async def _get_trades(self) -> Dict[str, Any]:
        """
        Fetch all trades.
        
        Returns:
            {
                "status": "success" | "error",
                "data": [
                    {
                        "trade_id": str,
                        "order_id": str,
                        "symbol": str,
                        "exchange": str,
                        "transaction_type": str,
                        "product": str,
                        "quantity": int,
                        "price": float,
                        "trade_timestamp": str,
                        "source": "mcp" | "dummy"
                    }
                ],
                "summary": {
                    "total_trades": int,
                    "total_quantity": int
                }
            }
        """
        try:
            # Fetch MCP data
            res = await self.kite_client.call("get_trades", {})
            mcp_data = _extract_mcp_data(res)
            
            # Normalize MCP data
            normalized_mcp = [_normalize_trade(item, "mcp") for item in mcp_data if isinstance(item, dict)]
            
            # Merge with dummy data if enabled
            if self.use_dummy_trades:
                dummy_normalized = [_normalize_trade(item, "dummy") for item in DUMMY_TRADES]
                all_trades = _merge_unique_by_key(normalized_mcp, dummy_normalized, "trade_id")
            else:
                all_trades = normalized_mcp
            
            # Calculate summary
            total_quantity = sum(t["quantity"] for t in all_trades)
            
            # Create summary with ALL trades data (excluding source) + totals
            summary = {
                "trades": [{k: v for k, v in t.items() if k != "source"} for t in all_trades],
                "totals": {
                    "total_trades": len(all_trades),
                    "total_quantity": total_quantity
                }
            }
            
            return {
                "status": "success",
                "data": all_trades,
                "summary": summary
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to fetch trades: {str(e)}",
                "data": [],
                "summary": None
            }

    async def _get_order_history(self, order_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch order history/timeline.
        
        Args:
            order_id: Specific order ID to fetch history for (optional)
        
        Returns:
            {
                "status": "success" | "error",
                "data": {
                    "order_id": str,
                    "history": [
                        {
                            "timestamp": str,
                            "status": str,
                            "message": str
                        }
                    ]
                } | list of order histories if no order_id provided,
                "summary": {
                    "total_events": int
                }
            }
        """
        try:
            # If no order_id and dummy enabled, return all dummy histories
            if not order_id and self.use_dummy_order_history:
                all_histories = []
                for oid, events in DUMMY_ORDER_HISTORY.items():
                    normalized_events = [_normalize_history_event(e) for e in events]
                    all_histories.append({
                        "order_id": oid,
                        "history": normalized_events
                    })
                
                total_events = sum(len(h["history"]) for h in all_histories)
                # Create summary with ALL history data
                summary = {
                    "order_histories": all_histories,
                    "totals": {"total_events": total_events}
                }
                
                return {
                    "status": "success",
                    "data": all_histories,
                    "summary": summary
                }
            
            # IMPROVED: If no order_id provided, fetch all orders and show rejected/failed ones
            if not order_id:
                # Fallback: Get all orders and filter for rejected/failed ones
                orders_result = await self._get_orders()
                
                if orders_result.get("status") != "success":
                    return {
                        "status": "error",
                        "message": "Could not fetch orders to analyze failures. Please provide a specific order_id.",
                        "data": None,
                        "summary": None
                    }
                
                all_orders = orders_result.get("data", [])
                failed_orders = [
                    o for o in all_orders 
                    if "REJECT" in (o.get("status") or "").upper() or 
                       "CANCEL" in (o.get("status") or "").upper()
                ]
                
                if not failed_orders:
                    return {
                        "status": "success",
                        "message": "No rejected or cancelled orders found.",
                        "data": [],
                        "summary": {
                            "failed_orders": [],
                            "totals": {"total_failed": 0}
                        }
                    }
                
                # Create summary with failed orders and their reasons
                summary = {
                    "failed_orders": [
                        {
                            "order_id": o["order_id"],
                            "symbol": o["symbol"],
                            "status": o["status"],
                            "rejection_reason": o.get("rejection_reason", "No reason provided"),
                            "timestamp": o.get("order_timestamp", "")
                        }
                        for o in failed_orders
                    ],
                    "totals": {"total_failed": len(failed_orders)}
                }
                
                return {
                    "status": "success",
                    "data": failed_orders,
                    "summary": summary
                }
            
            # Fetch MCP data for specific order
            res = await self.kite_client.call("get_order_history", {"order_id": order_id})
            mcp_data = _extract_mcp_data(res)
            
            # Normalize MCP data
            normalized_mcp = [_normalize_history_event(item) for item in mcp_data if isinstance(item, dict)]
            
            # Merge with dummy data if enabled
            if self.use_dummy_order_history and order_id in DUMMY_ORDER_HISTORY:
                dummy_events = [_normalize_history_event(e) for e in DUMMY_ORDER_HISTORY[order_id]]
                # Merge and remove duplicates based on timestamp+status
                seen = {(e["timestamp"], e["status"]) for e in normalized_mcp}
                for e in dummy_events:
                    sig = (e["timestamp"], e["status"])
                    if sig not in seen:
                        normalized_mcp.append(e)
                        seen.add(sig)
                # Sort by timestamp
                normalized_mcp.sort(key=lambda x: x["timestamp"])
            
            # Create summary with complete history data
            summary = {
                "order_id": order_id,
                "history": normalized_mcp,
                "totals": {"total_events": len(normalized_mcp)}
            }
            
            return {
                "status": "success",
                "data": {
                    "order_id": order_id,
                    "history": normalized_mcp
                },
                "summary": summary
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to fetch order history: {str(e)}",
                "data": None,
                "summary": None
            }
