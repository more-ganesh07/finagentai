# src/kite/portbot/tool/market_data.py
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from typing import Any, Dict, Optional, List, Tuple
import datetime as dt

from src.kite.portbot.base import Agent
from src.kite.client.kite_mcp_client import KiteMCPClient

# NEW: shared JSON unwrappers
from src.kite.portbot.utils.unwrapper import unwrap_json, unwrap_list

class MarketDataAgent(Agent):
    """
    MarketDataAgent — compact, chatbot-friendly market data tools.
    """

    name = "market_data"
    description = "Real-time and historical market data utilities (compact + token auto-resolution)."

    tools = [
        {
            "name": "search_instruments",
            "description": "Search trading instruments and show the first few best matches.",
            "parameters": {
                "query": "str e.g. 'INFY'",
                "limit": "int (optional)"
            },
        },
        {
            "name": "get_quotes",
            "description": "Real-time quotes for one or more instruments.",
            "parameters": {
                "instruments": "List[str] e.g. ['NSE:INFY','NSE:RELIANCE']"
            },
        },
        {
            "name": "get_historical_data",
            "description": "Historical OHLC for a symbol or token.",
            "parameters": {
                "instrument": "str e.g. 'NSE:INFY'",
                "instrument_token": "int (optional)",
                "from_": "YYYY-MM-DD",
                "to": "YYYY-MM-DD",
                "interval": "str e.g. 'day'",
                "limit": "int number of rows"
            },
        },
    ]

    def __init__(self, kite_client: KiteMCPClient, shared_state=None):
        super().__init__(shared_state)
        self.kite_client = kite_client

    # ---------------------------------------------------------------
    # MAIN DISPATCH
    # ---------------------------------------------------------------
    async def run(self, tool_name: str, **kwargs: Any) -> Dict[str, Any]:
        try:
            if tool_name == "search_instruments":
                return await self._search_instruments(**kwargs)
            elif tool_name == "get_quotes":
                return await self._get_quotes(**kwargs)
            elif tool_name == "get_historical_data":
                return await self._get_historical_data(**kwargs)
            raise ValueError(f"Unknown tool: {tool_name}")
        except Exception as e:
            return {"status": "error", "message": str(e), "data": []}

    # ---------------------------------------------------------------
    # SEARCH INSTRUMENTS
    # ---------------------------------------------------------------
    async def _search_instruments(self, query: Optional[str] = None, limit: int = 10):
        query = (query or "INFY").strip()

        res = await self.kite_client.call("search_instruments", {"query": query})
        items = unwrap_list(res)

        if not items:
            return {"status": "error", "message": "No instruments found.", "data": []}

        rows = []
        for row in items[: max(1, limit)]:
            rows.append({
                "exchange": row.get("exchange"),
                "symbol": row.get("tradingsymbol") or row.get("name"),
                "type": row.get("instrument_type"),
                "token": row.get("instrument_token"),
            })

        header = f"🔎 Instruments for '{query}' — {len(items)} match(es). Showing first {min(limit, len(items))}."

        if rows:
            table = ["Exchange Symbol             Type  Token"]
            for r in rows:
                exch = (r["exchange"] or "")[:4].ljust(4)
                sym  = (r["symbol"] or "")[:19].ljust(19)
                typ  = (r["type"] or "")[:3].ljust(3)
                tok  = str(r["token"] or "")
                table.append(f"{exch}  {sym}  {typ}  {tok}")
            message = header + "\n" + "\n".join(table)
        else:
            message = header + "\n(no matches)"

        return {"status": "success", "message": message, "data": rows}

    # ---------------------------------------------------------------
    # GET QUOTES
    # ---------------------------------------------------------------
    async def _get_quotes(self, instruments: Optional[List[str]] = None):
        instruments = instruments or ["NSE:INFY", "NSE:RELIANCE"]

        res = await self.kite_client.call("get_quotes", {"instruments": instruments})
        obj = unwrap_json(res)

        if not obj:
            return {"status": "error", "message": "No quotes available.", "data": []}

        compact = []
        lines = []

        if isinstance(obj, dict):
            for key, q in obj.items():
                if not isinstance(q, dict):
                    continue

                ohlc = q.get("ohlc") or {}
                row = {
                    "instrument": key,
                    "last_price": q.get("last_price"),
                    "open":  ohlc.get("open"),
                    "high":  ohlc.get("high"),
                    "low":   ohlc.get("low"),
                    "close": ohlc.get("close"),
                    "last_trade_time": self._short_ts(q.get("last_trade_time")),
                }
                compact.append(row)

                # Pretty one-liner
                sym = key.split(":")[-1]
                lp  = self._fmt(row["last_price"])
                o   = self._fmt(row["open"]); h = self._fmt(row["high"])
                l   = self._fmt(row["low"]);  c = self._fmt(row["close"])
                ts  = row["last_trade_time"] or "-"
                lines.append(f"{sym} {lp} (O {o} H {h} L {l} C {c}) @ {ts}")

        msg = "⚡ Quotes"
        msg += "\n" + ("\n".join(lines) if lines else "(no data)")

        return {"status": "success", "message": msg, "data": compact}

    # ---------------------------------------------------------------
    # GET HISTORICAL DATA
    # ---------------------------------------------------------------
    async def _get_historical_data(
        self,
        instrument: Optional[str] = None,
        instrument_token: Optional[int] = None,
        from_: Optional[str] = None,
        to: Optional[str] = None,
        interval: Optional[str] = None,
        limit: int = 10,
        **_
    ):
        instrument = instrument or "NSE:INFY"
        interval = interval or "day"

        today = dt.date.today()
        def _ds(d: dt.date) -> str: return d.strftime("%Y-%m-%d")
        from_ = from_ or _ds(today - dt.timedelta(days=20))
        to    = to    or _ds(today)

        # Resolve token if not provided
        token = instrument_token
        if token is None:
            symbol = instrument.split(":")[-1]
            sr = await self.kite_client.call("search_instruments", {"query": symbol})
            items = unwrap_list(sr)
            token = self._pick_token(items, symbol=symbol)

        if token is None:
            return {"status": "error", "message": f"Could not resolve instrument_token for {instrument}", "data": []}

        payload = {
            "instrument_token": token,
            "from_date": f"{from_} 00:00:00",
            "to_date":   f"{to} 23:59:59",
            "interval": interval,
        }

        res = await self.kite_client.call("get_historical_data", payload)
        bars = unwrap_list(res)

        # Only latest "limit" bars
        if isinstance(bars, list) and len(bars) > limit:
            bars = bars[-limit:]

        compact = []
        for b in bars or []:
            if isinstance(b, dict):
                compact.append({
                    "time": self._short_ts(b.get("date") or b.get("time") or b.get("timestamp")),
                    "open": b.get("open"),
                    "high": b.get("high"),
                    "low":  b.get("low"),
                    "close": b.get("close"),
                    "volume": b.get("volume"),
                    "oi": b.get("oi"),
                })

        # Display lines
        lines = []
        for r in compact:
            o = self._fmt(r["open"]); h = self._fmt(r["high"])
            l = self._fmt(r["low"]);  c = self._fmt(r["close"])
            t = r["time"] or "-"
            lines.append(f"{t}  O {o}  H {h}  L {l}  C {c}")

        msg = f"📈 {instrument} — {interval}, {from_} → {to} • {len(compact)} bar(s)"
        msg += "\n" + ("\n".join(lines) if lines else "(no candles)")

        return {"status": "success", "message": msg, "data": compact}

    # ---------------------------------------------------------------
    # UTILITIES
    # ---------------------------------------------------------------
    @staticmethod
    def _fmt(x):
        try:
            return f"{float(x):.2f}"
        except Exception:
            return "-"

    @staticmethod
    def _short_ts(ts):
        if not ts or not isinstance(ts, str):
            return ts
        ts = ts.replace("T", " ")
        ts = ts.split("+")[0]
        return ts[:16] if len(ts) >= 16 else ts
