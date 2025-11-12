"""
Voucher and Cooldown Models
Reference: docs/06-data_schema.md, docs/03-prd.md (Giveaway System)
"""

from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    BigInteger,
    String,
    Numeric,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from src.core.database import Base


class Voucher(Base):
    """Promotional voucher model"""

    __tablename__ = "vouchers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    created_by = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    is_used = Column(Boolean, nullable=False, default=False)
    used_by = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    used_at = Column(DateTime, nullable=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    user = relationship("User", foreign_keys=[used_by])
    order = relationship("Order")

    def __repr__(self):
        return f"<Voucher(code={self.code}, amount={self.amount}, used={self.is_used})>"

    @property
    def is_valid(self) -> bool:
        """Check if voucher is still valid"""
        return not self.is_used and datetime.utcnow() < self.expires_at


class VoucherUsageCooldown(Base):
    """Track voucher usage cooldown (5 minutes between usage)"""

    __tablename__ = "voucher_usage_cooldown"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    last_voucher_used = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<VoucherCooldown(user_id={self.user_id}, expires={self.expires_at})>"
