import json
import asyncio
from datetime import datetime
from pathlib import Path
import os
import base64
import markdown
from dotenv import load_dotenv

from src.kite.portrep.portreport.deepagent import DeepAgent
from src.kite.portrep.portreport.emailer import send_email_with_attachment

load_dotenv(override=True)

# File Paths
SCRIPT_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent.parent

DATA_DIR = Path(os.getenv("REPORTS_DIR", str(PROJECT_ROOT / "data" / "reports")))
DATA_DIR.mkdir(parents=True, exist_ok=True)

JSON_FILE = Path(os.getenv("PORTFOLIO_SUMMARY_JSON_PATH", str(SCRIPT_DIR / "mcp_summary.json")))
REPORT_FILE = DATA_DIR / "portfolio_report.html"
MD_REPORT_FILE = DATA_DIR / "portfolio_report.md"
CHARTS_DIR = SCRIPT_DIR / "viz" / "charts"


def get_image_base64(image_path):
    """Convert image file to base64 data URI for HTML embedding"""
    try:
        if not image_path.exists():
            return None
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
            return f"data:image/png;base64,{encoded_string}"
    except Exception as e:
        print(f"⚠️ Error encoding image {image_path.name}: {e}")
        return None


def format_currency(val):
    """Format value as Indian Rupee currency"""
    try:
        return f"₹{float(val):,.2f}"
    except Exception:
        return str(val)


