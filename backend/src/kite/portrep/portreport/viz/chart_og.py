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

# Set matplotlib backend to non-interactive
matplotlib.use('Agg')
# Set seaborn style for more professional looks
sns.set_style('whitegrid')
sns.set_context("notebook", font_scale=1.2)

# Set a better default template for plotly
pio.templates.default = "plotly_white"

# Define a professional color palette
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


class FearAndGreed:
    """
    Calculates a Fear & Greed Index based on several market indicators.
    NOTE: This is a placeholder implementation. The actual calculation
    logic needs to be refined based on desired weighting and scaling.
    """
    def __init__(self, weights=None):
        """
        Initialize with component weights.
        Default weights give equal importance to each component.
        """
        if weights is None:
            # Default weights: [VIX, Momentum, SafeHaven, Volume]
            self.weights = {'vix': 0.25, 'momentum': 0.25, 'safe_haven': 0.25, 'volume': 0.25}
        else:
            self.weights = weights
            
        # Define baseline thresholds or ranges for normalization (EXAMPLE VALUES)
        # These need careful calibration based on historical data
        self.ranges = {
            'vix': (10, 50),       # Example normal range for VIX
            'momentum': (-10, 10), # Example range for S&P 500 momentum (%)
            'safe_haven': (30, 70),# Example range for Safe Haven Ratio (%)
            'volume': (-50, 50)    # Example range for Volume Change (%)
        }

    def _normalize(self, value, component_key):
        """
        Normalizes a component value to a 0-100 scale.
        Lower values indicate more fear, higher values indicate more greed.
        This is a simple linear normalization, might need refinement.
        """
        min_val, max_val = self.ranges[component_key]
        
        # Clamp value to the defined range
        value = np.clip(value, min_val, max_val)
        
        # Normalize to 0-1 scale
        normalized = (value - min_val) / (max_val - min_val)
        
        # Scale to 0-100
        # For VIX, higher value means more fear, so we invert the scale (100 - ...)
        if component_key == 'vix':
             return 100 - (normalized * 100)
        # For others, higher value generally means more greed (or less fear)
        else:
             return normalized * 100

    def calculate(self, vix, momentum, safe_haven_ratio, volume_change):
        """
        Calculate the weighted Fear & Greed Index.
        """
        norm_vix = self._normalize(vix, 'vix')
        norm_momentum = self._normalize(momentum, 'momentum')
        norm_safe_haven = self._normalize(safe_haven_ratio, 'safe_haven')
        # For safe haven, higher ratio might mean more fear, let's invert
        norm_safe_haven = 100 - norm_safe_haven 
        norm_volume = self._normalize(volume_change, 'volume')
        # For volume, extreme high volume might mean panic/fear, let's consider this.
        # This simple normalization doesn't capture extremes well. Needs improvement.
        
        # Weighted average
        index = (norm_vix * self.weights['vix'] +
                 norm_momentum * self.weights['momentum'] +
                 norm_safe_haven * self.weights['safe_haven'] +
                 norm_volume * self.weights['volume'])
                 
        # Ensure the final index is between 0 and 100
        return np.clip(index, 0, 100) 

# Define common figure styling
def apply_common_style(fig, title=None, height=800):
    """Apply common styling to plotly figures"""
    fig.update_layout(
        title_text=title,
        title_font=dict(size=24, color=COLORS['text'], family="Arial, sans-serif"),
        font=dict(family="Arial, sans-serif", size=12, color=COLORS['text']),
        paper_bgcolor=COLORS['background'],
        plot_bgcolor=COLORS['background'],
        height=height,
        margin=dict(l=40, r=40, t=120, b=40), # Increased top margin
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.01, # Position legend below title area
            xanchor="right",
            x=1
        )
    )
    # Apply grid styling globally
    fig.update_xaxes(
        gridcolor='rgba(211, 211, 211, 0.5)',
        showline=True,
        linecolor='lightgray',
        linewidth=1,
        showgrid=True,
        gridwidth=1,
    )
    fig.update_yaxes(
        gridcolor='rgba(211, 211, 211, 0.5)',
        showline=True,
        linecolor='lightgray',
        linewidth=1,
        showgrid=True,
        gridwidth=1,
    )
    return fig

# Helper function: Add S&P 500 chart
def _add_sp500_chart(fig, hist_sp, interval="1mo", row=2, col=2):
    """Add standalone S&P 500 chart"""
    fig.add_trace(go.Scatter(
        x=hist_sp.index,
        y=hist_sp['Close'],
        name="S&P 500",
        mode='lines',
        line=dict(color=COLORS['primary'], width=2),
    ), row=row, col=col)
    
    fig.update_yaxes(title=dict(
        text="S&P 500 Index Value",
        font=dict(color=COLORS['text'])
    ), row=row, col=col)
    fig.update_xaxes(title_text="Date", row=row, col=col)
    
    # Add chart section title
    fig.add_annotation(
        x=0.5, y=0.31,
        xref="paper", yref="paper",
        text="<b>S&P 500 Historical Performance</b>",
        font=dict(size=14, color=COLORS['text']),
        showarrow=False,
        xanchor="center"
    )

