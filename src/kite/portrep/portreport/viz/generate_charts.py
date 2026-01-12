"""
Dynamic Portfolio Chart Generator
Reads mcp_summary.json and generates charts based on actual portfolio holdings.
"""

import os
import json
import base64
from datetime import datetime
from pathlib import Path

# Import visualization classes
import sys
sys.path.append(os.path.dirname(__file__))

from port_viz import PortfolioVisualizer
from sysmbol_utils import normalize_symbol
from mf_viz import MutualFundVisualizer


class PortfolioChartGenerator:
    def __init__(self, json_path, output_dir):
        """
        Initialize chart generator.
        
        Args:
            json_path: Path to mcp_summary.json
            output_dir: Directory to save chart images
        """
        self.json_path = json_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load portfolio data
        with open(json_path, 'r') as f:
            self.data = json.load(f)
        
        self.viz = PortfolioVisualizer()
        self.generated_charts = []
    
    def save_base64_image(self, encoded_str, filename):
        """Save base64 encoded image to file."""
        try:
            img_data = base64.b64decode(encoded_str)
            filepath = self.output_dir / filename
            with open(filepath, "wb") as f:
                f.write(img_data)
            print(f"✅ Saved: {filename}")
            self.generated_charts.append(str(filepath))
            return str(filepath)
        except Exception as e:
            print(f"❌ Error saving {filename}: {e}")
            return None
    
    def generate_market_sentiment(self):
        """Generate market sentiment dashboard (Indian indices)."""
        print("\n📊 Generating Market Sentiment Dashboard...")
        try:
            # Indian market indices
            indices = ['^NSEI', '^BSESN', '^NSEBANK', '^NSEMDCP50', '^INDIAVIX']
            
            sentiment_img = self.viz.generate_market_sentiment_dashboard(indices=indices)
            return self.save_base64_image(sentiment_img, "market_sentiment_dashboard.png")
        except Exception as e:
            print(f"❌ Market Sentiment Dashboard failed: {e}")
            return None
    
    def generate_portfolio_tracker(self):
        """Generate portfolio performance tracker with actual holdings."""
        print("\n📈 Generating Portfolio Performance Tracker...")
        
        # Extract stock symbols from holdings
        holdings = self.data.get('holdings', [])
        
        if not holdings:
            print("⚠️ No holdings found in portfolio")
            return None
        
        # Convert to Yahoo Finance format (add .NS for NSE stocks)
        symbols = [normalize_symbol(h['symbol']) for h in holdings]
        
        print(f"   - Tracking {len(symbols)} stocks: {', '.join(symbols)}")
        
        try:
            portfolio_img = self.viz.generate_portfolio_tracking(symbols=symbols)
            return self.save_base64_image(portfolio_img, "portfolio_performance_tracker.png")
        except Exception as e:
            print(f"❌ Portfolio Tracker failed: {e}")
            return None
    
    def generate_stock_analyses(self):
        """Generate technical analysis charts for each stock in portfolio."""
        print("\n🔍 Generating Individual Stock Analysis Charts...")
        
        holdings = self.data.get('holdings', [])
        
        if not holdings:
            print("⚠️ No holdings found for analysis")
            return []
        
        chart_paths = []
        
        for holding in holdings:
            symbol = holding['symbol']
            yahoo_symbol = normalize_symbol(symbol)
            
            print(f"   - Analyzing {symbol} ({yahoo_symbol})...")
            
            try:
                stock_img = self.viz.generate_stock_analysis(symbol=yahoo_symbol)
                filename = f"stock_analysis_{symbol}.png"
                path = self.save_base64_image(stock_img, filename)
                if path:
                    chart_paths.append(path)
            except Exception as e:
                print(f"     ❌ Failed to analyze {symbol}: {e}")
                continue
        
        return chart_paths
    
    def generate_mf_performance(self):
        """Generate mutual fund performance chart."""
        print("\n💰 Generating Mutual Fund Performance Chart...")
        
        # Extract MF data
        mutual_funds = self.data.get('mutual_funds', [])
        
        if not mutual_funds:
            print("⚠️ No mutual funds found in portfolio")
            return None
        
        print(f"   - Analyzing {len(mutual_funds)} mutual fund schemes")
        
        try:
            mf_viz = MutualFundVisualizer()
            mf_img = mf_viz.generate_mf_performance(mutual_funds)
            return self.save_base64_image(mf_img, "mf_performance_overview.png")
        except Exception as e:
            print(f"❌ MF Performance Chart failed: {e}")
            return None
    
    def generate_all_charts(self):
        """Generate all portfolio charts dynamically."""
        print("=" * 60)
        print("🚀 PORTFOLIO CHART GENERATOR")
        print("=" * 60)
        print(f"📂 Input: {self.json_path}")
        print(f"📂 Output: {self.output_dir}")
        
        # Display portfolio summary
        holdings = self.data.get('holdings', [])
        mutual_funds = self.data.get('mutual_funds', [])
        
        print(f"\n📊 Portfolio Summary:")
        print(f"   - Stocks: {len(holdings)}")
        print(f"   - Mutual Funds: {len(mutual_funds)}")
        
        if holdings:
            print(f"\n   Stock Holdings:")
            for h in holdings:
                print(f"      • {h['symbol']}: {h['qty']} shares @ ₹{h['avg']:.2f}")
        
        # Generate charts
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n⏰ Started at: {timestamp}")
        print("\n" + "=" * 60)
        
        # 1. Market Sentiment Dashboard
        self.generate_market_sentiment()
        
        # 2. Portfolio Performance Tracker
        self.generate_portfolio_tracker()
        
        # 3. Individual Stock Analyses (dynamic count)
        self.generate_stock_analyses()
        
        # 4. Mutual Fund Performance Chart
        self.generate_mf_performance()
        
        # Summary
        print("\n" + "=" * 60)
        print(f"✅ COMPLETED: Generated {len(self.generated_charts)} charts")
        print("=" * 60)
        
        for i, chart in enumerate(self.generated_charts, 1):
            print(f"   {i}. {os.path.basename(chart)}")
        
        print(f"\n📂 All charts saved to: {self.output_dir}")
        
        return self.generated_charts


def main():
    """Main entry point."""
    from dotenv import load_dotenv
    load_dotenv(override=True)
    
    # Paths logic
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent.parent.parent
    default_reports_dir = project_root / "data" / "reports"
    
    # Use environment variables with dynamic defaults
    json_path = Path(os.getenv("PORTFOLIO_SUMMARY_JSON_PATH", str(default_reports_dir / "mcp_summary.json")))
    output_dir = Path(os.getenv("CHARTS_DIR", str(script_dir / "charts")))
    
    # Verify JSON exists
    if not json_path.exists():
        print(f"❌ Error: {json_path} not found!")
        print("   Please run filter_mcp_data.py first to generate portfolio data.")
        return
    
    # Generate charts
    generator = PortfolioChartGenerator(json_path, output_dir)
    charts = generator.generate_all_charts()
    
    if charts:
        print(f"\n🎉 Success! Generated {len(charts)} charts for your portfolio.")
    else:
        print("\n⚠️ No charts were generated. Please check the errors above.")


if __name__ == "__main__":
    main()
