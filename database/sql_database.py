"""
Database Layer: Multi-Tenant Schema with Eager Loading
"""

import os
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, joinedload

Base = declarative_base()

class UserModel(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    products = relationship("ProductModel", back_populates="user", cascade="all, delete-orphan")


class CategoryModel(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    products = relationship("ProductModel", back_populates="category")


class ProductModel(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    title = Column(String(500), nullable=False)
    url = Column(String(2048), nullable=False)
    target_price = Column(Float, nullable=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("UserModel", back_populates="products")
    # lazy="joined" prevents DetachedInstanceError when accessing product.category
    category = relationship("CategoryModel", back_populates="products", lazy="joined")
    price_history = relationship("PriceHistoryModel", back_populates="product", cascade="all, delete-orphan")


class PriceHistoryModel(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    price = Column(Float, nullable=False)
    in_stock = Column(Boolean, default=True)
    rating = Column(Float, nullable=True)
    scraped_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    product = relationship("ProductModel", back_populates="price_history")


class ScrapeLogModel(Base):
    __tablename__ = "scrape_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(String(50), nullable=False)
    products_checked = Column(Integer, default=0)
    duration_seconds = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class SQLDatabase:
    def __init__(self, db_url: Optional[str] = None) -> None:
        self.db_url = db_url or os.getenv("DATABASE_URL", "sqlite:///data/price_tracker.db")
        os.makedirs(os.path.dirname(self.db_url.replace("sqlite:///", "")) or ".", exist_ok=True)
        self.engine = create_engine(
            self.db_url,
            connect_args={"check_same_thread": False} if "sqlite" in self.db_url else {}
        )
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
            bind=self.engine
        )

    def init_db(self) -> None:
        Base.metadata.create_all(bind=self.engine)

    def get_or_create_user(self, email: str) -> UserModel:
        with self.SessionLocal() as session:
            user = session.query(UserModel).filter_by(email=email.lower().strip()).first()
            if not user:
                user = UserModel(email=email.lower().strip())
                session.add(user)
                session.commit()
                session.refresh(user)
            return user

    def add_product(self, title: str, url: str, target_price: Optional[float] = None, category_name: Optional[str] = None, user_id: Optional[int] = None) -> ProductModel:
        with self.SessionLocal() as session:
            existing = session.query(ProductModel).options(joinedload(ProductModel.category)).filter_by(url=url, user_id=user_id).first()
            if existing:
                if target_price is not None:
                    existing.target_price = target_price
                    session.commit()
                    session.refresh(existing)
                return existing

            cat = None
            if category_name:
                cat = session.query(CategoryModel).filter_by(name=category_name).first()
                if not cat:
                    cat = CategoryModel(name=category_name)
                    session.add(cat)
                    session.flush()

            product = ProductModel(
                title=title,
                url=url,
                target_price=target_price,
                category_id=cat.id if cat else None,
                user_id=user_id,
            )
            session.add(product)
            session.commit()
            session.refresh(product)
            # Access category once inside the active session so it is cached on the object
            _ = product.category
            return product

    def get_user_products(self, user_id: int, active_only: bool = False) -> List[ProductModel]:
        with self.SessionLocal() as session:
            query = session.query(ProductModel).options(joinedload(ProductModel.category)).filter_by(user_id=user_id)
            if active_only:
                query = query.filter_by(is_active=True)
            return query.all()

    def get_all_products(self, active_only: bool = False) -> List[ProductModel]:
        with self.SessionLocal() as session:
            query = session.query(ProductModel).options(joinedload(ProductModel.category))
            if active_only:
                query = query.filter_by(is_active=True)
            return query.all()

    def get_product_by_id(self, product_id: int) -> Optional[ProductModel]:
        with self.SessionLocal() as session:
            return session.query(ProductModel).options(joinedload(ProductModel.category)).filter_by(id=product_id).first()

    def add_price_record(self, product_id: int, price: float, in_stock: bool = True, rating: Optional[float] = None) -> PriceHistoryModel:
        with self.SessionLocal() as session:
            rec = PriceHistoryModel(product_id=product_id, price=price, in_stock=in_stock, rating=rating)
            session.add(rec)
            session.commit()
            session.refresh(rec)
            return rec

    def get_price_history(self, product_id: int, limit: int = 1000) -> List[PriceHistoryModel]:
        with self.SessionLocal() as session:
            return session.query(PriceHistoryModel).filter_by(product_id=product_id).order_by(PriceHistoryModel.scraped_at.desc()).limit(limit).all()

    def log_scrape_run(self, status: str, products_checked: int, duration_seconds: float) -> None:
        with self.SessionLocal() as session:
            session.add(ScrapeLogModel(status=status, products_checked=products_checked, duration_seconds=duration_seconds))
            session.commit()
