"""
QuickCart Database Configuration and Connection Management

This module provides async database connections for:
1. Main operational database (db_store1)
2. Permanent audit database (db_audits)

Reference: docs/05-architecture.md, docs/06-data_schema.md
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import create_engine, event, pool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

from src.core.config import settings

logger = logging.getLogger(__name__)

# Base class for all ORM models
Base = declarative_base()


class DatabaseManager:
    """
    Manages database connections and sessions for main and audit databases.

    Best Practice (CR-003): Separate audit database for permanent compliance logs
    """

    def __init__(self):
        """Initialize database engines and session factories"""

        # Main Database Engine (Operational Data)
        self.main_engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
            pool_size=settings.db_pool_size,
            max_overflow=settings.db_max_overflow,
            pool_timeout=settings.db_pool_timeout,
            pool_recycle=settings.db_pool_recycle,
            pool_pre_ping=True,  # Verify connections before using
        )

        # Audit Database Engine (Permanent Logs)
        self.audit_engine = create_async_engine(
            settings.audit_database_url,
            echo=settings.debug,
            pool_size=settings.audit_db_pool_size,
            max_overflow=settings.audit_db_max_overflow,
            pool_timeout=settings.db_pool_timeout,
            pool_pre_ping=True,
        )

        # Session factories
        self.main_session_factory = async_sessionmaker(
            self.main_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        self.audit_session_factory = async_sessionmaker(
            self.audit_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        logger.info("Database engines initialized successfully")

    @asynccontextmanager
    async def get_main_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get async session for main operational database

        Usage:
            async with db_manager.get_main_session() as session:
                # Perform database operations
                result = await session.execute(query)
        """
        async with self.main_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Database transaction failed: {e}")
                raise
            finally:
                await session.close()

    @asynccontextmanager
    async def get_audit_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get async session for audit database (write-only for compliance)

        Usage:
            async with db_manager.get_audit_session() as session:
                # Log audit event
                await session.execute(insert_audit_log)
        """
        async with self.audit_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Audit log write failed: {e}")
                # Critical: Audit failures must be escalated
                raise
            finally:
                await session.close()

    async def create_all_tables(self) -> None:
        """
        Create all database tables (development/testing only)

        Production uses Alembic migrations instead
        """
        async with self.main_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with self.audit_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("Database tables created successfully")

    async def drop_all_tables(self) -> None:
        """
        Drop all database tables (testing only - DANGEROUS)

        WARNING: This will delete all data!
        """
        if settings.is_production:
            raise RuntimeError("Cannot drop tables in production!")

        async with self.main_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

        async with self.audit_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

        logger.warning("All database tables dropped")

    async def check_connection(self) -> dict:
        """
        Health check for database connections

        Returns:
            dict: Status of main and audit database connections
        """
        status = {"main_db": "unknown", "audit_db": "unknown"}

        try:
            async with self.main_engine.connect() as conn:
                from sqlalchemy import text

                await conn.execute(text("SELECT 1"))
                status["main_db"] = "ok"
        except Exception as e:
            status["main_db"] = f"error: {str(e)}"
            logger.error(f"Main database connection failed: {e}")

        try:
            async with self.audit_engine.connect() as conn:
                from sqlalchemy import text

                await conn.execute(text("SELECT 1"))
                status["audit_db"] = "ok"
        except Exception as e:
            status["audit_db"] = f"error: {str(e)}"
            logger.error(f"Audit database connection failed: {e}")

        return status

    async def close(self) -> None:
        """Close all database connections gracefully"""
        await self.main_engine.dispose()
        await self.audit_engine.dispose()
        logger.info("Database connections closed")


# Global database manager instance
db_manager = DatabaseManager()


# Dependency injection for FastAPI endpoints
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for main database session

    Usage in route:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db_session)):
            result = await db.execute(select(User))
            return result.scalars().all()
    """
    async with db_manager.get_main_session() as session:
        yield session


async def get_audit_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for audit database session

    Usage in route:
        @app.post("/log-action")
        async def log_action(audit_db: AsyncSession = Depends(get_audit_session)):
            await audit_db.execute(insert(AuditLog).values(...))
    """
    async with db_manager.get_audit_session() as session:
        yield session


# Event listeners for connection pool management
@event.listens_for(pool.Pool, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Set database-specific pragmas on connection (if needed)"""
    pass


@event.listens_for(pool.Pool, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Log connection checkout for debugging (development only)"""
    if settings.debug:
        logger.debug("Database connection checked out from pool")


@event.listens_for(pool.Pool, "checkin")
def receive_checkin(dbapi_conn, connection_record):
    """Log connection checkin for debugging (development only)"""
    if settings.debug:
        logger.debug("Database connection returned to pool")