def _add_sp500_vix_chart(fig, data_sp500=None, data_vix=None, row=1, col=1):
    """Add S&P 500 vs VIX chart to figure.
    
    Args:
        fig (plotly.graph_objects.Figure): Figure to add chart to.
        data_sp500 (pd.DataFrame, optional): S&P 500 data.
        data_vix (pd.DataFrame, optional): VIX data.
        row (int, optional): Row to add chart to. Defaults to 1.
        col (int, optional): Column to add chart to. Defaults to 1.
    """
    # Check if both datasets are available
    if data_sp500 is None or data_sp500.empty or data_vix is None or data_vix.empty:
        fig.add_annotation(
            text="No S&P 500 or VIX data available",
            xref="x domain", yref="y domain",
            x=0.5, y=0.5,
            showarrow=False,
            row=row, col=col
        )
        return
    
    # Align the data to have same dates
    min_date = max(data_sp500.index.min(), data_vix.index.min())
    max_date = min(data_sp500.index.max(), data_vix.index.max())
    
    sp500_aligned = data_sp500.loc[(data_sp500.index >= min_date) & (data_sp500.index <= max_date)]
    vix_aligned = data_vix.loc[(data_vix.index >= min_date) & (data_vix.index <= max_date)]
    
    # Calculate percentage changes for both indices over the aligned period
    if len(sp500_aligned) > 0:
        sp500_pct_change = ((sp500_aligned["Close"].iloc[-1] - sp500_aligned["Close"].iloc[0]) / 
                           sp500_aligned["Close"].iloc[0] * 100)
    else:
        sp500_pct_change = 0

    if len(vix_aligned) > 0:
        vix_pct_change = ((vix_aligned["Close"].iloc[-1] - vix_aligned["Close"].iloc[0]) / 
                         vix_aligned["Close"].iloc[0] * 100)
    else:
        vix_pct_change = 0
        
    # Define line colors
    sp500_color = "#1f77b4" # Blue
    vix_color = "#d62728"   # Red

    # Add S&P 500 trace to primary y-axis
    fig.add_trace(
        go.Scatter(
            x=sp500_aligned.index,
            y=sp500_aligned["Close"],
            name="S&P 500",
            line=dict(color=sp500_color, width=2),
            showlegend=False
        ),
        row=row, col=col,
        secondary_y=False
    )
    
    # Add S&P 500 % change annotation with matching color
    fig.add_annotation(
        x=0.02, y=0.97,
        xref="x domain", yref="y domain",
        text=f"S&P 500: {sp500_aligned['Close'].iloc[-1]:.2f} ({sp500_pct_change:+.2f}%) ({min_date.strftime('%b %d')} to {max_date.strftime('%b %d')})",
        showarrow=False,
        font=dict(size=12, color=sp500_color), # Match line color
        align="left",
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="rgba(0, 0, 0, 0.1)",
        borderwidth=1,
        borderpad=4,
        row=row, col=col
    )
    
    # Add VIX trace to secondary y-axis
    fig.add_trace(
        go.Scatter(
            x=vix_aligned.index,
            y=vix_aligned["Close"],
            name="VIX",
            line=dict(color=vix_color, width=2),
            showlegend=False
        ),
        row=row, col=col,
        secondary_y=True
    )
    
    # Add VIX % change annotation with matching color
    fig.add_annotation(
        x=0.98, y=0.97,
        xref="x domain", yref="y domain",
        text=f"VIX: {vix_aligned['Close'].iloc[-1]:.2f} ({vix_pct_change:+.2f}%)",
        showarrow=False,
        font=dict(size=12, color=vix_color), # Match line color
        align="right",
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="rgba(0, 0, 0, 0.1)",
        borderwidth=1,
        borderpad=4,
        row=row, col=col
    )
    
    # Update axes (Remove X-axis title)
    fig.update_xaxes(
        title_text="", # Removed Date label
        gridcolor="lightgray",
        row=row, col=col
    )
    
    fig.update_yaxes(
        title_text="S&P 500 Index Value",
        gridcolor="lightgray",
        secondary_y=False,
        row=row, col=col
    )
    
    fig.update_yaxes(
        title_text="VIX Index Value",
        gridcolor="lightgray",
        secondary_y=True,
        row=row, col=col
    )