def load_data():
    if not JSON_FILE.exists():
        print(f"❌ Error: {JSON_FILE} not found.")
        return None
    with open(JSON_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def format_analysis_content(analysis_text, is_mf=False):
    """Format analysis text into professional structure using markdown library"""
    
    if not analysis_text or "Error" in analysis_text or "unavailable" in analysis_text:
        msg = analysis_text or "Analysis unavailable"
        return f'<div class="analysis-container"><p style="color: #64748b; font-style: italic;">{msg}</p></div>'
    
    # Clean LLM output if it's wrapped in triple backticks
    analysis_text = analysis_text.strip()
    if analysis_text.startswith("```"):
        # Remove opening backticks line (e.g. ```markdown)
        lines = analysis_text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        # Remove closing backticks
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        analysis_text = "\n".join(lines).strip()

    # Use markdown library for robust conversion
    # Supports tables, lists, bolding, etc.
    html_content = markdown.markdown(analysis_text, extensions=['extra', 'nl2br'])
    
    # Highlight keywords in the generated HTML
    html_content = highlight_keywords(html_content)
    
    # Wrap in a container for specific styling
    return f'<div class="analysis-container">{html_content}</div>'


# format_mf_analysis removed as format_analysis_content handles all cases via markdown now.


def highlight_keywords(text):
    """Highlight important financial keywords in text"""
    keywords = {
        'Buy': 'buy-tag',
        'Sell': 'sell-tag',
        'Hold': 'hold-tag',
        'Accumulate': 'accumulate-tag',
        'profitable': 'positive-keyword',
        'growth': 'positive-keyword',
        'upside': 'positive-keyword',
        'bullish': 'positive-keyword',
        'positive': 'positive-keyword',
        'risk': 'negative-keyword',
        'challenge': 'negative-keyword',
        'loss': 'negative-keyword',
        'decline': 'negative-keyword',
        'bearish': 'negative-keyword'
    }
    
    for keyword, css_class in keywords.items():
        if keyword in text:
            text = text.replace(keyword, f'<span class="{css_class}">{keyword}</span>')
    
    return text


def get_html_template():
    """Returns professional HTML template with CSS styling optimized for PDF and web viewing"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Investment Portfolio Analysis Report</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        @page {
            size: A4;
            margin: 1.5cm;
        }
        
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #1e293b;
            background: #ffffff;
            font-size: 10pt;
        }
        
        .page {
            background: white;
            padding: 30px;
            page-break-after: always;
            max-width: 900px;
            margin: auto;
        }
        
        .page:last-child {
            page-break-after: auto;
        }
        
        /* Header Styles */
        .header {
            border-bottom: 2px solid #1e3a8a;
            padding-bottom: 15px;
            margin-bottom: 30px;
            position: relative;
        }
        
        .header h1 {
            font-size: 24pt;
            font-weight: 700;
            color: #1e3a8a;
            margin-bottom: 5px;
            letter-spacing: -0.02em;
        }
        
        .header .subtitle {
            font-size: 10pt;
            color: #475569;
            font-weight: 500;
        }
        
        /* Section Styles */
        .section {
            margin-bottom: 35px;
        }
        
        .section-title {
            font-size: 16pt;
            font-weight: 700;
            color: #1e3a8a;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 12px;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 10px;
        }
        
        .section-title .number {
            background: #1e3a8a;
            color: white;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 14pt;
        }
        
        .subsection-title {
            font-size: 13pt;
            font-weight: 700;
            color: #1e3a8a;
            margin: 25px 0 12px 0;
            border-left: 4px solid #3b82f6;
            padding-left: 10px;
        }
        
        /* Profile Card */
        .profile-card {
            background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
            border-radius: 12px;
            padding: 25px;
            color: white;
            margin-bottom: 25px;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
        
        .profile-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
        }
        
        .profile-item {
            display: flex;
            flex-direction: column;
        }
        
        .profile-label {
            font-size: 8pt;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            opacity: 0.8;
            font-weight: 600;
            margin-bottom: 4px;
        }
        
        .profile-value {
            font-size: 11pt;
            font-weight: 600;
        }
        
        /* Stats Cards */
        .stats-container {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin: 25px 0;
        }
        
        .stat-card {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-left: 4px solid #1e3a8a;
            border-radius: 10px;
            padding: 20px 15px;
            transition: all 0.3s;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        }
        
        .stat-card.positive { border-left-color: #10b981; }
        .stat-card.negative { border-left-color: #ef4444; }
        
        .stat-label {
            font-size: 8.5pt;
            color: #475569;
            text-transform: uppercase;
            font-weight: 700;
            margin-bottom: 10px;
            letter-spacing: 0.05em;
        }
        
        .stat-value {
            font-size: 18pt;
            font-weight: 700;
            color: #0f172a;
            margin-bottom: 3px;
        }
        
        .stat-hint {
            font-size: 8pt;
            color: #475569;
            font-weight: 500;
        }
        
        .stat-change {
            font-size: 10pt;
            margin-top: 6px;
            font-weight: 700;
            display: inline-flex;
            align-items: center;
            background: #eff6ff;
            padding: 3px 8px;
            border-radius: 5px;
        }
        
        .stat-change.positive { color: #059669; background: #ecfdf5; }
        .stat-change.negative { color: #dc2626; background: #fef2f2; }
        
        /* Tables */
        .table-container {
            margin: 25px 0;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            overflow: hidden;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 10.5pt;
        }
        
        thead {
            background: #1e3a8a;
            color: white;
        }
        
        th {
            padding: 14px 12px;
            text-align: left;
            font-weight: 700;
            font-size: 9.5pt;
            text-transform: uppercase;
            letter-spacing: 0.03em;
        }
        
        td {
            padding: 12px 12px;
            border-bottom: 1px solid #f1f5f9;
            font-size: 10pt;
        }
        
        tbody tr:nth-child(even) {
            background-color: #f8fafc;
        }
        
        .symbol-cell {
            font-weight: 700;
            color: #1e3a8a;
        }
        
        /* KPI / Metric Boxes */
        .stock-metrics {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin: 20px 0;
        }
        
        .metric {
            background: #f8fafc;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 12px 8px;
            text-align: center;
            transition: transform 0.2s;
        }
        
        .metric-label {
            font-size: 7.2pt;
            text-transform: uppercase;
            color: #475569;
            font-weight: 700;
            margin-bottom: 5px;
            letter-spacing: 0.02em;
        }
        
        .metric-value {
            font-size: 11pt;
            font-weight: 700;
            color: #0f172a;
        }
        
        /* Analysis Content Styling */
        .analysis-container {
            background: white;
            line-height: 1.7;
        }
        
        .analysis-container h1, .analysis-container h2, .analysis-container h3, .analysis-container h4 {
            color: #1e3a8a;
            margin: 20px 0 10px 0;
            font-weight: 700;
        }
        
        .analysis-container h1 { font-size: 16pt; }
        .analysis-container h2 { font-size: 14pt; }
        .analysis-container h3 { 
            font-size: 12pt; 
            border-left: 4px solid #3b82f6; 
            padding: 8px 12px; 
            background: #eff6ff; 
            border-radius: 0 6px 6px 0; 
            margin-top: 25px;
        }
        
        .analysis-container p { margin-bottom: 12px; color: #1e293b; }
        
        .analysis-container ul, .analysis-container ol {
            margin: 12px 0 18px 20px;
        }
        
        .analysis-container li {
            margin-bottom: 8px;
            position: relative;
        }

        /* Stock Analysis Card */
        .stock-card {
            background: white;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 25px;
            border: 1px solid #e2e8f0;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        
        .stock-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            border-bottom: 1px solid #f1f5f9;
            padding-bottom: 15px;
        }
        
        .stock-name {
            font-size: 20pt;
            font-weight: 700;
            color: #1e3a8a;
        }
        
        .chart-container {
            margin: 25px 0;
            background: #f8fafc;
            padding: 15px;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            text-align: center;
        }
        
        .chart-container img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
        }
        
        /* Tags & Highlights */
        .buy-tag, .accumulate-tag, .positive-keyword { color: #059669; font-weight: 700; }
        .sell-tag, .negative-keyword { color: #dc2626; font-weight: 700; }
        .hold-tag { color: #d97706; font-weight: 700; }

        .footer {
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #e2e8f0;
            text-align: center;
            font-size: 8.5pt;
            color: #475569;
        }

        @media print {
            .page { width: 100%; padding: 0 !important; margin: 0 !important; box-shadow: none; }
            .stock-card { page-break-inside: avoid; }
            .analysis-container h3 { background: #f1f5f9 !important; -webkit-print-color-adjust: exact; }
        }
    </style>
</head>
<body>
<div class="main-wrapper">
{CONTENT}
</div>
</body>
</html>
"""


def generate_markdown_content(data, analyses):
    """Generate professional Markdown version of the report"""
    profile = data.get("profile", {})
    holdings = data.get("holdings", [])
    mfs = data.get("mutual_funds", [])
    timestamp = data.get("timestamp", datetime.now().strftime("%B %d, %Y at %I:%M %p"))

    total_investment = sum(h["qty"] * h["avg"] for h in holdings)
    current_value = sum(h["qty"] * h["ltp"] for h in holdings)
    total_pnl = sum(h["pnl"] for h in holdings)
    pnl_pct = (total_pnl / total_investment * 100) if total_investment > 0 else 0

    md = f"# Investment Portfolio Analysis Report\n"
    md += f"Generated on: {timestamp}\n\n"

    md += "## 1. Client Profile\n"
    md += f"- **Name:** {profile.get('name', 'N/A')}\n"
    md += f"- **Client ID:** {profile.get('user_id', 'N/A')}\n"
    md += f"- **Broker:** {profile.get('broker', 'N/A')}\n"
    md += f"- **Email:** {profile.get('email', 'N/A')}\n\n"

    md += "## 2. Portfolio Summary\n"
    md += f"- **Total Investment:** {format_currency(total_investment)}\n"
    md += f"- **Current Value:** {format_currency(current_value)}\n"
    md += f"- **Total P&L:** {format_currency(total_pnl)} ({pnl_pct:+.2f}%)\n\n"

    md += "### Holdings\n"
    md += "| Symbol | Qty | Avg Cost | LTP | P&L |\n"
    md += "| :--- | :--- | :--- | :--- | :--- |\n"
    for h in holdings:
        md += f"| {h['symbol']} | {h['qty']} | {format_currency(h['avg'])} | {format_currency(h['ltp'])} | {format_currency(h['pnl'])} |\n"
    
    md += "\n## 3. Detailed Analysis\n"
    for h in holdings:
        sym = h['symbol']
        analysis = analyses.get(f"STOCK_{sym}", "Analysis unavailable")
        md += f"\n### {sym}\n"
        md += f"{analysis}\n"
        md += "\n---\n"

    if mfs:
        md += "\n## 4. Mutual Funds\n"
        for m in mfs:
            scheme = m['scheme_name']
            analysis = analyses.get(f"MF_{scheme}", "Analysis unavailable")
            md += f"\n### {scheme}\n"
            md += f"- **Units:** {m['units']}\n"
            md += f"- **Current Value:** {format_currency(m['value'])}\n"
            md += f"- **Gain:** {m['gain_pct']}%\n\n"
            md += f"{analysis}\n"
            md += "\n---\n"

    return md


def generate_html_content(data, analyses):
    """Generate HTML content with professional styling and proper page breaks"""
    profile = data.get("profile", {})
    holdings = data.get("holdings", [])
    mfs = data.get("mutual_funds", [])
    timestamp = data.get("timestamp", datetime.now().strftime("%B %d, %Y at %I:%M %p"))

    # Calculate totals
    total_investment = sum(h["qty"] * h["avg"] for h in holdings)
    current_value = sum(h["qty"] * h["ltp"] for h in holdings)
    total_pnl = sum(h["pnl"] for h in holdings)
    pnl_pct = (total_pnl / total_investment * 100) if total_investment > 0 else 0

    html = ''
    
    # ==================== PAGE 1: Header & Profile ====================
    html += '<div class="page">'
    
    html += f'''
    <div class="header">
        <h1>Investment Portfolio Analysis Report</h1>
        <div class="subtitle">Generated on {timestamp}</div>
    </div>
    '''
    
    html += '''
    <div class="section">
        <div class="section-title">
            <span class="number">1</span>
            Client Profile & Account Summary
        </div>
        <div class="profile-card">
            <div class="profile-grid">
    '''
    
    html += f'''
                <div class="profile-item">
                    <div class="profile-label">Client Name</div>
                    <div class="profile-value">{profile.get('name', 'N/A')}</div>
                </div>
                <div class="profile-item">
                    <div class="profile-label">Client ID</div>
                    <div class="profile-value">{profile.get('user_id', 'N/A')}</div>
                </div>
                <div class="profile-item">
                    <div class="profile-label">Brokerage</div>
                    <div class="profile-value">{profile.get('broker', 'N/A')}</div>
                </div>
                <div class="profile-item">
                    <div class="profile-label">Email Contact</div>
                    <div class="profile-value">{profile.get('email', 'N/A')}</div>
                </div>
    '''
    
    html += '''
            </div>
        </div>
    </div>
    '''
    
    # ==================== PAGE 2: Market Sentiment ====================
    html += '''
    <div class="section">
        <div class="section-title">
            <span class="number">2</span>
            Market Sentiment Dashboard
        </div>
        <p style="color: #64748b; margin-bottom: 15px;">Current Indian market overview with major indices performance and sentiment analysis.</p>
    '''
    
    market_chart = CHARTS_DIR / "market_sentiment_dashboard.png"
    if market_chart.exists():
        img_base64 = get_image_base64(market_chart)
        if img_base64:
            html += f'''
            <div class="chart-container">
                <img src="{img_base64}" alt="Market Sentiment Dashboard">
            </div>
            '''
    
    html += '''
        <div class="info-box">
            <p><strong>Top Left - Major Indices Performance:</strong> Shows percentage change for key Indian indices (NIFTY 50, SENSEX, BANKNIFTY, etc.) over the selected period.</p>
            <p><strong>Top Right - NIFTY 50 vs India VIX:</strong> Displays the inverse relationship between market performance and volatility. Higher VIX indicates increased market fear.</p>
            <p><strong>Bottom Left - Relative Performance:</strong> Compares normalized performance of different indices from a common starting point (100).</p>
            <p><strong>Bottom Right - Fear & Greed Index:</strong> Market sentiment gauge based on India VIX. Extreme Fear (&lt;25) suggests buying opportunity, Extreme Greed (&gt;75) suggests caution.</p>
        </div>
    </div>
    '''
    
    html += '</div>'  # Close PAGE 1
    
    # ==================== PAGE 2: Portfolio Overview ====================
    html += '<div class="page">'
    
    pnl_class = 'positive' if total_pnl >= 0 else 'negative'
    
    html += f'''
    <div class="section">
        <div class="section-title">
            <span class="number">3</span>
            Portfolio Performance Overview
        </div>
        
        <div class="stats-container">
            <div class="stat-card">
                <div class="stat-label">Total Investment</div>
                <div class="stat-value">{format_currency(total_investment)}</div>
                <div class="stat-hint">Original Capital</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Current Value</div>
                <div class="stat-value">{format_currency(current_value)}</div>
                <div class="stat-hint">Market Valuation</div>
            </div>
            <div class="stat-card {pnl_class}">
                <div class="stat-label">Net Profit/Loss</div>
                <div class="stat-value">{format_currency(total_pnl)}</div>
                <div class="stat-change {pnl_class}">{pnl_pct:+.2f}% ROI</div>
            </div>
        </div>
    '''
    
    portfolio_chart = CHARTS_DIR / "portfolio_performance_tracker.png"
    if portfolio_chart.exists():
        img_base64 = get_image_base64(portfolio_chart)
        if img_base64:
            html += f'''
            <div class="subsection-title">Portfolio Performance Chart</div>
            <p style="color: #64748b; margin-bottom: 12px;">Year-to-date performance tracking of your equity holdings with benchmark comparison.</p>
            <div class="chart-container">
                <img src="{img_base64}" alt="Portfolio Performance Tracker">
            </div>
            '''
    
    # Holdings Table
    html += '''
        <div class="subsection-title">Portfolio Details</div>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th style="width: 25%;">Symbol</th>
                        <th>Quantity</th>
                        <th>Avg. Cost</th>
                        <th>Current Price</th>
                        <th>Net P&L</th>
                    </tr>
                </thead>
                <tbody>
    '''
    
    for h in holdings:
        pnl_class = 'positive-value' if h['pnl'] >= 0 else 'negative-value'
        pnl_pct = (h['pnl'] / (h['qty'] * h['avg']) * 100) if (h['qty'] * h['avg']) > 0 else 0
        html += f'''
                    <tr>
                        <td class="symbol-cell">{h['symbol']}</td>
                        <td>{h['qty']}</td>
                        <td>{format_currency(h['avg'])}</td>
                        <td>{format_currency(h['ltp'])}</td>
                        <td class="{pnl_class}">{format_currency(h['pnl'])} <br><small>({pnl_pct:+.2f}%)</small></td>
                    </tr>
        '''
    
    html += '''
                </tbody>
            </table>
        </div>
    </div>
    '''
    
    html += '</div>'  # Close PAGE 2
    
    # ==================== Individual Stock Analysis - Each stock gets 2 pages ====================
    for idx, h in enumerate(holdings):
        sym = h["symbol"]
        analysis = analyses.get(f"STOCK_{sym}", "Analysis unavailable.")
        
        # PAGE: Stock Chart
        html += '<div class="page">'
        html += f'''
        <div class="section">
            <div class="section-title">
                <span class="number">4.{idx + 1}</span>
                {sym} - Technical Chart Analysis
            </div>
            
            <div class="stock-card">
                <div class="stock-header">
                    <div class="stock-name">{sym}</div>
                </div>
                
                <div class="stock-metrics">
                    <div class="metric">
                        <div class="metric-label">Position</div>
                        <div class="metric-value">{h['qty']} shares</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Avg. Cost</div>
                        <div class="metric-value">{format_currency(h['avg'])}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Current Price</div>
                        <div class="metric-value">{format_currency(h['ltp'])}</div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Net P&L</div>
                        <div class="metric-value {'positive-value' if h['pnl'] >= 0 else 'negative-value'}">{format_currency(h['pnl'])}</div>
                    </div>
                </div>
        '''
        
        stock_chart = CHARTS_DIR / f"stock_analysis_{sym}.png"
        if stock_chart.exists():
            img_base64 = get_image_base64(stock_chart)
            if img_base64:
                html += f'''
                <div class="chart-container">
                    <img src="{img_base64}" alt="{sym} Technical Analysis">
                </div>
                '''
        else:
            html += '<p style="color: #64748b; text-align: center; padding: 40px;">Chart not available</p>'
        
        html += '''
            </div>
        </div>
        '''
        html += '</div>'  # Close chart page
        
        # PAGE: Stock Analysis Text
        html += '<div class="page">'
        html += f'''
        <div class="section">
            <div class="section-title">
                <span class="number">4.{idx + 1}</span>
                {sym} - Research & Analysis
            </div>
            
            <div class="stock-card">
                <div class="subsection-title">Comprehensive Investment Analysis</div>
                {format_analysis_content(analysis, is_mf=False)}
            </div>
        </div>
        '''
        html += '</div>'  # Close analysis page
    
    # ==================== Mutual Fund Analysis ====================
    if mfs:
        # PAGE: MF Summary & Chart
        html += '<div class="page">'
        
        html += '''
        <div class="section">
            <div class="section-title">
                <span class="number">5</span>
                Mutual Fund Portfolio Analysis
            </div>
        '''
        
        mf_chart = CHARTS_DIR / "mf_performance_overview.png"
        if mf_chart.exists():
            img_base64 = get_image_base64(mf_chart)
            if img_base64:
                html += f'''
                <div class="subsection-title">Performance Overview</div>
                <div class="chart-container">
                    <img src="{img_base64}" alt="Mutual Fund Performance Overview">
                </div>
                '''
        
        # MF Summary Table (Scheme-wise Holdings)
        html += '''
            <div class="subsection-title">Scheme-wise Holdings</div>
            <div class="table-container">
                <table>
                    <thead>
                        <tr>
                            <th>Scheme Name</th>
                            <th>Units</th>
                            <th>NAV</th>
                            <th>Current Value</th>
                            <th>Gain %</th>
                        </tr>
                    </thead>
                    <tbody>
        '''
        
        for m in mfs:
            gain_class = 'positive-value' if m['gain_pct'] >= 0 else 'negative-value'
            html += f'''
                        <tr>
                            <td class="symbol-cell" style="max-width: 400px; font-weight: 700;">{m['scheme_name']}</td>
                            <td>{m['units']:.2f}</td>
                            <td>{format_currency(m['nav'])}</td>
                            <td>{format_currency(m['value'])}</td>
                            <td class="{gain_class}" style="font-weight: 700;">{m['gain_pct']:.2f}%</td>
                        </tr>
            '''
            
        html += '''
                    </tbody>
                </table>
            </div>
        </div>
        '''
        html += '</div>'  # Close summary page
        
        # Each MF gets its own page
        for mf_idx, m in enumerate(mfs):
            html += '<div class="page">'
            
            scheme_name = m["scheme_name"]
            analysis = analyses.get(f"MF_{scheme_name}", "Analysis unavailable.")
            gain_class = 'positive-value' if m['gain_pct'] >= 0 else 'negative-value'
            
            html += f'''
            <div class="section">
                <div class="section-title">
                    <span class="number">5.{mf_idx + 1}</span>
                    {scheme_name}
                </div>
                
                <div class="stock-card">
                    <div class="stock-header">
                        <div class="stock-name" style="font-size: 16pt;">{scheme_name}</div>
                    </div>
                    
                    <div class="stock-metrics">
                        <div class="metric">
                            <div class="metric-label">Units</div>
                            <div class="metric-value">{m['units']:.2f}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">NAV</div>
                            <div class="metric-value">{format_currency(m['nav'])}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Market Value</div>
                            <div class="metric-value">{format_currency(m['value'])}</div>
                        </div>
                        <div class="metric">
                            <div class="metric-label">Gain</div>
                            <div class="metric-value {gain_class}">{m['gain_pct']:.2f}%</div>
                        </div>
                    </div>
                    
                    <div class="subsection-title">Fund Analysis</div>
                    {format_analysis_content(analysis, is_mf=True)}
                </div>
            </div>
            '''
            html += '</div>'  # Close MF page
    
    # ==================== Footer Page ====================
    html += '<div class="page">'
    html += '''
    <div class="footer">
        <p><strong>Disclaimer</strong></p>
        <p>This report is generated automatically and is for informational purposes only.</p>
        <p>Past performance does not guarantee future results. Please consult with a financial advisor before making investment decisions.</p>
        <p>All data is sourced from authorized brokers and market data providers.</p>
    </div>
    '''
    html += '</div>'
    
    return html


def convert_html_to_pdf(html_content, pdf_path):
    """Convert HTML to PDF using multiple methods"""
    
    # Method 1: Try xhtml2pdf (simplest, no external dependencies)
    try:
        from xhtml2pdf import pisa
        
        with open(pdf_path, "w+b") as pdf_file:
            pisa_status = pisa.CreatePDF(html_content, dest=pdf_file)
            
        if not pisa_status.err:
            print(f"✅ PDF generated successfully: {pdf_path}")
            return True
    except ImportError:
        print("⚠️ xhtml2pdf not installed. Trying next method...")
    except Exception as e:
        print(f"⚠️ xhtml2pdf failed: {e}")
    
    # Method 2: Try weasyprint
    try:
        from weasyprint import HTML, CSS
        HTML(string=html_content).write_pdf(pdf_path)
        print(f"✅ PDF generated successfully: {pdf_path}")
        return True
    except ImportError:
        print("⚠️ weasyprint not installed. Trying next method...")
    except Exception as e:
        print(f"⚠️ weasyprint failed: {e}")
    
    # Method 3: Try pdfkit
    try:
        import pdfkit
        options = {
            'encoding': 'UTF-8',
            'enable-local-file-access': None,
            'quiet': ''
        }
        pdfkit.from_string(html_content, pdf_path, options=options)
        print(f"✅ PDF generated successfully: {pdf_path}")
        return True
    except ImportError:
        print("⚠️ pdfkit not installed.")
    except Exception as e:
        print(f"⚠️ pdfkit failed: {e}")
    
    # All methods failed
    print("\n" + "="*60)
    print("❌ PDF CONVERSION FAILED - No suitable library found")
    print("="*60)
    print("\n📋 INSTALLATION OPTIONS (choose ONE):\n")
    print("1️⃣  EASIEST - xhtml2pdf (Pure Python, no dependencies):")
    print("   pip install xhtml2pdf")
    print("\n2️⃣  BEST QUALITY - weasyprint:")
    print("   pip install weasyprint")
    print("\n3️⃣  ALTERNATIVE - pdfkit (requires wkhtmltopdf):")
    print("   pip install pdfkit")
    print("   Download wkhtmltopdf: https://wkhtmltopdf.org/downloads.html")
    print("\n" + "="*60)
    print("💡 TIP: Use option 1 (xhtml2pdf) for quickest setup")
    print("="*60 + "\n")
    
    return False


async def main_async(send_email: bool = True):
    """Main async function - generates report from existing data."""
    print("🚀 Creating Professional Portfolio Report...")
    
    # Load Data
    data = load_data()
    if not data:
        print("\n❌ FAILED: Could not load portfolio data")
        return None

    agent = DeepAgent()
    analyses = {}

    # Parallel Processing Configuration
    CONCURRENCY_LIMIT = 5
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

    async def analyze_item_safe(key, name, type_label, details):
        """Analyze a single item with semaphore protection"""
        async with semaphore:
            print(f"   - Analyzing {name}...")
            try:
                result = await agent.analyze_asset(name, type_label, details)
                return key, result
            except Exception as e:
                print(f"     ❌ Failed {name}: {e}")
                return key, f"Error analyzing {name}: {str(e)}"

    # 1. Prepare Stock Tasks
    print(f"\n📦 Analyzing Equity Holdings (Parallel x{CONCURRENCY_LIMIT})...")
    stock_tasks = []
    for h in data.get("holdings", []):
        sym = h["symbol"]
        details = (
            f"Quantity: {h['qty']}, Average Price: ₹{h['avg']}, "
            f"Current Price: ₹{h['ltp']}, Total P&L: ₹{h['pnl']}"
        )
        stock_tasks.append(analyze_item_safe(f"STOCK_{sym}", sym, "Stock", details))

    # 2. Prepare MF Tasks
    print(f"\n🏦 Analyzing Mutual Funds (Parallel x{CONCURRENCY_LIMIT})...")
    mf_tasks = []
    for m in data.get("mutual_funds", []):
        scheme_name = m["scheme_name"]
        details = (
            f"Units: {m['units']}, NAV: ₹{m['nav']}, "
            f"Current Value: ₹{m['value']}, Gain: {m['gain_pct']}%"
        )
        mf_tasks.append(analyze_item_safe(f"MF_{scheme_name}", scheme_name, "Mutual Fund", details))

    # 3. Execute All Tasks concurrently
    all_tasks = stock_tasks + mf_tasks
    if all_tasks:
        results = await asyncio.gather(*all_tasks)
        analyses = dict(results)
    else:
        print("   ⚠️ No items to analyze.")

    # Generate HTML Report
    print("\n📝 Compiling Professional Report...")
    html_content = generate_html_content(data, analyses)
    full_html = get_html_template().replace("{CONTENT}", html_content)

    # Save HTML Report
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(full_html)

    # Save Markdown Report
    md_content = generate_markdown_content(data, analyses)
    with open(MD_REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"\n✅ HTML Report generated: {REPORT_FILE}")
    print(f"✅ Markdown Report generated: {MD_REPORT_FILE}")

    # Convert to PDF
    pdf_file = os.getenv("PORTFOLIO_REPORT_PDF_PATH", str(REPORT_FILE).replace(".html", ".pdf"))
    if not convert_html_to_pdf(full_html, pdf_file):
        print("   ⚠️ PDF conversion failed. HTML report available.")
        pdf_file = None

    # Email if requested
    if send_email and pdf_file:
        print("\n📧 Preparing Email...")
        try:
            # 1. Resolve Recipient Email (with fallback)
            user_email = data.get("profile", {}).get("email")
            if not user_email or user_email == "N/A":
                user_email = os.getenv("FALLBACK_EMAIL")
                print(f"   ℹ️ Using fallback email: {user_email}")
            
            # 2. Resolve User Name
            user_name = data.get("profile", {}).get("name", "Investor")
            if not user_name or user_name == "N/A":
                user_name = "Investor"
            
            if user_email and "@" in user_email:
                print(f"   - Sending to: {user_email}")
                
                subject = f"Your Investment Portfolio Analysis - {datetime.now().strftime('%B %d, %Y')}"
                
                body = f"""Dear {user_name},

Please find attached your comprehensive Investment Portfolio Analysis Report.

This document contains specialized insights into your current holdings, including:
- Portfolio Performance & Profitability Tracking
- Real-time Market Sentiment Analysis
- Detailed Research on your Equity Holdings
- Scheme-wise Analysis of your Mutual Fund Portfolio

Our AI-driven analysis is designed to provide you with technical clarity and actionable insights into your wealth trajectory.

Best Regards,
Project KiteInfi Mastery Team
"""
                
                send_email_with_attachment(
                    to_addr=user_email,
                    subject=subject,
                    body=body,
                    attachment_path=pdf_file,
                )
            else:
                msg = f"No valid email address found (Resolved: {user_email}). Could not send report."
                print(f"   ⚠️ {msg}")
                raise ValueError(msg)
        except Exception as e:
            print(f"   ❌ Email failed: {e}")
            raise e
    
    return full_html


def main():
    """Main entry point."""
    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(main_async())
        else:
            return loop.create_task(main_async())

    except KeyboardInterrupt:
        print("\n\n⚠️ Process interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()