"""
User Model - QuickCart
Reference: docs/06-data_schema.md
"""

from datetime import datetime
from sqlalchemy import Boolean, Column, BigInteger, String, Numeric, DateTime
from sqlalchemy.orm import relationship
from src.core.database import Base


class User(Base):
    """
    User model for customers, resellers, and admins
    Primary key is Telegram user ID for seamless authentication
    """

    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True)  # Telegram User ID
    name = Column(String(255), nullable=False)
    username = Column(String(255), unique=True, nullable=True)
    email = Column(String(255), unique=True, nullable=True)
    whatsapp_number = Column(String(20), nullable=True)
    member_status = Column(
        String(10), nullable=False, default="customer"
    )  # customer/reseller/admin
    bank_id = Column(String(10), unique=True, nullable=False)  # 6-digit internal ID
    account_balance = Column(Numeric(15, 2), nullable=False, default=0.00)
    is_banned = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    orders = relationship("Order", back_populates="user", lazy="dynamic")

    def __repr__(self):
        return f"<User(id={self.id}, name={self.name}, status={self.member_status})>"

    @property
    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self.member_status == "admin"

    @property
    def is_reseller(self) -> bool:
        """Check if user is reseller"""
        return self.member_status == "reseller"

    @property
    def display_name(self) -> str:
        """Get display name (username or name)"""
        return self.username or self.name