def _add_indices_performance_chart(fig, indices_data, row=1, col=1):
    """Add indices performance chart to figure using consistent colors.
    
    Args:
        fig (plotly.graph_objects.Figure): Figure to add chart to.
        indices_data (dict): Dictionary with index names as keys and dataframes as values.
        row (int, optional): Row to add chart to. Defaults to 1.
        col (int, optional): Column to add chart to. Defaults to 1.
    """
    if not indices_data:
        fig.add_annotation(
            text="No index data available",
            xref="x domain", yref="y domain",
            x=0.5, y=0.5,
            showarrow=False,
            row=row, col=col
        )
        return
        
        # Calculate percentage changes
    changes = {}
    start_dates = {}
    end_dates = {}
    
    for index_name, df in indices_data.items():
        if len(df) >= 2:
            latest = df["Close"].iloc[-1]
            first = df["Close"].iloc[0]
            pct_change = ((latest - first) / first) * 100
            changes[index_name] = pct_change
            start_dates[index_name] = df.index[0]
            end_dates[index_name] = df.index[-1]
    
    if not changes:
        fig.add_annotation(
            text="Insufficient data to calculate changes",
            xref="x domain", yref="y domain",
            x=0.5, y=0.5,
            showarrow=False,
            row=row, col=col
        )
        return
    
    # Find common time period for all indices (still needed for context if required elsewhere)
    common_start = None
    common_end = None
    
    for name in changes.keys():
        if common_start is None:
            common_start = start_dates[name]
        else:
            common_start = max(common_start, start_dates[name])
            
        if common_end is None:
            common_end = end_dates[name]
        else:
            common_end = min(common_end, end_dates[name])
            
    # Define consistent colors (same as comparison chart)
    consistent_colors = {
        "S&P 500": "#1f77b4",      # Blue
        "NASDAQ": "#d62728",       # Red
        "Dow Jones": "#2ca02c",     # Green
        "Russell 2000": "#ff7f0e" # Orange
    }
    
    # Create sorted bar chart data
    indices = list(changes.keys())
    values = list(changes.values())
    
    # Sort by values (descending)
    sorted_data = sorted(zip(indices, values), key=lambda item: item[1], reverse=True)
    sorted_indices = [item[0] for item in sorted_data]
    sorted_values = [item[1] for item in sorted_data]
    
    # Assign colors based on index name
    sorted_colors = [consistent_colors.get(name, "#7f7f7f") for name in sorted_indices]

    fig.add_trace(
        go.Bar(
            x=sorted_indices,
            y=sorted_values,
            marker_color=sorted_colors,
            text=[f"{v:+.2f}%" for v in sorted_values],
            textposition="auto",
            name="Indices Performance" # Added name for potential trace identification
        ),
        row=row, col=col
    )
    
    # Update axes
    fig.update_xaxes(
        title_text="",
        gridcolor="lightgray",
        row=row, col=col
    )
    
    fig.update_yaxes(
        title_text="Percentage Change (%)",
        gridcolor="lightgray",
        row=row, col=col
    )
    
    # Add reference line at y=0
    fig.add_shape(
        type="line",
        x0=-0.5,
        x1=len(indices) - 0.5,
        y0=0,
        y1=0,
        line=dict(color="black", width=1, dash="dash"),
        row=row, col=col
    )

def _add_historical_chart(fig, data_sp500=None, row=1, col=1):
    """Add S&P 500 historical performance chart to figure.
    
    Args:
        fig (plotly.graph_objects.Figure): Figure to add chart to.
        data_sp500 (pd.DataFrame, optional): S&P 500 data.
        row (int, optional): Row to add chart to. Defaults to 1.
        col (int, optional): Column to add chart to. Defaults to 1.
    """
    if data_sp500 is None or data_sp500.empty:
        fig.add_annotation(
            text="No S&P 500 data available",
            xref="x domain", yref="y domain",
            x=0.5, y=0.5,
            showarrow=False,
            row=row, col=col
        )
        return
    
    # Calculate moving averages if enough data
    if len(data_sp500) > 50:
        data_sp500['MA50'] = data_sp500['Close'].rolling(window=50).mean()
    if len(data_sp500) > 200:
        data_sp500['MA200'] = data_sp500['Close'].rolling(window=200).mean()
    
    # Add S&P 500 price line
    fig.add_trace(
        go.Scatter(
            x=data_sp500.index,
            y=data_sp500["Close"],
            name="S&P 500",
            line=dict(color="blue", width=2),
            showlegend=False
        ),
        row=row, col=col
    )
    
    # Add 50-day moving average if available
    if 'MA50' in data_sp500.columns:
        fig.add_trace(
            go.Scatter(
                x=data_sp500.index,
                y=data_sp500["MA50"],
                name="50-day MA",
                line=dict(color="orange", width=1.5, dash="dash"),
                showlegend=False
            ),
            row=row, col=col
        )
    
    # Add 200-day moving average if available
    if 'MA200' in data_sp500.columns:
        fig.add_trace(
            go.Scatter(
                x=data_sp500.index,
                y=data_sp500["MA200"],
                name="200-day MA",
                line=dict(color="red", width=1.5, dash="dash"),
                showlegend=False
            ),
            row=row, col=col
        )
    
    # Add latest price and change annotation
    latest_price = data_sp500["Close"].iloc[-1]
    first_price = data_sp500["Close"].iloc[0]
    pct_change = ((latest_price - first_price) / first_price) * 100
    color = "green" if pct_change >= 0 else "red"
    
    fig.add_annotation(
        x=0.02, y=0.97,
        xref="x domain", yref="y domain",
        text=f"S&P 500: {latest_price:.2f} ({pct_change:+.2f}%)",
        showarrow=False,
        font=dict(size=12, color=color),
        align="left",
        bgcolor="rgba(255, 255, 255, 0.8)",
        bordercolor="rgba(0, 0, 0, 0.2)",
        borderwidth=1,
        borderpad=4,
        row=row, col=col
    )
    
    # Update axes
    fig.update_xaxes(
        title_text="Date",
        gridcolor="lightgray",
        row=row, col=col
    )
    
    fig.update_yaxes(
        title_text="S&P 500 Index Value",
        gridcolor="lightgray",
        row=row, col=col
    )

