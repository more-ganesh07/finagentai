
import asyncio
import os
import json
from datetime import datetime
from dotenv import load_dotenv

# Import existing agents
from src.kite.mcpclient.kite_mcp_client import KiteMCPClient
from src.kite.portbot.tool.portfolio import PortfolioAgent
from src.kite.portbot.tool.login import LoginAgent
from src.kite.portbot.tool.account import AccountAgent   # NEW

from pathlib import Path

load_dotenv(override=True)

# File Paths Management
SCRIPT_DIR = Path(__file__).parent
# Project root is 4 levels up from src/kite/portrep/portreport/
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent.parent

# Take RAW_FILE and FINAL_FILE paths from .env with sensible defaults
# Default to data/reports in project root
DEFAULT_DATA_DIR = PROJECT_ROOT / "data" / "reports"
DEFAULT_DATA_DIR.mkdir(parents=True, exist_ok=True)

RAW_FILE = Path(os.getenv("PORTFOLIO_RAW_DATA_PATH", str(DEFAULT_DATA_DIR / "mcp_raw_data.json")))
FINAL_FILE = Path(os.getenv("PORTFOLIO_SUMMARY_JSON_PATH", str(DEFAULT_DATA_DIR / "mcp_summary.json")))

RAW_OUTPUT = {}


# ------------------ Helper Functions (Improved Robustness) ------------------
def _safe_float(val, default=0.0):
    """Safely convert value to float, handling None and non-numeric strings."""
    try:
        if val is None:
            return default
        return float(val)
    except (ValueError, TypeError):
        return default

def _safe_get(d, *keys, default=None):
    """Deep get for dictionaries to prevent NoneType errors in chains."""
    curr = d
    for key in keys:
        if isinstance(curr, dict):
            curr = curr.get(key)
        else:
            return default
    return curr if curr is not None else default


# ------------------ Save RAW Data (Overwrite Once) ------------------
def write_raw_file():
    """Write RAW_OUTPUT dict to file (overwrite mode)"""
    with open(RAW_FILE, "w") as f:
        json.dump(RAW_OUTPUT, f, indent=4)
    print(f"📁 Raw response stored (OVERWRITTEN) → {RAW_FILE}")


# ------------------ Filter Final Data ------------------
def filter_data():
    try:
        with open(RAW_FILE, "r") as f:
            raw_dict = json.load(f)

        # Validate presence of core API data
        required = ["holdings", "mutual_funds", "profile"]
        for key in required:
            if key not in raw_dict:
                # Instead of raising error, we initialize as empty to prevent crash
                print(f"⚠️ Warning: Missing required data '{key}'. Initializing as empty.")
                raw_dict[key] = {}

        final = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "profile": {
                "user_id": _safe_get(raw_dict, "profile", "data", "user_id", default="N/A"),
                "name": _safe_get(raw_dict, "profile", "data", "user_name", default="N/A"),
                "email": _safe_get(raw_dict, "profile", "data", "email", default="N/A"),
                "broker": _safe_get(raw_dict, "profile", "data", "broker", default="N/A"),
                "products": _safe_get(raw_dict, "profile", "data", "products", default=[]),
                "exchanges": _safe_get(raw_dict, "profile", "data", "exchanges", default=[]),
            },
            "holdings": [],
            "mutual_funds": []
        }

        # ---------------- HOLDINGS CLEANING ----------------
        holdings_data = _safe_get(raw_dict, "holdings", "data", default=[])
        if not isinstance(holdings_data, list):
            holdings_data = []
            
        for h in holdings_data:
            if not isinstance(h, dict): continue
            final["holdings"].append({
                "symbol": h.get("symbol") or h.get("tradingsymbol") or "UNKNOWN",
                "qty": _safe_float(h.get("quantity") or h.get("qty")),
                "avg": round(_safe_float(h.get("average_price") or h.get("avg")), 2),
                "ltp": round(_safe_float(h.get("last_price") or h.get("ltp")), 2),
                "pnl": round(_safe_float(h.get("pnl")), 2),
            })

        # ---------------- MUTUAL FUNDS CLEANING ----------------
        mf_data = _safe_get(raw_dict, "mutual_funds", "data", default=[])
        if not isinstance(mf_data, list):
            mf_data = []
            
        for m in mf_data:
            if not isinstance(m, dict): continue
            final["mutual_funds"].append({
                "scheme_name": m.get("scheme_name", "MF_Symbol"),
                "units": round(_safe_float(m.get("units")), 3),
                "avg_nav": round(_safe_float(m.get("average_nav") or m.get("avg_nav")), 4),
                "nav": round(_safe_float(m.get("current_nav") or m.get("nav")), 4),
                "value": round(_safe_float(m.get("current_value") or m.get("value")), 2),
                "gain_pct": round(_safe_float(m.get("pnl_percentage") or m.get("gain_pct")), 2),
            })

        # ---------------- WRITE FINAL FILE ----------------
        with open(FINAL_FILE, "w") as f:
            json.dump(final, f, indent=4)

        print(f"🎯 Final filtered summary stored → {FINAL_FILE}")

    except Exception as e:
        print(f"❌ Error in filter_data: {e}")
        import traceback
        traceback.print_exc()
        raise

# ------------------ Test Functions ------------------
async def setup_agents():
    from src.kite.portbot.agent.master_agent import MasterAgent
    
    # Initialize MasterAgent (which now handles non-interactive login)
    master = MasterAgent(user_id="default_user")
    await master.__aenter__()
    
    # Check if we are logged in
    session = master.shared_state.get("session")
    if not session:
        print("⚠️ No active session found. Please login via the Portfolio Chatbot Connect button first.")
        await master.__aexit__(None, None, None)
        return None, None

    print("✅ Session detected via MasterAgent")
    return master.agents["portfolio"], master.agents["account"]


async def test_and_save(label, func):
    """Store result in RAW_OUTPUT dict (AND NOT APPEND TO FILE)"""
    result = await func
    RAW_OUTPUT[label] = result


# ------------------ Main ------------------
async def main(master_agent=None):
    if master_agent:
        portfolio_agent = master_agent.agents.get("portfolio")
        account_agent = master_agent.agents.get("account")
    else:
        portfolio_agent, account_agent = await setup_agents()
        
    if portfolio_agent is None:
        raise RuntimeError("No active Zerodha session. Please login via the Portfolio Chatbot Connect button.")

    # API calls — store in RAW_OUTPUT {}
    holdings_res = await portfolio_agent._get_holdings()
    if holdings_res.get("status") != "success":
        print(f"❌ Failed to fetch holdings: {holdings_res.get('message')}")
    RAW_OUTPUT["holdings"] = holdings_res
    
    mf_res = await portfolio_agent._get_mf_holdings()
    if mf_res.get("status") != "success":
        print(f"❌ Failed to fetch mutual funds: {mf_res.get('message')}")
    RAW_OUTPUT["mutual_funds"] = mf_res

    profile_res = await account_agent.run("get_profile")
    if profile_res.get("status") != "success":
        print(f"❌ Failed to fetch profile: {profile_res.get('message')}")
    RAW_OUTPUT["profile"] = profile_res

    write_raw_file()    # Write once — overwrite file
    filter_data()       # Create final summary


if __name__ == "__main__":
    asyncio.run(main())
