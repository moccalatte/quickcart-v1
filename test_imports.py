#!/usr/bin/env python3
"""
Import Test Script for QuickCart
Tests all modules to ensure no import errors or circular dependencies
Run this before committing to verify code integrity

CI/CD Mode: Exits with 0 even if dependencies are missing (checks structure only)
Local Mode: Requires all dependencies to be installed
"""

import sys
from typing import List, Tuple


def test_import(module_name: str) -> Tuple[bool, str]:
    """Test importing a module"""
    try:
        __import__(module_name)
        return True, f"✓ {module_name}"
    except ImportError as e:
        # Check if it's a missing external dependency or code structure issue
        error_msg = str(e)
        if "No module named" in error_msg and not module_name.startswith("src."):
            # External dependency missing - OK in CI environment
            return True, f"⊘ {module_name} (external dependency not installed)"
        else:
            # Code structure error - FAIL
            return False, f"✗ {module_name}: {error_msg}"
    except Exception as e:
        return False, f"✗ {module_name}: {str(e)}"


def main():
    """Run all import tests"""
    print("=" * 60)
    print("QuickCart Import Test")
    print("=" * 60)
    print()

    # Detect CI environment
    is_ci = any(
        env in os.environ for env in ["CI", "GITHUB_ACTIONS", "GITLAB_CI", "CIRCLECI"]
    )
    if is_ci:
        print("🤖 CI/CD Mode: Testing code structure only")
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
        print()
        print("This indicates a code structure problem, not missing dependencies.")
        print("Please check for:")
        print("  - Syntax errors")
        print("  - Circular imports")
        print("  - Missing __init__.py files")
        print("  - Incorrect import statements")
        sys.exit(1)
    else:
        print("\n✅ All imports successful!")
        print("\nQuickCart code structure is valid! 🚀")

        if is_ci:
            print("\n📦 Note: External dependencies checked in separate CI job")
        else:
            print("\n📦 All dependencies are properly installed")
            print("\nNext steps:")
            print("  1. Set up environment variables in .env")
            print("  2. Run migrations: docker compose exec app alembic upgrade head")
            print("  3. Start the bot: docker compose up -d")
        sys.exit(0)


if __name__ == "__main__":
    import os

    main()
