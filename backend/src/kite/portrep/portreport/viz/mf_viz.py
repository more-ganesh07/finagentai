"""
Mutual Fund Visualization Module
Generates performance charts for mutual fund holdings.
"""

import io
import base64
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime
from PIL import Image

COLORS = {
    'primary': '#1F77B4',
    'secondary': '#FF7F0E',
    'positive': '#2CA02C',
    'negative': '#D62728',
    'neutral': '#7F7F7F',
    'accent1': '#9467BD',
    'accent2': '#8C564B',
    'background': '#FFFFFF',
    'text': '#333333'
}


class MutualFundVisualizer:
    
    @staticmethod
    def generate_mf_performance(mf_data):
        """
        Generate mutual fund performance overview chart.
        
        Args:
            mf_data (list): List of mutual fund dictionaries with scheme, units, nav, value, gain_pct
            
        Returns:
            str: base64 encoded image
        """
        if not mf_data:
            # Return empty chart with message
            fig = go.Figure()
            fig.add_annotation(
                text="No mutual fund holdings found",
                xref="paper", yref="paper",
                x=0.5, y=0.5,
                showarrow=False,
                font=dict(size=20)
            )
            img_bytes = fig.to_image(format="png", width=1200, height=800)
            return base64.b64encode(img_bytes).decode('ascii')
        
        # Define consistent colors for each MF (up to 10 schemes)
        scheme_colors = [
            '#1F77B4',  # Blue
            '#FF7F0E',  # Orange
            '#2CA02C',  # Green
            '#D62728',  # Red
            '#9467BD',  # Purple
            '#8C564B',  # Brown
            '#E377C2',  # Pink
            '#7F7F7F',  # Gray
            '#BCBD22',  # Olive
            '#17BECF'   # Cyan
        ]
        
        # Assign colors to each scheme
        color_map = {mf['scheme_name']: scheme_colors[i % len(scheme_colors)] for i, mf in enumerate(mf_data)}
        
        # Create subplots with more spacing
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=(
                "Performance Comparison (Gain %)",
                "Value Distribution",
                "Scheme-wise Holdings",
                ""
            ),
            specs=[
                [{"type": "bar"}, {"type": "pie"}],
                [{"type": "table", "colspan": 2}, None]
            ],
            vertical_spacing=0.20,  # Increased spacing
            horizontal_spacing=0.1,
            row_heights=[0.45, 0.55]  # More space for table
        )
        
        # Extract data
        schemes = [mf['scheme_name'][:30] + "..." if len(mf['scheme_name']) > 30 else mf['scheme_name'] for mf in mf_data]
        full_schemes = [mf['scheme_name'] for mf in mf_data]
        gains = [mf['gain_pct'] for mf in mf_data]
        values = [mf['value'] for mf in mf_data]
        units = [mf['units'] for mf in mf_data]
        navs = [mf['nav'] for mf in mf_data]
        
        # Get colors for each scheme (consistent across charts)
        bar_colors = [color_map[mf['scheme_name']] for mf in mf_data]
        
        # 1. Performance Bar Chart with consistent colors
        fig.add_trace(
            go.Bar(
                x=schemes,
                y=gains,
                marker_color=bar_colors,
                text=[f"{g:.2f}%" for g in gains],
                textposition='auto',
                name="Gain %",
                showlegend=False
            ),
            row=1, col=1
        )
        
        # Add average line
        avg_gain = sum(gains) / len(gains)
        fig.add_shape(
            type="line",
            x0=-0.5, y0=avg_gain,
            x1=len(schemes)-0.5, y1=avg_gain,
            line=dict(color="black", width=2, dash="dash"),
            row=1, col=1
        )
        
        fig.add_annotation(
            x=len(schemes)-0.5, y=avg_gain,
            text=f"Avg: {avg_gain:.2f}%",
            showarrow=True,
            arrowhead=1,
            row=1, col=1
        )
        
        # 2. Pie Chart - Value Distribution with same colors
        fig.add_trace(
            go.Pie(
                labels=schemes,
                values=values,
                textinfo='percent',
                hovertemplate='<b>%{label}</b><br>Value: ₹%{value:,.2f}<br>%{percent}<extra></extra>',
                marker=dict(colors=bar_colors),
                showlegend=True,
                name=""
            ),
            row=1, col=2
        )
        
        # 3. Holdings Table (positioned lower)
        table_data = []
        for mf in mf_data:
            scheme_name = mf['scheme_name'][:40] + "..." if len(mf['scheme_name']) > 40 else mf['scheme_name']
            table_data.append([
                scheme_name,
                f"{mf['units']:.2f}",
                f"₹{mf['nav']:.2f}",
                f"₹{mf['value']:,.2f}",
                f"{mf['gain_pct']:.2f}%"
            ])
        
        transposed_data = list(map(list, zip(*table_data)))
        
        # Color code gain column
        gain_colors = ['green' if mf['gain_pct'] >= 0 else 'red' for mf in mf_data]
        
        fig.add_trace(
            go.Table(
                header=dict(
                    values=['<b>Scheme Name</b>', '<b>Units</b>', '<b>NAV</b>', '<b>Current Value</b>', '<b>Gain %</b>'],
                    line_color='white',
                    fill_color=COLORS['primary'],
                    align='left',
                    font=dict(color='white', size=12)
                ),
                cells=dict(
                    values=transposed_data,
                    line_color='white',
                    fill_color=[[COLORS['background'], '#E6F2FF'] * len(mf_data)],
                    align='left',
                    font=dict(
                        color=[
                            [COLORS['text']] * len(mf_data),
                            [COLORS['text']] * len(mf_data),
                            [COLORS['text']] * len(mf_data),
                            [COLORS['text']] * len(mf_data),
                            gain_colors
                        ],
                        size=11
                    ),
                    height=30
                )
            ),
            row=2, col=1
        )
        
        # Update layout
        fig.update_layout(
            title_text="<b>Mutual Fund Portfolio Overview</b>",
            title_font=dict(size=24, color=COLORS['text']),
            font=dict(family="Arial, sans-serif", size=12, color=COLORS['text']),
            paper_bgcolor=COLORS['background'],
            plot_bgcolor=COLORS['background'],
            height=1100,  # Increased height for better spacing
            margin=dict(l=40, r=40, t=120, b=40),  # More top margin
            legend=dict(
                orientation="v",
                yanchor="top",
                y=0.98,
                xanchor="right",
                x=0.98,
                bgcolor="rgba(255, 255, 255, 0.8)",
                bordercolor="gray",
                borderwidth=1,
                font=dict(size=10)
            )
        )
        
        # Update axes with more bottom margin for bar chart
        # fig.update_xaxes(title_text="", gridcolor="lightgray", tickangle=-45, row=1, col=1)
        fig.update_yaxes(title_text="Gain (%)", gridcolor="lightgray", row=1, col=1)
        
        # Add timestamp
        fig.add_annotation(
            text=f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            showarrow=False,
            xref="paper", yref="paper",
            x=0.01, y=0.01,
            font=dict(size=10, color=COLORS['neutral'])
        )
        
        # Convert to base64
        img_bytes = fig.to_image(format="png", width=1200, height=1100, scale=2)
        encoded = base64.b64encode(img_bytes).decode('ascii')
        
        return encoded


if __name__ == "__main__":
    # Test with sample data
    sample_mf_data = [
        {
            "scheme_name": "MOTILAL OSWAL MIDCAP FUND - DIRECT PLAN",
            "units": 96.559,
            "nav": 119.3549,
            "value": 11524.79,
            "gain_pct": 4.78
        },
        {
            "scheme_name": "MOTILAL OSWAL LARGE CAP FUND - DIRECT PLAN",
            "units": 808.836,
            "nav": 14.6721,
            "value": 11867.32,
            "gain_pct": 7.89
        },
        {
            "scheme_name": "MOTILAL OSWAL SMALL CAP FUND - DIRECT PLAN",
            "units": 802.603,
            "nav": 14.8176,
            "value": 11892.65,
            "gain_pct": 8.12
        }
    ]
    
    viz = MutualFundVisualizer()
    img = viz.generate_mf_performance(sample_mf_data)
    
    # Save test image
    import base64
    img_data = base64.b64decode(img)
    with open("test_mf_chart.png", "wb") as f:
        f.write(img_data)
    print("✅ Test chart saved as test_mf_chart.png")