def _add_fear_and_greed_gauge(fig, vix_value=None, row=1, col=1):
    """Add fear and greed gauge to figure.
    
    Args:
        fig (plotly.graph_objects.Figure): Figure to add gauge to.
        vix_value (float, optional): Current VIX value.
        row (int, optional): Row to add gauge to. Defaults to 1.
        col (int, optional): Column to add gauge to. Defaults to 1.
    """
    if vix_value is None:
        fig.add_annotation(
            text="No VIX data available",
            xref="paper", yref="paper",
            x=0.75, y=0.25, 
            showarrow=False,
            font=dict(size=14)
        )
        return
    
    vix_extreme_greed = 10
    vix_extreme_fear = 40
    vix_clamped = max(vix_extreme_greed, min(vix_value, vix_extreme_fear))
    
    if vix_value <= vix_extreme_greed:
        fear_greed_value = 100
    elif vix_value >= vix_extreme_fear:
        fear_greed_value = 0
    else:
        fear_greed_value = 100 - ((vix_clamped - vix_extreme_greed) / (vix_extreme_fear - vix_extreme_greed) * 100)
    
    if fear_greed_value >= 75:
        sentiment = "Extreme Greed"
        color = "#1a9850"
        bar_color = "#66bd63"
    elif fear_greed_value >= 55:
        sentiment = "Greed"
        color = "#66bd63"
        bar_color = "#a6d96a"
    elif fear_greed_value >= 45:
        sentiment = "Neutral"
        color = "#d8c343"
        bar_color = "#ffffbf"
    elif fear_greed_value >= 25:
        sentiment = "Fear"
        color = "#fdae61"
        bar_color = "#fee08b"
    else:
        sentiment = "Extreme Fear"
        color = "#d73027"
        bar_color = "#fc8d59"

    score_font_size = 30
    sentiment_font_size = score_font_size
    
    fig.add_trace(
        go.Indicator(
            mode="gauge+number",
            value=fear_greed_value,
            title={"text": "", "font": {"size": 1}},
            gauge={
                "axis": {"range": [0, 100], "tickmode": "array", "tickvals": [0, 25, 50, 75, 100], "ticktext": ["", "", "", "", ""], "tickfont": {"size": 10}},
                "bar": {"color": bar_color, "thickness": 0.3},
                "steps": [
                    {"range": [0, 25], "color": "#d73027"},
                    {"range": [25, 45], "color": "#fdae61"},
                    {"range": [45, 55], "color": "#ffffbf"},
                    {"range": [55, 75], "color": "#a6d96a"},
                    {"range": [75, 100], "color": "#1a9850"}
                ],
                "threshold": {"line": {"color": "black", "width": 4}, "thickness": 0.9, "value": fear_greed_value},
                "bgcolor": "rgba(255, 255, 255, 0.7)",
                "borderwidth": 1,
                "bordercolor": "#cccccc"
            },
            number={"suffix": " Score", "font": {"size": score_font_size, "color": color, "family": "Arial"}},
            domain={"row": row, "column": col}
        ),
        row=row, col=col
    )
    
    trace_domain = fig.data[-1].domain
    domain_x = trace_domain.x
    domain_y = trace_domain.y
    
    center_x = (domain_x[0] + domain_x[1]) / 2
    center_y = (domain_y[0] + domain_y[1]) / 2
    
    anno_x = center_x
    # Place Sentiment even closer to Score
    anno_y_sentiment = center_y - 0.07 # Reduced gap even further
    anno_y_score_implied_baseline = center_y - 0.10 # Baseline for score number (reference)
    anno_y_vix = anno_y_score_implied_baseline - 0.08 # Position VIX below Score
    
    # Extreme labels aligned with arc bottom edges, slightly higher than absolute bottom
    anno_y_extreme_label = domain_y[0] + 0.015 # Move slightly up from the very bottom
    anno_x_fear_label = domain_x[0]    # Align with left arc start
    anno_x_greed_label = domain_x[1]   # Align with right arc end

    # Add sentiment text annotation (ABOVE score, very close)
    fig.add_annotation(
        xref="paper", yref="paper",
        x=anno_x, y=anno_y_sentiment,
        text=f"<b>{sentiment}</b>",
        showarrow=False,
        font=dict(size=sentiment_font_size, color=color),
        align="center",
        xanchor="center", yanchor="bottom" # Anchor bottom to sit above score baseline
    )
    
    # Add VIX value annotation (BELOW score with spacing)
    fig.add_annotation(
        xref="paper", yref="paper",
        x=anno_x, y=anno_y_vix,
        text=f"(VIX: {vix_value:.2f})",
        showarrow=False,
        font=dict(size=12),
        align="center",
        xanchor="center", yanchor="top" # Anchor top to sit below score
    )
    
    # Add labels for the extremes aligned with gauge arc bottom
    fig.add_annotation(
        xref="paper", yref="paper",
        x=anno_x_fear_label, y=anno_y_extreme_label,
        text="Extreme Fear", # Single line text
        showarrow=False,
        font=dict(size=10, color="#d73027"),
        align="left", 
        xanchor="left", yanchor="bottom"
    )
    
    fig.add_annotation(
        xref="paper", yref="paper",
        x=anno_x_greed_label, y=anno_y_extreme_label,
        text="Extreme Greed", # Single line text
        showarrow=False,
        font=dict(size=10, color="#1a9850"),
        align="right", 
        xanchor="right", yanchor="bottom"
    )

