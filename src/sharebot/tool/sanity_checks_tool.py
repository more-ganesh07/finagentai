# tool/sanity_checks_tool.py

from typing import Dict, Optional

def _parse_value(value_str) -> Optional[float]:
    """Extract numeric float from formatted strings like '₹344.40', '18.00%', '8,805,932'."""
    if value_str is None:
        return None
    s = str(value_str).strip()
    if not s or s == "N/A":
        return None

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
        v = float(cleaned)
        return -v if neg else v
    except Exception:
        return None


def build_warnings(stock_data: Dict) -> Dict[str, str]:
    """
    Returns a dict: { parameter_name: warning_message }
    Only includes keys that need warnings.
    """
    w: Dict[str, str] = {}
    d = stock_data or {}

    current_price = _parse_value(d.get("Current Price"))
    dividend_yield_pct = _parse_value(d.get("Dividend Yield"))   # already percent number (e.g., "3.2%" -> 3.2)
    dividend_rate = _parse_value(d.get("Dividend Rate"))
    debt_to_equity = _parse_value(d.get("Debt to Equity Ratio"))
    pe = _parse_value(d.get("P/E Ratio"))
    fwd_pe = _parse_value(d.get("Forward P/E Ratio"))
    rsi = _parse_value(d.get("RSI (14)"))
    current_ratio = _parse_value(d.get("Current Ratio"))
    quick_ratio = _parse_value(d.get("Quick Ratio"))
    vol_pct = _parse_value(d.get("Annual Volatility"))
    dist_high = _parse_value(d.get("Distance from 52 Week High (%)"))
    dist_low = _parse_value(d.get("Distance from 52 Week Low (%)"))

    # Dividend sanity
    if dividend_yield_pct is not None:
        if dividend_yield_pct > 50:
            w["Dividend Yield"] = (
                "Extremely high yield is usually a data glitch, special one-time dividend, or price distortion. "
                "Verify from NSE filings/company dividend history before relying on it."
            )
        elif dividend_yield_pct > 20:
            w["Dividend Yield"] = (
                "Unusually high yield. Often caused by special dividends or data issues. "
                "Confirm the latest dividend announcements and whether it’s recurring."
            )

    # Cross-check dividend rate vs price (extra hint)
    if current_price and dividend_rate:
        implied_yield = (dividend_rate / current_price) * 100
        if implied_yield > 20 and dividend_yield_pct is None:
            w["Dividend Rate"] = (
                "Dividend looks very large versus current price. Check if this includes special dividends or if data is stale."
            )

    # Debt-to-equity sanity (common scaling issue)
    if debt_to_equity is not None:
        if debt_to_equity > 10:
            w["Debt to Equity Ratio"] = (
                "This value looks like it may be reported in percent (e.g., 127 means ~1.27). "
                "Use caution and cross-check with financial statements or another data source."
            )
        elif debt_to_equity > 5:
            w["Debt to Equity Ratio"] = (
                "Very high leverage. Higher debt can increase risk, especially when interest rates rise. "
                "Compare with peers and check interest coverage if available."
            )

    # P/E sanity
    if pe is not None and pe < 0:
        w["P/E Ratio"] = (
            "Negative P/E usually means the company has negative earnings (losses). "
            "In this case P/E is not useful for valuation—look at revenue, margins, and turnaround signs."
        )
    if pe is not None and pe > 100:
        w["P/E Ratio"] = (
            "Very high P/E suggests the market expects strong growth, or earnings are temporarily low. "
            "Compare with sector peers and check whether profits are stable."
        )

    if fwd_pe is not None and pe is not None and fwd_pe > pe * 1.5:
        w["Forward P/E Ratio"] = (
            "Forward P/E much higher than current P/E may indicate expected earnings drop or conservative forecasts. "
            "Check guidance and recent quarterly results."
        )

    # RSI bounds
    if rsi is not None and (rsi < 0 or rsi > 100):
        w["RSI (14)"] = "RSI should normally be between 0 and 100. This may indicate a data/parse issue."

    # Liquidity
    if current_ratio is not None and current_ratio < 1:
        w["Current Ratio"] = (
            "Below 1 can indicate short-term liquidity pressure (current liabilities exceed current assets). "
            "This can be normal in some businesses, but it’s worth checking cash flows and debt schedule."
        )

    if quick_ratio is not None and quick_ratio < 0.5:
        w["Quick Ratio"] = (
            "Low quick ratio suggests limited liquid assets to cover short-term liabilities. "
            "Not always bad, but beginners should treat it as a caution flag and check cash flow stability."
        )

    # Volatility sanity (percent number)
    if vol_pct is not None and vol_pct > 120:
        w["Annual Volatility"] = (
            "Very high volatility implies large price swings and higher risk. "
            "Consider position sizing and risk controls, or verify if this is a data anomaly."
        )

    # 52-week distance sanity
    if dist_high is not None and (dist_high < -100 or dist_high > 200):
        w["Distance from 52 Week High (%)"] = "This percentage looks out of expected range. It may be a formatting/data issue."
    if dist_low is not None and (dist_low < -100 or dist_low > 500):
        w["Distance from 52 Week Low (%)"] = "This percentage looks out of expected range. It may be a formatting/data issue."

    return w
 