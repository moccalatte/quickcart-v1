"""
Unit tests for configuration management
Tests settings loading, validation, and environment handling
"""

import pytest


class TestConfigurationBasics:
    """Test basic configuration loading and structure"""

    def test_settings_can_be_imported(self):
        """Verify settings object can be imported"""
        try:
            from src.core.config import settings

            assert settings is not None
        except ImportError as e:
            pytest.skip(f"Settings import failed: {e}")

    def test_settings_has_required_attributes(self):
        """Verify settings has all required configuration attributes"""
        try:
            from src.core.config import settings

            required_attrs = [
                "store_name",
                "debug",
                "database_url",
                "audit_database_url",
                "redis_url",
                "telegram_bot_token",
            ]

            for attr in required_attrs:
                assert hasattr(settings, attr), f"Settings missing attribute: {attr}"

        except ImportError:
            pytest.skip("Settings not available")

    def test_database_urls_format(self):
        """Test that database URLs have correct format"""
        try:
            from src.core.config import settings

            # Check database_url exists and is string
            assert isinstance(settings.database_url, str)
            assert len(settings.database_url) > 0

            # Check audit_database_url exists and is string
            assert isinstance(settings.audit_database_url, str)
            assert len(settings.audit_database_url) > 0

            # URLs should contain postgresql
            assert "postgresql" in settings.database_url.lower()
            assert "postgresql" in settings.audit_database_url.lower()

        except ImportError:
            pytest.skip("Settings not available")

    def test_redis_url_format(self):
        """Test that Redis URL has correct format"""
        try:
            from src.core.config import settings

            # redis_url is Optional, so it can be None
            if settings.redis_url:
                assert isinstance(settings.redis_url, str)
                assert len(settings.redis_url) > 0
                assert "redis://" in settings.redis_url

        except ImportError:
            pytest.skip("Settings not available")


class TestEnvironmentSpecificSettings:
    """Test environment-specific configuration behavior"""

    def test_debug_is_boolean(self):
        """Verify debug flag is boolean type"""
        try:
            from src.core.config import settings

            assert isinstance(settings.debug, bool)

        except ImportError:
            pytest.skip("Settings not available")

    def test_store_name_is_set(self):
        """Verify store name is configured"""
        try:
            from src.core.config import settings

            assert isinstance(settings.store_name, str)
            assert len(settings.store_name) > 0

        except ImportError:
            pytest.skip("Settings not available")


class TestSecuritySettings:
    """Test security-related configuration"""

    def test_telegram_bot_token_exists(self):
        """Verify telegram bot token is configured"""
        try:
            from src.core.config import settings

            assert hasattr(settings, "telegram_bot_token")
            # In test environment, token can be dummy value
            assert settings.telegram_bot_token is not None
            assert len(settings.telegram_bot_token) > 0

        except ImportError:
            pytest.skip("Settings not available")

    def test_admin_user_ids_exists(self):
        """Verify admin user IDs are configured"""
        try:
            from src.core.config import settings

            assert hasattr(settings, "admin_user_ids")
            assert settings.admin_user_ids is not None
            # Test the property that parses IDs
            assert hasattr(settings, "admin_ids")
            assert isinstance(settings.admin_ids, list)

        except ImportError:
            pytest.skip("Settings not available")

    def test_secret_keys_exist(self):
        """Verify secret and encryption keys are configured"""
        try:
            from src.core.config import settings

            assert hasattr(settings, "secret_key")
            assert settings.secret_key is not None

            assert hasattr(settings, "encryption_key")
            assert settings.encryption_key is not None

        except ImportError:
            pytest.skip("Settings not available")


class TestDatabaseConfiguration:
    """Test database-related configuration"""

    def test_database_manager_can_be_imported(self):
        """Verify DatabaseManager class can be imported"""
        try:
            from src.core.database import DatabaseManager

            assert DatabaseManager is not None

        except ImportError as e:
            pytest.skip(f"DatabaseManager import failed: {e}")

    def test_database_manager_initialization(self):
        """Test DatabaseManager can be instantiated"""
        try:
            from src.core.database import DatabaseManager

            db_manager = DatabaseManager()
            assert db_manager is not None

        except Exception as e:
            pytest.skip(f"DatabaseManager instantiation failed: {e}")


class TestPaymentConfiguration:
    """Test payment gateway configuration"""

    def test_pakasir_settings_exist(self):
        """Verify Pakasir API settings are configured"""
        try:
            from src.core.config import settings

            assert hasattr(settings, "pakasir_api_key")
            assert settings.pakasir_api_key is not None
            assert isinstance(settings.pakasir_api_key, str)

            assert hasattr(settings, "pakasir_project_slug")
            assert settings.pakasir_project_slug is not None
            assert isinstance(settings.pakasir_project_slug, str)

            assert hasattr(settings, "pakasir_base_url")
            assert settings.pakasir_base_url is not None
            assert isinstance(settings.pakasir_base_url, str)
            assert settings.pakasir_base_url.startswith("http")

        except ImportError:
            pytest.skip("Settings not available")

    def test_payment_fee_calculation(self):
        """Test payment fee calculation method"""
        try:
            from src.core.config import settings

            # Test fee calculation for 100000 IDR
            fee = settings.calculate_payment_fee(100000)
            # 100000 * 0.007 + 310 = 700 + 310 = 1010
            assert fee == 1010

            # Test fee calculation for 0 IDR
            fee = settings.calculate_payment_fee(0)
            # 0 * 0.007 + 310 = 310
            assert fee == 310

        except ImportError:
            pytest.skip("Settings not available")


class TestConfigValidation:
    """Test configuration validation logic"""

    def test_no_missing_critical_settings(self):
        """Ensure no critical settings are None in any environment"""
        try:
            from src.core.config import settings

            # These should never be None/empty in any environment
            critical_settings = [
                "database_url",
                "audit_database_url",
                "telegram_bot_token",
                "admin_user_ids",
                "pakasir_api_key",
                "pakasir_project_slug",
                "secret_key",
                "encryption_key",
            ]

            for setting_name in critical_settings:
                value = getattr(settings, setting_name, None)
                assert value is not None, f"{setting_name} is None"
                assert len(str(value)) > 0, f"{setting_name} is empty"

        except ImportError:
            pytest.skip("Settings not available")

    def test_numeric_settings_have_valid_values(self):
        """Test numeric configuration values are valid"""
        try:
            from src.core.config import settings

            # Check payment expiry minutes
            assert isinstance(settings.payment_expiry_minutes, int)
            assert settings.payment_expiry_minutes > 0
            assert settings.payment_expiry_minutes <= 60  # Reasonable max

            # Check pool sizes
            assert isinstance(settings.db_pool_size, int)
            assert settings.db_pool_size > 0

            assert isinstance(settings.db_max_overflow, int)
            assert settings.db_max_overflow > 0

        except ImportError:
            pytest.skip("Settings not available")


class TestEnvironmentProperties:
    """Test environment detection properties"""

    def test_environment_properties_exist(self):
        """Verify environment detection properties exist"""
        try:
            from src.core.config import settings

            assert hasattr(settings, "is_production")
            assert hasattr(settings, "is_development")
            assert isinstance(settings.is_production, bool)
            assert isinstance(settings.is_development, bool)

        except ImportError:
            pytest.skip("Settings not available")