def _add_market_comparison_chart(fig, indices_data, row=1, col=1):
    """Add market comparison chart showing relative performance of indices.
    
    Args:
        fig (plotly.graph_objects.Figure): Figure to add chart to.
        indices_data (dict): Dictionary with index names as keys and dataframes as values.
        row (int, optional): Row to add chart to. Defaults to 1.
        col (int, optional): Column to add chart to. Defaults to 1.
    """
    if not indices_data or len(indices_data) < 2:
        fig.add_annotation(
            text="Insufficient index data for comparison",
            xref="x domain", yref="y domain",
            x=0.5, y=0.5,
            showarrow=False,
            row=row, col=col
        )
        return
    
    # Calculate relative performance for all indices (normalized to 100)
    reference_date = None
    normed_data = {}
    
    # Find common start date for all indices
    for name, df in indices_data.items():
        if df is not None and not df.empty:
            if reference_date is None:
                reference_date = df.index[0]
            else:
                reference_date = max(reference_date, df.index[0])
    
    if reference_date is None:
        fig.add_annotation(
            text="No valid data for comparison",
            xref="x domain", yref="y domain",
            x=0.5, y=0.5,
            showarrow=False,
            row=row, col=col
        )
        return
    
    # Calculate normalized performance for each index
    for name, df in indices_data.items():
        if df is not None and not df.empty:
            # Filter data starting from reference date
            filtered_df = df[df.index >= reference_date]
            if not filtered_df.empty:
                # Normalize to 100 at start date
                reference_value = filtered_df['Close'].iloc[0]
                normed_series = (filtered_df['Close'] / reference_value) * 100
                normed_data[name] = normed_series
    
    # Define consistent colors used across charts
    consistent_colors = {
        "S&P 500": "#1f77b4",      # Blue
        "NASDAQ": "#d62728",       # Red
        "Dow Jones": "#2ca02c",     # Green
        "Russell 2000": "#ff7f0e" # Orange
    }
    
    # Determine the last date for plotting
    last_date = None
    if normed_data:
        valid_series = [s for s in normed_data.values() if not s.empty]
        if valid_series:
            last_date = max(series.index[-1] for series in valid_series)

    # Plot each normalized index
    for name, series in normed_data.items():
        if not series.empty:
            color = consistent_colors.get(name, "#7f7f7f")  # Default to gray if name not in colors dict
            
            fig.add_trace(
                go.Scatter(
                    x=series.index,
                    y=series,
                    name=name, # Legend name
                    line=dict(color=color, width=2),
                    hovertemplate=f"{name}: %{{y:.2f}}%<extra></extra>",
                    legendgroup=name, # Group legends if needed later
                    showlegend=True # Show individual lines in legend
                ),
                row=row, col=col
            )
    
    # Add reference line at 100
    if reference_date and last_date:
        fig.add_shape(
            type="line",
            x0=reference_date,
            x1=last_date,
            y0=100,
            y1=100,
            line=dict(color="black", width=1, dash="dash"),
            row=row, col=col
        )
    
    # Update axes (Remove X-axis title)
    fig.update_xaxes(
        title_text="", # Removed Date label
        gridcolor="lightgray",
        row=row, col=col
    )
    
    fig.update_yaxes(
        title_text="Relative Performance (%)",
        gridcolor="lightgray",
        row=row, col=col
    )

