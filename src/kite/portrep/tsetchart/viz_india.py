import yfinance as yf
import base64
from datetime import datetime
# from mcp_yahoo_finance.visualization import create_dashboard  # Assuming you have this function

def generate_indian_market_sentiment_dashboard(indices=None):
    """
    Generate a professional Indian market sentiment dashboard.
    Includes major index performance, relative performance comparison, and Fear/Greed indicator.
    
    Args:
        indices (list): List of indices, default is Nifty 50, BSE Sensex, Nifty IT, India VIX.
    
    Returns:
        str: base64 encoded image
    """
    # Default Indian indices
    if indices is None:
        indices = ['^NSEI', '^BSESN', '^CNXIT', '^INDIAVIX']
    
    # --- Data Fetching ---
    end_date = datetime.now()
    start_date = datetime(end_date.year, 1, 1)  # Year-to-Date

    # Prepare empty dataframes for each index
    data_nifty = None
    data_sensex = None
    data_it = None
    data_vix = None

    print(f"Fetching Indian market data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")
    
    for index in indices:
        ticker = yf.Ticker(index)
        try:
            hist = ticker.history(start=start_date, end=end_date)
            if not hist.empty:
                print(f"Retrieved {index} data, {len(hist)} trading days")
                if index == '^NSEI':
                    data_nifty = hist
                elif index == '^BSESN':
                    data_sensex = hist
                elif index == '^CNXIT':
                    data_it = hist
                elif index == '^INDIAVIX':
                    data_vix = hist
            else:
                print(f"Warning: No data for {index}")
        except Exception as e:
            print(f"Error fetching {index}: {str(e)}")

    # --- Dashboard Creation ---
    interval = "YTD"  # Year-to-Date
    fig = create_dashboard(
        data_sp500=data_nifty,   # Using same function, but rename variable for Indian context
        data_nasdaq=data_it,
        data_dji=data_sensex,
        data_rut=None,           # Optional: add more indices if needed
        data_vix=data_vix,
        interval=interval
    )

    # --- Convert to Image & Encode ---
    img_bytes = fig.to_image(format="png", width=1200, height=800, scale=2)
    encoded = base64.b64encode(img_bytes).decode('utf-8')
    
    return encoded



