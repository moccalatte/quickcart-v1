"""
User Repository - Data Access for User Operations
Reference: docs/06-data_schema.md
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.user import User


class UserRepository:
    """Repository for user data access"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by Telegram ID"""
        result = await self.session.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        result = await self.session.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def create(self, user_data: dict) -> User:
        """Create new user"""
        user = User(**user_data)
        self.session.add(user)
        await self.session.flush()
        return user

    async def update(self, user_id: int, updates: dict) -> Optional[User]:
        """Update user fields"""
        user = await self.get_by_id(user_id)
        if user:
            for key, value in updates.items():
                setattr(user, key, value)
            await self.session.flush()
        return user

    async def ban_user(self, user_id: int) -> bool:
        """Ban user"""
        user = await self.get_by_id(user_id)
        if user:
            user.is_banned = True
            await self.session.flush()
            return True
        return False

    async def unban_user(self, user_id: int) -> bool:
        """Unban user"""
        user = await self.get_by_id(user_id)
        if user:
            user.is_banned = False
            await self.session.flush()
            return True
        return False
