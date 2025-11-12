"""
Pakasir Payment Gateway Integration
Reference: docs/07-api_contracts.md, docs/08-integration_plan.md (CR-001)
"""

import logging
from typing import Dict, Optional

import httpx

from src.core.config import settings

logger = logging.getLogger(__name__)


class PakasirClient:
    """
    Pakasir QRIS payment gateway client
    Reference: CR-001 Best Practice - Health checks before payment creation
    """

    def __init__(self):
        self.base_url = settings.pakasir_base_url
        self.api_key = settings.pakasir_api_key
        self.project_slug = settings.pakasir_project_slug
        self.custom_domain = settings.pakasir_payment_custom_domain

    async def check_health(self) -> bool:
        """Check if Pakasir is operational before showing payment option"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(self.base_url)
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"Pakasir health check failed: {e}")
            return False

    async def create_payment(self, order_id: str, amount: int) -> Optional[Dict]:
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
            logger.error("Pakasir is not available, cannot create payment")
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
                data = response.json()

                logger.info(f"Payment created successfully for order {order_id}")
                return data

        except httpx.HTTPStatusError as e:
            logger.error(
                f"Pakasir API error: {e.response.status_code} - {e.response.text}"
            )
            return None
        except Exception as e:
            logger.error(f"Pakasir payment creation failed: {e}")
            return None

    async def check_payment_status(self, order_id: str) -> Optional[Dict]:
        """
        Check payment status for an order

        Args:
            order_id: Order ID to check

        Returns:
            Payment status data or None if failed
        """
        url = f"{self.base_url}/api/checkstatus"
        payload = {
            "project": self.project_slug,
            "order_id": order_id,
            "api_key": self.api_key,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to check payment status for {order_id}: {e}")
            return None

    def get_checkout_url(self, order_id: str) -> str:
        """
        Get checkout URL for payment page

        Args:
            order_id: Order ID

        Returns:
            Full checkout URL
        """
        return f"{self.custom_domain}/{self.project_slug}/{order_id}"

    async def cancel_payment(self, order_id: str) -> bool:
        """
        Cancel/expire a payment (if supported by Pakasir API)

        Args:
            order_id: Order ID to cancel

        Returns:
            True if successful, False otherwise
        """
        # Note: This may not be supported by Pakasir API
        # Implement if the API provides this functionality
        logger.warning(
            f"Payment cancellation requested for {order_id} - may not be supported"
        )
        return False


# Singleton instance
pakasir_client = PakasirClient()
