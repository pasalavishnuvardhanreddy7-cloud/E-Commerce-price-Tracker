"""
Headless Chart Visualization Engine
Generates dynamic Base64 PNG data strings with date filtering and interval aggregation.
"""

import io
import base64
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from typing import List, Dict, Any, Optional


class ChartGenerator:
    @staticmethod
    def generate_price_history_chart(
        records: List[Dict[str, Any]],
        product_title: str,
        target_price: Optional[float] = None,
        interval: str = "days",
    ) -> Optional[str]:
        if not records:
            return None

        df = pd.DataFrame(records)
        df["scraped_at"] = pd.to_datetime(df["scraped_at"])
        df = df.sort_values(by="scraped_at", ascending=True)

        # Map UI intervals to Pandas frequency rules
        interval_map = {
            "days": "D",
            "weeks": "W",
            "months": "ME",
            "years": "YE",
        }
        freq = interval_map.get(interval.lower(), "D")

        # Resample data if there are enough points and interval is larger than daily
        if freq != "D" and len(df) > 1:
            df = df.set_index("scraped_at").resample(freq).mean().dropna().reset_index()

        fig, ax = plt.subplots(figsize=(9.5, 4.5), dpi=100)
        ax.plot(
            df["scraped_at"],
            df["price"],
            marker="o",
            color="#2563eb",
            linewidth=2.2,
            label=f"Avg Price ({interval.capitalize()})",
        )

        if len(df) >= 3:
            df["ma"] = df["price"].rolling(window=3, min_periods=1).mean()
            ax.plot(df["scraped_at"], df["ma"], linestyle="--", color="#f59e0b", linewidth=1.6, label="Trend MA")

        if target_price:
            ax.axhline(y=target_price, color="#10b981", linestyle=":", linewidth=2, label=f"Target (${target_price:.2f})")

        ax.set_title(f"{product_title[:35]} — Price Trend ({interval.capitalize()})", fontsize=12, fontweight="bold", pad=10)
        ax.set_ylabel("Price ($)", fontsize=10)
        ax.grid(True, linestyle="--", alpha=0.5)
        ax.legend(loc="best", frameon=True)
        fig.autofmt_xdate()
        plt.tight_layout()

        buffer = io.BytesIO()
        plt.savefig(buffer, format="png", bbox_inches="tight")
        plt.close(fig)
        buffer.seek(0)
        return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("utf-8")

    @staticmethod
    def generate_price_distribution_chart(records: List[Dict[str, Any]], product_title: str) -> Optional[str]:
        if not records or len(records) < 1:
            return None

        df = pd.DataFrame(records)
        fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        ax.boxplot(df["price"], patch_artist=True, boxprops=dict(facecolor="#93c5fd"))
        ax.set_title(f"Price Spread: {product_title[:30]}", fontsize=12, fontweight="bold")
        ax.set_ylabel("Price ($)")
        ax.grid(True, linestyle="--", alpha=0.5)
        plt.tight_layout()

        buffer = io.BytesIO()
        plt.savefig(buffer, format="png", bbox_inches="tight")
        plt.close(fig)
        buffer.seek(0)
        return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("utf-8")

    generate_distribution_chart = generate_price_distribution_chart
