import numpy as np
import yfinance as yf
from datetime import datetime, timedelta

class FearAndGreedIndia:
    """
    Calculates a Fear & Greed Index for the Indian market based on:
    - India VIX (^INDIAVIX)
    - Nifty 50 momentum (^NSEI)
    - Safe Haven Ratio (optional)
    - Volume Change (optional, for portfolio/stocks)
    """
    def __init__(self, weights=None):
        # Default weights: equal importance
        if weights is None:
            self.weights = {'vix': 0.25, 'momentum': 0.25, 'safe_haven': 0.25, 'volume': 0.25}
        else:
            self.weights = weights
            
        # Ranges adjusted for Indian market
        self.ranges = {
            'vix': (10, 35),        # India VIX normal range
            'momentum': (-8, 8),    # Nifty 50 % change over period
            'safe_haven': (30, 70), # Optional
            'volume': (-50, 50)     # Optional
        }

    def _normalize(self, value, component_key):
        min_val, max_val = self.ranges[component_key]
        value = np.clip(value, min_val, max_val)
        normalized = (value - min_val) / (max_val - min_val)
        if component_key == 'vix':
            return 100 - (normalized * 100)
        elif component_key == 'safe_haven':
            return 100 - (normalized * 100)  # Invert for safe haven
        else:
            return normalized * 100

    def fetch_vix(self):
        """Fetch latest India VIX value"""
        vix_data = yf.Ticker("^INDIAVIX").history(period="1d")
        # Use iloc instead of [-1]
        return float(vix_data['Close'].iloc[-1])


    def fetch_momentum(self, days=7):
        """Calculate Nifty 50 momentum over the last 'days'"""
        nifty = yf.Ticker("^NSEI")
        hist = nifty.history(period=f"{days}d")
        if len(hist) < 2:
            return 0
        # Use iloc for position-based access
        start = hist['Close'].iloc[0]
        end = hist['Close'].iloc[-1]
        momentum = ((end - start) / start) * 100
        return momentum

    def calculate(self, safe_haven_ratio=50, volume_change=0):
        """
        Calculate Fear & Greed Index for India.
        safe_haven_ratio and volume_change are optional and can be passed manually.
        """
        vix = self.fetch_vix()
        momentum = self.fetch_momentum()
        
        norm_vix = self._normalize(vix, 'vix')
        norm_momentum = self._normalize(momentum, 'momentum')
        norm_safe_haven = self._normalize(safe_haven_ratio, 'safe_haven')
        norm_volume = self._normalize(volume_change, 'volume')
        
        index = (norm_vix * self.weights['vix'] +
                 norm_momentum * self.weights['momentum'] +
                 norm_safe_haven * self.weights['safe_haven'] +
                 norm_volume * self.weights['volume'])
        
        return np.clip(index, 0, 100)
