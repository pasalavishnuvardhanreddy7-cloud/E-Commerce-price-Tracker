"""
Price Analytics Engine
Performs statistical transformations, moving averages, and discount analytics using Pandas and NumPy.
"""

from typing import List, Dict, Any, Optional
import numpy as np
import pandas as pd


class PriceAnalyzer:
    """Computes time-series statistical metrics on historical price data."""

    def __init__(self, records: List[Dict[str, Any]]) -> None:
        """
        Initializes the analyzer with a list of price dictionary records.
        Expected format: [{"price": float, "scraped_at": str or datetime, "in_stock": bool}]
        """
        self.df = pd.DataFrame(records)
        if not self.df.empty and "scraped_at" in self.df.columns:
            self.df["scraped_at"] = pd.to_datetime(self.df["scraped_at"])
            self.df = self.df.sort_values("scraped_at").reset_index(drop=True)

    def is_valid(self) -> bool:
        """Returns True if there is sufficient data for analysis."""
        return not self.df.empty and "price" in self.df.columns and len(self.df) > 0

    def compute_summary_statistics(self) -> Dict[str, Optional[float]]:
        """Calculates standard central tendency and dispersion metrics."""
        if not self.is_valid():
            return {
                "current_price": None,
                "min_price": None,
                "max_price": None,
                "mean_price": None,
                "median_price": None,
                "std_dev": None,
                "volatility_pct": None,
                "total_observations": 0,
            }

        prices = self.df["price"].to_numpy(dtype=float)
        mean_val = float(np.mean(prices))
        std_val = float(np.std(prices, ddof=1)) if len(prices) > 1 else 0.0

        return {
            "current_price": round(float(prices[-1]), 2),
            "min_price": round(float(np.min(prices)), 2),
            "max_price": round(float(np.max(prices)), 2),
            "mean_price": round(mean_val, 2),
            "median_price": round(float(np.median(prices)), 2),
            "std_dev": round(std_val, 2),
            "volatility_pct": round((std_val / mean_val * 100), 2) if mean_val > 0 else 0.0,
            "total_observations": int(len(prices)),
        }

    def compute_moving_averages(self, window_sizes: List[int] = [3, 7]) -> pd.DataFrame:
        """Calculates rolling window moving averages for trend analysis."""
        if not self.is_valid():
            return pd.DataFrame()

        df_ma = self.df[["scraped_at", "price"]].copy()
        for window in window_sizes:
            df_ma[f"ma_{window}"] = df_ma["price"].rolling(window=window, min_periods=1).mean().round(2)
        return df_ma

    def compute_percentiles(self) -> Dict[str, Optional[float]]:
        """Calculates 25th, 50th, and 75th percentiles."""
        if not self.is_valid():
            return {"p25": None, "p50": None, "p75": None}

        prices = self.df["price"].to_numpy(dtype=float)
        return {
            "p25": round(float(np.percentile(prices, 25)), 2),
            "p50": round(float(np.percentile(prices, 50)), 2),
            "p75": round(float(np.percentile(prices, 75)), 2),
        }

    def generate_recommendation(self, target_price: Optional[float] = None) -> Dict[str, Any]:
        """
        Generates actionable purchase advice based on target comparison 
        and historical discount percentiles.
        """
        if not self.is_valid():
            return {"action": "NO_DATA", "reason": "Insufficient historical data"}

        stats = self.compute_summary_statistics()
        current = stats["current_price"]
        min_p = stats["min_price"]
        mean_p = stats["mean_price"]

        if target_price is not None and current <= target_price:
            return {
                "action": "BUY_NOW",
                "reason": f"Target met! Current price (${current}) is at or below target (${target_price}).",
            }

        if current == min_p:
            return {
                "action": "BUY_NOW",
                "reason": f"All-time low! Current price (${current}) is the lowest recorded.",
            }

        if current < mean_p:
            return {
                "action": "CONSIDER",
                "reason": f"Good deal: Current price (${current}) is below historical average (${mean_p}).",
            }

        return {
            "action": "WAIT",
            "reason": f"Current price (${current}) is above historical average (${mean_p}).",
        }
