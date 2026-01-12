import yfinance as yf
import logging
import asyncio
import json
from typing import Dict, Any
from datetime import datetime
import random
import pytz

logger = logging.getLogger("MarketIndices")

def is_market_open() -> bool:
    """
    Check if Indian stock market is currently open
    NSE/BSE trading hours: Monday-Friday, 9:15 AM - 3:30 PM IST
    """
    ist = pytz.timezone('Asia/Kolkata')
    now = datetime.now(ist)
    
    # Check if weekend
    if now.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    
    # Check trading hours (9:15 AM to 3:30 PM)
    market_open = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    
    return market_open <= now <= market_close

# Cache to store the last fetched data
_cache = {
    "data": None,
    "last_fetch": None,
    "fetch_interval": 5  # Fetch from API every 5 seconds
}


def get_market_indices_snapshot() -> Dict[str, Any]:
    """
    Fetch market data from yfinance API
    This is called every 5 seconds to avoid rate limiting
    """
    market_is_open = is_market_open()
    
    indices = {
        "SENSEX": "^BSESN",
        "NIFTY": "^NSEI",
        "FINNIFTY": "^CNXFIN"
    }
    
    result = {
        "status": "success",
        "data": {},
        "timestamp": datetime.now().isoformat(),
        "market_open": market_is_open,
        "message": "Live trading" if market_is_open else "Market Closed - Showing last traded prices"
    }
    
    try:
        for index_name, symbol in indices.items():
            try:
                ticker = yf.Ticker(symbol)
                hist = ticker.history(period="1d", interval="1m")
                
                if hist.empty:
                    result["data"][index_name] = {
                        "open": None,
                        "current": None,
                        "high": None,
                        "low": None,
                        "change": None,
                        "change_percent": None,
                        "color": "gray",
                        "status": "unavailable"
                    }
                    continue
                
                open_price = float(hist['Open'].iloc[0])
                current_price = float(hist['Close'].iloc[-1])
                high_price = float(hist['High'].max())
                low_price = float(hist['Low'].min())
                
                change = current_price - open_price
                change_percent = (change / open_price) * 100
                color = "green" if current_price > open_price else "red" if current_price < open_price else "gray"
                
                result["data"][index_name] = {
                    "open": round(open_price, 2),
                    "current": round(current_price, 2),
                    "high": round(high_price, 2),
                    "low": round(low_price, 2),
                    "change": round(change, 2),
                    "change_percent": round(change_percent, 2),
                    "color": color,
                    "status": "active",
                    "base_price": current_price  # Store for interpolation
                }
                
            except Exception as e:
                logger.error(f"Error fetching {index_name}: {e}")
                result["data"][index_name] = {
                    "open": None,
                    "current": None,
                    "high": None,
                    "low": None,
                    "change": None,
                    "change_percent": None,
                    "color": "gray",
                    "status": "error"
                }
        
        return result
        
    except Exception as e:
        logger.error(f"Critical error: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e),
            "data": {},
            "timestamp": datetime.now().isoformat()
        }


def simulate_live_tick(base_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulate micro-movements between API calls for smoother UX
    Only simulates if market is OPEN
    """
    result = {
        "status": "success",
        "data": {},
        "timestamp": datetime.now().isoformat(),
        "simulated": True,
        "market_open": base_data.get("market_open", False),
        "message": base_data.get("message", "")
    }
    
    # Don't simulate if market is closed
    if not base_data.get("market_open", False):
        return base_data
    
    for index_name, index_data in base_data["data"].items():
        if index_data.get("status") != "active":
            result["data"][index_name] = index_data
            continue
        
        base_price = index_data.get("base_price", index_data["current"])
        
        # Simulate tiny random movement (±0.05%)
        variation = random.uniform(-0.0005, 0.0005)
        simulated_price = base_price * (1 + variation)
        
        open_price = index_data["open"]
        change = simulated_price - open_price
        change_percent = (change / open_price) * 100
        color = "green" if simulated_price > open_price else "red" if simulated_price < open_price else "gray"
        
        result["data"][index_name] = {
            "open": index_data["open"],
            "current": round(simulated_price, 2),
            "high": index_data["high"],
            "low": index_data["low"],
            "change": round(change, 2),
            "change_percent": round(change_percent, 2),
            "color": color,
            "status": "active",
            "base_price": base_price
        }
    
    return result


async def stream_market_indices_realtime():
    """
    Stream market indices with second-by-second updates
    - Fetches real data from API every 5 seconds
    - Simulates micro-movements every second for live feel
    - Yields updates continuously
    """
    global _cache
    tick_count = 0
    
    while True:
        try:
            # Fetch fresh data from API every 5 seconds
            if tick_count % 5 == 0:
                logger.info("🔄 Fetching fresh market data from API...")
                _cache["data"] = get_market_indices_snapshot()
                _cache["last_fetch"] = datetime.now()
                yield json.dumps(_cache["data"])
            else:
                # Simulate live ticks between API calls
                if _cache["data"] and _cache["data"]["status"] == "success":
                    simulated_data = simulate_live_tick(_cache["data"])
                    yield json.dumps(simulated_data)
                else:
                    # If no cached data, fetch immediately
                    _cache["data"] = get_market_indices_snapshot()
                    yield json.dumps(_cache["data"])
            
            tick_count += 1
            await asyncio.sleep(1)  # Update every second
            
        except asyncio.CancelledError:
            logger.info("Market indices stream cancelled")
            break
        except Exception as e:
            logger.error(f"Stream error: {e}")
            error_data = {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            yield json.dumps(error_data)
            await asyncio.sleep(1)


def get_market_indices() -> Dict[str, Any]:
    """
    One-time fetch for initial load or manual refresh
    """
    return get_market_indices_snapshot()