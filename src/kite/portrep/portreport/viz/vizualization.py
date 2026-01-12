import base64
import os
from datetime import datetime

# Import your class
from port_viz import PortfolioVisualizer


def save_base64_image(encoded_str, filename):
    """Helper to save base64 image to PNG file."""
    try:
        img_data = base64.b64decode(encoded_str)
        with open(filename, "wb") as f:
            f.write(img_data)
        print(f"✅ Saved {filename}")
    except Exception as e:
        print(f"❌ Error saving {filename}: {e}")


def main():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("output", exist_ok=True)

    viz = PortfolioVisualizer()  # create class instance

    # --- Test Market Sentiment Dashboard ---
    try:
        sentiment_img = viz.generate_market_sentiment_dashboard()
        save_base64_image(sentiment_img, f"output/market_sentiment_{timestamp}.png")
    except Exception as e:
        print(f"❌ Market Sentiment Dashboard failed: {e}")

    # --- Test Portfolio Tracker ---
    try:
        portfolio_img = viz.generate_portfolio_tracking()
        save_base64_image(portfolio_img, f"output/portfolio_tracker_{timestamp}.png")
    except Exception as e:
        print(f"❌ Portfolio Tracker failed: {e}")

    # --- Test Stock Analysis (RELIANCE.NS as example) ---
    try:
        stock_img = viz.generate_stock_analysis(symbol="WIPRO.NS")
        save_base64_image(stock_img, f"output/stock_analysis_{timestamp}.png")
    except Exception as e:
        print(f"❌ Stock Analysis failed: {e}")


if __name__ == "__main__":
    main()
