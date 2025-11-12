#!/usr/bin/env python3
"""
Import Test Script for QuickCart
Tests all modules to ensure no import errors or circular dependencies
Run this before committing to verify code integrity
"""

import sys
from typing import List, Tuple


def test_import(module_name: str) -> Tuple[bool, str]:
    """Test importing a module"""
    try:
        __import__(module_name)
        return True, f"✓ {module_name}"
    except Exception as e:
        return False, f"✗ {module_name}: {str(e)}"


def main():
    """Run all import tests"""
    print("=" * 60)
    print("QuickCart Import Test")
    print("=" * 60)
    print()

    modules_to_test = [
        # Core modules
        "src.core.config",
        "src.core.database",
        "src.core.redis",
        # Models
        "src.models",
        "src.models.user",
        "src.models.product",
        "src.models.order",
        "src.models.voucher",
        "src.models.audit",
        # Repositories
        "src.repositories",
        "src.repositories.user_repository",
        "src.repositories.product_repository",
        "src.repositories.order_repository",
        "src.repositories.audit_repository",
        # Services
        "src.services",
        "src.services.user_service",
        # Integrations
        "src.integrations",
        "src.integrations.pakasir",
        # Bot components
        "src.bot",
        "src.bot.application",
        "src.bot.keyboards",
        "src.bot.keyboards.reply",
        "src.bot.keyboards.inline",
        "src.bot.utils",
        "src.bot.utils.messages",
        "src.bot.handlers",
        # Main application
        "src.main",
    ]

    results: List[Tuple[bool, str]] = []

    print("Testing core dependencies...")
    print("-" * 60)

    # Test external dependencies first
    external_deps = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "alembic",
        "asyncpg",
        "psycopg2",
        "redis",
        "telegram",
        "telegram.ext",
        "httpx",
        "pydantic",
        "pydantic_settings",
        "cryptography",
        "qrcode",
        "tenacity",
    ]

    for dep in external_deps:
        success, msg = test_import(dep)
        results.append((success, msg))
        print(msg)

    print()
    print("Testing QuickCart modules...")
    print("-" * 60)

    for module in modules_to_test:
        success, msg = test_import(module)
        results.append((success, msg))
        print(msg)

    print()
    print("=" * 60)

    # Summary
    total = len(results)
    passed = sum(1 for success, _ in results if success)
    failed = total - passed

    print(f"Results: {passed}/{total} passed")

    if failed > 0:
        print(f"\n❌ {failed} import(s) failed!")
        print("\nFailed imports:")
        for success, msg in results:
            if not success:
                print(f"  {msg}")
        sys.exit(1)
    else:
        print("\n✅ All imports successful!")
        print("\nQuickCart is ready to run! 🚀")
        print("\nNext steps:")
        print("  1. Set up environment variables in .env")
        print("  2. Run migrations: docker compose exec app alembic upgrade head")
        print("  3. Start the bot: docker compose up -d")
        sys.exit(0)


if __name__ == "__main__":
    main()