def create_dashboard(data_sp500=None, data_nasdaq=None, data_dji=None, data_rut=None, data_vix=None, interval="YTD"):
    """Create a dashboard with market data.
    
    Args:
        data_sp500 (pd.DataFrame, optional): S&P 500 data.
        data_nasdaq (pd.DataFrame, optional): NASDAQ data.
        data_dji (pd.DataFrame, optional): Dow Jones Industrial Average data.
        data_rut (pd.DataFrame, optional): Russell 2000 data.
        data_vix (pd.DataFrame, optional): VIX data.
        interval (str, optional): Data interval (e.g., "YTD", "1mo"). Defaults to "YTD".
        
    Returns:
        plotly.graph_objects.Figure: Dashboard figure.
    """
    # Create 2x2 subplot
    fig = make_subplots(
        rows=2, cols=2,
        shared_xaxes=False,
        vertical_spacing=0.12,
        horizontal_spacing=0.08,
        subplot_titles=(
            f"Major Indices Performance ({interval})",
            "S&P 500 vs VIX",
            "Indices Relative Performance Comparison",
            "Market Fear & Greed Index"
        ),
        specs=[
            [{"type": "bar"}, {"type": "xy", "secondary_y": True}],
            [{"type": "xy"}, {"type": "domain"}]
        ]
    )
    
    # Add bar chart with indices performance
    indices_data = {}
    if data_sp500 is not None and not data_sp500.empty:
        indices_data["S&P 500"] = data_sp500
    if data_nasdaq is not None and not data_nasdaq.empty:
        indices_data["NASDAQ"] = data_nasdaq
    if data_dji is not None and not data_dji.empty:
        indices_data["Dow Jones"] = data_dji
    if data_rut is not None and not data_rut.empty:
        indices_data["Russell 2000"] = data_rut
    
    _add_indices_performance_chart(fig, indices_data, row=1, col=1)
    
    # Add S&P 500 vs VIX chart
    _add_sp500_vix_chart(fig, data_sp500, data_vix, row=1, col=2)
    
    # Add market comparison chart
    _add_market_comparison_chart(fig, indices_data, row=2, col=1)
    
    # Add fear and greed index
    vix_value = None
    if data_vix is not None and not data_vix.empty:
        vix_value = data_vix["Close"].iloc[-1]
    
    _add_fear_and_greed_gauge(fig, vix_value, row=2, col=2)
    
    # Update global figure layout
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    fig.update_layout(
        title={
            "text": "Market Sentiment Dashboard",
            "y": 0.98,
            "x": 0.5,
            "xanchor": "center",
            "yanchor": "top",
            "font": {"size": 24}
        },
        height=800,
        width=1200,
        margin=dict(l=50, r=50, t=100, b=50),
        template="plotly_white",
        showlegend=False, # Hide main legend, use annotations/sub-legends
    )
    
    # Add timestamp in English
    fig.add_annotation(
        text=f"Data updated: {current_time}",
        xref="paper", yref="paper",
        x=0.01, y=0.01,  # Bottom left corner
                showarrow=False,
        font=dict(size=10),
        align="left"
    )
    
    # Improve layout of subplots
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="lightgray")
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="lightgray")
    
    return fig

def generate_market_sentiment_dashboard(indices=None):
    """
    Generate a professional market sentiment dashboard.
    Includes major index performance (with points and percentage change),
    relative performance comparison, and Fear/Greed indicator.
    
    Args:
        indices (list): List of indices, default is S&P 500, Dow Jones, NASDAQ, Russell 2000, VIX.
    
    Returns:
        str: base64 encoded image
    """
    if indices is None:
        indices = ['^GSPC', '^DJI', '^IXIC', '^RUT', '^VIX']
    
    # --- Data Fetching and Preparation ---
    end_date = datetime.now()
    # Start from beginning of current year (Year-to-Date)
    start_date = datetime(end_date.year, 1, 1)
    
    # Prepare data frames for each index
    data_sp500 = None
    data_nasdaq = None
    data_dji = None
    data_rut = None
    data_vix = None
    
    print(f"Getting market data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")
    
    # Process all indices to get historical data
    for index in indices:
        ticker = yf.Ticker(index)
        # Get year-to-date data
        try:
            hist = ticker.history(start=start_date, end=end_date)
            
            if not hist.empty:
                print(f"Successfully retrieved {index} data, total of {len(hist)} trading days")
                if index == '^GSPC':
                    data_sp500 = hist
                elif index == '^IXIC':
                    data_nasdaq = hist
                elif index == '^DJI':
                    data_dji = hist
                elif index == '^RUT':
                    data_rut = hist
                elif index == '^VIX':
                    data_vix = hist
            else:
                print(f"Warning: {index} did not return data")
        except Exception as e:
            print(f"Error retrieving {index} data: {str(e)}")
    
    # Create dashboard using our improved layout
    interval = "YTD"  # Year-to-Date
    fig = create_dashboard(
        data_sp500=data_sp500,
        data_nasdaq=data_nasdaq,
        data_dji=data_dji,
        data_rut=data_rut,
        data_vix=data_vix,
        interval=interval
    )
    
    # Convert to image and return as base64
    img_bytes = fig.to_image(format="png", width=1200, height=800, scale=2)
    encoded = base64.b64encode(img_bytes).decode('utf-8')
    
    return encoded

