import json
import asyncio
from datetime import datetime
from pathlib import Path

from src.kite.portrep.portreport.deepagent import DeepAgent
from src.kite.portrep.portreport.emailer import send_email_with_attachment

import os
import base64
from dotenv import load_dotenv

load_dotenv(override=True)

# File Paths
SCRIPT_DIR = Path(__file__).parent
# Project root is 4 levels up from src/kite/portrep/portreport/
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent.parent

# Use environment variables with sensible defaults
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


def format_analysis_content(analysis_text):
    """Format analysis text into professional structure with headings and bullet points"""
    
    if not analysis_text or "Error" in analysis_text or "unavailable" in analysis_text:
        return f'<div class="analysis-box"><p style="color: #64748b; font-style: italic;">{analysis_text}</p></div>'
    
    # Remove markdown headers and clean text
    analysis_text = analysis_text.replace('###', '').replace('##', '').strip()
    
    # Define section patterns to look for
    section_patterns = {
        'Investment Verdict': ['Investment Verdict', 'investment verdict', 'Verdict', 'Rating'],
        'Financial Health Assessment': ['Financial Health', 'Financial Assessment', 'financial health', 'financial metrics'],
        'Key Catalysts & Risks': ['Catalyst', 'Risk', 'catalyst', 'risk', 'Key Catalysts'],
        'Position Analysis': ['Position Analysis', 'position analysis', 'Position Review', 'client\'s current position'],
        'Outlook': ['Outlook', 'outlook', 'Forecast', 'forecast', '12-month', 'projection']
    }
    
    # Parse sections
    sections = {}
    current_section = None
    current_content = []
    
    # Split into sentences
    sentences = []
    for part in analysis_text.replace('. ', '.|').split('|'):
        part = part.strip()
        if len(part) > 15:  # Minimum sentence length
            sentences.append(part)
    
    # Assign sentences to sections
    for sentence in sentences:
        sentence = sentence.strip()
        
        # Check if this sentence starts a new section
        section_found = False
        for section_name, patterns in section_patterns.items():
            for pattern in patterns:
                if pattern.lower() in sentence.lower():
                    # Save previous section
                    if current_section and current_content:
                        if current_section not in sections:
                            sections[current_section] = []
                        sections[current_section].extend(current_content)
                    
                    # Start new section
                    current_section = section_name
                    current_content = []
                    section_found = True
                    
                    # Add remaining text from this sentence if it has content after the pattern
                    remaining = sentence[sentence.lower().index(pattern.lower()) + len(pattern):].strip()
                    if remaining and len(remaining) > 10:
                        current_content.append(remaining)
                    break
            if section_found:
                break
        
        # If no section header found, add to current section
        if not section_found and sentence:
            if current_section:
                current_content.append(sentence)
            else:
                # If no section yet, start with Investment Verdict
                current_section = 'Investment Verdict'
                current_content.append(sentence)
    
    # Save last section
    if current_section and current_content:
        if current_section not in sections:
            sections[current_section] = []
        sections[current_section].extend(current_content)
    
    # Build formatted HTML
    html = '<div class="analysis-container">'
    
    # Define section order and styling
    section_order = ['Investment Verdict', 'Financial Health Assessment', 'Key Catalysts & Risks', 'Position Analysis', 'Outlook']
    section_colors = {
        'Investment Verdict': '#10b981',
        'Financial Health Assessment': '#3b82f6',
        'Key Catalysts & Risks': '#f59e0b',
        'Position Analysis': '#8b5cf6',
        'Outlook': '#06b6d4'
    }
    section_icons = {
        'Investment Verdict': '📊',
        'Financial Health Assessment': '💰',
        'Key Catalysts & Risks': '⚠️',
        'Position Analysis': '📈',
        'Outlook': '🔮'
    }
    
    for section_name in section_order:
        if section_name not in sections or not sections[section_name]:
            continue
        
        content = sections[section_name]
        color = section_colors.get(section_name, '#3b82f6')
        icon = section_icons.get(section_name, '•')
        
        html += f'''
        <div class="analysis-section" style="border-left-color: {color};">
            <div class="analysis-section-title" style="color: {color};">
                <span class="analysis-icon">{icon}</span>
                {section_name}
            </div>
            <div class="analysis-content">
                <ul class="analysis-list">
        '''
        
        for sentence in content:
            sentence = sentence.strip()
            if not sentence:
                continue
            
            # Ensure proper punctuation
            if not sentence.endswith(('.', '!', '?', '%')):
                sentence += '.'
            
            # Highlight keywords
            sentence = highlight_keywords(sentence)
            html += f'<li>{sentence}</li>'
        
        html += '''
                </ul>
            </div>
        </div>
        '''
    
    html += '</div>'
    return html


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
    """Returns professional HTML template with CSS styling optimized for PDF"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Investment Portfolio Analysis Report</title>
    <style>
        @page {
            size: A4;
            margin: 2cm;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Arial', 'Helvetica', sans-serif;
            line-height: 1.6;
            color: #1a1a1a;
            background: #ffffff;
            font-size: 11pt;
        }
        
        .page {
            background: white;
            padding: 20px;
            page-break-after: always;
        }
        
        .page:last-child {
            page-break-after: auto;
        }
        
        /* Header Styles */
        .header {
            border-bottom: 4px solid #2563eb;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 28pt;
            font-weight: bold;
            color: #1e3a8a;
            margin-bottom: 8px;
        }
        
        .header .subtitle {
            font-size: 11pt;
            color: #64748b;
        }
        
        /* Section Styles */
        .section {
            margin-bottom: 30px;
        }
        
        .section-title {
            font-size: 18pt;
            font-weight: bold;
            color: #1e3a8a;
            margin-bottom: 15px;
            padding-bottom: 8px;
            border-bottom: 2px solid #e2e8f0;
            display: table;
            width: 100%;
        }
        
        .section-title .number {
            display: inline-block;
            width: 35px;
            height: 35px;
            background: #2563eb;
            color: white;
            border-radius: 6px;
            text-align: center;
            line-height: 35px;
            font-size: 16pt;
            font-weight: bold;
            margin-right: 10px;
            float: left;
        }
        
        .subsection-title {
            font-size: 14pt;
            font-weight: bold;
            color: #334155;
            margin: 20px 0 12px 0;
        }
        
        /* Profile Card */
        .profile-card {
            background: #667eea;
            border-radius: 8px;
            padding: 20px;
            color: white;
            margin-bottom: 25px;
        }
        
        .profile-grid {
            display: table;
            width: 100%;
        }
        
        .profile-item {
            display: table-cell;
            width: 50%;
            padding: 8px;
            vertical-align: top;
        }
        
        .profile-label {
            font-size: 9pt;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            opacity: 0.9;
            margin-bottom: 4px;
            font-weight: bold;
        }
        
        .profile-value {
            font-size: 12pt;
            font-weight: bold;
        }
        
        /* Stats Cards */
        .stats-container {
            display: table;
            width: 100%;
            margin: 20px 0;
        }
        
        .stat-card {
            display: table-cell;
            width: 33.33%;
            background: #f8fafc;
            border-radius: 8px;
            padding: 15px;
            border-left: 4px solid #2563eb;
            margin: 0 5px;
        }
        
        .stat-card.positive {
            border-left-color: #10b981;
        }
        
        .stat-card.negative {
            border-left-color: #ef4444;
        }
        
        .stat-label {
            font-size: 9pt;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
            font-weight: bold;
        }
        
        .stat-value {
            font-size: 20pt;
            font-weight: bold;
            color: #1e293b;
        }
        
        .stat-change {
            font-size: 11pt;
            margin-top: 4px;
            font-weight: bold;
        }
        
        .stat-change.positive {
            color: #10b981;
        }
        
        .stat-change.negative {
            color: #ef4444;
        }
        
        /* Tables */
        .table-container {
            margin: 15px 0;
            border-radius: 8px;
            overflow: hidden;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            background: white;
            border: 1px solid #e2e8f0;
        }
        
        thead {
            background: #1e40af;
            color: white;
        }
        
        th {
            padding: 12px 10px;
            text-align: left;
            font-weight: bold;
            font-size: 10pt;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        td {
            padding: 10px;
            border-bottom: 1px solid #e2e8f0;
            font-size: 10pt;
        }
        
        tbody tr:last-child td {
            border-bottom: none;
        }
        
        .symbol-cell {
            font-weight: bold;
            color: #1e40af;
            font-size: 11pt;
        }
        
        .positive-value {
            color: #10b981;
            font-weight: bold;
        }
        
        .negative-value {
            color: #ef4444;
            font-weight: bold;
        }
        
        /* Stock Analysis Card */
        .stock-card {
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 25px;
            border: 1px solid #e2e8f0;
            border-top: 4px solid #2563eb;
        }
        
        .stock-header {
            padding-bottom: 12px;
            border-bottom: 2px solid #e2e8f0;
            margin-bottom: 15px;
        }
        
        .stock-name {
            font-size: 16pt;
            font-weight: bold;
            color: #1e3a8a;
        }
        
        .stock-metrics {
            display: table;
            width: 100%;
            margin-bottom: 15px;
        }
        
        .metric {
            display: table-cell;
            width: 25%;
            background: #f8fafc;
            padding: 10px;
            border-radius: 6px;
            margin: 0 2px;
        }
        
        .metric-label {
            font-size: 8pt;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
            font-weight: bold;
        }
        
        .metric-value {
            font-size: 12pt;
            font-weight: bold;
            color: #1e293b;
        }
        
        .chart-container {
            margin: 15px 0;
            text-align: center;
        }
        
        .chart-container img {
            max-width: 100%;
            height: auto;
            border-radius: 6px;
            border: 1px solid #e2e8f0;
        }
        
        /* Info Box */
        .info-box {
            background: #eff6ff;
            border-left: 4px solid #3b82f6;
            padding: 15px;
            border-radius: 6px;
            margin: 15px 0;
        }
        
        .info-box p {
            margin-bottom: 8px;
            color: #1e40af;
            font-size: 10pt;
            line-height: 1.6;
        }
        
        .info-box strong {
            color: #1e3a8a;
            font-weight: bold;
        }
        
        /* Analysis Container Styles */
        .analysis-container {
            margin-top: 15px;
        }
        
        .analysis-section {
            background: #ffffff;
            border-left: 4px solid #3b82f6;
            border-radius: 6px;
            padding: 15px;
            margin-bottom: 15px;
            border: 1px solid #e2e8f0;
        }
        
        .analysis-section-title {
            font-size: 12pt;
            font-weight: bold;
            color: #1e40af;
            margin-bottom: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .analysis-icon {
            font-size: 14pt;
            margin-right: 8px;
        }
        
        .analysis-content {
            color: #334155;
            line-height: 1.7;
        }
        
        .analysis-list {
            list-style: none;
            padding-left: 0;
            margin: 0;
        }
        
        .analysis-list li {
            padding: 8px 0 8px 25px;
            position: relative;
            border-bottom: 1px solid #f1f5f9;
            font-size: 10pt;
            line-height: 1.6;
        }
        
        .analysis-list li:last-child {
            border-bottom: none;
        }
        
        .analysis-list li:before {
            content: "▸";
            position: absolute;
            left: 8px;
            color: #3b82f6;
            font-weight: bold;
        }
        
        /* Keyword Highlighting */
        .buy-tag, .accumulate-tag {
            background: #d1fae5;
            color: #065f46;
            padding: 2px 6px;
            border-radius: 3px;
            font-weight: bold;
            font-size: 10pt;
        }
        
        .sell-tag {
            background: #fee2e2;
            color: #991b1b;
            padding: 2px 6px;
            border-radius: 3px;
            font-weight: bold;
            font-size: 10pt;
        }
        
        .hold-tag {
            background: #fef3c7;
            color: #92400e;
            padding: 2px 6px;
            border-radius: 3px;
            font-weight: bold;
            font-size: 10pt;
        }
        
        .positive-keyword {
            color: #059669;
            font-weight: bold;
        }
        
        .negative-keyword {
            color: #dc2626;
            font-weight: bold;
        }
        
        /* Footer */
        .footer {
            text-align: center;
            padding: 20px;
            color: #64748b;
            font-size: 9pt;
            border-top: 2px solid #e2e8f0;
            margin-top: 30px;
        }
        
        .footer p {
            margin: 5px 0;
        }
        
        /* Print specific fixes */
        @media print {
            body {
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }
            
            .page {
                page-break-after: always;
            }
            
            .stock-card, .analysis-section {
                page-break-inside: avoid;
            }
        }
    </style>
</head>
<body>
{CONTENT}
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
    """Generate HTML content with professional styling"""
    profile = data.get("profile", {})
    holdings = data.get("holdings", [])
    mfs = data.get("mutual_funds", [])
    timestamp = data.get("timestamp", datetime.now().strftime("%B %d, %Y at %I:%M %p"))

    # Calculate totals
    total_investment = sum(h["qty"] * h["avg"] for h in holdings)
    current_value = sum(h["qty"] * h["ltp"] for h in holdings)
    total_pnl = sum(h["pnl"] for h in holdings)
    pnl_pct = (total_pnl / total_investment * 100) if total_investment > 0 else 0

    html = '<div class="page">'
    
    # Header
    html += f'''
    <div class="header">
        <h1>Investment Portfolio Analysis Report</h1>
        <div class="subtitle">Generated on {timestamp}</div>
    </div>
    '''
    
    # Section 1: Client Profile
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
    
    # Section 2: Market Sentiment
    html += '''
    <div class="section">
        <div class="section-title">
            <span class="number">2</span>
            Market Sentiment Dashboard
        </div>
        <p style="color: #64748b; margin-bottom: 20px;">Current Indian market overview with major indices performance and sentiment analysis.</p>
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
    
    html += '</div><div class="page">'  # Page break
    
    # Section 3: Portfolio Overview
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
            </div>
            <div class="stat-card">
                <div class="stat-label">Current Value</div>
                <div class="stat-value">{format_currency(current_value)}</div>
            </div>
            <div class="stat-card {pnl_class}">
                <div class="stat-label">Total P&L</div>
                <div class="stat-value">{format_currency(total_pnl)}</div>
                <div class="stat-change {pnl_class}">{pnl_pct:+.2f}%</div>
            </div>
        </div>
    '''
    
    portfolio_chart = CHARTS_DIR / "portfolio_performance_tracker.png"
    if portfolio_chart.exists():
        img_base64 = get_image_base64(portfolio_chart)
        if img_base64:
            html += f'''
            <div class="subsection-title">Portfolio Performance Chart</div>
            <p style="color: #64748b; margin-bottom: 15px;">Year-to-date performance tracking of your equity holdings with benchmark comparison.</p>
            <div class="chart-container">
                <img src="{img_base64}" alt="Portfolio Performance Tracker">
            </div>
            '''
    
    # Holdings Table
    html += '''
        <div class="subsection-title">Holdings Summary</div>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Symbol</th>
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
        html += f'''
                    <tr>
                        <td class="symbol-cell">{h['symbol']}</td>
                        <td>{h['qty']}</td>
                        <td>{format_currency(h['avg'])}</td>
                        <td>{format_currency(h['ltp'])}</td>
                        <td class="{pnl_class}">{format_currency(h['pnl'])}</td>
                    </tr>
        '''
    
    html += '''
                </tbody>
            </table>
        </div>
    </div>
    '''
    
    html += '</div>'  # Close page
    
    # Section 4: Individual Stock Analysis
    for idx, h in enumerate(holdings):
        if idx % 2 == 0:
            html += '<div class="page">'
        
        sym = h["symbol"]
        analysis = analyses.get(f"STOCK_{sym}", "Analysis unavailable.")
        
        html += f'''
        <div class="section">
            <div class="section-title">
                <span class="number">4.{idx + 1}</span>
                {sym} - Detailed Analysis
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
        
        html += f'''
                <div class="subsection-title">Research & Analysis</div>
                {format_analysis_content(analysis)}
            </div>
        </div>
        '''
        
        if idx % 2 == 1 or idx == len(holdings) - 1:
            html += '</div>'  # Close page
    
    # Section 5: Mutual Fund Analysis
    html += '<div class="page">'
    
    html += '''
    <div class="section">
        <div class="section-title">
            <span class="number">5</span>
            Mutual Fund Portfolio Analysis
        </div>
    '''
    
    if not mfs:
        html += '<p style="color: #64748b;">No mutual fund holdings found.</p>'
    else:
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
        
        html += '<div class="subsection-title">Detailed Fund Analysis</div>'
        
        for m in mfs:
            scheme_name = m["scheme_name"]
            analysis = analyses.get(f"MF_{scheme_name}", "Analysis unavailable.")
            gain_class = 'positive-value' if m['gain_pct'] >= 0 else 'negative-value'
            
            html += f'''
            <div class="stock-card">
                <div class="stock-header">
                    <div class="stock-name">{scheme_name}</div>
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
                
                {format_analysis_content(analysis)}
            </div>
            '''
    
    html += '''
    </div>
    
    <div class="footer">
        <p>This report is generated automatically and is for informational purposes only.</p>
        <p>Past performance does not guarantee future results. Please consult with a financial advisor before making investment decisions.</p>
    </div>
    '''
    
    html += '</div>'  # Close final page
    
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
    CONCURRENCY_LIMIT = 5  # Adjust based on rate limits/keys
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

    async def analyze_item_safe(key, name, type_label, details):
        """Analyze a single item with semaphore protection"""
        async with semaphore:
            print(f"   - Analyzing {name}...")
            try:
                # DeepAgent is now async, no need for asyncio.to_thread
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

    # 2. Prepare MD Tasks
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
            user_email = data.get("profile", {}).get("email")
            if user_email:
                print(f"   - Sending to: {user_email}")
                send_email_with_attachment(
                    to_addr=user_email,
                    subject=f"Portfolio Analysis Report - {datetime.now().strftime('%Y-%m-%d')}",
                    body=(
                        "Please find attached your detailed portfolio analysis report "
                        "with market insights and comprehensive analysis."
                    ),
                    attachment_path=pdf_file,
                )
            else:
                print("   ⚠️ No email found in profile. Skipping email.")
        except Exception as e:
            print(f"   ❌ Email failed: {e}")
            import traceback
            traceback.print_exc()
    
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


    