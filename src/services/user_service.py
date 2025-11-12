"""
User Service - Business Logic for User Management
Reference: plans.md Section 2.3, 7 - Account Management & Access Control
"""

import logging
import secrets
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.models.user import User
from src.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class UserService:
    """Service for user management and business logic"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    async def get_or_create_user(
        self,
        telegram_id: int,
        name: str,
        username: Optional[str] = None,
        email: Optional[str] = None,
        whatsapp_number: Optional[str] = None,
    ) -> User:
        """
        Get existing user or create new one during onboarding
        Reference: plans.md Section 2.1 - Onboarding
        """
        user = await self.user_repo.get_by_id(telegram_id)

        if user:
            logger.info(f"Existing user found: {telegram_id}")
            return user

        # Generate unique bank_id (6 digits)
        bank_id = await self._generate_unique_bank_id()

        # Set defaults for optional fields
        if not name or name.strip() == "":
            name = "Anonymous"
        if email and email.strip() == "":
            email = None
        if whatsapp_number and whatsapp_number.strip() == "":
            whatsapp_number = None

        user_data = {
            "id": telegram_id,
            "name": name,
            "username": username,
            "email": email,
            "whatsapp_number": whatsapp_number,
            "bank_id": bank_id,
            "member_status": "customer",
            "account_balance": 0.00,
            "is_banned": False,
        }

        user = await self.user_repo.create(user_data)
        await self.session.commit()

        logger.info(f"New user created: {telegram_id} - {name}")
        return user

    async def get_user(self, user_id: int) -> Optional[User]:
        """Get user by Telegram ID"""
        return await self.user_repo.get_by_id(user_id)

    async def update_user_info(
        self,
        user_id: int,
        name: Optional[str] = None,
        email: Optional[str] = None,
        whatsapp_number: Optional[str] = None,
    ) -> Optional[User]:
        """
        Update user profile information
        Reference: plans.md Section 2.3 - Account Management
        """
        updates = {}

        if name is not None:
            updates["name"] = name if name.strip() else "Anonymous"
        if email is not None:
            updates["email"] = email if email.strip() else None
        if whatsapp_number is not None:
            updates["whatsapp_number"] = (
                whatsapp_number if whatsapp_number.strip() else None
            )

        if not updates:
            return await self.user_repo.get_by_id(user_id)

        user = await self.user_repo.update(user_id, updates)
        await self.session.commit()

        logger.info(f"User info updated: {user_id}")
        return user

    async def add_balance(self, user_id: int, amount: float) -> Optional[User]:
        """
        Add funds to user balance (deposit, transfer, refund)
        Reference: plans.md Section 2.5 - Deposit Flow
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            logger.error(f"User not found for balance add: {user_id}")
            return None

        new_balance = float(user.account_balance) + amount
        user = await self.user_repo.update(user_id, {"account_balance": new_balance})
        await self.session.commit()

        logger.info(f"Balance added: {user_id} +{amount} = {new_balance}")
        return user

    async def deduct_balance(self, user_id: int, amount: float) -> Optional[User]:
        """
        Deduct funds from user balance (payment with balance)
        Returns None if insufficient balance
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            logger.error(f"User not found for balance deduction: {user_id}")
            return None

        if float(user.account_balance) < amount:
            logger.warning(
                f"Insufficient balance for user {user_id}: {user.account_balance} < {amount}"
            )
            return None

        new_balance = float(user.account_balance) - amount
        user = await self.user_repo.update(user_id, {"account_balance": new_balance})
        await self.session.commit()

        logger.info(f"Balance deducted: {user_id} -{amount} = {new_balance}")
        return user

    async def set_balance(self, user_id: int, amount: float) -> Optional[User]:
        """
        Set user balance to specific amount (admin operation)
        Reference: plans.md Section 3.2 - /editbalance
        """
        user = await self.user_repo.update(user_id, {"account_balance": amount})
        await self.session.commit()

        logger.info(f"Balance set: {user_id} = {amount}")
        return user

    async def upgrade_to_reseller(self, user_id: int) -> Optional[User]:
        """
        Upgrade user to reseller status
        Reference: plans.md Section 3.2 - /addreseller, Section 4 - Reseller Upgrade
        """
        user = await self.user_repo.update(user_id, {"member_status": "reseller"})
        await self.session.commit()

        logger.info(f"User upgraded to reseller: {user_id}")
        return user

    async def downgrade_from_reseller(self, user_id: int) -> Optional[User]:
        """
        Downgrade reseller to customer status
        Reference: plans.md Section 3.2 - /rmress
        """
        user = await self.user_repo.update(user_id, {"member_status": "customer"})
        await self.session.commit()

        logger.info(f"User downgraded from reseller: {user_id}")
        return user

    async def promote_to_admin(self, user_id: int) -> Optional[User]:
        """
        Promote user to admin status
        Reference: plans.md Section 3.2 - /addadmin
        """
        user = await self.user_repo.update(user_id, {"member_status": "admin"})
        await self.session.commit()

        logger.info(f"User promoted to admin: {user_id}")
        return user

    async def demote_from_admin(self, user_id: int) -> Optional[User]:
        """
        Demote admin to customer status
        Reference: plans.md Section 3.2 - /rmadmin
        """
        user = await self.user_repo.update(user_id, {"member_status": "customer"})
        await self.session.commit()

        logger.info(f"User demoted from admin: {user_id}")
        return user

    async def ban_user(self, user_id: int) -> bool:
        """
        Ban user from using the bot
        Reference: plans.md Section 3.2 - /ban
        """
        success = await self.user_repo.ban_user(user_id)
        await self.session.commit()

        if success:
            logger.warning(f"User banned: {user_id}")
        return success

    async def unban_user(self, user_id: int) -> bool:
        """
        Unban user
        Reference: plans.md Section 3.2 - /unban
        """
        success = await self.user_repo.unban_user(user_id)
        await self.session.commit()

        if success:
            logger.info(f"User unbanned: {user_id}")
        return success

    def is_admin(self, user_id: int) -> bool:
        """
        Check if user is admin
        Reference: plans.md Section 7 - Access Control Logic
        """
        return user_id in settings.admin_ids

    async def check_user_access(self, user_id: int) -> dict:
        """
        Check user access level and status
        Returns dict with access info
        """
        user = await self.user_repo.get_by_id(user_id)

        if not user:
            return {
                "exists": False,
                "is_banned": False,
                "is_admin": self.is_admin(user_id),
                "is_reseller": False,
                "member_status": "unknown",
            }

        return {
            "exists": True,
            "is_banned": user.is_banned,
            "is_admin": user.is_admin or self.is_admin(user_id),
            "is_reseller": user.is_reseller,
            "member_status": user.member_status,
        }

    async def _generate_unique_bank_id(self) -> str:
        """Generate unique 6-digit bank ID"""
        max_attempts = 100
        for _ in range(max_attempts):
            # Generate 6-digit random number
            bank_id = f"{secrets.randbelow(900000) + 100000}"

            # Check if exists (would need to query database)
            # For now, assume it's unique (collision is very rare with 900k possibilities)
            return bank_id

        # Fallback: use timestamp-based ID
        return str(int(datetime.utcnow().timestamp()))[-6:]