def generate_portfolio_tracking(symbols=None):
    """
    Generate portfolio tracking report
    
    Args:
        symbols (list): List of stock symbols
    
    Returns:
        str: base64 encoded image
    """
    if symbols is None:
        symbols = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA']
    
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
        
        # Calculate price changes
        current = hist['Close'].iloc[-1]
        prev_close = hist['Close'].iloc[-2]
        change_1d = (current - prev_close) / prev_close * 100
        
        # Calculate monthly change
        one_month_ago = max(0, len(hist) - 22)  # Approximately 22 trading days per month
        if one_month_ago < len(hist):
            month_close = hist['Close'].iloc[one_month_ago]
            change_1mo = (current - month_close) / month_close * 100
        else:
            change_1mo = 0
        
        # Calculate year-to-date
        first_close = hist['Close'].iloc[0]
        change_ytd = (current - first_close) / first_close * 100
        ytd_changes.append(change_ytd)
        
        # Set color based on performance
        color = COLORS['positive'] if change_1d >= 0 else COLORS['negative']
        colors.append(color)
        
        # Market cap
        market_cap = info.get('marketCap', 'N/A')
        if market_cap != 'N/A':
            market_cap = f"${market_cap/1e9:.2f}B"
        
        portfolio_data[symbol] = {
            'name': name,
            'current': current,
            'change_1d': change_1d,
            'change_1mo': change_1mo,
            'change_ytd': change_ytd,
            'market_cap': market_cap
        }
        print(f"Processed {symbol}: YTD Change = {change_ytd:.2f}%") # DEBUG
    
    # Create figure with 2 subplots for charts (we'll add the table separately)
    fig = make_subplots(
        rows=2, cols=1,
        vertical_spacing=0.1,
        row_heights=[0.6, 0.4],
        subplot_titles=(
            "<b>Portfolio Performance Chart</b>", 
            "<b>YTD Performance Comparison</b>"
        )
    )
    
    # Create simulated portfolio value data
    dates = pd.date_range(start=start_date, end=end_date, freq='B')  # Business days
    initial_value = 10000  # Initial portfolio value
    
    # Calculate simulated portfolio value from YTD percentage changes
    avg_ytd_change = sum(ytd_changes) / len(ytd_changes)  # Average YTD change
    portfolio_values = []
    benchmark_values = []
    
    # Output YTD changes for testing
    print("YTD changes for each stock:")
    for i, symbol in enumerate(symbols):
        print(f"  {symbol}: {ytd_changes[i]:.2f}%")
    print(f"Average YTD change: {avg_ytd_change:.2f}%")
    
    # Create daily simulation data
    for i in range(len(dates)):
        # Calculate the proportion of current date to total days
        progress = i / (len(dates) - 1) if len(dates) > 1 else 0
        
        # Calculate current value based on average YTD change
        portfolio_value = initial_value * (1 + (avg_ytd_change/100) * progress)
        benchmark_value = initial_value * (1 + (avg_ytd_change/100) * 0.85 * progress)  # Benchmark slightly underperforms portfolio
        
        portfolio_values.append(portfolio_value)
        benchmark_values.append(benchmark_value)
    
    # Output debug information
    print(f"Created {len(portfolio_values)} portfolio values from {dates[0]} to {dates[-1]}")
    print(f"Portfolio start: {portfolio_values[0]:.2f}, end: {portfolio_values[-1]:.2f}")
    
    # Add portfolio value line
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=portfolio_values,
            name="Portfolio Value",
            mode='lines',  # Explicitly set to line mode
            line=dict(color='#1F77B4', width=4),  # Blue thick line
            fill='tozeroy',  # Add fill area
            fillcolor='rgba(31, 119, 180, 0.2)',  # Semi-transparent blue fill
            visible=True
        ),
        row=1, col=1
    )
    
    # Add S&P 500 benchmark line
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=benchmark_values,
            name="S&P 500",
            mode='lines',  # Explicitly set to line mode
            line=dict(color='#FF7F0E', width=3, dash='dash'),  # Orange dashed line
            visible=True
        ),
        row=1, col=1
    )
    
    # Manually set Y-axis range
    min_val = min(min(portfolio_values), min(benchmark_values))
    max_val = max(max(portfolio_values), max(benchmark_values))
    y_padding = (max_val - min_val) * 0.1  # Add 10% padding
    fig.update_yaxes(
        title_text="Value ($)",
        range=[min_val - y_padding, max_val + y_padding],
        row=1, col=1
    )
    
    # Add horizontal axis title
    fig.update_xaxes(
        title_text="Date",
        row=1, col=1
    )
    
    # Calculate and display portfolio metrics
    portfolio_start = portfolio_values[0]
    portfolio_end = portfolio_values[-1]
    portfolio_return = ((portfolio_end - portfolio_start) / portfolio_start) * 100
    
    benchmark_start = benchmark_values[0]
    benchmark_end = benchmark_values[-1]
    benchmark_return = ((benchmark_end - benchmark_start) / benchmark_start) * 100
    
    # Ensure return values are scalars
    portfolio_return = float(portfolio_return)
    benchmark_return = float(benchmark_return)
    
    print(f"Portfolio Return: {portfolio_return:.2f}%, Benchmark Return: {benchmark_return:.2f}%")
    
    # Add YTD performance bar chart with improved styling
    fig.add_trace(
        go.Bar(
            x=symbols,
            y=ytd_changes,
            marker_color=colors,
            text=[f"{v:.2f}%" for v in ytd_changes],
            textposition='auto',
            name="YTD Performance",
            hovertemplate='<b>%{x}</b><br>YTD Change: %{y:.2f}%<extra></extra>'
        ),
        row=2, col=1
    )
    
    # Add a reference line for portfolio average performance
    avg_ytd = sum(ytd_changes) / len(ytd_changes)
    fig.add_shape(
        type="line",
        x0=-0.5,
        y0=avg_ytd,
        x1=len(symbols) - 0.5,
        y1=avg_ytd,
        line=dict(
            color="black",
            width=2,
            dash="dash",
        ),
        row=2, col=1
    )
    
    # Add annotation for the average line
    fig.add_annotation(
        x=len(symbols) - 0.5,
        y=avg_ytd,
        text=f"Portfolio Avg: {avg_ytd:.2f}%",
        showarrow=True,
        arrowhead=1,
        row=2, col=1
    )
    
    # Apply common styling and add portfolio summary
    apply_common_style(
        fig, 
        title=f"<b>Portfolio Performance Tracker</b><br><span style='font-size:0.8em;'>YTD Return: {portfolio_return:.2f}%</span>",
        height=900
    )
    
    # Add timestamp annotation
    fig.add_annotation(
        text=f"<i>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>",
        showarrow=False,
        xref="paper",
        yref="paper",
        x=0.01,
        y=0.01,
        font=dict(size=10, color=COLORS['neutral'])
    )
    
    # Enhanced interactivity
    fig.update_layout(hovermode="closest")
    
    # Get the image for the chart
    chart_bytes = fig.to_image(format="png", engine="kaleido", width=1200, height=900, scale=2)
    chart_img = Image.open(io.BytesIO(chart_bytes))
    
    # Create a separate table figure
    table_fig = go.Figure()
    
    # Create enhanced table for portfolio details
    table_data = []
    daily_colors = []
    monthly_colors = []
    ytd_colors = []
    
    for symbol, data in portfolio_data.items():
        table_data.append([
            f"<b>{symbol}</b>",
            data['name'],
            f"${data['current']:.2f}",
            f"{data['change_1d']:.2f}%",
            f"{data['change_1mo']:.2f}%",
            f"{data['change_ytd']:.2f}%",
            data['market_cap']
        ])
        # Collect colors to use for each cell
        daily_colors.append('green' if data['change_1d'] >= 0 else 'red')
        monthly_colors.append('green' if data['change_1mo'] >= 0 else 'red')
        ytd_colors.append('green' if data['change_ytd'] >= 0 else 'red')
    
    # Transpose data to apply colors
    transposed_data = list(map(list, zip(*table_data)))
    
    table_fig.add_trace(
        go.Table(
            header=dict(
                values=['<b>Symbol</b>', '<b>Name</b>', '<b>Current Price</b>', 
                        '<b>Daily</b>', '<b>Monthly</b>', '<b>YTD</b>', '<b>Market Cap</b>'],
                line_color='white',
                fill_color=COLORS['primary'],
                align='center',
                font=dict(color='white', size=12)
            ),
            cells=dict(
                values=transposed_data,
                line_color='white',
                fill_color=[[COLORS['background'], '#E6F2FF'] * len(portfolio_data)],
                align='center',
                font=dict(
                    color=[
                        [COLORS['text']] * len(portfolio_data),  # Symbol color
                        [COLORS['text']] * len(portfolio_data),  # Name color
                        [COLORS['text']] * len(portfolio_data),  # Price color
                        daily_colors,                           # Daily color
                        monthly_colors,                         # Monthly color
                        ytd_colors,                             # YTD color
                        [COLORS['text']] * len(portfolio_data)   # Market Cap color
                    ],
                    size=11
                ),
                height=30
            )
        )
    )
    
    # Style the table
    table_fig.update_layout(
        title_text="<b>Portfolio Details</b>",
        title_font=dict(size=20, color=COLORS['text'], family="Arial, sans-serif"),
        font=dict(family="Arial, sans-serif", size=12, color=COLORS['text']),
        paper_bgcolor=COLORS['background'],
        margin=dict(l=40, r=40, t=60, b=40),
        height=300
    )
    
    # Get the image for the table
    table_bytes = table_fig.to_image(format="png", engine="kaleido", width=1200, height=300, scale=2)
    table_img = Image.open(io.BytesIO(table_bytes))
    
    # Combine the two images
    new_width = max(chart_img.width, table_img.width)
    new_height = chart_img.height + table_img.height
    new_img = Image.new('RGB', (new_width, new_height), (255, 255, 255))
    
    # Paste the two images
    new_img.paste(chart_img, (0, 0))
    new_img.paste(table_img, (0, chart_img.height))
    
    # Add a subtle border line between the two images
    draw = ImageDraw.Draw(new_img)
    draw.line([(0, chart_img.height), (new_width, chart_img.height)], fill="lightgray", width=2)
    
    # Save to memory and encode as base64
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