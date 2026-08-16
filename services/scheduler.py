"""
Background Task Scheduler (APScheduler)
Executes scheduled background scrape intervals without blocking Flask.
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from config import Config
from services.price_tracker import PriceTrackerService

logger = logging.getLogger(__name__)


class PriceTrackerScheduler:
    """Manages recurring background scraping jobs."""

    def __init__(self, service: PriceTrackerService, interval_hours: int = None) -> None:
        self.service = service
        self.interval_hours = interval_hours or Config.SCRAPE_INTERVAL_HOURS
        self.scheduler = BackgroundScheduler(daemon=True)

    def _scheduled_job(self) -> None:
        """Periodic job entry point."""
        logger.info("[Scheduler] Starting automatic background scrape cycle...")
        try:
            result = self.service.track_all_products()
            logger.info(
                f"[Scheduler] Completed cycle: {result['products_checked']} checked, "
                f"{len(result.get('alerts', []))} alerts in {result['duration_seconds']}s"
            )
        except Exception as exc:
            logger.error(f"[Scheduler] Job failed: {exc}")

    def start(self) -> None:
        """Starts the scheduler in a background thread."""
        if not self.scheduler.running:
            self.scheduler.add_job(
                self._scheduled_job,
                "interval",
                hours=self.interval_hours,
                id="batch_price_scrape",
                replace_existing=True,
            )
            self.scheduler.start()
            logger.info(f"[Scheduler] Running on interval: every {self.interval_hours} hour(s)")

    def shutdown(self) -> None:
        """Gracefully terminates background worker threads."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
