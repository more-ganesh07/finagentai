from typing import Dict, List

from tool.sanity_checks_tool import build_warnings

PARAMETER_ORDER: List[str] = [
    "Company Name",
    "Sector",
    "Stock Symbol",
    "Industry",
    "Current Price",
    "Previous Close",
    "Opening Price",
    "Day High",
    "Day Low",
    "1 Day Change (%)",
    "1 Week Change (%)",
    "1 Month Change (%)",
    "3 Month Change (%)",
    "1 Year Change (%)",
    "Market Capitalization",
    "Enterprise Value",
    "Current Volume",
    "Average Volume (30 Days)",
    "Volume Ratio",
    "P/E Ratio",
    "Forward P/E Ratio",
    "Price to Book Ratio",
    "Price to Sales Ratio",
    "Earnings Per Share (EPS)",
    "Forward EPS",
    "Revenue Growth",
    "Profit Margin",
    "Operating Margin",
    "Gross Margin",
    "Return on Equity (ROE)",
    "Return on Assets (ROA)",
    "Debt to Equity Ratio",
    "Current Ratio",
    "Quick Ratio",
    "Dividend Yield",
    "Dividend Rate",
    "Payout Ratio",
    "RSI (14)",
    "MACD",
    "MACD Signal",
    "Annual Volatility",
    "20 Day SMA",
    "50 Day SMA",
    "200 Day SMA",
    "52 Week High",
    "52 Week Low",
    "Distance from 52 Week High (%)",
    "Distance from 52 Week Low (%)",
    "Bollinger Band Upper",
    "Bollinger Band Middle",
    "Bollinger Band Lower",
    "Book Value",
]


PARAMETER_MEANINGS: Dict[str, str] = {
    "Company Name": "Official name of the company whose stock you're analyzing.",
    "Sector": "Broad business category like Utilities, IT, Banking, or FMCG.",
    "Stock Symbol": "Unique trading code used on exchange, usually ends with .NS.",
    "Industry": "Specific classification within sector showing exact business type and revenue drivers.",
    "Current Price": "Latest market price of one share during the current trading day.",
    "Previous Close": "Stock price at end of previous trading day used for comparison.",
    "Opening Price": "First traded price when market opened, reflects overnight sentiment and news.",
    "Day High": "Highest price reached during current trading day showing upside movement.",
    "Day Low": "Lowest price reached during current trading day showing downside pressure.",
    "1 Day Change (%)": "Percentage change from previous close showing today's movement direction and sentiment.",
    "1 Week Change (%)": "Percentage price change over last five trading sessions showing short-term momentum.",
    "1 Month Change (%)": "Percentage price change over last month showing short-term trend strength.",
    "3 Month Change (%)": "Percentage change over three months filtering daily noise and showing momentum.",
    "1 Year Change (%)": "Yearly percentage change showing long-term performance across different market conditions.",
    "Market Capitalization": "Total market value calculated as current price multiplied by total shares outstanding.",
    "Enterprise Value": "Company's full valuation including debt and excluding excess cash holdings.",
    "Current Volume": "Number of shares traded today indicating market interest and activity level.",
    "Average Volume (30 Days)": "Average daily shares traded over last month showing normal activity baseline.",
    "Volume Ratio": "Current volume divided by 30-day average, above 1 means higher activity.",
    "P/E Ratio": "Price divided by earnings showing how much investors pay for ₹1 profit.",
    "Forward P/E Ratio": "Price divided by expected future earnings showing market's growth expectations.",
    "Price to Book Ratio": "Price compared to book value per share, commonly used for banks.",
    "Price to Sales Ratio": "Market value compared to total revenue, useful when earnings fluctuate significantly.",
    "Earnings Per Share (EPS)": "Company's net profit per share over the last reported period.",
    "Forward EPS": "Expected earnings per share for upcoming periods based on analyst forecasts.",
    "Revenue Growth": "How quickly company's sales are increasing compared to the previous period.",
    "Profit Margin": "Percentage of revenue remaining as net profit after all expenses are paid.",
    "Operating Margin": "Profit from core operations before interest and taxes showing business efficiency.",
    "Gross Margin": "Profit after direct costs but before overheads showing basic profitability level.",
    "Return on Equity (ROE)": "How effectively company generates profit using shareholders' money, higher is better.",
    "Return on Assets (ROA)": "How efficiently company uses its total assets to generate profit.",
    "Debt to Equity Ratio": "Total debt compared to shareholders' equity showing reliance on borrowing.",
    "Current Ratio": "Current assets divided by current liabilities showing short-term payment ability.",
    "Quick Ratio": "Current ratio excluding inventory showing immediate liquidity without selling stock.",
    "Dividend Yield": "Annual dividend per share divided by current price shown as percentage.",
    "Dividend Rate": "Approximate annual dividend amount paid per share to shareholders regularly.",
    "Payout Ratio": "Percentage of earnings paid out as dividends showing distribution sustainability.",
    "RSI (14)": "Momentum indicator from 0-100, above 70 overbought, below 30 oversold.",
    "MACD": "Moving average convergence divergence showing momentum shifts and trend strength changes.",
    "MACD Signal": "Smoothed MACD line for crossovers, crossing above signals bullish momentum shift.",
    "Annual Volatility": "How much stock price typically fluctuates yearly, higher values mean riskier.",
    "20 Day SMA": "Average closing price over last 20 days showing short-term trend direction.",
    "50 Day SMA": "Average closing price over last 50 days showing medium-term trend direction.",
    "200 Day SMA": "Average closing price over last 200 days showing long-term trend direction.",
    "52 Week High": "Highest price reached in last year showing recent peak valuation level.",
    "52 Week Low": "Lowest price reached in last year showing worst recent valuation point.",
    "Distance from 52 Week High (%)": "How far current price is below or above the yearly high.",
    "Distance from 52 Week Low (%)": "How far current price is above or below the yearly low.",
    "Bollinger Band Upper": "Upper band indicating strong momentum or stretched move when price approaches it.",
    "Bollinger Band Middle": "Usually 20-day moving average acting as dynamic support or resistance level.",
    "Bollinger Band Lower": "Lower band indicating weakness or oversold condition when price touches it.",
    "Book Value": "Net assets per share from balance sheet, useful for asset-heavy businesses.",
}

def build_parameter_table(stock_data: Dict) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    stock_data = stock_data or {}

    warnings = build_warnings(stock_data)

    for key in PARAMETER_ORDER:
        base_meaning = PARAMETER_MEANINGS.get(
            key,
            "Meaning not available for this parameter yet. It represents a standard stock-related metric used in market analysis."
        )

        warn = warnings.get(key)
        # ✅ Put warning on a new line (still only 3 columns)
        meaning = base_meaning
        if warn:
            meaning = f"{base_meaning}\n⚠️ Note: {warn}"

        rows.append(
            {
                "parameter": key,
                "value": stock_data.get(key, "N/A"),
                "meaning": meaning,
            }
        )

    return rows