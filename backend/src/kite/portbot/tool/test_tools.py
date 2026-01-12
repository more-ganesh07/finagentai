import asyncio
import json
from src.kite.mcpclient.kite_mcp_client import KiteMCPClient
from src.kite.portbot.tool.login import LoginAgent
from src.kite.portbot.tool.orders import OrdersAgent
from src.kite.portbot.tool.portfolio import PortfolioAgent
from src.kite.portbot.tool.account import AccountAgent
from dotenv import load_dotenv

load_dotenv(override=True)


async def main():
    """Run all agent tests and output results as JSON"""
    
    # Initialize
    kite_client = KiteMCPClient()
    shared_state = {}
    
    print("Logging in...")
    login_agent = LoginAgent(kite_client, shared_state=shared_state)
    login_result = await login_agent.run(tool_name="login")
    
    if login_result.get("status") != "success":
        print(json.dumps({"error": "Login failed"}, indent=2))
        return
    
    print("Login successful!\n")
    
    # Initialize all agents
    orders_agent = OrdersAgent(kite_client, shared_state=shared_state)
    portfolio_agent = PortfolioAgent(kite_client, shared_state=shared_state)
    account_agent = AccountAgent(kite_client, shared_state=shared_state)
    
    # Collect all results (SUMMARY ONLY for LLM)
    results = {}
    
    # ===== ORDERS AGENT =====
    print("Fetching orders data...")
    orders_data = {
        "get_orders": await orders_agent.run("get_orders"),
        "get_trades": await orders_agent.run("get_trades"),
        "get_order_history": await orders_agent.run("get_order_history")
    }
    
    # Extract only summary
    results["orders"] = {
        "get_orders": {
            "status": orders_data["get_orders"]["status"],
            "summary": orders_data["get_orders"]["summary"]
        },
        "get_trades": {
            "status": orders_data["get_trades"]["status"],
            "summary": orders_data["get_trades"]["summary"]
        },
        "get_order_history": {
            "status": orders_data["get_order_history"]["status"],
            "summary": orders_data["get_order_history"]["summary"]
        }
    }
    
    # ===== PORTFOLIO AGENT =====
    print("Fetching portfolio data...")
    portfolio_data = {
        "get_holdings": await portfolio_agent.run("get_holdings"),
        "get_positions": await portfolio_agent.run("get_positions"),
        "get_mf_holdings": await portfolio_agent.run("get_mf_holdings")
    }
    
    # Extract only summary
    results["portfolio"] = {
        "get_holdings": {
            "status": portfolio_data["get_holdings"]["status"],
            "summary": portfolio_data["get_holdings"]["summary"]
        },
        "get_positions": {
            "status": portfolio_data["get_positions"]["status"],
            "summary": portfolio_data["get_positions"]["summary"]
        },
        "get_mf_holdings": {
            "status": portfolio_data["get_mf_holdings"]["status"],
            "summary": portfolio_data["get_mf_holdings"]["summary"]
        }
    }
    
    # ===== ACCOUNT AGENT =====
    print("Fetching account data...")
    account_data = {
        "get_profile": await account_agent.run("get_profile"),
        "get_margins": await account_agent.run("get_margins")
    }
    
    # Extract only summary
    results["account"] = {
        "get_profile": {
            "status": account_data["get_profile"]["status"],
            "summary": account_data["get_profile"]["summary"]
        },
        "get_margins": {
            "status": account_data["get_margins"]["status"],
            "summary": account_data["get_margins"]["summary"]
        }
    }
    
    # Output as JSON (SUMMARY ONLY)
    print("\n" + "="*60)
    print("ALL AGENT RESULTS - SUMMARY ONLY (FOR LLM)")
    print("="*60 + "\n")
    print(json.dumps(results, indent=2))
    
    # Also save to file
    with open("all_agent_results_summary.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    
    print("\n" + "="*60)
    print("✅ Summary results saved to: all_agent_results_summary.json")
    print("="*60)


if __name__ == "__main__":
    asyncio.run(main())
