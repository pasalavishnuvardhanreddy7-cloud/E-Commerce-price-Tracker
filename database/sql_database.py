"""
SQL Relational Database Layer (SQLAlchemy ORM)
Manages structured products, price history checkpoints, and scrape logs.
"""

from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, joinedload
from config import Config

Base = declarative_base()


class CategoryModel(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)

    products = relationship("ProductModel", back_populates="category")


class ProductModel(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(255), nullable=False)
    url = Column(String(500), unique=True, nullable=False, index=True)
    target_price = Column(Float, nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    category = relationship("CategoryModel", back_populates="products")
    price_history = relationship(
        "PriceHistoryModel",
        back_populates="product",
        cascade="all, delete-orphan",
        order_by="desc(PriceHistoryModel.scraped_at)",
    )


class PriceHistoryModel(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    price = Column(Float, nullable=False)
    in_stock = Column(Boolean, default=True, nullable=False)
    rating = Column(Float, nullable=True)
    scraped_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    product = relationship("ProductModel", back_populates="price_history")


class ScrapeLogModel(Base):
    __tablename__ = "scrape_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scraped_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    status = Column(String(50), nullable=False)
    products_checked = Column(Integer, nullable=False)
    duration_seconds = Column(Float, nullable=False)


class SQLDatabase:
    """Manages SQLite / PostgreSQL connection pools and CRUD transactions."""

    def __init__(self, db_url: Optional[str] = None) -> None:
        self.db_url = db_url or getattr(Config, "DATABASE_URL", getattr(Config, "SQL_DATABASE_URI", "sqlite:///data/ecommerce.db"))
        self.engine = create_engine(self.db_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)

    def init_db(self) -> None:
        Base.metadata.create_all(self.engine)

    def get_or_create_category(self, category_name: str) -> CategoryModel:
        with self.SessionLocal() as session:
            category = session.query(CategoryModel).filter_by(name=category_name).first()
            if not category:
                category = CategoryModel(name=category_name)
                session.add(category)
                session.commit()
                session.refresh(category)
            return category

    def add_product(
        self,
        title: str,
        url: str,
        target_price: Optional[float] = None,
        category_name: Optional[str] = None,
    ) -> ProductModel:
        with self.SessionLocal() as session:
            product = session.query(ProductModel).filter_by(url=url).first()
            if product:
                return product

            category_id = None
            if category_name:
                category = self.get_or_create_category(category_name)
                category_id = category.id

            new_product = ProductModel(
                title=title,
                url=url,
                target_price=target_price,
                category_id=category_id,
            )
            session.add(new_product)
            session.commit()
            session.refresh(new_product)
            return new_product

    def add_price_record(
        self,
        product_id: int,
        price: float,
        in_stock: bool = True,
        rating: Optional[float] = None,
    ) -> PriceHistoryModel:
        with self.SessionLocal() as session:
            record = PriceHistoryModel(
                product_id=product_id,
                price=price,
                in_stock=in_stock,
                rating=rating,
                scraped_at=datetime.now(timezone.utc),
            )
            session.add(record)
            session.commit()
            session.refresh(record)
            return record

    def get_all_products(self, active_only: bool = True) -> List[ProductModel]:
        with self.SessionLocal() as session:
            query = session.query(ProductModel).options(joinedload(ProductModel.category))
            if active_only:
                query = query.filter_by(is_active=True)
            return query.all()

    def get_product_by_id(self, product_id: int) -> Optional[ProductModel]:
        with self.SessionLocal() as session:
            return (
                session.query(ProductModel)
                .options(joinedload(ProductModel.category))
                .filter(ProductModel.id == product_id)
                .first()
            )

    def get_price_history(self, product_id: int, limit: int = 50) -> List[PriceHistoryModel]:
        with self.SessionLocal() as session:
            return (
                session.query(PriceHistoryModel)
                .filter_by(product_id=product_id)
                .order_by(PriceHistoryModel.scraped_at.desc())
                .limit(limit)
                .all()
            )

    def log_scrape_run(
        self,
        status: str,
        products_checked: int,
        duration_seconds: float,
    ) -> ScrapeLogModel:
        with self.SessionLocal() as session:
            log_entry = ScrapeLogModel(
                status=status,
                products_checked=products_checked,
                duration_seconds=duration_seconds,
                scraped_at=datetime.now(timezone.utc),
            )
            session.add(log_entry)
            session.commit()
            session.refresh(log_entry)
            return log_entry
