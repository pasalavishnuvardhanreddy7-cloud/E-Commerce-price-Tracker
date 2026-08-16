from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any


@dataclass
class PriceRecord:
    price: float
    in_stock: bool = True
    rating: Optional[float] = None
    scraped_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: Optional[int] = None
    product_id: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "product_id": self.product_id,
            "price": round(self.price, 2),
            "in_stock": self.in_stock,
            "rating": self.rating,
            "scraped_at": self.scraped_at.isoformat() if self.scraped_at else None,
        }


@dataclass
class Product:
    title: str
    url: str
    category: Optional[str] = None
    target_price: Optional[float] = None
    is_active: bool = True
    id: Optional[int] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    price_history: List[PriceRecord] = field(default_factory=list)

    @property
    def current_price(self) -> Optional[float]:
        if not self.price_history:
            return None
        sorted_records = sorted(
            self.price_history,
            key=lambda x: x.scraped_at,
            reverse=True,
        )
        return sorted_records[0].price

    @property
    def lowest_price(self) -> Optional[float]:
        if not self.price_history:
            return None
        return min(record.price for record in self.price_history)

    @property
    def highest_price(self) -> Optional[float]:
        if not self.price_history:
            return None
        return max(record.price for record in self.price_history)

    @property
    def price_change_percentage(self) -> float:
        if len(self.price_history) < 2:
            return 0.0

        sorted_records = sorted(self.price_history, key=lambda x: x.scraped_at)
        initial_price = sorted_records[0].price
        latest_price = sorted_records[-1].price

        if initial_price == 0:
            return 0.0

        return round(((latest_price - initial_price) / initial_price) * 100, 2)

    @property
    def is_target_met(self) -> bool:
        if self.target_price is None or self.current_price is None:
            return False
        return self.current_price <= self.target_price

    def add_price_record(self, record: PriceRecord) -> None:
        record.product_id = self.id
        self.price_history.append(record)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "category": self.category,
            "target_price": self.target_price,
            "is_active": self.is_active,
            "current_price": self.current_price,
            "lowest_price": self.lowest_price,
            "highest_price": self.highest_price,
            "price_change_percentage": self.price_change_percentage,
            "is_target_met": self.is_target_met,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "price_history": [rec.to_dict() for rec in self.price_history],
        }
