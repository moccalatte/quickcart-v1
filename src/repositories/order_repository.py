"""
Order Repository - Data Access for Order Operations
Reference: docs/06-data_schema.md (CR-002: One Active Order Per User)
"""

from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.order import Order, OrderItem
from src.models.product import ProductStock


class OrderRepository:
    """
    Repository for order data access
    Implements CR-002: Only one pending order per user at a time
    """

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, order_id: int) -> Optional[Order]:
        """Get order by ID with items"""
        result = await self.session.execute(select(Order).where(Order.id == order_id))
        return result.scalar_one_or_none()

    async def get_by_invoice_id(self, invoice_id: str) -> Optional[Order]:
        """Get order by invoice ID"""
        result = await self.session.execute(
            select(Order).where(Order.invoice_id == invoice_id)
        )
        return result.scalar_one_or_none()

    async def has_pending_order(self, user_id: int) -> bool:
        """
        Check if user has pending order (CR-002 enforcement)

        Business Rule: Only one pending order allowed per user at a time

        Args:
            user_id: User's Telegram ID

        Returns:
            True if user has pending order
        """
        result = await self.session.execute(
            select(func.count(Order.id)).where(
                and_(Order.user_id == user_id, Order.status == "pending")
            )
        )
        count = result.scalar_one()
        return count > 0

    async def get_pending_order(self, user_id: int) -> Optional[Order]:
        """Get user's current pending order if exists"""
        result = await self.session.execute(
            select(Order)
            .where(and_(Order.user_id == user_id, Order.status == "pending"))
            .order_by(desc(Order.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def create(self, order_data: dict) -> Order:
        """
        Create new order

        Note: Caller must check has_pending_order() first (CR-002)
        """
        order = Order(**order_data)
        self.session.add(order)
        await self.session.flush()
        await self.session.refresh(order)
        return order

    async def add_order_item(self, order_id: int, item_data: dict) -> OrderItem:
        """Add item to order"""
        item = OrderItem(order_id=order_id, **item_data)
        self.session.add(item)
        await self.session.flush()
        return item

    async def update_status(self, order_id: int, new_status: str) -> Optional[Order]:
        """Update order status"""
        order = await self.get_by_id(order_id)
        if order:
            order.status = new_status
            order.updated_at = datetime.utcnow()
            await self.session.flush()
            await self.session.refresh(order)
        return order

    async def cancel_order(self, order_id: int) -> bool:
        """
        Cancel order and release stock

        Args:
            order_id: Order ID to cancel

        Returns:
            True if cancelled successfully
        """
        order = await self.get_by_id(order_id)
        if not order:
            return False

        # Update order status
        order.status = "cancelled"
        order.updated_at = datetime.utcnow()

        # Release stock items back to inventory
        for item in order.items:
            stock = await self.session.get(ProductStock, item.stock_id)
            if stock:
                stock.is_sold = False
                stock.order_id = None
                stock.updated_at = datetime.utcnow()

        await self.session.flush()
        return True

    async def expire_order(self, order_id: int) -> bool:
        """
        Mark order as expired and release stock
        Called when payment expires (10 minutes)

        Args:
            order_id: Order ID to expire

        Returns:
            True if expired successfully
        """
        order = await self.get_by_id(order_id)
        if not order or order.status != "pending":
            return False

        # Update order status
        order.status = "expired"
        order.updated_at = datetime.utcnow()

        # Release stock items
        for item in order.items:
            stock = await self.session.get(ProductStock, item.stock_id)
            if stock:
                stock.is_sold = False
                stock.order_id = None
                stock.updated_at = datetime.utcnow()

        await self.session.flush()
        return True

    async def complete_order(self, order_id: int) -> Optional[Order]:
        """
        Mark order as paid/completed

        Args:
            order_id: Order ID to complete

        Returns:
            Completed order or None if not found
        """
        order = await self.get_by_id(order_id)
        if order:
            order.status = "paid"
            order.updated_at = datetime.utcnow()
            await self.session.flush()
            await self.session.refresh(order)
        return order

    async def get_user_orders(
        self, user_id: int, limit: int = 50, offset: int = 0
    ) -> List[Order]:
        """
        Get user's order history (paginated)

        Args:
            user_id: User's Telegram ID
            limit: Max orders to return
            offset: Pagination offset

        Returns:
            List of orders (newest first)
        """
        result = await self.session.execute(
            select(Order)
            .where(Order.user_id == user_id)
            .order_by(desc(Order.created_at))
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def get_recent_orders_count(self, user_id: int, hours: int = 1) -> int:
        """
        Get count of recent orders for fraud detection

        Args:
            user_id: User's Telegram ID
            hours: Time window in hours

        Returns:
            Number of orders in time window
        """
        since = datetime.utcnow() - timedelta(hours=hours)
        result = await self.session.execute(
            select(func.count(Order.id)).where(
                and_(Order.user_id == user_id, Order.created_at >= since)
            )
        )
        return result.scalar_one()

    async def get_failed_payment_count(self, user_id: int, days: int = 7) -> int:
        """
        Get count of failed/expired payments for fraud detection

        Args:
            user_id: User's Telegram ID
            days: Time window in days

        Returns:
            Number of failed payments
        """
        since = datetime.utcnow() - timedelta(days=days)
        result = await self.session.execute(
            select(func.count(Order.id)).where(
                and_(
                    Order.user_id == user_id,
                    Order.status.in_(["expired", "cancelled"]),
                    Order.created_at >= since,
                )
            )
        )
        return result.scalar_one()

    async def get_total_spent(self, user_id: int) -> float:
        """Get total amount spent by user"""
        result = await self.session.execute(
            select(func.sum(Order.total_bill)).where(
                and_(Order.user_id == user_id, Order.status == "paid")
            )
        )
        total = result.scalar_one()
        return float(total) if total else 0.0

    async def get_expired_payments(self, limit: int = 100) -> List[Order]:
        """
        Get pending orders that should be expired
        Used by background worker to process expired payments

        Args:
            limit: Max orders to process at once

        Returns:
            List of orders pending expiry processing
        """
        expiry_time = datetime.utcnow() - timedelta(minutes=10)
        result = await self.session.execute(
            select(Order)
            .where(
                and_(
                    Order.status == "pending",
                    Order.created_at <= expiry_time,
                )
            )
            .limit(limit)
        )
        return result.scalars().all()

    async def get_order_stats(self) -> dict:
        """
        Get overall order statistics
        Used for admin dashboard and monitoring

        Returns:
            Dictionary with order statistics
        """
        # Total orders
        total_result = await self.session.execute(select(func.count(Order.id)))
        total_orders = total_result.scalar_one()

        # Paid orders
        paid_result = await self.session.execute(
            select(func.count(Order.id)).where(Order.status == "paid")
        )
        paid_orders = paid_result.scalar_one()

        # Total revenue
        revenue_result = await self.session.execute(
            select(func.sum(Order.total_bill)).where(Order.status == "paid")
        )
        total_revenue = revenue_result.scalar_one() or 0

        # Today's orders
        today_start = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        today_result = await self.session.execute(
            select(func.count(Order.id)).where(
                and_(Order.created_at >= today_start, Order.status == "paid")
            )
        )
        today_orders = today_result.scalar_one()

        return {
            "total_orders": total_orders,
            "paid_orders": paid_orders,
            "total_revenue": float(total_revenue),
            "today_orders": today_orders,
            "success_rate": (paid_orders / total_orders * 100)
            if total_orders > 0
            else 0,
        }
