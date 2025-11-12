"""
Audit Repository - Compliance and Security Logging
Reference: docs/10-audit_architecture.md, docs/06-data_schema.md

Provides data access layer for audit logging to separate audit database.
All critical operations must be logged for regulatory compliance.
"""

from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.audit import AdminActionAudit, AuditLog, PaymentAuditLog


class AuditRepository:
    """
    Repository for audit log operations

    Important: Audit logs are write-mostly, stored in separate database,
    and NEVER deleted (permanent retention for compliance)
    """

    def __init__(self, audit_session: AsyncSession):
        """
        Initialize audit repository

        Args:
            audit_session: AsyncSession connected to audit database (separate from main)
        """
        self.session = audit_session

    async def log_action(
        self,
        actor_id: Optional[int],
        actor_type: str,
        entity_type: str,
        entity_id: str,
        action: str,
        before_state: Optional[Dict] = None,
        after_state: Optional[Dict] = None,
        context: Optional[Dict] = None,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        """
        Log any system action to audit trail

        Args:
            actor_id: User ID who performed action (None for system actions)
            actor_type: Type of actor (user/admin/system)
            entity_type: Type of entity affected (user/product/order/payment)
            entity_id: ID of entity affected
            action: Action performed (create/update/delete/login/payment)
            before_state: Entity state before action (JSON)
            after_state: Entity state after action (JSON)
            context: Additional context information (JSON)
            ip_address: IP address of actor (if available)

        Returns:
            Created audit log entry
        """
        audit_entry = AuditLog(
            timestamp=datetime.utcnow(),
            actor_id=actor_id,
            actor_type=actor_type,
            entity_type=entity_type,
            entity_id=str(entity_id),
            action=action,
            before_state=before_state,
            after_state=after_state,
            context=context,
            ip_address=ip_address,
        )

        self.session.add(audit_entry)
        await self.session.flush()
        return audit_entry

    async def log_payment_transaction(
        self,
        order_id: str,
        user_id: int,
        amount: str,
        payment_method: str,
        status: str,
        gateway_response: Optional[Dict] = None,
        metadata: Optional[Dict] = None,
    ) -> PaymentAuditLog:
        """
        Log payment transaction for financial compliance

        Args:
            order_id: Order invoice ID
            user_id: User ID making payment
            amount: Payment amount (as string to preserve precision)
            payment_method: Payment method (qris/account_balance)
            status: Payment status (pending/paid/failed/expired)
            gateway_response: Raw gateway response (JSON)
            metadata: Additional payment metadata (JSON)

        Returns:
            Created payment audit log entry
        """
        payment_log = PaymentAuditLog(
            timestamp=datetime.utcnow(),
            order_id=order_id,
            user_id=user_id,
            amount=amount,
            payment_method=payment_method,
            status=status,
            gateway_response=gateway_response,
            metadata=metadata,
        )

        self.session.add(payment_log)
        await self.session.flush()
        return payment_log

    async def log_admin_action(
        self,
        admin_id: int,
        command: str,
        target_entity: Optional[str],
        target_id: Optional[str],
        parameters: Optional[Dict],
        result: str,
        ip_address: Optional[str] = None,
    ) -> AdminActionAudit:
        """
        Log admin command execution for security audit

        Args:
            admin_id: Admin user ID
            command: Command executed (e.g., "/add", "/ban", "/giveaway")
            target_entity: Entity type affected (user/product/voucher)
            target_id: ID of affected entity
            parameters: Command parameters (JSON)
            result: Execution result (success/failure with details)
            ip_address: Admin IP address

        Returns:
            Created admin action audit entry
        """
        admin_log = AdminActionAudit(
            timestamp=datetime.utcnow(),
            admin_id=admin_id,
            command=command,
            target_entity=target_entity,
            target_id=target_id,
            parameters=parameters,
            result=result,
            ip_address=ip_address,
        )

        self.session.add(admin_log)
        await self.session.flush()
        return admin_log

    async def get_user_activity(
        self, user_id: int, limit: int = 100, offset: int = 0
    ) -> List[AuditLog]:
        """
        Get audit trail for specific user

        Args:
            user_id: User ID to query
            limit: Maximum records to return
            offset: Pagination offset

        Returns:
            List of audit log entries for user
        """
        query = (
            select(AuditLog)
            .where(AuditLog.actor_id == user_id)
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
            .offset(offset)
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_entity_history(
        self, entity_type: str, entity_id: str, limit: int = 50
    ) -> List[AuditLog]:
        """
        Get complete history of changes to an entity

        Args:
            entity_type: Type of entity (user/product/order)
            entity_id: Entity ID
            limit: Maximum records to return

        Returns:
            List of audit log entries for entity
        """
        query = (
            select(AuditLog)
            .where(
                AuditLog.entity_type == entity_type,
                AuditLog.entity_id == str(entity_id),
            )
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_payment_history(
        self, user_id: Optional[int] = None, limit: int = 100
    ) -> List[PaymentAuditLog]:
        """
        Get payment transaction history

        Args:
            user_id: Filter by user ID (None for all payments)
            limit: Maximum records to return

        Returns:
            List of payment audit logs
        """
        query = select(PaymentAuditLog).order_by(PaymentAuditLog.timestamp.desc())

        if user_id:
            query = query.where(PaymentAuditLog.user_id == user_id)

        query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_admin_actions(
        self, admin_id: Optional[int] = None, limit: int = 100
    ) -> List[AdminActionAudit]:
        """
        Get admin command execution history

        Args:
            admin_id: Filter by admin ID (None for all admins)
            limit: Maximum records to return

        Returns:
            List of admin action audit logs
        """
        query = select(AdminActionAudit).order_by(AdminActionAudit.timestamp.desc())

        if admin_id:
            query = query.where(AdminActionAudit.admin_id == admin_id)

        query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def search_logs(
        self,
        start_date: datetime,
        end_date: datetime,
        actor_id: Optional[int] = None,
        entity_type: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 1000,
    ) -> List[AuditLog]:
        """
        Search audit logs with filters

        Args:
            start_date: Start of date range
            end_date: End of date range
            actor_id: Filter by actor ID
            entity_type: Filter by entity type
            action: Filter by action type
            limit: Maximum records to return

        Returns:
            List of matching audit log entries
        """
        query = select(AuditLog).where(
            AuditLog.timestamp >= start_date, AuditLog.timestamp <= end_date
        )

        if actor_id:
            query = query.where(AuditLog.actor_id == actor_id)

        if entity_type:
            query = query.where(AuditLog.entity_type == entity_type)

        if action:
            query = query.where(AuditLog.action == action)

        query = query.order_by(AuditLog.timestamp.desc()).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_recent_security_events(
        self, hours: int = 24, limit: int = 100
    ) -> List[AuditLog]:
        """
        Get recent security-relevant events for monitoring

        Args:
            hours: Look back this many hours
            limit: Maximum records to return

        Returns:
            List of recent security-relevant audit logs
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        security_actions = [
            "login",
            "failed_login",
            "ban",
            "unban",
            "permission_change",
        ]

        query = (
            select(AuditLog)
            .where(
                AuditLog.timestamp >= cutoff_time, AuditLog.action.in_(security_actions)
            )
            .order_by(AuditLog.timestamp.desc())
            .limit(limit)
        )

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_user_actions(
        self, user_id: int, action: str, since: datetime
    ) -> int:
        """
        Count specific user actions since a given time
        Used for fraud detection and rate limiting

        Args:
            user_id: User ID
            action: Action type to count
            since: Count actions since this time

        Returns:
            Count of matching actions
        """
        from sqlalchemy import func

        query = select(func.count(AuditLog.id)).where(
            AuditLog.actor_id == user_id,
            AuditLog.action == action,
            AuditLog.timestamp >= since,
        )

        result = await self.session.execute(query)
        return result.scalar() or 0


from datetime import timedelta
