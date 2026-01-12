import yfinance as yf
import json
import os
import pandas as pd
import numpy as np
from groq import Groq
from src.utils.llm_balancer import balancer
from dotenv import load_dotenv
import pickle
from pathlib import Path
from datetime import datetime, timedelta
import logging
import re

load_dotenv(override=True)

logger = logging.getLogger(__name__)

# ============================================================================
# CACHING SETUP
# ============================================================================
CACHE_DIR = Path(".cache/stock_data")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DURATION = timedelta(minutes=15)  # Cache stock data for 15 minutes


def get_cached_data(symbol):
    """Get cached stock data if available and fresh"""
    cache_file = CACHE_DIR / f"{symbol.replace('.', '_')}.pkl"
    if cache_file.exists():
        try:
            with open(cache_file, "rb") as f:
                cached = pickle.load(f)
                if datetime.now() - cached["timestamp"] < CACHE_DURATION:
                    return cached["data"]
        except Exception as e:
            logger.debug(f"Cache read error for {symbol}: {e}")
    return None


def save_cached_data(symbol, data):
    """Save stock data to cache"""
    cache_file = CACHE_DIR / f"{symbol.replace('.', '_')}.pkl"
    tmp_file = cache_file.with_suffix(".pkl.tmp")
    try:
        with open(tmp_file, "wb") as f:
            pickle.dump({"timestamp": datetime.now(), "data": data}, f, protocol=pickle.HIGHEST_PROTOCOL)
        tmp_file.replace(cache_file)  # atomic on most platforms
    except Exception as e:
        logger.debug(f"Cache write error for {symbol}: {e}")
        try:
            if tmp_file.exists():
                tmp_file.unlink()
        except Exception:
            pass


def get_stock_symbol(company_name):
    """Map company name to NSE symbol using Groq LLM"""
    next_key = balancer.get_next_key()
    client = Groq(api_key=next_key)

    prompt = f"""You are an expert in Indian stock markets and NSE symbols.

Task: Convert the given Indian company name to its exact NSE stock ticker symbol.

Company Name: {company_name}

Instructions:
1. Identify the correct company from NSE (National Stock Exchange of India)
2. Return ONLY the stock symbol with .NS suffix (for NSE listing)
3. Use the most common/primary listing symbol
4. Do not include any explanation, just the symbol
5. If the company has both NSE and BSE listings, prefer NSE (.NS)

Examples:
- "Reliance Industries" → RELIANCE.NS
- "Tata Consultancy Services" → TCS.NS
- "HDFC Bank" → HDFCBANK.NS
- "Infosys" → INFY.NS
- "State Bank of India" → SBIN.NS

Your response (symbol only):"""

    response = client.chat.completions.create(
        model=os.getenv("GROQ_MODEL"),
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=20,
    )

    raw = (response.choices[0].message.content or "").strip()

    # Sanitize common LLM formatting issues (backticks, quotes, code fences)
    raw = raw.replace("`", "").replace('"', "").replace("'", "").strip()
    raw = raw.splitlines()[0].strip()

    # Extract the first thing that looks like a NSE ticker with .NS
    m = re.search(r"\b([A-Z0-9&._-]+\.NS)\b", raw.upper())
    if m:
        return m.group(1).strip()

    # Fallback: enforce .NS suffix if missing
    sym = raw.upper().strip()
    if sym and not sym.endswith(".NS"):
        sym = f"{sym}.NS"
    return sym


def format_value(value, value_type):
    """Format values with appropriate symbols and decimals"""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "N/A"

    try:
        if value_type == "currency":
            return f"₹{float(value):.2f}"
        elif value_type == "crores":
            return f"₹{(float(value) / 10000000):.2f} Cr"
        elif value_type == "percentage":
            return f"{(float(value) * 100):.2f}%"
        elif value_type == "ratio":
            return f"{float(value):.2f}"
        elif value_type == "number":
            return f"{float(value):,.0f}"
        else:
            return f"{float(value):.2f}"
    except Exception:
        return "N/A"


