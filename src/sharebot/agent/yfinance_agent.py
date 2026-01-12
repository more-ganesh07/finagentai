import json
import sys
from pathlib import Path
import logging
import pickle
import re
import yfinance as yf  # ✅ added for symbol validation

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('stock_analysis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Add the parent directory to the path to import the tool
sys.path.insert(0, str(Path(__file__).parent.parent))

from tool.yfinance_tool import (
    get_stock_symbol,
    fetch_stock_data,
    generate_recommendation
)

from tool.para_info_tool import build_parameter_table

# ============================================================================
# CACHING LAYER - Reduces API calls and LLM usage
# ============================================================================

CACHE_DIR = Path(".cache")
CACHE_DIR.mkdir(exist_ok=True)
SYMBOL_CACHE_FILE = CACHE_DIR / "symbol_cache.pkl"

# Load symbol cache from disk (robust to corruption)
if SYMBOL_CACHE_FILE.exists():
    try:
        with open(SYMBOL_CACHE_FILE, 'rb') as f:
            SYMBOL_CACHE = pickle.load(f)
        if not isinstance(SYMBOL_CACHE, dict):
            SYMBOL_CACHE = {}
        logger.info(f"Loaded {len(SYMBOL_CACHE)} cached symbols")
    except Exception as e:
        logger.warning(f"Symbol cache load failed (starting fresh): {e}")
        SYMBOL_CACHE = {}
else:
    SYMBOL_CACHE = {}


def save_symbol_cache():
    """Save symbol cache to disk (atomic write to prevent corruption)"""
    tmp_file = SYMBOL_CACHE_FILE.with_suffix(".pkl.tmp")
    try:
        with open(tmp_file, 'wb') as f:
            pickle.dump(SYMBOL_CACHE, f, protocol=pickle.HIGHEST_PROTOCOL)
        tmp_file.replace(SYMBOL_CACHE_FILE)
    except Exception as e:
        logger.error(f"Failed to save symbol cache: {e}")
        try:
            if tmp_file.exists():
                tmp_file.unlink()
        except Exception:
            pass


def is_valid_symbol(symbol: str) -> bool:
    """
    Validate symbol by checking if yfinance returns any recent price data.
    Keeps it lightweight: 5d history.
    """
    if not symbol:
        return False
    try:
        hist = yf.Ticker(symbol).history(period="5d")
        return hist is not None and not hist.empty
    except Exception:
        return False


def sanitize_symbol(symbol: str) -> str:
    """Defensively sanitize symbols coming from cache/LLM."""
    symbol = (symbol or "").strip().upper()
    symbol = symbol.replace("`", "").replace('"', "").replace("'", "").strip()
    symbol = symbol.splitlines()[0].strip() if symbol else symbol
    if symbol and not symbol.endswith(".NS"):
        symbol += ".NS"
    return symbol


def looks_like_ticker(text: str) -> bool:
    """
    If user types 'bhel', 'itc', 'icici', treat as ticker candidate.
    - no spaces
    - only alnum & . & & & - & _
    - reasonable length
    """
    if not text:
        return False
    t = text.strip()
    if " " in t:
        return False
    return re.fullmatch(r"[A-Za-z0-9&._-]{1,15}", t) is not None


def get_cached_symbol(company_name: str) -> str:
    """Get symbol with caching to avoid LLM calls + auto-evict invalid cached symbols"""
    cache_key = company_name.lower().strip()

    # 1) Cache hit → validate; if invalid, evict
    if cache_key in SYMBOL_CACHE:
        cached = sanitize_symbol(SYMBOL_CACHE[cache_key])
        if is_valid_symbol(cached):
            logger.info(f"Cache hit for '{company_name}' -> {cached}")
            return cached
        else:
            logger.warning(f"Cached symbol invalid for '{company_name}' -> {cached}. Evicting cache entry.")
            try:
                del SYMBOL_CACHE[cache_key]
                save_symbol_cache()
            except Exception:
                pass

    # 2) If user typed a ticker-like input, try direct symbol guess first
    if looks_like_ticker(company_name):
        guessed = sanitize_symbol(company_name)
        if is_valid_symbol(guessed):
            logger.info(f"Using direct ticker guess for '{company_name}' -> {guessed}")
            SYMBOL_CACHE[cache_key] = guessed
            save_symbol_cache()
            return guessed

    # 3) Cache miss → call LLM
    logger.info(f"Cache miss for '{company_name}' - calling LLM")
    symbol = sanitize_symbol(get_stock_symbol(company_name))

    # Validate LLM result; if invalid and input looked like ticker, fallback to guess
    if not is_valid_symbol(symbol) and looks_like_ticker(company_name):
        fallback = sanitize_symbol(company_name)
        if is_valid_symbol(fallback):
            logger.warning(f"LLM symbol invalid ({symbol}). Falling back to ticker guess: {fallback}")
            symbol = fallback

    # Store in cache (store normalized)
    SYMBOL_CACHE[cache_key] = symbol
    save_symbol_cache()
    return symbol


def analyze_stock(company_name: str) -> dict:
    if not company_name or not company_name.strip():
        return {
            "status": "error",
            "error": "Company name cannot be empty",
            "stock_data": None,
            "stock_data_ui": None,
            "recommendation": None
        }

    company_name = company_name.strip()

    try:
        # Step 1: Get stock symbol (cached + validated)
        try:
            symbol = get_cached_symbol(company_name)
        except Exception as e:
            logger.error(f"Symbol lookup failed: {e}")
            return {
                "status": "error",
                "error": f"Failed to get stock symbol: {str(e)}",
                "stock_data": None,
                "stock_data_ui": None,
                "recommendation": None
            }

        # Step 2: Fetch stock data
        try:
            stock_data = fetch_stock_data(symbol)

            if not stock_data.get('Current Price') or stock_data.get('Current Price') == 'N/A':
                return {
                    "status": "error",
                    "error": "Unable to fetch stock data. Check company name or symbol.",
                    "stock_data": None,
                    "stock_data_ui": None,
                    "recommendation": None
                }

        except Exception as e:
            logger.error(f"Data fetch failed for {symbol}: {e}")
            return {
                "status": "error",
                "error": f"Failed to fetch stock data: {str(e)}",
                "stock_data": None,
                "stock_data_ui": None,
                "recommendation": None
            }

        # Step 2.5: Build UI rows (3 columns)
        try:
            ui_rows = build_parameter_table(stock_data)
        except Exception as e:
            logger.error(f"UI table build failed: {e}")
            ui_rows = None

        # Step 3: Generate recommendation
        try:
            recommendation = generate_recommendation(stock_data)
        except Exception as e:
            logger.error(f"Recommendation generation failed: {e}")
            return {
                "status": "error",
                "error": f"Failed to generate recommendation: {str(e)}",
                "stock_data": stock_data,
                "stock_data_ui": ui_rows,
                "recommendation": None
            }

        return {
            "status": "success",
            "symbol": symbol,
            "stock_data": stock_data,
            "stock_data_ui": ui_rows,
            "recommendation": recommendation
        }

    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return {
            "status": "error",
            "error": f"Unexpected error: {str(e)}",
            "stock_data": None,
            "stock_data_ui": None,
            "recommendation": None
        }


def main():
    print("=" * 80)
    print("Indian Stock Market Analysis Agent (YFinance)")
    print("=" * 80)
    print("Enter Indian company name to get comprehensive stock analysis.")
    print("Type 'exit' or 'quit' to end the program.\n")

    while True:
        try:
            company_name = input("\n💼 Enter company name: ").strip()

            if not company_name:
                continue

            if company_name.lower() in ['exit', 'quit', 'bye']:
                print("\n👋 Thank you for using the Stock Analysis Agent. Happy investing!")
                break

            print(f"\n🔍 Analyzing '{company_name}'...\n")
            result = analyze_stock(company_name)

            if result["status"] == "success":
                print("=" * 60)
                print("UI TABLE (Parameter | Value | Meaning)")
                print("=" * 60)
                print(json.dumps(result["stock_data_ui"], indent=2, ensure_ascii=False))

                print("\n" + "=" * 60)
                print("RECOMMENDATION")
                print("=" * 60)
                print(json.dumps(result["recommendation"], indent=2, ensure_ascii=False))

                print("\n" + "=" * 60)
                print(f"✅ Analysis completed successfully for {result['symbol']}")
                print("=" * 60)
            else:
                print("=" * 60)
                print(f"❌ Error: {result['error']}")
                print("=" * 60)
                print("\n💡 Please try again with a different company name.")

        except KeyboardInterrupt:
            print("\n\n👋 Program interrupted. Goodbye!")
            break
        except Exception as e:
            logger.error(f"Main loop error: {e}", exc_info=True)
            print(f"\n⚠️ Unexpected error: {str(e)}")
            print("💡 Please try again with a different company name.")


if __name__ == "__main__":
    main()
 