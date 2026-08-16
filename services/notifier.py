"""
Notification Service Layer
Dispatches alert notifications when tracked items drop below target thresholds.
"""

import logging
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class NotificationService:
    """Handles dispatching price drop alerts via webhooks."""

    def __init__(self, webhook_url: Optional[str] = None) -> None:
        self.webhook_url = webhook_url

    def send_price_drop_alert(
        self,
        product_title: str,
        current_price: float,
        target_price: float,
        product_url: str,
    ) -> bool:
        """
        Sends an alert formatted for webhooks (e.g. Discord/Slack) or logs to console.
        """
        savings = round(target_price - current_price, 2)
        message = (
            f"🚨 **PRICE DROP ALERT!**\n"
            f"**Product:** {product_title}\n"
            f"**Current Price:** ${current_price:.2f}\n"
            f"**Target Price:** ${target_price:.2f}\n"
            f"**Savings:** ${savings:.2f}\n"
            f"**Store Link:** {product_url}"
        )

        logger.info(f"[Alert] Price drop triggered for '{product_title}' -> ${current_price:.2f} (Target: ${target_price:.2f})")

        if self.webhook_url:
            try:
                payload = {"content": message}
                response = requests.post(self.webhook_url, json=payload, timeout=5)
                if response.status_code in (200, 204):
                    logger.info("[Alert] Webhook notification delivered successfully.")
                    return True
                else:
                    logger.warning(f"[Alert] Webhook returned status: {response.status_code}")
                    return False
            except Exception as exc:
                logger.error(f"[Alert] Failed to send webhook: {exc}")
                return False
        
        # Fallback to local console notification if no webhook configured
        print("\n" + "="*50)
        print(message)
        print("="*50 + "\n")
        return True