def calculate_rsi(prices, period=14):
    """Calculate Relative Strength Index (Wilder's RSI)"""
    if prices is None or len(prices) < period + 1:
        return None

    prices = pd.Series(prices).dropna()
    if len(prices) < period + 1:
        return None

    delta = prices.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    # Wilder's smoothing via EMA with alpha = 1/period
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()

    last_gain = avg_gain.iloc[-1]
    last_loss = avg_loss.iloc[-1]
    if pd.isna(last_gain) or pd.isna(last_loss):
        return None

    if last_loss == 0:
        return 100.0  # no losses => RSI maxed

    rs = last_gain / last_loss
    rsi = 100 - (100 / (1 + rs))
    return float(rsi)


def calculate_macd(prices):
    """Calculate MACD"""
    if prices is None or len(prices) < 26:
        return None, None

    prices = pd.Series(prices).dropna()
    if len(prices) < 26:
        return None, None

    exp1 = prices.ewm(span=12, adjust=False).mean()
    exp2 = prices.ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    return float(macd.iloc[-1]), float(signal.iloc[-1])


def calculate_bollinger_bands(prices, period=20):
    """Calculate Bollinger Bands"""
    if prices is None or len(prices) < period:
        return None, None, None

    prices = pd.Series(prices).dropna()
    if len(prices) < period:
        return None, None, None

    sma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()
    upper = sma + (std * 2)
    lower = sma - (std * 2)
    return float(upper.iloc[-1]), float(sma.iloc[-1]), float(lower.iloc[-1])


def calculate_volatility(prices, period=30):
    """Calculate historical volatility (annualized)"""
    if prices is None or len(prices) < period + 1:
        return None

    prices = pd.Series(prices).dropna()
    if len(prices) < period + 1:
        return None

    # log returns = diff(log(price))
    logp = np.log(prices.replace(0, np.nan))
    log_returns = logp.diff()
    vol = log_returns.rolling(window=period).std() * np.sqrt(252)
    last = vol.iloc[-1]
    if pd.isna(last):
        return None
    return float(last)


