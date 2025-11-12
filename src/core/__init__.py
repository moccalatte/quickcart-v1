"""
QuickCart Core Module
Exposes core configuration, database, and Redis utilities.
"""

from src.core.config import settings
from src.core.database import Base, db_manager, get_audit_session, get_db_session
from src.core.redis import (
    get_cache_manager,
    get_payment_queue,
    get_rate_limiter,
    get_redis,
    get_session_manager,
    redis_client,
)

__all__ = [
    # Configuration
    "settings",
    # Database
    "Base",
    "db_manager",
    "get_db_session",
    "get_audit_session",
    # Redis
    "redis_client",
    "get_redis",
    "get_session_manager",
    "get_cache_manager",
    "get_rate_limiter",
    "get_payment_queue",
]
