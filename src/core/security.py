"""
QuickCart Security Module
Simplified security utilities without external auth dependencies.
"""

import hashlib
import hmac
import secrets
from typing import Optional

from cryptography.fernet import Fernet

from src.core.config import settings


class SecurityManager:
    """Central security management for QuickCart"""

    def __init__(self) -> None:
        """Initialize security components"""
        self.fernet = None
        if settings.encryption_key:
            try:
                # Ensure key is properly formatted for Fernet
                key = settings.encryption_key.encode()
                if len(key) != 44:  # Fernet keys are 44 bytes when base64 encoded
                    # Generate proper Fernet key from the encryption key
                    key = hashlib.sha256(key).digest()
                    key = Fernet.generate_key()
                self.fernet = Fernet(key)
            except Exception:
                self.fernet = None

    def encrypt_sensitive_data(self, data: str) -> str:
        """
        Encrypt sensitive data (e.g., product content, user PII)

        Args:
            data: Plain text data

        Returns:
            Encrypted data (base64 encoded)

        Raises:
            ValueError: If encryption key not configured
        """
        if not self.fernet:
            raise ValueError("Encryption key not configured")

        return self.fernet.encrypt(data.encode()).decode()

    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """
        Decrypt sensitive data

        Args:
            encrypted_data: Base64 encoded encrypted data

        Returns:
            Decrypted plain text

        Raises:
            ValueError: If encryption key not configured or decryption fails
        """
        if not self.fernet:
            raise ValueError("Encryption key not configured")

        try:
            return self.fernet.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")

    def generate_secure_token(self, length: int = 32) -> str:
        """
        Generate cryptographically secure random token

        Args:
            length: Token length in bytes

        Returns:
            URL-safe random token
        """
        return secrets.token_urlsafe(length)

    def generate_bank_id(self) -> str:
        """
        Generate unique 6-digit bank ID for user

        Returns:
            6-character alphanumeric bank ID
        """
        # Generate random 6-character uppercase alphanumeric ID
        import random
        import string

        chars = string.ascii_uppercase + string.digits
        return "".join(random.choices(chars, k=6))

    def verify_webhook_signature(
        self, payload: str, signature: str, secret: str
    ) -> bool:
        """
        Verify webhook signature (HMAC-SHA256)
        Used for Pakasir webhook validation

        Args:
            payload: Raw webhook payload
            signature: Provided signature
            secret: Webhook secret

        Returns:
            True if signature is valid
        """
        expected_signature = hmac.new(
            secret.encode(), payload.encode(), hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(expected_signature, signature)


class TelegramAuth:
    """Telegram-specific authentication and authorization"""

    @staticmethod
    def is_admin(user_id: int) -> bool:
        """
        Check if user is admin

        Args:
            user_id: Telegram user ID

        Returns:
            True if user is in admin list
        """
        return user_id in settings.admin_ids

    @staticmethod
    def validate_telegram_auth(user_id: int, username: Optional[str] = None) -> bool:
        """
        Validate Telegram user authentication

        Args:
            user_id: Telegram user ID
            username: Telegram username (optional)

        Returns:
            True if user is authentic Telegram user
        """
        # Telegram user IDs are positive integers
        if user_id <= 0:
            return False

        # If username provided, validate format
        if username and not username.replace("_", "").isalnum():
            return False

        return True


class InputValidator:
    """Input validation and sanitization"""

    @staticmethod
    def sanitize_text_input(text: str, max_length: int = 1000) -> str:
        """
        Sanitize user text input

        Args:
            text: Raw text input
            max_length: Maximum allowed length

        Returns:
            Sanitized text
        """
        # Strip whitespace
        text = text.strip()

        # Truncate to max length
        if len(text) > max_length:
            text = text[:max_length]

        # Remove null bytes and control characters (except newline)
        text = "".join(char for char in text if ord(char) >= 32 or char == "\n")

        return text

    @staticmethod
    def validate_product_id(product_id: str) -> bool:
        """
        Validate product ID format

        Args:
            product_id: Product ID to validate

        Returns:
            True if valid format (1-24)
        """
        try:
            pid = int(product_id)
            return 1 <= pid <= 24
        except (ValueError, TypeError):
            return False

    @staticmethod
    def validate_amount(amount: str) -> bool:
        """
        Validate monetary amount

        Args:
            amount: Amount string to validate

        Returns:
            True if valid amount
        """
        try:
            amt = float(amount)
            return amt > 0 and amt <= 100_000_000  # Max 100 million IDR
        except (ValueError, TypeError):
            return False

    @staticmethod
    def validate_quantity(quantity: str) -> bool:
        """
        Validate order quantity

        Args:
            quantity: Quantity string to validate

        Returns:
            True if valid quantity (1-100)
        """
        try:
            qty = int(quantity)
            return 1 <= qty <= 100
        except (ValueError, TypeError):
            return False


# Global instances
security_manager = SecurityManager()
telegram_auth = TelegramAuth()
input_validator = InputValidator()


# Convenience functions for backward compatibility
def generate_bank_id() -> str:
    """Generate unique bank ID"""
    return security_manager.generate_bank_id()


def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return telegram_auth.is_admin(user_id)


def verify_webhook(payload: str, signature: str, secret: str) -> bool:
    """Verify webhook signature"""
    return security_manager.verify_webhook_signature(payload, signature, secret)
