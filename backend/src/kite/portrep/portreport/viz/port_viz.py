import io
import base64
import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import yfinance as yf
from PIL import Image, ImageDraw, ImageFont
import plotly.io as pio


from nse_vix import NseVixVisualizer


COLORS = {
    'primary': '#1F77B4',  # Blue
    'secondary': '#FF7F0E',  # Orange
    'positive': '#2CA02C',  # Green
    'negative': '#D62728',  # Red
    'neutral': '#7F7F7F',   # Gray
    'accent1': '#9467BD',   # Purple
    'accent2': '#8C564B',   # Brown
    'background': '#FFFFFF', # White background
    'text': '#333333'       # Dark gray
}


class PortfolioVisualizer:

    @staticmethod
    def generate_market_sentiment_dashboard(indices=None):
        """
        Generate a professional market sentiment dashboard.
        Includes major index performance (with points and percentage change),
        relative performance comparison, and Fear/Greed indicator.

        Args:
            indices (list): List of indices, default is NIFTY 50, SENSEX, BANKNIFTY, NIFTY MIDCAP 50, INDIA VIX.

        Returns:
            str: base64 encoded image
        """
        if indices is None:
            # NSE/BSE Indices
            indices = ['^NSEI', '^BSESN', '^NSEBANK', '^NSEMDCP50', '^INDIAVIX']

        end_date = datetime.now()
        # fetching 1 year data ensures we have enough data points even early in the year
        start_date = end_date - timedelta(days=365)  

        # Prepare data frames
        data_nifty = None
        data_sensex = None
        data_banknifty = None
        data_midcap = None
        data_vix = None

        print(f"📊 Fetching Indian market data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")

        # Fetch historical data for all indices
        for index in indices:
            ticker = yf.Ticker(index)
            try:
                hist = ticker.history(start=start_date, end=end_date)
                if not hist.empty:
                    print(f"✅ Retrieved {index} ({len(hist)} trading days)")
                    if index == '^NSEI':
                        data_nifty = hist
                    elif index == '^BSESN':
                        data_sensex = hist
                    elif index == '^NSEBANK':
                        data_banknifty = hist
                    elif index == '^NSEMDCP50':
                        data_midcap = hist
                    elif index == '^INDIAVIX':
                        data_vix = hist
                else:
                    print(f"⚠️ No data for {index}")
            except Exception as e:
                print(f"❌ Error retrieving {index}: {str(e)}")

        # Build dashboard using NseVixVisualizer
        interval = "1 Year"
        fig = NseVixVisualizer.create_dashboard(
            data_nifty=data_nifty,
            data_nifty_next50=data_banknifty,
            data_sensex=data_sensex,
            data_smallcap=data_midcap,
            data_vix=data_vix,
            interval=interval
        )


        # Convert to base64 image
        img_bytes = fig.to_image(format="png", width=1200, height=800, scale=2)
        encoded = base64.b64encode(img_bytes).decode('utf-8')

        return encoded


    @staticmethod
    def generate_portfolio_tracking(symbols=None):
        """
        Generate portfolio tracking report for Indian market (NSE)

        Args:
            symbols (list): List of NSE stock symbols

        Returns:
            str: base64 encoded image
        """
        if symbols is None:
            # Example NSE portfolio
            symbols = ['INFY.NS', 'TCS.NS', 'RELIANCE.NS', 'HDFCBANK.NS', 'ICICIBANK.NS']

        end_date = datetime.now()
        start_date = datetime(end_date.year, 1, 1)  # Year-to-date

        portfolio_data = {}
        colors = []
        ytd_changes = []

        for symbol in symbols:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(start=start_date, end=end_date)
            info = ticker.info
            name = info.get('shortName', symbol)

            if hist.empty or len(hist) < 2:
                print(f"⚠️ Not enough data for {symbol}")
                continue

            # Daily change
            current = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2]
            change_1d = (current - prev_close) / prev_close * 100

            # Monthly change (~22 trading days = 1 month)
            one_month_ago = max(0, len(hist) - 22)
            month_close = hist['Close'].iloc[one_month_ago]
            change_1mo = (current - month_close) / month_close * 100 if month_close > 0 else 0

            # YTD change
            first_close = hist['Close'].iloc[0]
            change_ytd = (current - first_close) / first_close * 100
            ytd_changes.append(change_ytd)

            # Performance color
            color = COLORS['positive'] if change_1d >= 0 else COLORS['negative']
            colors.append(color)

            # Market cap formatting
            market_cap = info.get('marketCap', 'N/A')
            if market_cap != 'N/A':
                market_cap = f"₹{market_cap/1e9:.2f}B"

            portfolio_data[symbol] = {
                'name': name,
                'current': current,
                'change_1d': change_1d,
                'change_1mo': change_1mo,
                'change_ytd': change_ytd,
                'market_cap': market_cap
            }

        # --- Portfolio Simulation ---
        dates = pd.date_range(start=start_date, end=end_date, freq='B')  # Business days
        initial_value = 100000  # Portfolio starts with ₹1,00,000

        avg_ytd_change = sum(ytd_changes) / len(ytd_changes) if ytd_changes else 0
        portfolio_values, benchmark_values = [], []

        for i in range(len(dates)):
            progress = i / (len(dates) - 1) if len(dates) > 1 else 0
            portfolio_value = initial_value * (1 + (avg_ytd_change/100) * progress)
            benchmark_value = initial_value * (1 + (avg_ytd_change/100) * 0.85 * progress)
            portfolio_values.append(portfolio_value)
            benchmark_values.append(benchmark_value)

        # --- Chart ---
        fig = make_subplots(
            rows=2, cols=1,
            vertical_spacing=0.1,
            row_heights=[0.6, 0.4],
            subplot_titles=("Portfolio Performance Chart", "YTD Performance Comparison")
        )

        # Portfolio line
        fig.add_trace(
            go.Scatter(
                x=dates, y=portfolio_values,
                name="Portfolio Value",
                mode='lines',
                line=dict(color='#1F77B4', width=4),
                fill='tozeroy',
                fillcolor='rgba(31, 119, 180, 0.2)'
            ),
            row=1, col=1
        )

        # Benchmark line
        fig.add_trace(
            go.Scatter(
                x=dates, y=benchmark_values,
                name="Nifty 50 (Benchmark)",
                mode='lines',
                line=dict(color='#FF7F0E', width=3, dash='dash')
            ),
            row=1, col=1
        )

        # Y-axis (₹)
        min_val, max_val = min(portfolio_values + benchmark_values), max(portfolio_values + benchmark_values)
        y_padding = (max_val - min_val) * 0.1
        fig.update_yaxes(title_text="Value (₹)", range=[min_val - y_padding, max_val + y_padding], row=1, col=1)
        fig.update_xaxes(title_text="Date", row=1, col=1)

        # YTD bar chart
        fig.add_trace(
            go.Bar(
                x=symbols, y=ytd_changes,
                marker_color=colors,
                text=[f"{v:.2f}%" for v in ytd_changes],
                textposition='auto',
                name="YTD Performance"
            ),
            row=2, col=1
        )

        # Add portfolio average line
        if ytd_changes:
            avg_ytd = sum(ytd_changes) / len(ytd_changes)
            fig.add_shape(
                type="line",
                x0=-0.5, y0=avg_ytd,
                x1=len(symbols)-0.5, y1=avg_ytd,
                line=dict(color="black", width=2, dash="dash"),
                row=2, col=1
            )
            fig.add_annotation(
                x=len(symbols)-0.5, y=avg_ytd,
                text=f"Portfolio Avg: {avg_ytd:.2f}%",
                showarrow=True, arrowhead=1,
                row=2, col=1
            )

        # Apply styling
        NseVixVisualizer.apply_common_style(fig, title="Portfolio Performance Tracker", height=900)

        # Add timestamp
        fig.add_annotation(
            text=f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            showarrow=False, xref="paper", yref="paper",
            x=0.01, y=0.01, font=dict(size=10, color=COLORS['neutral'])
        )

        # Export chart
        chart_bytes = fig.to_image(format="png", engine="kaleido", width=1200, height=900, scale=2)
        chart_img = Image.open(io.BytesIO(chart_bytes))

        # --- Portfolio Table ---
        table_fig = go.Figure()
        table_data, daily_colors, monthly_colors, ytd_colors = [], [], [], []

        for symbol, data in portfolio_data.items():
            table_data.append([
                f"{symbol}", data['name'],
                f"₹{data['current']:.2f}",
                f"{data['change_1d']:.2f}%",
                f"{data['change_1mo']:.2f}%",
                f"{data['change_ytd']:.2f}%",
                data['market_cap']
            ])
            daily_colors.append('green' if data['change_1d'] >= 0 else 'red')
            monthly_colors.append('green' if data['change_1mo'] >= 0 else 'red')
            ytd_colors.append('green' if data['change_ytd'] >= 0 else 'red')

        transposed_data = list(map(list, zip(*table_data)))
        table_fig.add_trace(
            go.Table(
                header=dict(
                    values=['Symbol', 'Name', 'Current Price', 'Daily', 'Monthly', 'YTD', 'Market Cap'],
                    line_color='white', fill_color=COLORS['primary'],
                    align='center', font=dict(color='white', size=12)
                ),
                cells=dict(
                    values=transposed_data,
                    line_color='white',
                    fill_color=[[COLORS['background'], '#E6F2FF'] * len(portfolio_data)],
                    align='center',
                    font=dict(color=[
                        [COLORS['text']] * len(portfolio_data),
                        [COLORS['text']] * len(portfolio_data),
                        [COLORS['text']] * len(portfolio_data),
                        daily_colors, monthly_colors, ytd_colors,
                        [COLORS['text']] * len(portfolio_data)
                    ], size=11),
                    height=30
                )
            )
        )

        table_fig.update_layout(
            title_text="Portfolio Details",
            title_font=dict(size=20, color=COLORS['text']),
            font=dict(size=12, color=COLORS['text']),
            paper_bgcolor=COLORS['background'],
            margin=dict(l=40, r=40, t=60, b=40),
            height=300
        )

        table_bytes = table_fig.to_image(format="png", engine="kaleido", width=1200, height=300, scale=2)
        table_img = Image.open(io.BytesIO(table_bytes))

        # --- Merge Chart + Table ---
        new_width = max(chart_img.width, table_img.width)
        new_height = chart_img.height + table_img.height
        new_img = Image.new('RGB', (new_width, new_height), (255, 255, 255))
        new_img.paste(chart_img, (0, 0))
        new_img.paste(table_img, (0, chart_img.height))

        draw = ImageDraw.Draw(new_img)
        draw.line([(0, chart_img.height), (new_width, chart_img.height)], fill="lightgray", width=2)

        buffer = io.BytesIO()
        new_img.save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode('ascii')

        return encoded

    @staticmethod
    def generate_stock_analysis(symbol='WIPRO.NS'):
        """
        Generate stock technical analysis chart
        
        Args:
            symbol (str): Stock symbol
        
        Returns:
            str: base64 encoded image
        """
        try:
            # Get stock data
            ticker = yf.Ticker(symbol)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=180)  # 6 months of data
            hist = ticker.history(start=start_date, end=end_date)
            
            if hist.empty:
                # If no data, return a message
                fig = go.Figure()
                fig.add_annotation(
                    text="No data available for this symbol",
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                    font=dict(size=24)
                )
                img_bytes = fig.to_image(format="png", engine="kaleido")
                encoded = base64.b64encode(img_bytes).decode('ascii')
                return encoded
        
            # Calculate technical indicators
            # 50-day and 200-day moving averages
            hist['MA50'] = hist['Close'].rolling(window=50).mean()
            hist['MA200'] = hist['Close'].rolling(window=200).mean()
            
            # Exponential Moving Averages
            hist['EMA20'] = hist['Close'].ewm(span=20, adjust=False).mean()
        
            # Relative Strength Index (RSI)
            delta = hist['Close'].diff()
            gain = delta.mask(delta < 0, 0)
            loss = -delta.mask(delta > 0, 0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            hist['RSI'] = 100 - (100 / (1 + rs))
            
            # MACD
            hist['EMA12'] = hist['Close'].ewm(span=12, adjust=False).mean()
            hist['EMA26'] = hist['Close'].ewm(span=26, adjust=False).mean()
            hist['MACD'] = hist['EMA12'] - hist['EMA26']
            hist['Signal'] = hist['MACD'].ewm(span=9, adjust=False).mean()
            hist['MACD_Hist'] = hist['MACD'] - hist['Signal']
        
            # Bollinger Bands
            hist['MA20'] = hist['Close'].rolling(window=20).mean()
            hist['Upper'] = hist['MA20'] + (hist['Close'].rolling(window=20).std() * 2)
            hist['Lower'] = hist['MA20'] - (hist['Close'].rolling(window=20).std() * 2)
        
            # Create a more comprehensive technical analysis dashboard
            fig = make_subplots(
                rows=4, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.06,
                row_heights=[0.6, 0.13, 0.13, 0.14],
                subplot_titles=(
                    "<b>Price Action & Technical Indicators</b>", 
                    "<b>Volume Analysis</b>", 
                    "<b>MACD Indicator</b>", 
                    "<b>Relative Strength Index (RSI)</b>"
                )
            )
            
            # Add candlestick chart with improved styling
            fig.add_trace(
                go.Candlestick(
                    x=hist.index,
                    open=hist['Open'],
                    high=hist['High'],
                    low=hist['Low'],
                    close=hist['Close'],
                    name="Price",
                    increasing=dict(line=dict(color=COLORS['positive'])),
                    decreasing=dict(line=dict(color=COLORS['negative']))
                ),
                row=1, col=1
            )
        
            # Add moving averages with improved styling
            fig.add_trace(
                go.Scatter(
                    x=hist.index,
                    y=hist['MA50'],
                    name="50-day MA",
                    line=dict(color='#2196F3', width=1.5)
                ),
                row=1, col=1
            )
        
            fig.add_trace(
                go.Scatter(
                    x=hist.index,
                    y=hist['MA200'],
                    name="200-day MA",
                    line=dict(color='#FF5722', width=1.5)
                ),
                row=1, col=1
            )
        
            fig.add_trace(
                go.Scatter(
                    x=hist.index,
                    y=hist['EMA20'],
                    name="20-day EMA",
                    line=dict(color='#673AB7', width=1.5, dash='dot')
                ),
                row=1, col=1
            )
            
            # Add Bollinger Bands with more professional styling
            fig.add_trace(
                go.Scatter(
                    x=hist.index,
                    y=hist['Upper'],
                    name="Upper Band",
                    line=dict(color='rgba(77, 208, 225, 0.8)', width=1),
                    fill=None
                ),
                row=1, col=1
            )
        
            fig.add_trace(
                go.Scatter(
                    x=hist.index,
                    y=hist['Lower'],
                    name="Lower Band",
                    line=dict(color='rgba(77, 208, 225, 0.8)', width=1),
                    fill='tonexty',
                    fillcolor='rgba(77, 208, 225, 0.15)'
                ),
                row=1, col=1
            )
        
            # Add volume chart with enhanced styling
            colors = [COLORS['positive'] if row['Close'] >= row['Open'] else COLORS['negative'] for i, row in hist.iterrows()]
            
            fig.add_trace(
                go.Bar(
                    x=hist.index,
                    y=hist['Volume'],
                    name="Volume",
                    marker=dict(
                        color=colors,
                        line=dict(color=colors, width=1)
                    ),
                    hovertemplate='<b>%{x}</b><br>Volume: %{y:,.0f}<extra></extra>'
                ),
                row=2, col=1
            )
        
            # Add MACD with enhanced styling
            fig.add_trace(
                go.Scatter(
                    x=hist.index,
                    y=hist['MACD'],
                    name="MACD",
                    line=dict(color='#2962FF', width=1.5)
                ),
                row=3, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=hist.index,
                    y=hist['Signal'],
                    name="Signal",
                    line=dict(color='#FF6D00', width=1.5)
                ),
                row=3, col=1
            )
            
            # Add MACD histogram
            histogram_colors = [COLORS['positive'] if val >= 0 else COLORS['negative'] for val in hist['MACD_Hist']]
            
            fig.add_trace(
                go.Bar(
                    x=hist.index,
                    y=hist['MACD_Hist'],
                    name="MACD Histogram",
                    marker=dict(color=histogram_colors),
                    hovertemplate='<b>%{x}</b><br>Histogram: %{y:.4f}<extra></extra>'
                ),
                row=3, col=1
            )
            
            # Add RSI with improved styling
            fig.add_trace(
                go.Scatter(
                    x=hist.index,
                    y=hist['RSI'],
                    name="RSI(14)",
                    line=dict(color='#9C27B0', width=1.5)
                ),
                row=4, col=1
            )
        
            # Add RSI reference lines with improved styling
            fig.add_trace(
                go.Scatter(
                    x=[hist.index[0], hist.index[-1]],
                    y=[70, 70],
                    name="Overbought (70)",
                    line=dict(color='rgba(213, 0, 0, 0.7)', width=1, dash='dash')
                ),
                row=4, col=1
            )
        
            fig.add_trace(
                go.Scatter(
                    x=[hist.index[0], hist.index[-1]],
                    y=[30, 30],
                    name="Oversold (30)",
                    line=dict(color='rgba(0, 200, 83, 0.7)', width=1, dash='dash')
                ),
                row=4, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=[hist.index[0], hist.index[-1]],
                    y=[50, 50],
                    name="Neutral (50)",
                    line=dict(color='rgba(117, 117, 117, 0.7)', width=1, dash='dot')
                ),
                row=4, col=1
            )
            
            # Calculate support and resistance levels with a more sophisticated approach
            recent_window = min(40, len(hist))
            recent_data = hist.iloc[-recent_window:]
            
            # Identify pivots, supports and resistances
            pivot_high = []
            pivot_low = []
            
            for i in range(2, len(recent_data) - 2):
                if (recent_data['High'].iloc[i] > recent_data['High'].iloc[i-1] and 
                    recent_data['High'].iloc[i] > recent_data['High'].iloc[i-2] and
                    recent_data['High'].iloc[i] > recent_data['High'].iloc[i+1] and
                    recent_data['High'].iloc[i] > recent_data['High'].iloc[i+2]):
                    pivot_high.append(recent_data['High'].iloc[i])
                    
                if (recent_data['Low'].iloc[i] < recent_data['Low'].iloc[i-1] and 
                    recent_data['Low'].iloc[i] < recent_data['Low'].iloc[i-2] and
                    recent_data['Low'].iloc[i] < recent_data['Low'].iloc[i+1] and
                    recent_data['Low'].iloc[i] < recent_data['Low'].iloc[i+2]):
                    pivot_low.append(recent_data['Low'].iloc[i])
            
            # Get most significant levels
            if len(pivot_high) > 0:
                resistance_level = max(pivot_high[-3:]) if len(pivot_high) >= 3 else max(pivot_high)
            else:
                resistance_level = recent_data['High'].max()
                
            if len(pivot_low) > 0:
                support_level = min(pivot_low[-3:]) if len(pivot_low) >= 3 else min(pivot_low)
            else:
                support_level = recent_data['Low'].min()
            
            # Add support and resistance levels with improved styling
            fig.add_shape(
                type="line",
                x0=hist.index[-recent_window],
                y0=support_level,
                x1=hist.index[-1],
                y1=support_level,
                line=dict(color="rgba(0, 200, 83, 0.8)", width=2, dash="dash"),
                row=1, col=1
            )
        
            fig.add_shape(
                type="line",
                x0=hist.index[-recent_window],
                y0=resistance_level,
                x1=hist.index[-1],
                y1=resistance_level,
                line=dict(color="rgba(213, 0, 0, 0.8)", width=2, dash="dash"),
                row=1, col=1
            )
        
            # Position resistance and support annotations to avoid overlapping
            # Always position resistance annotation ABOVE the resistance line
            # Always position support annotation BELOW the support line
            
            # Calculate positions - horizontal offset from the right edge
            date_range = (hist.index[-1] - hist.index[0]).days
            x_offset = hist.index[-1] - pd.Timedelta(days=int(date_range * 0.03))  # 3% from the right edge
            
            # Add support annotation (always positioned BELOW the line)
            fig.add_annotation(
                x=x_offset,  # Position slightly to the left of the right edge
                y=support_level,
                text=f"Support: ${support_level:.2f}",
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                arrowcolor="rgba(0, 200, 83, 0.8)",
                font=dict(size=12, color="rgba(0, 200, 83, 1)"),
                bordercolor="rgba(0, 200, 83, 0.8)",
                borderwidth=2,
                borderpad=4,
                bgcolor="rgba(255, 255, 255, 0.9)",
                standoff=5,  # Spacing between text and point
                # Ensure annotation is BELOW the support line
                yanchor="top",  # Anchor at top of text box
                ay=20,         # Positive value moves down
                axref="pixel",
                ayref="pixel",
                row=1, col=1
            )
        
            # Add resistance annotation (always positioned ABOVE the line)
            fig.add_annotation(
                x=x_offset,  # Position slightly to the left of the right edge
                y=resistance_level,
                text=f"Resistance: ${resistance_level:.2f}",
                showarrow=True,
                arrowhead=2,
                arrowsize=1,
                arrowwidth=2,
                arrowcolor="rgba(213, 0, 0, 0.8)",
                font=dict(size=12, color="rgba(213, 0, 0, 1)"),
                bordercolor="rgba(213, 0, 0, 0.8)",
                borderwidth=2,
                borderpad=4,
                bgcolor="rgba(255, 255, 255, 0.9)",
                standoff=5,  # Spacing between text and point
                # Ensure annotation is ABOVE the resistance line
                yanchor="bottom",  # Anchor at bottom of text box
                ay=-20,          # Negative value moves up
                axref="pixel",
                ayref="pixel",
                row=1, col=1
            )
        
            # Add price performance metrics
            current_price = hist['Close'].iloc[-1]
            change_1d = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100
            change_1wk = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-5]) / hist['Close'].iloc[-5]) * 100 if len(hist) >= 5 else 0
            change_1mo = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-21]) / hist['Close'].iloc[-21]) * 100 if len(hist) >= 21 else 0
            change_3mo = ((hist['Close'].iloc[-1] - hist['Close'].iloc[-63]) / hist['Close'].iloc[-63]) * 100 if len(hist) >= 63 else 0
            
            perf_color = COLORS['positive'] if change_1d >= 0 else COLORS['negative']
            
            # Get stock information
            info = ticker.info
            stock_name = info.get('shortName', symbol)
            
            # Update layout with comprehensive info
            NseVixVisualizer.apply_common_style(
                fig, 
                title=f"<b>{stock_name} ({symbol}) Technical Analysis</b><br>" +
                    f"<span style='font-size:0.8em;'>Current: ${current_price:.2f} " +
                    f"<span style='color:{perf_color}'>({'+' if change_1d >= 0 else ''}{change_1d:.2f}%)</span> | " +
                    f"1W: <span style='color:{'green' if change_1wk >= 0 else 'red'}'>{change_1wk:.2f}%</span> | " +
                    f"1M: <span style='color:{'green' if change_1mo >= 0 else 'red'}'>{change_1mo:.2f}%</span> | " +
                    f"3M: <span style='color:{'green' if change_3mo >= 0 else 'red'}'>{change_3mo:.2f}%</span></span>",
                height=1050
            )
            
            # Move legend and set a more generous margin
            fig.update_layout(
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=0.96,
                    xanchor="center",
                    x=0.5
                ),
                margin=dict(t=130),
                title=dict(
                    y=0.98,
                    yanchor="top",
                    pad=dict(b=15)
                )
            )
            
            # Adjust subplot title positions
            for i in range(len(fig.layout.annotations)):
                fig.layout.annotations[i].y = fig.layout.annotations[i].y + 0.02
            
            # Configure subplot-specific settings
            fig.update_xaxes(
                rangeslider_visible=False,
                rangebreaks=[
                    # hide weekends
                    dict(bounds=["sat", "mon"])
                ]
            )
            
            # Configure RSI y-axis range
            fig.update_yaxes(range=[0, 100], row=4, col=1)
            
            # Add grid lines to all subplots
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="rgba(211, 211, 211, 0.3)")
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="rgba(211, 211, 211, 0.3)")
            
            # Enhanced interactivity
            fig.update_layout(hovermode="x unified")
            
            # Add timestamp
            fig.add_annotation(
                text=f"<i>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>",
                showarrow=False,
                xref="paper",
                yref="paper",
                x=0.01,
                y=0.01,
                font=dict(size=10, color=COLORS['neutral'])
            )
            
            # Convert to base64 image with higher quality
            img_bytes = fig.to_image(format="png", engine="kaleido", width=1200, height=1000, scale=2)
            encoded = base64.b64encode(img_bytes).decode('ascii')
            return encoded
            
        except Exception as e:
            # Log the actual error
            print(f"Error generating analysis for {symbol}: {e}")
            
            # Create a simple error message chart if anything goes wrong
            fig = go.Figure()
            
            fig.add_annotation(
                text=f"Error generating analysis for {symbol}",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
                font=dict(size=20, color="red")
            )
            
            fig.add_annotation(
                text=f"Please try again later",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.4,
                showarrow=False,
                font=dict(size=16)
            )
            
            fig.update_layout(
                paper_bgcolor=COLORS['background'],
                plot_bgcolor=COLORS['background'],
                height=800,
                width=1000
            )
            
            img_bytes = fig.to_image(format="png", engine="kaleido")
            encoded = base64.b64encode(img_bytes).decode('ascii')
            # Re-raise the exception to make tests fail
            raise e
        
        return encoded 