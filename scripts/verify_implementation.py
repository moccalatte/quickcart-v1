#!/usr/bin/env python3
"""
QuickCart Implementation Verification Script
Checks if codebase matches documentation in docs/ and plans.md
"""

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Color codes for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"


class ImplementationVerifier:
    def __init__(self):
        self.root = Path(__file__).parent.parent
        self.errors = []
        self.warnings = []
        self.passed = []

    def log_pass(self, msg: str):
        self.passed.append(msg)
        print(f"{GREEN}✓{RESET} {msg}")

    def log_error(self, msg: str):
        self.errors.append(msg)
        print(f"{RED}✗{RESET} {msg}")

    def log_warning(self, msg: str):
        self.warnings.append(msg)
        print(f"{YELLOW}⚠{RESET} {msg}")

    def log_info(self, msg: str):
        print(f"{BLUE}ℹ{RESET} {msg}")

    def check_file_exists(self, path: str) -> bool:
        """Check if file exists"""
        full_path = self.root / path
        return full_path.exists()

    def read_file(self, path: str) -> str:
        """Read file content"""
        try:
            full_path = self.root / path
            return full_path.read_text()
        except Exception as e:
            self.log_error(f"Cannot read {path}: {e}")
            return ""

    def check_in_file(self, path: str, pattern: str, description: str) -> bool:
        """Check if pattern exists in file"""
        content = self.read_file(path)
        if not content:
            return False

        if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
            self.log_pass(f"{description} - Found in {path}")
            return True
        else:
            self.log_error(f"{description} - NOT found in {path}")
            return False

    def verify_models(self):
        """Verify database models match schema docs"""
        print("\n" + "=" * 70)
        print("VERIFYING DATABASE MODELS")
        print("=" * 70)

        # Check User model
        self.check_in_file(
            "src/models/user.py", r"class User.*Base", "User model class"
        )
        self.check_in_file(
            "src/models/user.py",
            r"id.*=.*Column.*BigInteger.*primary_key",
            "User.id (telegram_id as primary key)",
        )
        self.check_in_file(
            "src/models/user.py",
            r"member_status.*=.*Column",
            "User.member_status (customer/reseller/admin)",
        )
        self.check_in_file(
            "src/models/user.py",
            r"account_balance.*=.*Column.*Numeric",
            "User.account_balance",
        )

        # Check Product model
        self.check_in_file(
            "src/models/product.py", r"class Product.*Base", "Product model class"
        )
        self.check_in_file(
            "src/models/product.py",
            r"customer_price.*=.*Column.*Numeric",
            "Product.customer_price",
        )
        self.check_in_file(
            "src/models/product.py",
            r"reseller_price.*=.*Column.*Numeric",
            "Product.reseller_price",
        )

        # Check ProductStock model
        self.check_in_file(
            "src/models/product.py",
            r"class ProductStock.*Base",
            "ProductStock model class",
        )

        # Check Order model
        self.check_in_file(
            "src/models/order.py", r"class Order.*Base", "Order model class"
        )
        self.check_in_file(
            "src/models/order.py",
            r"status.*=.*Column",
            "Order.status (pending/paid/delivered/cancelled/refunded)",
        )

        # Check Voucher model
        self.check_in_file(
            "src/models/voucher.py", r"class Voucher.*Base", "Voucher model class"
        )

        # Check Audit models
        self.check_in_file(
            "src/models/audit.py", r"class.*AuditLog.*Base", "AuditLog model class"
        )
        self.check_in_file(
            "src/models/audit.py",
            r"payment_metadata",
            "PaymentAuditLog.payment_metadata (not 'metadata' - reserved)",
        )

    def verify_integrations(self):
        """Verify external integrations"""
        print("\n" + "=" * 70)
        print("VERIFYING INTEGRATIONS")
        print("=" * 70)

        # Check Pakasir integration
        self.check_in_file(
            "src/integrations/pakasir.py",
            r"create_qris_payment",
            "Pakasir.create_qris_payment() method",
        )
        self.check_in_file(
            "src/integrations/pakasir.py",
            r"get_payment_status",
            "Pakasir.get_payment_status() method",
        )
        self.check_in_file(
            "src/integrations/pakasir.py",
            r"get_checkout_url",
            "Pakasir.get_checkout_url() method",
        )
        self.check_in_file(
            "src/integrations/pakasir.py",
            r"extract_qris_code",
            "Pakasir.extract_qris_code() method",
        )
        self.check_in_file(
            "src/integrations/pakasir.py",
            r"/api/transactioncreate/qris",
            "Pakasir API endpoint (transactioncreate)",
        )
        self.check_in_file(
            "src/integrations/pakasir.py",
            r"/api/transactiondetail",
            "Pakasir API endpoint (transactiondetail)",
        )
        self.check_in_file(
            "src/integrations/pakasir.py", r"qris_only=1", "Pakasir QRIS-only parameter"
        )

    def verify_config(self):
        """Verify configuration"""
        print("\n" + "=" * 70)
        print("VERIFYING CONFIGURATION")
        print("=" * 70)

        self.check_in_file(
            "src/core/config.py",
            r"telegram_bot_token.*str.*Field",
            "Config: telegram_bot_token (required)",
        )
        self.check_in_file(
            "src/core/config.py",
            r"admin_user_ids.*str.*Field",
            "Config: admin_user_ids (required)",
        )
        self.check_in_file(
            "src/core/config.py",
            r"pakasir_api_key.*str.*Field",
            "Config: pakasir_api_key (required)",
        )
        self.check_in_file(
            "src/core/config.py",
            r"pakasir_project_slug.*str.*Field",
            "Config: pakasir_project_slug (required)",
        )
        self.check_in_file(
            "src/core/config.py",
            r"secret_key.*str.*Field",
            "Config: secret_key (required)",
        )
        self.check_in_file(
            "src/core/config.py",
            r"encryption_key.*str.*Field",
            "Config: encryption_key (required)",
        )

    def verify_webhooks(self):
        """Verify webhook handlers"""
        print("\n" + "=" * 70)
        print("VERIFYING WEBHOOKS")
        print("=" * 70)

        self.check_in_file(
            "src/main.py", r"@app\.post.*webhooks/pakasir", "Pakasir webhook endpoint"
        )
        self.check_in_file(
            "src/main.py",
            r"X-Pakasir-Signature",
            "Pakasir webhook signature validation",
        )
        self.check_in_file(
            "src/main.py",
            r"status.*==.*completed",
            "Pakasir webhook status handling (completed)",
        )
        self.check_in_file(
            "src/main.py",
            r"status.*==.*expired",
            "Pakasir webhook status handling (expired)",
        )

    def verify_env_template(self):
        """Verify environment template"""
        print("\n" + "=" * 70)
        print("VERIFYING ENVIRONMENT TEMPLATE")
        print("=" * 70)

        if not self.check_file_exists(".env.template"):
            self.log_error(".env.template does not exist")
            return

        self.check_in_file(
            ".env.template", r"TELEGRAM_BOT_TOKEN", "Env: TELEGRAM_BOT_TOKEN documented"
        )
        self.check_in_file(
            ".env.template", r"ADMIN_USER_IDS", "Env: ADMIN_USER_IDS documented"
        )
        self.check_in_file(
            ".env.template", r"PAKASIR_API_KEY", "Env: PAKASIR_API_KEY documented"
        )
        self.check_in_file(
            ".env.template",
            r"PAKASIR_PROJECT_SLUG",
            "Env: PAKASIR_PROJECT_SLUG documented",
        )
        self.check_in_file(
            ".env.template", r"DATABASE_URL", "Env: DATABASE_URL documented"
        )
        self.check_in_file(".env.template", r"SECRET_KEY", "Env: SECRET_KEY documented")
        self.check_in_file(
            ".env.template", r"ENCRYPTION_KEY", "Env: ENCRYPTION_KEY documented"
        )

    def verify_docker(self):
        """Verify Docker configuration"""
        print("\n" + "=" * 70)
        print("VERIFYING DOCKER CONFIGURATION")
        print("=" * 70)

        if not self.check_file_exists("docker-compose.yml"):
            self.log_error("docker-compose.yml does not exist")
            return

        self.check_in_file(
            "docker-compose.yml", r"services:", "Docker Compose: services defined"
        )
        self.check_in_file(
            "docker-compose.yml", r"db:", "Docker Compose: PostgreSQL service"
        )
        self.check_in_file(
            "docker-compose.yml", r"app:", "Docker Compose: Application service"
        )
        self.check_in_file(
            "docker-compose.yml", r"postgres:15", "Docker Compose: PostgreSQL 15 image"
        )

        # Check for docker-compose.production.yml (should NOT exist after cleanup)
        if self.check_file_exists("docker-compose.production.yml"):
            self.log_error(
                "docker-compose.production.yml should not exist (consolidated to one file)"
            )
        else:
            self.log_pass("docker-compose.production.yml removed (consolidated)")

    def verify_readme(self):
        """Verify README completeness"""
        print("\n" + "=" * 70)
        print("VERIFYING README")
        print("=" * 70)

        if not self.check_file_exists("README.md"):
            self.log_error("README.md does not exist")
            return

        self.check_in_file(
            "README.md",
            r"https://github.com/moccalatte/quickcart-v1",
            "README: Repository link",
        )
        self.check_in_file(
            "README.md",
            r"cp .env.template .env",
            "README: Setup instructions (.env.template)",
        )
        self.check_in_file(
            "README.md", r"docker.*compose.*up", "README: Docker Compose instructions"
        )
        self.check_in_file(
            "README.md", r"BotFather", "README: Telegram bot setup instructions"
        )
        self.check_in_file(
            "README.md", r"Pakasir", "README: Pakasir payment gateway mentioned"
        )

    def verify_migrations(self):
        """Verify Alembic migrations exist"""
        print("\n" + "=" * 70)
        print("VERIFYING MIGRATIONS")
        print("=" * 70)

        migrations_dir = self.root / "migrations" / "versions"
        if not migrations_dir.exists():
            self.log_error("migrations/versions directory does not exist")
            return

        migration_files = list(migrations_dir.glob("*.py"))
        migration_files = [f for f in migration_files if f.name != "__init__.py"]

        if len(migration_files) >= 2:
            self.log_pass(f"Found {len(migration_files)} migration files")
        else:
            self.log_error(
                f"Only {len(migration_files)} migration files (expected at least 2)"
            )

        # Check for audit schema migration
        audit_migration_found = False
        for mig in migration_files:
            content = mig.read_text()
            if "audit" in content.lower():
                audit_migration_found = True
                break

        if audit_migration_found:
            self.log_pass("Audit schema migration found")
        else:
            self.log_warning("No audit schema migration found")

    def verify_structure(self):
        """Verify project structure"""
        print("\n" + "=" * 70)
        print("VERIFYING PROJECT STRUCTURE")
        print("=" * 70)

        required_dirs = [
            "src",
            "src/models",
            "src/services",
            "src/repositories",
            "src/integrations",
            "src/bot",
            "src/bot/handlers",
            "src/bot/keyboards",
            "src/core",
            "tests",
            "tests/unit",
            "migrations",
            "docs",
        ]

        for dir_path in required_dirs:
            if self.check_file_exists(dir_path):
                self.log_pass(f"Directory exists: {dir_path}")
            else:
                self.log_error(f"Directory missing: {dir_path}")

        required_files = [
            "src/main.py",
            "src/core/config.py",
            "src/core/database.py",
            "src/models/user.py",
            "src/models/product.py",
            "src/models/order.py",
            "src/models/voucher.py",
            "src/models/audit.py",
            "src/integrations/pakasir.py",
            "requirements.txt",
            "Dockerfile",
            "docker-compose.yml",
            ".env.template",
            "alembic.ini",
            "README.md",
            "CHANGELOG.md",
        ]

        for file_path in required_files:
            if self.check_file_exists(file_path):
                self.log_pass(f"File exists: {file_path}")
            else:
                self.log_error(f"File missing: {file_path}")

    def verify_no_bloat(self):
        """Verify no bloat files exist"""
        print("\n" + "=" * 70)
        print("VERIFYING NO BLOAT FILES")
        print("=" * 70)

        bloat_files = [
            "FINAL_COMMIT_MESSAGE.txt",
            "READY_TO_COMMIT.md",
            "test_imports.py",
            ".env.example.template",
            ".env.production.template",
            "docker-compose.production.yml",
            "CLEANUP_COMMIT.md",
            "CLEANUP_SUMMARY.txt",
            "verify_cleanup.sh",
            "plans.md",  # Should be in docs/
            "DEPLOYMENT_QUICKREF.md",  # Should be in docs/
            "EXTERNAL_DB_CHANGES.md",  # Should be in docs/
        ]

        for file_path in bloat_files:
            if self.check_file_exists(file_path):
                self.log_error(f"Bloat file exists (should be removed): {file_path}")
            else:
                self.log_pass(f"Bloat file removed: {file_path}")

    def run(self):
        """Run all verifications"""
        print("\n" + "=" * 70)
        print("QUICKCART IMPLEMENTATION VERIFICATION")
        print("=" * 70)
        print(f"Root: {self.root}")
        print()

        self.verify_structure()
        self.verify_no_bloat()
        self.verify_models()
        self.verify_config()
        self.verify_integrations()
        self.verify_webhooks()
        self.verify_env_template()
        self.verify_docker()
        self.verify_readme()
        self.verify_migrations()

        # Summary
        print("\n" + "=" * 70)
        print("VERIFICATION SUMMARY")
        print("=" * 70)
        print(f"{GREEN}Passed:{RESET} {len(self.passed)}")
        print(f"{YELLOW}Warnings:{RESET} {len(self.warnings)}")
        print(f"{RED}Errors:{RESET} {len(self.errors)}")

        if self.errors:
            print(f"\n{RED}FAILED - {len(self.errors)} error(s) found{RESET}")
            print("\nErrors:")
            for i, err in enumerate(self.errors, 1):
                print(f"  {i}. {err}")
            return 1
        elif self.warnings:
            print(
                f"\n{YELLOW}PASSED WITH WARNINGS - {len(self.warnings)} warning(s){RESET}"
            )
            print("\nWarnings:")
            for i, warn in enumerate(self.warnings, 1):
                print(f"  {i}. {warn}")
            return 0
        else:
            print(f"\n{GREEN}ALL CHECKS PASSED! ✓{RESET}")
            return 0


if __name__ == "__main__":
    verifier = ImplementationVerifier()
    sys.exit(verifier.run())
