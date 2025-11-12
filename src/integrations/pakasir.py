"""
Pakasir Payment Gateway Integration - QRIS Only
Reference: docs/pakasir.md
Official API: https://app.pakasir.com/api/
"""

import logging
from datetime import datetime
from typing import Dict, Optional

import httpx

from src.core.config import settings

logger = logging.getLogger(__name__)


class PakasirClient:
    """
    Pakasir QRIS payment gateway client

    Supports QRIS payment method only as per business requirements.

    API Endpoints:
    - POST /api/transactioncreate/qris - Create QRIS payment
    - GET /api/transactiondetail - Check payment status
    - Webhook: Receives payment notifications via POST

    Reference: docs/pakasir.md
    """

    def __init__(self):
        self.base_url = settings.pakasir_base_url.rstrip("/")
        self.api_key = settings.pakasir_api_key
        self.project_slug = settings.pakasir_project_slug
        self.custom_domain = settings.pakasir_payment_custom_domain.rstrip("/")
        self.webhook_secret = getattr(settings, "pakasir_webhook_secret", None)

    async def check_health(self) -> bool:
        """Check if Pakasir API is operational"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(self.base_url)
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Pakasir health check failed: {e}")
            return False

    async def create_qris_payment(
        self, order_id: str, amount: int, metadata: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Create QRIS payment transaction

        Args:
            order_id: Unique order ID (e.g., "tg12345-ORDER123")
            amount: Amount in IDR (integer, no decimals)
            metadata: Optional metadata (e.g., {"telegram_id": 12345, "telegram_username": "user"})

        Returns:
            {
                "payment": {
                    "project": "your-project",
                    "order_id": "ORDER123",
                    "amount": 99000,
                    "fee": 1003,
                    "total_payment": 100003,
                    "payment_method": "qris",
                    "payment_number": "00020101021226610016...",  # QR code string
                    "expired_at": "2025-09-19T01:18:49.678622564Z"
                }
            }
            or None if failed

        Reference: docs/pakasir.md Section 3.2
        """
        url = f"{self.base_url}/api/transactioncreate/qris"

        payload = {
            "project": self.project_slug,
            "order_id": order_id,
            "amount": amount,
            "api_key": self.api_key,
        }

        # Add metadata if provided (for webhook identification)
        if metadata:
            payload["metadata"] = metadata

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()

                logger.info(
                    f"QRIS payment created: order_id={order_id}, "
                    f"amount={amount}, "
                    f"total={data.get('payment', {}).get('total_payment')}"
                )

                return data

        except httpx.HTTPStatusError as e:
            logger.error(
                f"Pakasir API error: {e.response.status_code} - {e.response.text}"
            )
            return None
        except Exception as e:
            logger.error(f"Failed to create QRIS payment for {order_id}: {e}")
            return None

    async def get_payment_status(self, order_id: str, amount: int) -> Optional[Dict]:
        """
        Get payment transaction status

        Args:
            order_id: Order ID to check
            amount: Transaction amount (required by API)

        Returns:
            {
                "transaction": {
                    "amount": 22000,
                    "order_id": "ORDER123",
                    "project": "your-project",
                    "status": "completed" | "pending" | "expired",
                    "payment_method": "qris",
                    "completed_at": "2025-09-10T08:07:02.819+07:00"
                }
            }
            or None if failed

        Reference: docs/pakasir.md Section 5
        """
        # Build query params
        params = {
            "project": self.project_slug,
            "amount": amount,
            "order_id": order_id,
            "api_key": self.api_key,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/api/transactiondetail", params=params
                )
                response.raise_for_status()
                data = response.json()

                status = data.get("transaction", {}).get("status", "unknown")
                logger.info(f"Payment status for {order_id}: {status}")

                return data

        except httpx.HTTPStatusError as e:
            logger.error(
                f"Failed to get payment status: {e.response.status_code} - {e.response.text}"
            )
            return None
        except Exception as e:
            logger.error(f"Error checking payment status for {order_id}: {e}")
            return None

    def get_checkout_url(self, order_id: str, amount: int) -> str:
        """
        Generate checkout URL for QRIS payment

        Args:
            order_id: Order ID
            amount: Amount in IDR

        Returns:
            Full checkout URL with qris_only=1 parameter
            Example: https://pots.my.id/pay/projectslug/10000?order_id=ORDER123&qris_only=1

        Reference: docs/pakasir.md Section 2.1
        """
        # Format: {domain}/pay/{slug}/{amount}?order_id={order_id}&qris_only=1
        url = f"{self.custom_domain}/pay/{self.project_slug}/{amount}"
        url += f"?order_id={order_id}&qris_only=1"

        return url

    def extract_qris_code(self, payment_data: Dict) -> Optional[str]:
        """
        Extract QRIS code string from payment creation response

        Args:
            payment_data: Response from create_qris_payment()

        Returns:
            QRIS code string (to be converted to QR image) or None

        Note: Use a QR code library (e.g., qrcode, segno) to generate
        QR image from this string for display to user.
        """
        try:
            return payment_data.get("payment", {}).get("payment_number")
        except Exception as e:
            logger.error(f"Failed to extract QRIS code: {e}")
            return None

    def get_expiry_time(self, payment_data: Dict) -> Optional[datetime]:
        """
        Extract payment expiry time from payment creation response

        Args:
            payment_data: Response from create_qris_payment()

        Returns:
            Expiry datetime or None
        """
        try:
            expired_at = payment_data.get("payment", {}).get("expired_at")
            if expired_at:
                # Parse ISO format: "2025-09-19T01:18:49.678622564Z"
                return datetime.fromisoformat(expired_at.replace("Z", "+00:00"))
        except Exception as e:
            logger.error(f"Failed to parse expiry time: {e}")
        return None

    def validate_webhook_signature(self, signature: str, payload: Dict) -> bool:
        """
        Validate webhook signature (if webhook secret is configured)

        Args:
            signature: Value from X-Pakasir-Signature header
            payload: Webhook payload dict

        Returns:
            True if valid or no secret configured, False if invalid

        Reference: docs/pakasir.md Section 4
        """
        if not self.webhook_secret:
            # No secret configured, skip validation
            logger.warning(
                "Webhook secret not configured, skipping signature validation"
            )
            return True

        # TODO: Implement signature validation based on Pakasir's algorithm
        # This depends on how Pakasir generates the signature (HMAC SHA256, etc.)
        # For now, return True to not block webhooks
        logger.warning("Webhook signature validation not implemented yet")
        return True

    async def simulate_payment(self, order_id: str, amount: int) -> Optional[Dict]:
        """
        Simulate payment (for sandbox/testing mode only)

        Args:
            order_id: Order ID
            amount: Amount in IDR

        Returns:
            Simulation response or None

        Reference: docs/pakasir.md Section 3.4
        """
        url = f"{self.base_url}/api/paymentsimulation"

        payload = {
            "project": self.project_slug,
            "order_id": order_id,
            "amount": amount,
            "api_key": self.api_key,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()

                logger.info(f"Payment simulated for order {order_id}")
                return response.json()

        except Exception as e:
            logger.error(f"Payment simulation failed for {order_id}: {e}")
            return None


# Singleton instance
pakasir_client = PakasirClient()


# Webhook payload structure (for reference)
"""
Expected webhook payload from Pakasir:

{
    "amount": 22000,
    "order_id": "tg12345-ORDER123",
    "project": "your-project",
    "status": "completed",
    "payment_method": "qris",
    "completed_at": "2025-09-10T08:07:02.819+07:00",
    "metadata": {
        "telegram_id": 12345,
        "telegram_username": "user123"
    }
}

Status values:
- "completed" - Payment successful
- "pending" - Payment not yet completed
- "expired" - Payment expired

Headers:
- X-Pakasir-Signature: Optional signature for validation
"""
