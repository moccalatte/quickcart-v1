"""Audit database schema

Revision ID: 002_audit_schema
Revises: 001_initial_schema
Create Date: 2025-01-12 14:05:00.000000

This migration creates audit tables in the separate audit database:
- audit_logs: Master audit log for all critical operations
- payment_audit_logs: Specialized payment transaction logs
- admin_action_audit: Admin command execution trail

Reference: docs/10-audit_architecture.md, docs/06-data_schema.md
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002_audit_schema"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all audit tables and indexes"""

    # ==========================================
    # AUDIT DATABASE TABLES
    # ==========================================

    # Table: audit_logs (Master audit log)
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "actor_id",
            sa.BigInteger(),
            nullable=True,
            comment="User who performed action",
        ),
        sa.Column(
            "actor_type",
            sa.String(length=20),
            nullable=False,
            comment="user/admin/system",
        ),
        sa.Column(
            "entity_type",
            sa.String(length=50),
            nullable=False,
            comment="Table/entity affected",
        ),
        sa.Column(
            "entity_id",
            sa.String(length=50),
            nullable=False,
            comment="Record ID affected",
        ),
        sa.Column(
            "action",
            sa.String(length=50),
            nullable=False,
            comment="create/update/delete/login",
        ),
        sa.Column(
            "before_state",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Previous values",
        ),
        sa.Column(
            "after_state",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="New values",
        ),
        sa.Column(
            "context",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Additional context",
        ),
        sa.Column(
            "ip_address",
            postgresql.INET(),
            nullable=True,
            comment="Source IP if available",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Indexes for audit_logs
    op.create_index(
        "idx_audit_logs_timestamp", "audit_logs", [sa.text("timestamp DESC")]
    )
    op.create_index("idx_audit_logs_entity", "audit_logs", ["entity_type", "entity_id"])
    op.create_index("idx_audit_logs_actor", "audit_logs", ["actor_id"])
    op.create_index("idx_audit_logs_action", "audit_logs", ["action"])

    # Table: payment_audit_logs (Payment-specific audit)
    op.create_table(
        "payment_audit_logs",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "order_id", sa.String(length=20), nullable=False, comment="Invoice ID"
        ),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "amount", sa.String(length=20), nullable=False, comment="Amount in IDR"
        ),
        sa.Column("payment_method", sa.String(length=20), nullable=False),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            comment="pending/paid/expired/cancelled",
        ),
        sa.Column(
            "gateway_response",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Payment gateway response",
        ),
        sa.Column(
            "payment_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Additional payment metadata",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Indexes for payment_audit_logs
    op.create_index(
        "idx_payment_audit_timestamp", "payment_audit_logs", [sa.text("timestamp DESC")]
    )
    op.create_index("idx_payment_audit_order_id", "payment_audit_logs", ["order_id"])
    op.create_index("idx_payment_audit_user_id", "payment_audit_logs", ["user_id"])
    op.create_index("idx_payment_audit_status", "payment_audit_logs", ["status"])

    # Table: admin_action_audit (Admin command tracking)
    op.create_table(
        "admin_action_audit",
        sa.Column("id", sa.BigInteger(), nullable=False, autoincrement=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("admin_id", sa.BigInteger(), nullable=False, comment="Admin user ID"),
        sa.Column(
            "command", sa.String(length=50), nullable=False, comment="Command executed"
        ),
        sa.Column(
            "target_entity",
            sa.String(length=50),
            nullable=True,
            comment="Entity affected",
        ),
        sa.Column(
            "target_id", sa.String(length=50), nullable=True, comment="Target entity ID"
        ),
        sa.Column(
            "parameters",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            comment="Command parameters",
        ),
        sa.Column("result", sa.Text(), nullable=False, comment="Command result/output"),
        sa.Column(
            "ip_address", postgresql.INET(), nullable=True, comment="Admin IP address"
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # Indexes for admin_action_audit
    op.create_index(
        "idx_admin_action_timestamp", "admin_action_audit", [sa.text("timestamp DESC")]
    )
    op.create_index("idx_admin_action_admin_id", "admin_action_audit", ["admin_id"])
    op.create_index("idx_admin_action_command", "admin_action_audit", ["command"])
    op.create_index(
        "idx_admin_action_target", "admin_action_audit", ["target_entity", "target_id"]
    )

    # ==========================================
    # RETENTION POLICY COMMENTS
    # ==========================================

    op.execute("""
        COMMENT ON TABLE audit_logs IS 'Master audit log - PERMANENT RETENTION for compliance';
        COMMENT ON TABLE payment_audit_logs IS 'Payment transaction audit - PERMANENT RETENTION for financial compliance';
        COMMENT ON TABLE admin_action_audit IS 'Admin command audit - PERMANENT RETENTION for security compliance';
    """)


def downgrade() -> None:
    """Drop all audit tables"""

    # Drop tables
    op.drop_table("admin_action_audit")
    op.drop_table("payment_audit_logs")
    op.drop_table("audit_logs")
