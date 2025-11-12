"""Initial database schema

Revision ID: 001_initial_schema
Revises:
Create Date: 2025-01-12 14:03:59.000000

This migration creates all tables for QuickCart:
- Main database: users, products, product_stocks, orders, order_items, vouchers, voucher_usage_cooldown
- Audit database: audit_logs, payment_audit_logs, admin_action_audit

Reference: docs/06-data_schema.md
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables and indexes"""

    # ==========================================
    # MAIN DATABASE TABLES
    # ==========================================

    # Table: users
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), nullable=False, comment="Telegram User ID"),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("whatsapp_number", sa.String(length=20), nullable=True),
        sa.Column(
            "member_status",
            sa.String(length=10),
            nullable=False,
            server_default="customer",
        ),
        sa.Column("bank_id", sa.String(length=10), nullable=False),
        sa.Column(
            "account_balance",
            sa.Numeric(precision=15, scale=2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column("is_banned", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("bank_id"),
    )

    # Indexes for users
    op.create_index("idx_users_member_status", "users", ["member_status"])
    op.create_index("idx_users_bank_id", "users", ["bank_id"])
    op.create_index(
        "idx_users_email",
        "users",
        ["email"],
        unique=False,
        postgresql_where=sa.text("email IS NOT NULL"),
    )

    # Table: products
    op.create_table(
        "products",
        sa.Column(
            "id", sa.Integer(), nullable=False, comment="Admin-defined Product ID"
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "category",
            sa.String(length=255),
            nullable=False,
            server_default="Uncategorized",
        ),
        sa.Column("customer_price", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("reseller_price", sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column("sold_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Indexes for products
    op.create_index("idx_products_category", "products", ["category"])
    op.create_index("idx_products_is_active", "products", ["is_active"])
    op.create_index("idx_products_sold_count", "products", [sa.text("sold_count DESC")])

    # Table: orders
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("invoice_id", sa.String(length=20), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("subtotal", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column(
            "voucher_discount",
            sa.Numeric(precision=15, scale=2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column(
            "payment_fee",
            sa.Numeric(precision=15, scale=2),
            nullable=False,
            server_default="0.00",
        ),
        sa.Column("total_bill", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("payment_method", sa.String(length=20), nullable=False),
        sa.Column(
            "status", sa.String(length=10), nullable=False, server_default="pending"
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("invoice_id"),
    )

    # Indexes for orders
    op.create_index("idx_orders_invoice_id", "orders", ["invoice_id"], unique=True)
    op.create_index("idx_orders_user_id", "orders", ["user_id"])
    op.create_index("idx_orders_status", "orders", ["status"])
    op.create_index("idx_orders_created_at", "orders", [sa.text("created_at DESC")])

    # Table: product_stocks
    op.create_table(
        "product_stocks",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column(
            "content",
            sa.Text(),
            nullable=False,
            comment="Digital content/keys/accounts",
        ),
        sa.Column("order_id", sa.Integer(), nullable=True),
        sa.Column("is_sold", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Indexes for product_stocks
    op.create_index("idx_product_stocks_product_id", "product_stocks", ["product_id"])
    op.create_index("idx_product_stocks_is_sold", "product_stocks", ["is_sold"])
    op.create_index("idx_product_stocks_order_id", "product_stocks", ["order_id"])

    # Table: order_items
    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("order_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("stock_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("price_per_unit", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(
            ["stock_id"], ["product_stocks.id"], ondelete="RESTRICT"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Indexes for order_items
    op.create_index("idx_order_items_order_id", "order_items", ["order_id"])
    op.create_index("idx_order_items_stock_id", "order_items", ["stock_id"])

    # Table: vouchers
    op.create_table(
        "vouchers",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("amount", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("created_by", sa.BigInteger(), nullable=False),
        sa.Column("is_used", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("used_by", sa.BigInteger(), nullable=True),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("order_id", sa.Integer(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["used_by"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    # Indexes for vouchers
    op.create_index("idx_vouchers_code", "vouchers", ["code"], unique=True)
    op.create_index("idx_vouchers_used_by", "vouchers", ["used_by"])
    op.create_index("idx_vouchers_is_used", "vouchers", ["is_used"])
    op.create_index("idx_vouchers_expires_at", "vouchers", ["expires_at"])

    # Table: voucher_usage_cooldown
    op.create_table(
        "voucher_usage_cooldown",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("last_voucher_used", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Indexes for voucher_usage_cooldown
    op.create_index(
        "idx_voucher_cooldown_user_id", "voucher_usage_cooldown", ["user_id"]
    )
    op.create_index(
        "idx_voucher_cooldown_expires_at", "voucher_usage_cooldown", ["expires_at"]
    )

    # ==========================================
    # TRIGGERS FOR AUTO-UPDATE TIMESTAMPS
    # ==========================================

    # Create trigger function for updating timestamps
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)

    # Apply triggers to all tables with updated_at column
    for table in ["users", "products", "product_stocks", "orders"]:
        op.execute(f"""
            CREATE TRIGGER update_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """)


def downgrade() -> None:
    """Drop all tables and triggers"""

    # Drop triggers first
    for table in ["users", "products", "product_stocks", "orders"]:
        op.execute(f"DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table};")

    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")

    # Drop tables in reverse order (respect foreign keys)
    op.drop_table("voucher_usage_cooldown")
    op.drop_table("vouchers")
    op.drop_table("order_items")
    op.drop_table("product_stocks")
    op.drop_table("orders")
    op.drop_table("products")
    op.drop_table("users")
