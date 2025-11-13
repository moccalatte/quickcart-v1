"""
Bot Context Utilities
Provides database session and service access for bot handlers

Since bot handlers don't have FastAPI's dependency injection,
we need async context managers for accessing database sessions.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import db_manager
from src.repositories.order_repository import OrderRepository
from src.repositories.product_repository import ProductRepository
from src.repositories.user_repository import UserRepository
from src.services.user_service import UserService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session for bot handlers

    Usage:
        async with get_db() as db:
            user_repo = UserRepository(db)
            user = await user_repo.get_by_id(user_id)
    """
    async with db_manager.get_main_session() as session:
        yield session


@asynccontextmanager
async def get_user_repo() -> AsyncGenerator[UserRepository, None]:
    """
    Get user repository with session

    Usage:
        async with get_user_repo() as repo:
            user = await repo.get_by_id(user_id)
    """
    async with db_manager.get_main_session() as session:
        yield UserRepository(session)


@asynccontextmanager
async def get_product_repo() -> AsyncGenerator[ProductRepository, None]:
    """
    Get product repository with session

    Usage:
        async with get_product_repo() as repo:
            products = await repo.get_all_active()
    """
    async with db_manager.get_main_session() as session:
        yield ProductRepository(session)


@asynccontextmanager
async def get_order_repo() -> AsyncGenerator[OrderRepository, None]:
    """
    Get order repository with session

    Usage:
        async with get_order_repo() as repo:
            order = await repo.get_by_invoice_id(invoice_id)
    """
    async with db_manager.get_main_session() as session:
        yield OrderRepository(session)


@asynccontextmanager
async def get_user_service() -> AsyncGenerator[UserService, None]:
    """
    Get user service with session

    Usage:
        async with get_user_service() as service:
            user = await service.create_user(...)
    """
    async with db_manager.get_main_session() as session:
        yield UserService(session)


class BotContext:
    """
    Bot context manager for accessing multiple repositories/services

    Usage:
        async with BotContext() as ctx:
            user = await ctx.user_repo.get_by_id(user_id)
            products = await ctx.product_repo.get_all_active()
            await ctx.session.commit()
    """

    def __init__(self):
        self.session: AsyncSession = None
        self.user_repo: UserRepository = None
        self.product_repo: ProductRepository = None
        self.order_repo: OrderRepository = None
        self.user_service: UserService = None

    async def __aenter__(self):
        """Enter async context and create session"""
        self._session_cm = db_manager.get_main_session()
        self.session = await self._session_cm.__aenter__()

        # Initialize repositories and services
        self.user_repo = UserRepository(self.session)
        self.product_repo = ProductRepository(self.session)
        self.order_repo = OrderRepository(self.session)
        self.user_service = UserService(self.session)

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context and close session"""
        await self._session_cm.__aexit__(exc_type, exc_val, exc_tb)