def fetch_stock_data(symbol):
    """
    Fetch comprehensive stock data with calculated parameters
    OPTIMIZED: Uses caching and single API call for historical data
    """
    # Check cache first
    cached = get_cached_data(symbol)
    if cached:
        return cached

    stock = yf.Ticker(symbol)

    # Try to get info safely (yfinance can be flaky)
    try:
        info = stock.info or {}
    except Exception as e:
        logger.debug(f"yfinance info error for {symbol}: {e}")
        info = {}

    # Single historical API call
    try:
        hist_full = stock.history(period="1y")
    except Exception as e:
        logger.debug(f"yfinance history error for {symbol}: {e}")
        hist_full = pd.DataFrame()

    # Slice the data in memory
    hist_1y = hist_full
    hist_3mo = hist_full.tail(63) if len(hist_full) > 63 else hist_full  # ~3 months
    hist_1mo = hist_full.tail(21) if len(hist_full) > 21 else hist_full  # ~1 month
    hist_1d = hist_full.tail(1) if len(hist_full) > 0 else hist_full     # Last day

    # Prefer fast_info for prices when available (often faster / more reliable)
    fast = {}
    try:
        fast = getattr(stock, "fast_info", {}) or {}
    except Exception:
        fast = {}

    # Current price & previous close (best-effort fallbacks)
    current = (
        info.get("currentPrice")
        or fast.get("last_price")
        or (hist_1d["Close"].iloc[-1] if not hist_1d.empty and "Close" in hist_1d else None)
    )

    prev_close = (
        info.get("previousClose")
        or fast.get("previous_close")
        or (hist_full["Close"].iloc[-2] if len(hist_full) > 1 and "Close" in hist_full else None)
    )

    # Calculate technical indicators
    rsi = calculate_rsi(hist_3mo["Close"], 14) if "Close" in hist_3mo and len(hist_3mo) >= 15 else None
    macd_val, signal_val = calculate_macd(hist_3mo["Close"]) if "Close" in hist_3mo and len(hist_3mo) >= 26 else (None, None)
    upper_bb, middle_bb, lower_bb = calculate_bollinger_bands(hist_1mo["Close"], 20) if "Close" in hist_1mo and len(hist_1mo) >= 20 else (None, None, None)
    volatility = calculate_volatility(hist_1y["Close"], 30) if "Close" in hist_1y and len(hist_1y) >= 31 else None

    # Calculate moving averages
    sma_20 = hist_1mo["Close"].rolling(window=20).mean().iloc[-1] if "Close" in hist_1mo and len(hist_1mo) >= 20 else None
    sma_50 = hist_3mo["Close"].rolling(window=50).mean().iloc[-1] if "Close" in hist_3mo and len(hist_3mo) >= 50 else None
    sma_200 = hist_1y["Close"].rolling(window=200).mean().iloc[-1] if "Close" in hist_1y and len(hist_1y) >= 200 else None

    # Price changes
    pct_change_1d = ((current - prev_close) / prev_close) if (current is not None and prev_close not in (None, 0)) else None

    pct_change_1w = (
        ((current - hist_1mo["Close"].iloc[-5]) / hist_1mo["Close"].iloc[-5])
        if (current is not None and "Close" in hist_1mo and len(hist_1mo) >= 5 and hist_1mo["Close"].iloc[-5] not in (None, 0))
        else None
    )

    pct_change_1m = (
        ((current - hist_1mo["Close"].iloc[0]) / hist_1mo["Close"].iloc[0])
        if (current is not None and "Close" in hist_1mo and len(hist_1mo) > 0 and hist_1mo["Close"].iloc[0] not in (None, 0))
        else None
    )

    pct_change_3m = (
        ((current - hist_3mo["Close"].iloc[0]) / hist_3mo["Close"].iloc[0])
        if (current is not None and "Close" in hist_3mo and len(hist_3mo) > 0 and hist_3mo["Close"].iloc[0] not in (None, 0))
        else None
    )

    pct_change_1y = (
        ((current - hist_1y["Close"].iloc[0]) / hist_1y["Close"].iloc[0])
        if (current is not None and "Close" in hist_1y and len(hist_1y) > 0 and hist_1y["Close"].iloc[0] not in (None, 0))
        else None
    )

    # 52-week metrics
    week_52_high = hist_1y["High"].max() if (not hist_1y.empty and "High" in hist_1y) else info.get("fiftyTwoWeekHigh")
    week_52_low = hist_1y["Low"].min() if (not hist_1y.empty and "Low" in hist_1y) else info.get("fiftyTwoWeekLow")

    distance_from_52w_high = ((current - week_52_high) / week_52_high) if (current is not None and week_52_high not in (None, 0)) else None
    distance_from_52w_low = ((current - week_52_low) / week_52_low) if (current is not None and week_52_low not in (None, 0)) else None

    # Average volume
    avg_volume_30d = hist_1mo["Volume"].mean() if (not hist_1mo.empty and "Volume" in hist_1mo) else None
    volume_ratio = (
        (hist_1d["Volume"].iloc[-1] / avg_volume_30d)
        if (not hist_1d.empty and "Volume" in hist_1d and avg_volume_30d not in (None, 0))
        else None
    )

    # Day OHLC best-effort
    open_px = info.get("open") or fast.get("open") or (hist_1d["Open"].iloc[-1] if not hist_1d.empty and "Open" in hist_1d else None)
    day_high = info.get("dayHigh") or fast.get("day_high") or (hist_1d["High"].iloc[-1] if not hist_1d.empty and "High" in hist_1d else None)
    day_low = info.get("dayLow") or fast.get("day_low") or (hist_1d["Low"].iloc[-1] if not hist_1d.empty and "Low" in hist_1d else None)
    cur_vol = (hist_1d["Volume"].iloc[-1] if not hist_1d.empty and "Volume" in hist_1d else info.get("volume") or fast.get("last_volume"))

    data = {
        # Company Information
        "Company Name": info.get("longName", info.get("shortName", "N/A")),
        "Sector": info.get("sector", "N/A"),
        "Stock Symbol": symbol,
        "Industry": info.get("industry", "N/A"),

        # Price Data
        "Current Price": format_value(current, "currency"),
        "Previous Close": format_value(prev_close, "currency"),
        "Opening Price": format_value(open_px, "currency"),
        "Day High": format_value(day_high, "currency"),
        "Day Low": format_value(day_low, "currency"),

        # Price Performance
        "1 Day Change (%)": format_value(pct_change_1d, "percentage"),
        "1 Week Change (%)": format_value(pct_change_1w, "percentage"),
        "1 Month Change (%)": format_value(pct_change_1m, "percentage"),
        "3 Month Change (%)": format_value(pct_change_3m, "percentage"),
        "1 Year Change (%)": format_value(pct_change_1y, "percentage"),

        # Market Metrics
        "Market Capitalization": format_value(info.get("marketCap"), "crores"),
        "Enterprise Value": format_value(info.get("enterpriseValue"), "crores"),

        # Volume Metrics
        "Current Volume": format_value(cur_vol, "number"),
        "Average Volume (30 Days)": format_value(avg_volume_30d, "number"),
        "Volume Ratio": format_value(volume_ratio, "ratio"),

        # Valuation Ratios
        "P/E Ratio": format_value(info.get("trailingPE"), "ratio"),
        "Forward P/E Ratio": format_value(info.get("forwardPE"), "ratio"),
        "Price to Book Ratio": format_value(info.get("priceToBook"), "ratio"),
        "Price to Sales Ratio": format_value(info.get("priceToSalesTrailing12Months"), "ratio"),
        "Earnings Per Share (EPS)": format_value(info.get("trailingEps"), "currency"),
        "Forward EPS": format_value(info.get("forwardEps"), "currency"),

        # Profitability Metrics
        "Revenue Growth": format_value(info.get("revenueGrowth"), "percentage"),
        "Profit Margin": format_value(info.get("profitMargins"), "percentage"),
        "Operating Margin": format_value(info.get("operatingMargins"), "percentage"),
        "Gross Margin": format_value(info.get("grossMargins"), "percentage"),
        "Return on Equity (ROE)": format_value(info.get("returnOnEquity"), "percentage"),
        "Return on Assets (ROA)": format_value(info.get("returnOnAssets"), "percentage"),

        # Financial Health
        "Debt to Equity Ratio": format_value(info.get("debtToEquity"), "ratio"),
        "Current Ratio": format_value(info.get("currentRatio"), "ratio"),
        "Quick Ratio": format_value(info.get("quickRatio"), "ratio"),

        # Dividend Information
        "Dividend Yield": format_value(info.get("dividendYield"), "percentage"),
        "Dividend Rate": format_value(info.get("dividendRate"), "currency"),
        "Payout Ratio": format_value(info.get("payoutRatio"), "percentage"),

        # Technical Indicators
        "RSI (14)": format_value(rsi, "ratio"),
        "MACD": format_value(macd_val, "ratio"),
        "MACD Signal": format_value(signal_val, "ratio"),
        "Annual Volatility": format_value(volatility, "percentage"),

        # Moving Averages
        "20 Day SMA": format_value(sma_20, "currency"),
        "50 Day SMA": format_value(sma_50, "currency"),
        "200 Day SMA": format_value(sma_200, "currency"),

        # 52 Week Range
        "52 Week High": format_value(week_52_high, "currency"),
        "52 Week Low": format_value(week_52_low, "currency"),
        "Distance from 52 Week High (%)": format_value(distance_from_52w_high, "percentage"),
        "Distance from 52 Week Low (%)": format_value(distance_from_52w_low, "percentage"),

        # Bollinger Bands
        "Bollinger Band Upper": format_value(upper_bb, "currency"),
        "Bollinger Band Middle": format_value(middle_bb, "currency"),
        "Bollinger Band Lower": format_value(lower_bb, "currency"),

        # Additional Metrics
        "Book Value": format_value(info.get("bookValue"), "currency"),
    }

    # Cache the result
    save_cached_data(symbol, data)
    return data


