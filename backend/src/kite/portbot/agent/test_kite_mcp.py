# run_agent_tests.py
# --------------------------------------------------------------------
# One-time login + multi-agent test runner for your Kite MCP setup.
# - Reuses session.json (no repeated logins)
# - Calls each agent/tool in a predictable order
# - Supplies inputs for Market Data tools
# - Prints raw outputs (so you can inspect payload shapes)
# --------------------------------------------------------------------

import asyncio
import json
from typing import Any, Dict, List, Optional

from master_agent import MasterAgent


def header(title: str):
    bar = "=" * len(title)
    print(f"\n{bar}\n{title}\n{bar}")


def pretty(obj: Any) -> str:
    try:
        if isinstance(obj, (dict, list)):
            return json.dumps(obj, indent=2, ensure_ascii=False)
        return str(obj)
    except Exception:
        return str(obj)


def _trim(obj: Any, limit: int = 10) -> Any:
    # For lists: keep first N and show a note
    if isinstance(obj, list) and len(obj) > limit:
        return {
            "_preview_note": f"showing first {limit} of {len(obj)} items",
            "items": obj[:limit]
        }
    return obj

def unwrap_result(result: Dict[str, Any]) -> str:
    """
    Prefer short 'message'. If 'data' is present, trim long lists for readability.
    """
    if not isinstance(result, dict):
        return pretty(result)

    if "message" in result and result["message"]:
        return str(result["message"])

    if "data" in result:
        return pretty(_trim(result["data"]))

    # fallback
    return pretty(result)



async def test_login(master: MasterAgent):
    header("STEP 0: LOGIN (one-time)")
    res = await master.execute("login", "login")
    print(unwrap_result(res))


async def test_account(master: MasterAgent):
    header("STEP 1: ACCOUNT")
    res1 = await master.execute("account", "get_profile")
    print("get_profile =>")
    print(unwrap_result(res1))

    res2 = await master.execute("account", "get_margins")
    print("\nget_margins =>")
    print(unwrap_result(res2))


async def test_portfolio(master: MasterAgent):
    header("STEP 2: PORTFOLIO")
    res1 = await master.execute("portfolio", "get_holdings")
    print("get_holdings =>")
    print(unwrap_result(res1))

    res2 = await master.execute("portfolio", "get_positions")
    print("\nget_positions =>")
    print(unwrap_result(res2))

    res3 = await master.execute("portfolio", "get_mf_holdings")
    print("\nget_mf_holdings =>")
    print(unwrap_result(res3))


async def test_market_data(master: MasterAgent):
    header("STEP 3: MARKET DATA (inputs provided)")

    # You can tweak the defaults below to match your watchlist
    instruments_multi = ["NSE:INFY", "NSE:RELIANCE"]
    instruments_single = ["NSE:INFY"]
    instrument_single = "NSE:INFY"
    from_date = "2025-09-15"
    to_date = "2025-10-21"
    interval = "day"

    res0 = await master.execute("market_data", "search_instruments", query="INFY")
    print("search_instruments('INFY') =>")
    print(unwrap_result(res0))

    res1 = await master.execute("market_data", "get_quotes", instruments=instruments_multi)
    print("\nget_quotes(['NSE:INFY','NSE:RELIANCE']) =>")
    print(unwrap_result(res1))

    res2 = await master.execute("market_data", "get_ltp", instruments=instruments_single)
    print("\nget_ltp(['NSE:INFY']) =>")
    print(unwrap_result(res2))

    res3 = await master.execute("market_data", "get_ohlc", instruments=instruments_single)
    print("\nget_ohlc(['NSE:INFY']) =>")
    print(unwrap_result(res3))

    res4 = await master.execute(
        "market_data",
        "get_historical_data",
        instrument=instrument_single,
        from_=from_date,
        to=to_date,
        interval=interval,
    )
    print(f"\nget_historical_data({instrument_single}, {interval}, {from_date}→{to_date}) =>")
    print(unwrap_result(res4))


def _maybe_first_order_id(orders_payload: Any) -> Optional[str]:
    """
    Best-effort probe to find an order_id in the orders payload.
    (Purely for testing convenience; does not alter agent logic.)
    """
    try:
        if isinstance(orders_payload, list):
            for row in orders_payload:
                if isinstance(row, dict) and "order_id" in row and row["order_id"]:
                    return str(row["order_id"])
        elif isinstance(orders_payload, dict):
            # common patterns: {'data': [...]} or {'orders': [...]}
            for key in ("data", "orders"):
                if key in orders_payload and isinstance(orders_payload[key], list):
                    for row in orders_payload[key]:
                        if isinstance(row, dict) and "order_id" in row and row["order_id"]:
                            return str(row["order_id"])
    except Exception:
        pass
    return None


async def test_orders(master: MasterAgent):
    header("STEP 4: ORDERS (read-only)")

    res_orders = await master.execute("orders", "get_orders")
    print("get_orders =>")
    print(unwrap_result(res_orders))

    res_trades = await master.execute("orders", "get_trades")
    print("\nget_trades =>")
    print(unwrap_result(res_trades))

    # Try get_order_history using a discovered order_id (if present)
    print("\nget_order_history (best-effort pick first order_id) =>")
    order_id = None
    payload = res_orders.get("data") if isinstance(res_orders, dict) else None
    order_id = _maybe_first_order_id(payload)
    if order_id:
        res_hist = await master.execute("orders", "get_order_history", order_id=order_id)
        print(unwrap_result(res_hist))
    else:
        print("No order_id found in get_orders payload — skipping history test.")


async def main():
    async with MasterAgent() as master:
        await test_login(master)
        await test_account(master)
        await test_portfolio(master)
        await test_market_data(master)
        await test_orders(master)

    print("\n✅ Finished test run (session reused; you can re-run without logging in again).")


if __name__ == "__main__":
    asyncio.run(main())
