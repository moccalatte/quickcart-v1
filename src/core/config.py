"""
QuickCart Application Configuration
Simple configuration with sensible defaults - only essential vars required
"""

import os
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration - most settings have defaults"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ========================================
    # REQUIRED - Must be set in .env
    # ========================================

    telegram_bot_token: str = Field(
        ..., description="Telegram Bot API token from @BotFather"
    )
    admin_user_ids: str = Field(
        ..., description="Comma-separated Telegram user IDs for admins"
    )
    pakasir_api_key: str = Field(..., description="Pakasir API key")
    pakasir_project_slug: str = Field(..., description="Pakasir project slug")
    secret_key: str = Field(..., description="Secret key for sessions/JWT")
    encryption_key: str = Field(..., description="Encryption key for sensitive data")

    # ========================================
    # OPTIONAL - Has sensible defaults
    # ========================================

    # Environment
    environment: str = Field(default="development")
    debug: bool = Field(default=True)
    log_level: str = Field(default="INFO")

    # Database URLs
    # For Docker Compose (development): use db:5432
    # For separate VPS (production): use your VPS IP/hostname
    # Example: postgresql+asyncpg://user:pass@your-db-server.com:5432/dbname
    database_url: str = Field(
        ...,
        description="Main database URL - change 'localhost' to your PostgreSQL server IP/hostname",
    )
    audit_database_url: str = Field(
        ...,
        description="Audit database URL - can be same or different PostgreSQL server",
    )

    # Database pool settings
    db_pool_size: int = Field(default=5)
    db_max_overflow: int = Field(default=10)
    db_pool_timeout: int = Field(default=30)
    db_pool_recycle: int = Field(default=3600)

    # Audit database pool settings (smaller pool)
    audit_db_pool_size: int = Field(default=2)
    audit_db_max_overflow: int = Field(default=5)

    # Redis URL (optional - system works without Redis)
    # For Docker Compose (development): use redis:6379
    # For separate VPS (production): use your Redis server IP/hostname
    # Example: redis://:password@your-redis-server.com:6379/0
    redis_url: Optional[str] = Field(
        default=None,
        description="Redis URL - set to your Redis server IP/hostname, or None to disable",
    )

    # Session TTL (24 hours in seconds)
    session_ttl_seconds: int = Field(default=86400)

    # Pakasir settings
    pakasir_base_url: str = Field(default="https://app.pakasir.com")
    pakasir_payment_custom_domain: str = Field(default="https://pots.my.id")
    pakasir_webhook_secret: Optional[str] = Field(default=None)

    # Payment configuration (from PRD: 0.7% + Rp310)
    payment_fee_percentage: float = Field(default=0.007)  # 0.7%
    payment_fee_fixed: int = Field(default=310)  # Rp310
    payment_expiry_minutes: int = Field(default=10)  # 10 minutes

    # Voucher cooldown (5 minutes in seconds)
    voucher_cooldown_seconds: int = Field(default=300)

    # Refund multipliers (from PRD)
    refund_multiplier_under_7_days: float = Field(default=0.8)
    refund_multiplier_7_plus_days: float = Field(default=0.7)
    refund_multiplier_1_2_claims: float = Field(default=0.6)
    refund_multiplier_3_claims: float = Field(default=0.5)
    refund_multiplier_over_3_claims: float = Field(default=0.4)

    # Store settings (customizable for each deployment)
    store_name: str = Field(
        default="QuickCart Store", description="Store name shown in bot messages"
    )
    bot_name: str = Field(
        default="QuickCart Bot",
        description="Bot name shown in help and version messages",
    )
    bot_username: Optional[str] = Field(
        default=None, description="Bot username (e.g., @YourBot) - optional"
    )
    documentation_url: str = Field(
        default="https://notion.so/quickcart-docs",
        description="URL to your store documentation",
    )
    support_contact: Optional[str] = Field(
        default=None, description="Support contact (username, phone, or URL)"
    )

    # External services (optional)
    sentry_dsn: Optional[str] = Field(default=None)

    # Telegram welcome sticker
    telegram_welcome_sticker: str = Field(
        default="CAACAgIAAxkBAAIDbWkLZHuqPRCqCqmL9flozT9YJdWOAAIZUAAC4KOCB7lIn3OKexieNgQ",
        description="Telegram sticker file ID to send on /start (optional, can be left as default or changed)",
    )

    # PostgreSQL credentials for init scripts (production only)
    # These are only used by init-db.sql if you need to create databases
    postgres_user: str = Field(default="quickcart")
    postgres_password: str = Field(default="quickcart")
    postgres_db: str = Field(default="quickcart")
    audit_postgres_user: str = Field(default="quickcart_audit")
    audit_postgres_password: str = Field(default="quickcart_audit")
    audit_postgres_db: str = Field(default="quickcart_audit")

    # ========================================
    # Computed properties
    # ========================================

    @property
    def admin_ids(self) -> List[int]:
        """Parse admin user IDs from comma-separated string"""
        return [int(id.strip()) for id in self.admin_user_ids.split(",") if id.strip()]

    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.environment.lower() == "development"

    def calculate_payment_fee(self, subtotal: int) -> int:
        """
        Calculate payment fee: subtotal * 0.7% + Rp310
        All amounts in Rupiah (integer)
        """
        fee = int(subtotal * self.payment_fee_percentage) + self.payment_fee_fixed
        return fee


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Convenience export
settings = get_settings()