# ============================================================================
# STOCK RECOMMENDER
# ============================================================================

def parse_value(value_str):
    """Extract numeric value from formatted strings"""
    if value_str == "N/A" or value_str is None:
        return None

    s = str(value_str).strip()
    if not s or s.lower() in {"nan", "none"}:
        return None

    # Handle accounting negatives like (123.45)
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1].strip()

    cleaned = (
        s.replace("₹", "")
        .replace("Cr", "")
        .replace(",", "")
        .replace("%", "")
        .strip()
    )

    try:
        val = float(cleaned)
        return -val if neg else val
    except (ValueError, AttributeError):
        return None


def analyze_stock(data):
    """Analyze stock and generate signals"""
    signals = {"bullish": [], "bearish": []}

    # Parse metrics
    current = parse_value(data.get("Current Price"))
    pe = parse_value(data.get("P/E Ratio"))
    fwd_pe = parse_value(data.get("Forward P/E Ratio"))
    roe = parse_value(data.get("Return on Equity (ROE)"))
    debt_eq = parse_value(data.get("Debt to Equity Ratio"))
    profit_margin = parse_value(data.get("Profit Margin"))
    revenue_growth = parse_value(data.get("Revenue Growth"))
    pb = parse_value(data.get("Price to Book Ratio"))
    current_ratio = parse_value(data.get("Current Ratio"))
    rsi = parse_value(data.get("RSI (14)"))
    sma_20 = parse_value(data.get("20 Day SMA"))
    sma_50 = parse_value(data.get("50 Day SMA"))
    sma_200 = parse_value(data.get("200 Day SMA"))
    dist_52w_high = parse_value(data.get("Distance from 52 Week High (%)"))
    macd = parse_value(data.get("MACD"))
    macd_signal = parse_value(data.get("MACD Signal"))
    chg_1m = parse_value(data.get("1 Month Change (%)"))
    chg_3m = parse_value(data.get("3 Month Change (%)"))
    chg_1y = parse_value(data.get("1 Year Change (%)"))
    volume_ratio = parse_value(data.get("Volume Ratio"))
    dividend_yield = parse_value(data.get("Dividend Yield"))

    # Normalize Debt-to-Equity (some feeds provide 120 instead of 1.20)
    if debt_eq is not None and debt_eq > 10:
        debt_eq = debt_eq / 100.0

    # Fundamental Analysis
    if pe is not None and pe < 15:
        signals["bullish"].append(f"Valuation: Undervalued at P/E {pe:.1f}, below market average")
    elif pe is not None and pe > 35:
        signals["bearish"].append(f"Valuation: Overvalued at P/E {pe:.1f}, significant premium")

    if fwd_pe is not None and pe is not None and fwd_pe < pe * 0.85:
        signals["bullish"].append(f"Growth: Strong earnings growth expected (Fwd P/E {fwd_pe:.1f} vs {pe:.1f})")

    if roe is not None and roe > 20:
        signals["bullish"].append(f"Profitability: Exceptional ROE of {roe:.1f}%, superior capital efficiency")
    elif roe is not None and roe < 10:
        signals["bearish"].append(f"Profitability: Weak ROE of {roe:.1f}%, poor profitability")

    if debt_eq is not None and debt_eq < 0.5:
        signals["bullish"].append(f"Health: Strong balance sheet, debt-to-equity at {debt_eq:.2f}")
    elif debt_eq is not None and debt_eq > 2.0:
        signals["bearish"].append(f"Health: High leverage risk, debt-to-equity at {debt_eq:.2f}")

    if profit_margin is not None and profit_margin > 20:
        signals["bullish"].append(f"Efficiency: Excellent {profit_margin:.1f}% profit margin shows pricing power")
    elif profit_margin is not None and profit_margin < 5:
        signals["bearish"].append(f"Efficiency: Thin {profit_margin:.1f}% margin limits flexibility")

    if revenue_growth is not None and revenue_growth > 15:
        signals["bullish"].append(f"Growth: Robust {revenue_growth:.1f}% revenue growth")
    elif revenue_growth is not None and revenue_growth < -10:
        signals["bearish"].append(f"Growth: Declining revenue of {revenue_growth:.1f}%")

    if pb is not None and pb < 1.5:
        signals["bullish"].append(f"Valuation: Trading below book value at P/B {pb:.1f}")
    elif pb is not None and pb > 5:
        signals["bearish"].append(f"Valuation: Premium valuation at P/B {pb:.1f}")

    if current_ratio is not None and current_ratio > 2.0:
        signals["bullish"].append(f"Liquidity: Strong liquidity, current ratio {current_ratio:.1f}")
    elif current_ratio is not None and current_ratio < 1.0:
        signals["bearish"].append(f"Liquidity: Liquidity concern, current ratio {current_ratio:.2f}")

    # Technical Analysis
    if rsi is not None and rsi < 30:
        signals["bullish"].append(f"Technical: Oversold at RSI {rsi:.0f}, potential reversal")
    elif rsi is not None and rsi > 70:
        signals["bearish"].append(f"Technical: Overbought at RSI {rsi:.0f}, correction risk")

    if current is not None and sma_20 is not None and sma_50 is not None and sma_200 is not None:
        if current > sma_20 > sma_50 > sma_200:
            signals["bullish"].append("Trend: Strong uptrend, above all moving averages")
        elif current < sma_20 < sma_50 < sma_200:
            signals["bearish"].append("Trend: Downtrend confirmed, below all moving averages")

    # Improved MACD logic: crossover matters even below zero
    if macd is not None and macd_signal is not None:
        if macd > macd_signal:
            if macd > 0:
                signals["bullish"].append("Momentum: MACD bullish crossover with positive momentum")
            else:
                signals["bullish"].append("Momentum: MACD bullish crossover (early reversal signal)")
        elif macd < macd_signal:
            if macd < 0:
                signals["bearish"].append("Momentum: MACD bearish crossover with negative momentum")
            else:
                signals["bearish"].append("Momentum: MACD bearish crossover (momentum cooling)")

    if dist_52w_high is not None and -25 < dist_52w_high < -15:
        signals["bullish"].append(f"Price Action: Trading {abs(dist_52w_high):.0f}% below 52W high, recovery potential")
    elif dist_52w_high is not None and dist_52w_high > -5:
        signals["bearish"].append("Price Action: Near 52-week high, limited upside")

    if chg_1m is not None and chg_3m is not None and chg_1m > 5 and chg_3m > 10:
        signals["bullish"].append(f"Performance: Strong momentum: +{chg_1m:.1f}% (1M), +{chg_3m:.1f}% (3M)")
    elif chg_1m is not None and chg_3m is not None and chg_1m < -5 and chg_3m < -10:
        signals["bearish"].append(f"Performance: Weak momentum: {chg_1m:.1f}% (1M), {chg_3m:.1f}% (3M)")

    if chg_1y is not None and chg_1y > 30:
        signals["bullish"].append(f"Performance: Outstanding {chg_1y:.1f}% annual return")
    elif chg_1y is not None and chg_1y < -20:
        signals["bearish"].append(f"Performance: Significant {chg_1y:.1f}% annual decline")

    if volume_ratio is not None and volume_ratio > 2.0:
        signals["bullish"].append(f"Volume: High volume at {volume_ratio:.1f}x average, strong interest")
    elif volume_ratio is not None and volume_ratio < 0.4:
        signals["bearish"].append(f"Volume: Low volume at {volume_ratio:.1f}x average, weak interest")

    if dividend_yield is not None and 2 < dividend_yield < 100:
        if dividend_yield > 4:
            signals["bullish"].append(f"Dividend: Attractive {dividend_yield:.1f}% dividend yield")

    return signals