def generate_portfolio_tracking_india(symbols=None):
    """
    Generate portfolio tracking report for Indian market
    
    Args:
        symbols (list): List of NSE stock symbols (Yahoo Finance format: RELIANCE.NS)
    
    Returns:
        str: base64 encoded image
    """
    if symbols is None:
        symbols = ['RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'HDFCBANK.NS', 'ICICIBANK.NS']
    
    # Get stock data
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
        
        if hist.empty:
            print(f"Warning: No data for {symbol}")
            continue
        
        # Calculate price changes
        current = hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current
        change_1d = (current - prev_close) / prev_close * 100
        
        # Monthly change (~22 trading days)
        one_month_ago = max(0, len(hist) - 22)
        month_close = hist['Close'].iloc[one_month_ago] if one_month_ago < len(hist) else current
        change_1mo = (current - month_close) / month_close * 100
        
        # Year-to-date change
        first_close = hist['Close'].iloc[0]
        change_ytd = (current - first_close) / first_close * 100
        ytd_changes.append(change_ytd)
        
        # Set color based on daily performance
        color = COLORS['positive'] if change_1d >= 0 else COLORS['negative']
        colors.append(color)
        
        # Market cap
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
    
    # Create figure with 2 subplots
    fig = make_subplots(
        rows=2, cols=1,
        vertical_spacing=0.1,
        row_heights=[0.6, 0.4],
        subplot_titles=(
            "<b>Portfolio Performance Chart</b>", 
            "<b>YTD Performance Comparison</b>"
        )
    )
    
    # Simulate portfolio values
    dates = pd.date_range(start=start_date, end=end_date, freq='B')
    initial_value = 100000  # Indian portfolio initial value in INR
    
    avg_ytd_change = sum(ytd_changes)/len(ytd_changes) if ytd_changes else 0
    portfolio_values = [initial_value * (1 + (avg_ytd_change/100) * i/(len(dates)-1)) for i in range(len(dates))]
    
    # Benchmark: Nifty 50
    nifty = yf.Ticker("^NSEI")
    hist_nifty = nifty.history(start=start_date, end=end_date)
    if not hist_nifty.empty:
        start_nifty = hist_nifty['Close'].iloc[0]
        end_nifty = hist_nifty['Close'].iloc[-1]
        nifty_change = ((end_nifty - start_nifty)/start_nifty) * 100
        benchmark_values = [initial_value * (1 + (nifty_change/100) * i/(len(dates)-1)) for i in range(len(dates))]
    else:
        benchmark_values = portfolio_values
    
    # Portfolio line
    fig.add_trace(go.Scatter(
        x=dates, y=portfolio_values,
        name="Portfolio Value",
        mode='lines',
        line=dict(color=COLORS['primary'], width=4),
        fill='tozeroy',
        fillcolor='rgba(31, 119, 180, 0.2)'
    ), row=1, col=1)
    
    # Benchmark line
    fig.add_trace(go.Scatter(
        x=dates, y=benchmark_values,
        name="Nifty 50",
        mode='lines',
        line=dict(color=COLORS['secondary'], width=3, dash='dash')
    ), row=1, col=1)
    
    # YTD performance bar chart
    fig.add_trace(go.Bar(
        x=list(portfolio_data.keys()),
        y=ytd_changes,
        marker_color=colors,
        text=[f"{v:.2f}%" for v in ytd_changes],
        textposition='auto',
        name="YTD Performance"
    ), row=2, col=1)
    
    # Average line
    avg_ytd = sum(ytd_changes)/len(ytd_changes) if ytd_changes else 0
    fig.add_shape(type="line", x0=-0.5, y0=avg_ytd, x1=len(symbols)-0.5, y1=avg_ytd,
                  line=dict(color="black", width=2, dash="dash"), row=2, col=1)
    fig.add_annotation(x=len(symbols)-0.5, y=avg_ytd, text=f"Portfolio Avg: {avg_ytd:.2f}%", showarrow=True, row=2, col=1)
    
    # Apply common style
    apply_common_style(fig, title=f"<b>Indian Portfolio Tracker</b><br><span style='font-size:0.8em;'>YTD Return: {avg_ytd:.2f}%</span>", height=900)
    
    # Timestamp
    fig.add_annotation(text=f"<i>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>",
                       showarrow=False, xref="paper", yref="paper", x=0.01, y=0.01,
                       font=dict(size=10, color=COLORS['neutral']))
    
    # Convert chart to image
    chart_bytes = fig.to_image(format="png", engine="kaleido", width=1200, height=900, scale=2)
    chart_img = Image.open(io.BytesIO(chart_bytes))
    
    # Create table
    table_fig = go.Figure()
    table_data = []
    daily_colors = []
    monthly_colors = []
    ytd_colors = []
    
    for symbol, data in portfolio_data.items():
        table_data.append([
            f"<b>{symbol}</b>", data['name'], f"₹{data['current']:.2f}",
            f"{data['change_1d']:.2f}%", f"{data['change_1mo']:.2f}%",
            f"{data['change_ytd']:.2f}%", data['market_cap']
        ])
        daily_colors.append('green' if data['change_1d'] >= 0 else 'red')
        monthly_colors.append('green' if data['change_1mo'] >= 0 else 'red')
        ytd_colors.append('green' if data['change_ytd'] >= 0 else 'red')
    
    transposed_data = list(map(list, zip(*table_data)))
    
    table_fig.add_trace(go.Table(
        header=dict(values=['Symbol', 'Name', 'Current Price', 'Daily', 'Monthly', 'YTD', 'Market Cap'],
                    fill_color=COLORS['primary'], font=dict(color='white', size=12), align='center'),
        cells=dict(values=transposed_data,
                   fill_color=[[COLORS['background'], '#E6F2FF']*len(portfolio_data)],
                   font=dict(color=[['black']*len(portfolio_data)]*7, size=11),
                   align='center', height=30)
    ))
    
    table_fig.update_layout(height=300, margin=dict(l=40, r=40, t=60, b=40), paper_bgcolor=COLORS['background'])
    
    # Combine chart + table
    table_bytes = table_fig.to_image(format="png", engine="kaleido", width=1200, height=300, scale=2)
    table_img = Image.open(io.BytesIO(table_bytes))
    
    new_img = Image.new('RGB', (chart_img.width, chart_img.height + table_img.height), (255, 255, 255))
    new_img.paste(chart_img, (0,0))
    new_img.paste(table_img, (0, chart_img.height))
    draw = ImageDraw.Draw(new_img)
    draw.line([(0, chart_img.height), (chart_img.width, chart_img.height)], fill="lightgray", width=2)
    
    buffer = io.BytesIO()
    new_img.save(buffer, format="PNG")
    encoded = base64.b64encode(buffer.getvalue()).decode('ascii')
    
    return encoded




def generate_stock_analysis(symbol='TSLA'):
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
        apply_common_style(
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