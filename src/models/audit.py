"""
Audit Log Models for Compliance
Reference: docs/10-audit_architecture.md, docs/06-data_schema.md
"""

from datetime import datetime
from sqlalchemy import Column, BigInteger, String, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB, INET
from src.core.database import Base


class AuditLog(Base):
    """
    Master audit log for all critical operations
    Stored in separate audit database (permanent retention)
    """

    __tablename__ = "audit_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    actor_id = Column(BigInteger, nullable=True)
    actor_type = Column(String(20), nullable=False)  # user/admin/system
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)  # create/update/delete/login
    before_state = Column(JSONB, nullable=True)
    after_state = Column(JSONB, nullable=True)
    context = Column(JSONB, nullable=True)
    ip_address = Column(INET, nullable=True)

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, entity={self.entity_type})>"


class PaymentAuditLog(Base):
    """Specialized audit log for payment transactions"""

    __tablename__ = "payment_audit_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    order_id = Column(String(20), nullable=False)
    user_id = Column(BigInteger, nullable=False)
    amount = Column(String(20), nullable=False)
    payment_method = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False)
    gateway_response = Column(JSONB, nullable=True)
    metadata = Column(JSONB, nullable=True)

    def __repr__(self):
        return f"<PaymentAuditLog(order={self.order_id}, status={self.status})>"


class AdminActionAudit(Base):
    """Audit trail for admin command executions"""

    __tablename__ = "admin_action_audit"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    admin_id = Column(BigInteger, nullable=False)
    command = Column(String(50), nullable=False)
    target_entity = Column(String(50), nullable=True)
    target_id = Column(String(50), nullable=True)
    parameters = Column(JSONB, nullable=True)
    result = Column(Text, nullable=False)
    ip_address = Column(INET, nullable=True)

    def __repr__(self):
        return f"<AdminActionAudit(admin={self.admin_id}, command={self.command})>"