def calculate_recommendation(signals):
    """Calculate Buy/Sell/Hold percentages"""
    bullish = len(signals["bullish"])
    bearish = len(signals["bearish"])

    if bullish + bearish == 0:
        return {"Buy": 33.33, "Sell": 33.33, "Hold": 33.34}

    total_signals = bullish + bearish
    buy_base = (bullish / total_signals) * 100
    sell_base = (bearish / total_signals) * 100

    balance_ratio = min(bullish, bearish) / max(bullish, bearish) if max(bullish, bearish) > 0 else 0
    hold_weight = balance_ratio * 40

    adjustment_factor = (100 - hold_weight) / 100
    buy = buy_base * adjustment_factor
    sell = sell_base * adjustment_factor
    hold = hold_weight

    if bullish > bearish * 2:
        buy = min(buy * 1.1, 100)
        hold = hold * 0.5
    elif bearish > bullish * 2:
        sell = min(sell * 1.1, 100)
        hold = hold * 0.5

    total = buy + sell + hold
    return {
        "Buy": round((buy / total) * 100, 2),
        "Sell": round((sell / total) * 100, 2),
        "Hold": round((hold / total) * 100, 2),
    }


def get_top_reasons(signals, recommendation):
    """Select top 5 most impactful and suitable reasons based on conviction"""
    def to_float(val):
        try:
            if isinstance(val, str):
                return float(val.replace("%", "").strip())
            return float(val)
        except Exception:
            return 0.0

    buy_pct = to_float(recommendation.get("Buy", 0))
    sell_pct = to_float(recommendation.get("Sell", 0))
    hold_pct = to_float(recommendation.get("Hold", 0))

    bullish = signals.get("bullish", [])
    bearish = signals.get("bearish", [])

    def format_reason(prefix, reason):
        clean_reason = reason.replace("[", "").replace("]", "")
        if ":" in clean_reason:
            parts = clean_reason.split(":", 1)
            return f"{prefix} - {parts[0].strip()}: {parts[1].strip()}"
        return f"{prefix}: {clean_reason}"

    if buy_pct > 60:
        selected = bullish[:4]
        if bearish:
            selected.append(format_reason("Risk", bearish[0]))
        elif len(bullish) >= 5:
            selected.append(bullish[4])
        return selected[:5]

    elif sell_pct > 60:
        selected = bearish[:4]
        if bullish:
            selected.append(format_reason("Opportunity", bullish[0]))
        elif len(bearish) >= 5:
            selected.append(bearish[4])
        return selected[:5]

    elif hold_pct > buy_pct and hold_pct > sell_pct:
        selected = []
        if bullish:
            selected.append(format_reason("Strength", bullish[0]))
        if bearish:
            selected.append(format_reason("Concern", bearish[0]))
        if len(bullish) > 1:
            selected.append(bullish[1])
        if len(bearish) > 1:
            selected.append(bearish[1])
        if len(bullish) > 2:
            selected.append(bullish[2])
        elif len(bearish) > 2:
            selected.append(bearish[2])
        return selected[:5]

    elif buy_pct > sell_pct:
        selected = bullish[:3]
        selected.extend(bearish[:2])
        return selected[:5]

    else:
        selected = bearish[:3]
        selected.extend(bullish[:2])
        return selected[:5]


def generate_recommendation(stock_data):
    """Generate recommendation from stock data"""
    signals = analyze_stock(stock_data)
    recommendation = calculate_recommendation(signals)
    reasons = get_top_reasons(signals, recommendation)

    return {
        "Buy": f"{recommendation['Buy']}%",
        "Sell": f"{recommendation['Sell']}%",
        "Hold": f"{recommendation['Hold']}%",
        "Investment Rationale": reasons if reasons else ["Insufficient data for comprehensive analysis"],
    }
