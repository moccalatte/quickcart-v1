"""
Unit tests for database models
Tests model definitions, constraints, and reserved attribute handling
"""

import pytest
from sqlalchemy import inspect
from sqlalchemy.orm import DeclarativeMeta

from src.models.audit import AdminActionAudit, AuditLog, PaymentAuditLog
from src.models.order import Order, OrderItem
from src.models.product import Product, ProductStock
from src.models.user import User
from src.models.voucher import Voucher


class TestModelDefinitions:
    """Test that all models are properly defined"""

    def test_all_models_are_declarative(self):
        """Verify all models inherit from Base correctly"""
        models = [
            User,
            Product,
            ProductStock,
            Order,
            OrderItem,
            Voucher,
            AuditLog,
            PaymentAuditLog,
            AdminActionAudit,
        ]

        for model in models:
            assert isinstance(model, DeclarativeMeta), (
                f"{model.__name__} is not a declarative model"
            )

    def test_all_models_have_tablename(self):
        """Verify all models have __tablename__ defined"""
        models = [
            (User, "users"),
            (Product, "products"),
            (ProductStock, "product_stocks"),
            (Order, "orders"),
            (OrderItem, "order_items"),
            (Voucher, "vouchers"),
            (AuditLog, "audit_logs"),
            (PaymentAuditLog, "payment_audit_logs"),
            (AdminActionAudit, "admin_action_audit"),
        ]

        for model, expected_table in models:
            assert hasattr(model, "__tablename__"), (
                f"{model.__name__} missing __tablename__"
            )
            assert model.__tablename__ == expected_table, (
                f"{model.__name__}.__tablename__ is '{model.__tablename__}', expected '{expected_table}'"
            )

    def test_models_have_primary_keys(self):
        """Verify all models have primary key defined"""
        models = [
            User,
            Product,
            ProductStock,
            Order,
            OrderItem,
            Voucher,
            AuditLog,
            PaymentAuditLog,
            AdminActionAudit,
        ]

        for model in models:
            mapper = inspect(model)
            assert len(mapper.primary_key) > 0, f"{model.__name__} has no primary key"


class TestReservedAttributes:
    """Test that models don't use SQLAlchemy reserved attributes"""

    RESERVED_NAMES = ["metadata", "registry", "mapper", "class_", "c", "columns"]

    def test_no_reserved_column_names(self):
        """Verify no model uses reserved SQLAlchemy attribute names as columns"""
        models = [
            User,
            Product,
            ProductStock,
            Order,
            OrderItem,
            Voucher,
            AuditLog,
            PaymentAuditLog,
            AdminActionAudit,
        ]

        for model in models:
            mapper = inspect(model)
            column_names = [col.name for col in mapper.columns]

            for reserved in self.RESERVED_NAMES:
                assert reserved not in column_names, (
                    f"{model.__name__} uses reserved attribute '{reserved}' as column name"
                )


class TestAuditModels:
    """Test audit-specific models"""

    def test_payment_audit_log_has_payment_metadata(self):
        """Verify PaymentAuditLog uses 'payment_metadata' not 'metadata'"""
        mapper = inspect(PaymentAuditLog)
        column_names = [col.name for col in mapper.columns]

        assert "payment_metadata" in column_names, (
            "PaymentAuditLog should have 'payment_metadata' column"
        )
        assert "metadata" not in column_names, (
            "PaymentAuditLog should NOT have 'metadata' column (reserved by SQLAlchemy)"
        )

    def test_audit_log_structure(self):
        """Test AuditLog has required fields"""
        mapper = inspect(AuditLog)
        column_names = [col.name for col in mapper.columns]

        required_fields = [
            "id",
            "timestamp",
            "actor_type",
            "entity_type",
            "entity_id",
            "action",
        ]

        for field in required_fields:
            assert field in column_names, f"AuditLog missing required field '{field}'"

    def test_payment_audit_log_structure(self):
        """Test PaymentAuditLog has required fields"""
        mapper = inspect(PaymentAuditLog)
        column_names = [col.name for col in mapper.columns]

        required_fields = [
            "id",
            "timestamp",
            "order_id",
            "user_id",
            "amount",
            "payment_method",
            "status",
        ]

        for field in required_fields:
            assert field in column_names, (
                f"PaymentAuditLog missing required field '{field}'"
            )

    def test_admin_action_audit_structure(self):
        """Test AdminActionAudit has required fields"""
        mapper = inspect(AdminActionAudit)
        column_names = [col.name for col in mapper.columns]

        required_fields = ["id", "timestamp", "admin_id", "command", "result"]

        for field in required_fields:
            assert field in column_names, (
                f"AdminActionAudit missing required field '{field}'"
            )


class TestUserModel:
    """Test User model specifics"""

    def test_user_has_required_fields(self):
        """Verify User model has all required fields"""
        mapper = inspect(User)
        column_names = [col.name for col in mapper.columns]

        required_fields = [
            "id",
            "name",
            "username",
            "member_status",
            "account_balance",
            "created_at",
        ]

        for field in required_fields:
            assert field in column_names, f"User missing required field '{field}'"


class TestProductModel:
    """Test Product model specifics"""

    def test_product_has_required_fields(self):
        """Verify Product model has all required fields"""
        mapper = inspect(Product)
        column_names = [col.name for col in mapper.columns]

        required_fields = ["id", "name", "customer_price", "category", "created_at"]

        for field in required_fields:
            assert field in column_names, f"Product missing required field '{field}'"


class TestOrderModel:
    """Test Order model specifics"""

    def test_order_has_required_fields(self):
        """Verify Order model has all required fields"""
        mapper = inspect(Order)
        column_names = [col.name for col in mapper.columns]

        required_fields = [
            "invoice_id",
            "user_id",
            "subtotal",
            "total_bill",
            "status",
            "created_at",
        ]

        for field in required_fields:
            assert field in column_names, f"Order missing required field '{field}'"

    def test_order_item_has_required_fields(self):
        """Verify OrderItem model has all required fields"""
        mapper = inspect(OrderItem)
        column_names = [col.name for col in mapper.columns]

        required_fields = ["id", "order_id", "product_id", "stock_id", "price_per_unit"]

        for field in required_fields:
            assert field in column_names, f"OrderItem missing required field '{field}'"
