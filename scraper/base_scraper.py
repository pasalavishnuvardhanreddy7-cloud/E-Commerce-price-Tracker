import time
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import requests
from config import Config

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    def __init__(self, delay_seconds: float = 1.0) -> None:
        self.delay_seconds = delay_seconds
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": Config.USER_AGENT,
            "Accept-Language": "en-US,en;q=0.9",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })

    def fetch_html(self, url: str) -> Optional[str]:
        try:
            time.sleep(self.delay_seconds)
            logger.info(f"Fetching URL: {url}")
            response = self.session.get(url, timeout=Config.REQUEST_TIMEOUT)
            if response.status_code == 200:
                return response.text
            else:
                logger.warning(f"Failed to fetch {url} - Status Code: {response.status_code}")
                return None
        except requests.exceptions.Timeout:
            logger.error(f"Request timed out while fetching {url}")
            return None
        except requests.exceptions.RequestException as exc:
            logger.error(f"Network error while fetching {url}: {exc}")
            return None

    @abstractmethod
    def scrape_product(self, url: str) -> Optional[Dict[str, Any]]:
        pass
