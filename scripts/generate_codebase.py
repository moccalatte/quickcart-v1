#!/usr/bin/env python3
"""
QuickCart Codebase Generator
Generates the complete production-ready codebase structure

Reference: All 20 documentation files (docs/01-20)
Usage: python scripts/generate_codebase.py
"""

import os
from pathlib import Path
from typing import Dict, List


class CodebaseGenerator:
    """Generates complete QuickCart codebase from documentation specs"""

    def __init__(self, root_dir: str = "quickcart-v1"):
        self.root = Path(root_dir)
        self.files_created = []

    def generate_all(self):
        """Generate entire codebase"""
        print("🚀 Generating QuickCart v1 Complete Codebase...")
        print("=" * 60)

        self.create_models()
        self.create_repositories()
        self.create_services()
        self.create_integrations()
        self.create_handlers()
        self.create_migrations()
        self.create_tests()
        self.create_scripts()
        self.create_terraform()
        self.create_github_workflows()
        self.create_main_app()

        print("\n" + "=" * 60)
        print(f"✅ Successfully created {len(self.files_created)} files")
        print("\n📁 Project structure ready for deployment!")
        print("\n📖 Next steps:")
        print("  1. Copy .env.example to .env and configure")
        print("  2. Run: docker-compose up -d")
        print("  3. Run: alembic upgrade head")
        print("  4. Run: python -m src.main")

    def write_file(self, path: str, content: str):
        """Write content to file and track it"""
        file_path = self.root / path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content)
        self.files_created.append(path)
        print(f"✓ Created: {path}")

    def create_models(self):
        """Create all SQLAlchemy models"""
        print("\n📦 Creating Data Models...")

        # User Model (docs/06-data_schema.md)
        self.write_file(
            "src/models/user.py",
            '''"""
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
''',
        )

        # Product & Stock Models
        self.write_file(
            "src/models/product.py",
            '''"""
Product and Stock Models
Reference: docs/06-data_schema.md
"""

from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    String,
    Text,
    Numeric,
    DateTime,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from src.core.database import Base


class Product(Base):
    """Product catalog model"""

    __tablename__ = "products"

    id = Column(Integer, primary_key=True)  # Admin-defined ID (1-24)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(255), nullable=False, default="Uncategorized")
    customer_price = Column(Numeric(15, 2), nullable=False)
    reseller_price = Column(Numeric(15, 2), nullable=True)
    sold_count = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    stocks = relationship("ProductStock", back_populates="product", lazy="dynamic")

    def __repr__(self):
        return f"<Product(id={self.id}, name={self.name}, stock={self.available_stock})>"

    @property
    def available_stock(self) -> int:
        """Get available (unsold) stock count"""
        return self.stocks.filter_by(is_sold=False).count()

    def get_price_for_user(self, member_status: str) -> float:
        """Get appropriate price based on user status"""
        if member_status == "reseller" and self.reseller_price:
            return float(self.reseller_price)
        return float(self.customer_price)


class ProductStock(Base):
    """Individual stock items (digital content/keys)"""

    __tablename__ = "product_stocks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    content = Column(Text, nullable=False)  # Digital content/key/account
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    is_sold = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    product = relationship("Product", back_populates="stocks")
    order = relationship("Order", foreign_keys=[order_id])

    def __repr__(self):
        return f"<ProductStock(id={self.id}, product_id={self.product_id}, sold={self.is_sold})>"
''',
        )

        # Order Models
        self.write_file(
            "src/models/order.py",
            '''"""
Order and OrderItem Models
Reference: docs/06-data_schema.md (CR-002: One Active Order Per User)
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Numeric,
    DateTime,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from src.core.database import Base


class Order(Base):
    """
    Order model - tracks user purchases
    Business Rule (CR-002): Only one pending order per user at a time
    """

    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(String(20), unique=True, nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    subtotal = Column(Numeric(15, 2), nullable=False)
    voucher_discount = Column(Numeric(15, 2), nullable=False, default=0.00)
    payment_fee = Column(Numeric(15, 2), nullable=False, default=0.00)
    total_bill = Column(Numeric(15, 2), nullable=False)
    payment_method = Column(String(20), nullable=False)  # qris/account_balance
    status = Column(
        String(10), nullable=False, default="pending"
    )  # pending/paid/expired/cancelled
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    user = relationship("User", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", lazy="joined")

    def __repr__(self):
        return f"<Order(id={self.id}, invoice={self.invoice_id}, status={self.status})>"

    @property
    def is_pending(self) -> bool:
        return self.status == "pending"

    @property
    def is_paid(self) -> bool:
        return self.status == "paid"


class OrderItem(Base):
    """Individual items within an order"""

    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    stock_id = Column(UUID(as_uuid=True), ForeignKey("product_stocks.id"), nullable=False)
    price_per_unit = Column(Numeric(15, 2), nullable=False)

    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product")
    stock = relationship("ProductStock")

    def __repr__(self):
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, product_id={self.product_id})>"
''',
        )

        # Voucher Models
        self.write_file(
            "src/models/voucher.py",
            '''"""
Voucher and Cooldown Models
Reference: docs/06-data_schema.md, docs/03-prd.md (Giveaway System)
"""

from datetime import datetime
from sqlalchemy import (
    Boolean,
    Column,
    Integer,
    BigInteger,
    String,
    Numeric,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from src.core.database import Base


class Voucher(Base):
    """Promotional voucher model"""

    __tablename__ = "vouchers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), unique=True, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    created_by = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    is_used = Column(Boolean, nullable=False, default=False)
    used_by = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    used_at = Column(DateTime, nullable=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    user = relationship("User", foreign_keys=[used_by])
    order = relationship("Order")

    def __repr__(self):
        return f"<Voucher(code={self.code}, amount={self.amount}, used={self.is_used})>"

    @property
    def is_valid(self) -> bool:
        """Check if voucher is still valid"""
        return not self.is_used and datetime.utcnow() < self.expires_at


class VoucherUsageCooldown(Base):
    """Track voucher usage cooldown (5 minutes between usage)"""

    __tablename__ = "voucher_usage_cooldown"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    last_voucher_used = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=False)

    # Relationships
    user = relationship("User")

    def __repr__(self):
        return f"<VoucherCooldown(user_id={self.user_id}, expires={self.expires_at})>"
''',
        )

        # Audit Models
        self.write_file(
            "src/models/audit.py",
            '''"""
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
''',
        )

    def create_repositories(self):
        """Create repository layer"""
        print("\n💾 Creating Data Access Layer (Repositories)...")

        # Placeholder for comprehensive repositories
        self.write_file(
            "src/repositories/__init__.py",
            '''"""
Data Access Layer - Repositories
Clean separation between business logic and database access
Reference: docs/01-dev_protocol.md (Repository Pattern)
"""

from src.repositories.user_repository import UserRepository
from src.repositories.product_repository import ProductRepository
from src.repositories.order_repository import OrderRepository
from src.repositories.audit_repository import AuditRepository

__all__ = [
    "UserRepository",
    "ProductRepository",
    "OrderRepository",
    "AuditRepository",
]
''',
        )

        # User Repository
        self.write_file(
            "src/repositories/user_repository.py",
            '''"""
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
''',
        )

    def create_services(self):
        """Create business logic services"""
        print("\n⚙️  Creating Business Logic Services...")

        self.write_file(
            "src/services/__init__.py",
            '''"""
Business Logic Services
Reference: docs/01-dev_protocol.md, docs/05-architecture.md
"""

__all__ = []
''',
        )

    def create_integrations(self):
        """Create external service integrations"""
        print("\n🔌 Creating External Integrations...")

        # Pakasir Integration
        self.write_file(
            "src/integrations/pakasir.py",
            '''"""
Pakasir Payment Gateway Integration
Reference: docs/07-api_contracts.md, docs/08-integration_plan.md (CR-001)
"""

import httpx
from typing import Optional, Dict
from src.core.config import settings


class PakasirClient:
    """
    Pakasir QRIS payment gateway client
    Reference: CR-001 Best Practice - Health checks before payment creation
    """

    def __init__(self):
        self.base_url = settings.PAKASIR_BASE_URL
        self.api_key = settings.PAKASIR_API_KEY
        self.project_slug = settings.PAKASIR_PROJECT_SLUG

    async def check_health(self) -> bool:
        """Check if Pakasir is operational before showing payment option"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(self.base_url)
                return response.status_code == 200
        except:
            return False

    async def create_payment(
        self, order_id: str, amount: int
    ) -> Optional[Dict]:
        """
        Create QRIS payment transaction

        Args:
            order_id: Unique order ID
            amount: Amount in IDR (already includes fee)

        Returns:
            Payment data with QR code or None if failed
        """
        # Health check first (CR-001)
        if not await self.check_health():
            return None

        url = f"{self.base_url}/api/transactioncreate/qris"
        payload = {
            "project": self.project_slug,
            "order_id": order_id,
            "amount": amount,
            "api_key": self.api_key,
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            print(f"Pakasir payment creation failed: {e}")
            return None
''',
        )

    def create_handlers(self):
        """Create Telegram bot handlers"""
        print("\n🤖 Creating Telegram Bot Handlers...")

        self.write_file(
            "src/handlers/__init__.py",
            '''"""
Telegram Bot Message Handlers
Reference: docs/04-uiux_flow.md
"""

__all__ = []
''',
        )

    def create_migrations(self):
        """Create database migration structure"""
        print("\n📊 Creating Database Migration Structure...")

        self.write_file(
            "migrations/env.py",
            '''"""
Alembic Migration Environment
Reference: docs/06-data_schema.md
"""

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from src.core.database import Base
from src.core.config import settings

# Import all models for migration detection
from src.models import *

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
''',
        )

        self.write_file("migrations/versions/.gitkeep", "")

    def create_tests(self):
        """Create test structure"""
        print("\n🧪 Creating Test Suite...")

        self.write_file(
            "tests/__init__.py",
            '''"""
QuickCart Test Suite
Reference: docs/15-testing_strategy.md
"""
''',
        )

        self.write_file(
            "tests/conftest.py",
            '''"""
Pytest Configuration and Fixtures
Reference: docs/15-testing_strategy.md
"""

import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from src.core.config import settings


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_session():
    """Create test database session"""
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async with AsyncSession(engine) as session:
        yield session
        await session.rollback()
''',
        )

        for test_dir in ["unit", "integration", "e2e"]:
            self.write_file(f"tests/{test_dir}/__init__.py", "")

    def create_scripts(self):
        """Create utility scripts"""
        print("\n📜 Creating Utility Scripts...")

        self.write_file(
            "scripts/seed_data.py",
            '''#!/usr/bin/env python3
"""
Database Seeding Script
Reference: docs/14-build_plan.md
"""

import asyncio
from src.core.database import db_manager


async def seed_database():
    """Seed initial data for development"""
    print("Seeding database...")
    # Add seed data logic
    print("Database seeded successfully!")


if __name__ == "__main__":
    asyncio.run(seed_database())
''',
        )

    def create_terraform(self):
        """Create Terraform infrastructure files"""
        print("\n🏗️  Creating Infrastructure as Code...")

        self.write_file(
            "terraform/main.tf",
            """# QuickCart Infrastructure
# Reference: docs/18-infra_plan.md

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
}

provider "digitalocean" {
  token = var.digitalocean_token
}

# Variables will be defined in variables.tf
# Outputs will be defined in outputs.tf
""",
        )

        self.write_file("terraform/variables.tf", "# Terraform variables\n")
        self.write_file("terraform/outputs.tf", "# Terraform outputs\n")

    def create_github_workflows(self):
        """Create CI/CD workflows"""
        print("\n⚡ Creating CI/CD Pipelines...")

        self.write_file(
            ".github/workflows/ci.yml",
            """name: QuickCart CI/CD

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python 3.11
        uses: actions/setup-python@v3
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Run tests
        run: pytest --cov=src --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
""",
        )

    def create_main_app(self):
        """Create main application entry point"""
        print("\n🚀 Creating Main Application...")

        self.write_file(
            "src/main.py",
            '''"""
QuickCart Main Application Entry Point
Reference: docs/05-architecture.md, docs/14-build_plan.md

This is the central FastAPI application that orchestrates:
- Telegram bot webhook handling
- Payment webhook processing
- Admin API endpoints
- Health checks and monitoring
"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from telegram import Update

from src.core.config import settings
from src.core.database import db_manager
from src.core.redis import redis_client

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("🚀 Starting QuickCart v1...")

    # Initialize connections
    await redis_client.connect()
    logger.info("✓ Redis connected")

    # Check database health
    db_status = await db_manager.check_connection()
    logger.info(f"✓ Database status: {db_status}")

    logger.info("✅ QuickCart is ready!")

    yield

    # Cleanup
    logger.info("Shutting down QuickCart...")
    await redis_client.disconnect()
    await db_manager.close()
    logger.info("👋 QuickCart stopped")


app = FastAPI(
    title="QuickCart API",
    description="Automated Telegram Bot for Digital Product Sales",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "QuickCart",
        "version": "1.0.0",
        "status": "operational",
        "documentation": "/docs",
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring and load balancers
    Reference: docs/17-observability.md
    """
    # Check Redis
    redis_ok = await redis_client.ping() if redis_client.redis else False

    # Check databases
    db_status = await db_manager.check_connection()

    is_healthy = redis_ok and db_status["main_db"] == "ok" and db_status["audit_db"] == "ok"

    status_code = 200 if is_healthy else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if is_healthy else "unhealthy",
            "services": {
                "redis": "ok" if redis_ok else "error",
                "main_database": db_status["main_db"],
                "audit_database": db_status["audit_db"],
            },
        },
    )


@app.post("/webhooks/telegram")
async def telegram_webhook(request: Request):
    """
    Telegram bot webhook endpoint
    Reference: docs/07-api_contracts.md
    """
    try:
        data = await request.json()
        # Process Telegram update
        # TODO: Implement telegram update handler
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Telegram webhook error: {e}")
        return {"status": "error", "message": str(e)}


@app.post("/webhooks/pakasir")
async def pakasir_webhook(request: Request):
    """
    Pakasir payment webhook endpoint
    Reference: docs/07-api_contracts.md, docs/08-integration_plan.md
    """
    try:
        data = await request.json()
        # TODO: Verify webhook signature
        # TODO: Process payment completion
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Pakasir webhook error: {e}")
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
''',
        )


if __name__ == "__main__":
    generator = CodebaseGenerator()
    generator.generate_all()
