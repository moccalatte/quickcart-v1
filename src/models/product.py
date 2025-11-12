"""
Product and Stock Models
Reference: docs/06-data_schema.md
"""

from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    String,
    Text,
    Numeric,
    DateTime,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from src.core.database import Base


class Product(Base):
    """Product catalog model"""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True)  # Admin-defined ID (1-24)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(255), nullable=False, default="Uncategorized")
    customer_price = Column(Numeric(15, 2), nullable=False)
    reseller_price = Column(Numeric(15, 2), nullable=True)
    sold_count = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    stocks = relationship("ProductStock", back_populates="product", lazy="dynamic")

    def __repr__(self):
        return f"<Product(id={self.id}, name={self.name}, stock={self.available_stock})>"

    @property
    def available_stock(self) -> int:
        """Get available (unsold) stock count"""
        return self.stocks.filter_by(is_sold=False).count()

    def get_price_for_user(self, member_status: str) -> float:
        """Get appropriate price based on user status"""
        if member_status == "reseller" and self.reseller_price:
            return float(self.reseller_price)
        return float(self.customer_price)


class ProductStock(Base):
    """Individual stock items (digital content/keys)"""

    __tablename__ = "product_stocks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    content = Column(Text, nullable=False)  # Digital content/key/account
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    is_sold = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    product = relationship("Product", back_populates="stocks")
    order = relationship("Order", foreign_keys=[order_id])

    def __repr__(self):
        return f"<ProductStock(id={self.id}, product_id={self.product_id}, sold={self.is_sold})>"
