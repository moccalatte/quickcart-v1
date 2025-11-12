"""
Order and OrderItem Models
Reference: docs/06-data_schema.md (CR-002: One Active Order Per User)
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Numeric,
    DateTime,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.core.database import Base


class Order(Base):
    """
    Order model - tracks user purchases
    Business Rule (CR-002): Only one pending order per user at a time
    """

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(String(20), unique=True, nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    subtotal = Column(Numeric(15, 2), nullable=False)
    voucher_discount = Column(Numeric(15, 2), nullable=False, default=0.00)
    payment_fee = Column(Numeric(15, 2), nullable=False, default=0.00)
    total_bill = Column(Numeric(15, 2), nullable=False)
    payment_method = Column(String(20), nullable=False)  # qris/account_balance
    status = Column(
        String(10), nullable=False, default="pending"
    )  # pending/paid/expired/cancelled
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", lazy="joined")

    def __repr__(self):
        return f"<Order(id={self.id}, invoice={self.invoice_id}, status={self.status})>"

    @property
    def is_pending(self) -> bool:
        return self.status == "pending"

    @property
    def is_paid(self) -> bool:
        return self.status == "paid"


class OrderItem(Base):
    """Individual items within an order"""

    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    stock_id = Column(UUID(as_uuid=True), ForeignKey("product_stocks.id"), nullable=False)
    price_per_unit = Column(Numeric(15, 2), nullable=False)

    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product")
    stock = relationship("ProductStock")

    def __repr__(self):
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, product_id={self.product_id})>"
