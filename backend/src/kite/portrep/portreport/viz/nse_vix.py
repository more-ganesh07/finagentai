import numpy as np
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
# from fear_greed_india import FearAndGreedIndia
# from ..vizualization import COLORS  # Assuming COLORS is defined as before


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



class NseVixVisualizer:
    # ----------------------------
    # Common Figure Styling
    # ----------------------------
    def apply_common_style(fig, title=None, height=800):
        """Apply common styling to plotly figures"""
        fig.update_layout(
            title_text=title,
            title_font=dict(size=24, color=COLORS['text'], family="Arial, sans-serif"),
            font=dict(family="Arial, sans-serif", size=12, color=COLORS['text']),
            paper_bgcolor=COLORS['background'],
            plot_bgcolor=COLORS['background'],
            height=height,
            margin=dict(l=40, r=40, t=120, b=40),
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.01,
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


    @staticmethod
    def _add_sp500_vix_chart(fig, data_sp500=None, data_vix=None, row=1, col=1):
        """Add Nifty 50 vs India VIX chart to figure (Indian market adaptation)."""
        if data_sp500 is None or data_sp500.empty or data_vix is None or data_vix.empty:
            fig.add_annotation(
                text="No Nifty 50 or India VIX data available",
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

        # Calculate percentage changes
        sp500_pct_change = ((sp500_aligned["Close"].iloc[-1] - sp500_aligned["Close"].iloc[0]) /
                            sp500_aligned["Close"].iloc[0] * 100) if len(sp500_aligned) > 0 else 0

        vix_pct_change = ((vix_aligned["Close"].iloc[-1] - vix_aligned["Close"].iloc[0]) /
                          vix_aligned["Close"].iloc[0] * 100) if len(vix_aligned) > 0 else 0

        # Define line colors
        sp500_color = "#1f77b4"  # Blue
        vix_color = "#d62728"    # Red

        # Add Nifty 50 trace
        fig.add_trace(
            go.Scatter(
                x=sp500_aligned.index,
                y=sp500_aligned["Close"],
                name="Nifty 50",
                line=dict(color=sp500_color, width=2),
                showlegend=False
            ),
            row=row, col=col,
            secondary_y=False
        )

        # Add Nifty 50 % change annotation
        fig.add_annotation(
            x=0.02, y=0.97,
            xref="x domain", yref="y domain",
            text=f"Nifty 50: {sp500_aligned['Close'].iloc[-1]:.2f} INR ({sp500_pct_change:+.2f}%) "
                 f"({min_date.strftime('%b %d')} to {max_date.strftime('%b %d')})",
            showarrow=False,
            font=dict(size=12, color=sp500_color),
            align="left",
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="rgba(0, 0, 0, 0.1)",
            borderwidth=1,
            borderpad=4,
            row=row, col=col
        )

        # Add India VIX trace
        fig.add_trace(
            go.Scatter(
                x=vix_aligned.index,
                y=vix_aligned["Close"],
                name="India VIX",
                line=dict(color=vix_color, width=2),
                showlegend=False
            ),
            row=row, col=col,
            secondary_y=True
        )

        # Add VIX % change annotation
        fig.add_annotation(
            x=0.98, y=0.97,
            xref="x domain", yref="y domain",
            text=f"India VIX: {vix_aligned['Close'].iloc[-1]:.2f} ({vix_pct_change:+.2f}%)",
            showarrow=False,
            font=dict(size=12, color=vix_color),
            align="right",
            bgcolor="rgba(255, 255, 255, 0.8)",
            bordercolor="rgba(0, 0, 0, 0.1)",
            borderwidth=1,
            borderpad=4,
            row=row, col=col
        )

        # Update axes
        fig.update_xaxes(title_text="", gridcolor="lightgray", row=row, col=col)
        fig.update_yaxes(title_text="Nifty 50 Value (INR)", gridcolor="lightgray", secondary_y=False, row=row, col=col)
        fig.update_yaxes(title_text="India VIX Value", gridcolor="lightgray", secondary_y=True, row=row, col=col)

    
    @staticmethod
    def _add_indices_performance_chart(fig, indices_data, row=1, col=1):
        """Add indices performance chart to figure using consistent colors (Indian market adaptation)."""
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

        # Find common time period (context)
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

        # Define consistent colors for Indian indices
        consistent_colors = {
            "Nifty 50": "#1f77b4",    # Blue
            "Nifty Bank": "#d62728",  # Red
            "Nifty IT": "#2ca02c",    # Green
            "Nifty Pharma": "#ff7f0e" # Orange
        }

        # Prepare bar chart data
        indices = list(changes.keys())
        values = list(changes.values())

        # Sort by values descending
        sorted_data = sorted(zip(indices, values), key=lambda item: item[1], reverse=True)
        sorted_indices = [item[0] for item in sorted_data]
        sorted_values = [item[1] for item in sorted_data]

        # Assign colors
        sorted_colors = [consistent_colors.get(name, "#7f7f7f") for name in sorted_indices]

        # Add bar trace
        fig.add_trace(
            go.Bar(
                x=sorted_indices,
                y=sorted_values,
                marker_color=sorted_colors,
                text=[f"{v:+.2f}%" for v in sorted_values],
                textposition="auto",
                name="Indices Performance"
            ),
            row=row, col=col
        )

        # Update axes
        fig.update_xaxes(title_text="", gridcolor="lightgray", row=row, col=col)
        fig.update_yaxes(title_text="Percentage Change (%)", gridcolor="lightgray", row=row, col=col)

        # Reference line at y=0
        fig.add_shape(
            type="line",
            x0=-0.5,
            x1=len(indices) - 0.5,
            y0=0,
            y1=0,
            line=dict(color="black", width=1, dash="dash"),
            row=row, col=col
        )

    @staticmethod
    def _add_fear_and_greed_gauge(fig, vix_value=None, row=1, col=1):
        """Add fear and greed gauge to figure (Indian market adaptation)."""
        if vix_value is None:
            fig.add_annotation(
                text="No India VIX data available",
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
        anno_y_sentiment = center_y - 0.07
        anno_y_score_implied_baseline = center_y - 0.10
        anno_y_vix = anno_y_score_implied_baseline - 0.08

        anno_y_extreme_label = domain_y[0] + 0.015
        anno_x_fear_label = domain_x[0]
        anno_x_greed_label = domain_x[1]

        # Sentiment text
        fig.add_annotation(
            xref="paper", yref="paper",
            x=anno_x, y=anno_y_sentiment,
            text=f"<b>{sentiment}</b>",
            showarrow=False,
            font=dict(size=sentiment_font_size, color=color),
            align="center",
            xanchor="center", yanchor="bottom"
        )

        # VIX value annotation (Indian market)
        fig.add_annotation(
            xref="paper", yref="paper",
            x=anno_x, y=anno_y_vix,
            text=f"(India VIX: {vix_value:.2f})",
            showarrow=False,
            font=dict(size=12),
            align="center",
            xanchor="center", yanchor="top"
        )

        # Extreme labels
        fig.add_annotation(
            xref="paper", yref="paper",
            x=anno_x_fear_label, y=anno_y_extreme_label,
            text="Extreme Fear",
            showarrow=False,
            font=dict(size=10, color="#d73027"),
            align="left", 
            xanchor="left", yanchor="bottom"
        )

        fig.add_annotation(
            xref="paper", yref="paper",
            x=anno_x_greed_label, y=anno_y_extreme_label,
            text="Extreme Greed",
            showarrow=False,
            font=dict(size=10, color="#1a9850"),
            align="right", 
            xanchor="right", yanchor="bottom"
        )


    @staticmethod
    def _add_market_comparison_chart(fig, indices_data, row=1, col=1):
        """Add market comparison chart showing relative performance of Indian indices.
        
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
                filtered_df = df[df.index >= reference_date]
                if not filtered_df.empty:
                    reference_value = filtered_df['Close'].iloc[0]
                    normed_series = (filtered_df['Close'] / reference_value) * 100
                    normed_data[name] = normed_series

        # Define consistent colors for Indian indices
        consistent_colors = {
            "Nifty 50": "#1f77b4",       # Blue
            "Nifty Next 50": "#d62728",  # Red
            "Sensex": "#2ca02c",         # Green
            "Nifty Smallcap 100": "#ff7f0e" # Orange
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
                color = consistent_colors.get(name, "#7f7f7f")  # Default gray if name not in colors dict
                fig.add_trace(
                    go.Scatter(
                        x=series.index,
                        y=series,
                        name=name,
                        line=dict(color=color, width=2),
                        hovertemplate=f"{name}: %{{y:.2f}}<extra></extra>",
                        legendgroup=name,
                        showlegend=True
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

        # Update axes
        fig.update_xaxes(
            title_text="",
            gridcolor="lightgray",
            row=row, col=col
        )
        fig.update_yaxes(
            title_text="Relative Performance (%)",
            gridcolor="lightgray",
            row=row, col=col
        )


    @staticmethod
    def create_dashboard(data_nifty=None, data_nifty_next50=None,
                         data_sensex=None, data_smallcap=None,
                         data_vix=None, interval="YTD"):
        """Create a dashboard with Indian market data."""
        fig = make_subplots(
            rows=2, cols=2,
            shared_xaxes=False,
            vertical_spacing=0.12,
            horizontal_spacing=0.08,
            subplot_titles=(
                f"Major Indian Indices Performance ({interval})",
                "Nifty 50 vs India VIX",
                "Indices Relative Performance Comparison",
                "Market Fear & Greed Index"
            ),
            specs=[
                [{"type": "bar"}, {"type": "xy", "secondary_y": True}],
                [{"type": "xy"}, {"type": "domain"}]
            ]
        )

        indices_data = {}
        if data_nifty is not None and not data_nifty.empty:
            indices_data["Nifty 50"] = data_nifty
        if data_nifty_next50 is not None and not data_nifty_next50.empty:
            indices_data["Nifty Next 50"] = data_nifty_next50
        if data_sensex is not None and not data_sensex.empty:
            indices_data["Sensex"] = data_sensex
        if data_smallcap is not None and not data_smallcap.empty:
            indices_data["Nifty Smallcap 100"] = data_smallcap

        NseVixVisualizer._add_indices_performance_chart(fig, indices_data, row=1, col=1)
        NseVixVisualizer._add_sp500_vix_chart(fig, data_nifty, data_vix, row=1, col=2)
        NseVixVisualizer._add_market_comparison_chart(fig, indices_data, row=2, col=1)

        vix_value = None
        if data_vix is not None and not data_vix.empty:
            vix_value = data_vix["Close"].iloc[-1]

        NseVixVisualizer._add_fear_and_greed_gauge(fig, vix_value, row=2, col=2)

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        fig.update_layout(
            title={
                "text": "Indian Market Sentiment Dashboard",
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
            showlegend=False
        )
        fig.add_annotation(
            text=f"Data updated: {current_time}",
            xref="paper", yref="paper",
            x=0.01, y=0.01,
            showarrow=False,
            font=dict(size=10),
            align="left"
        )

        fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="lightgray")
        fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="lightgray")

        return fig