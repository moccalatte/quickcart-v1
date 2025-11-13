"""
QuickCart Main Application Entry Point
Reference: docs/05-architecture.md, docs/14-build_plan.md

This is the central FastAPI application that orchestrates:
- Telegram bot webhook handling
- Payment webhook processing
- Admin API endpoints
- Health checks and monitoring
"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from telegram import Update

from src.bot.application import create_bot_application
from src.core.config import settings
from src.core.database import db_manager
from src.core.redis import redis_client

# Configure logging
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

logger = logging.getLogger(__name__)

# Global bot application instance
bot_app = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global bot_app

    logger.info("🚀 Starting QuickCart v1...")

    # Initialize connections
    await redis_client.connect()
    logger.info("✓ Redis connected")

    # Check database health
    db_status = await db_manager.check_connection()
    logger.info(f"✓ Database status: {db_status}")

    # Initialize bot application
    bot_app = create_bot_application()
    # await bot_app.initialize()
    logger.info("✓ Bot initialized")

    logger.info("✅ QuickCart is ready!")

    yield

    # Cleanup
    logger.info("Shutting down QuickCart...")

    if bot_app:
        await bot_app.shutdown()
        logger.info("✓ Bot shutdown complete")

    await redis_client.disconnect()
    await db_manager.close()
    logger.info("👋 QuickCart stopped")


app = FastAPI(
    title="QuickCart API",
    description="Automated Telegram Bot for Digital Product Sales",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "QuickCart",
        "version": "1.0.0",
        "status": "operational",
        "documentation": "/docs",
    }


@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring and load balancers
    Reference: docs/17-observability.md
    """
    # Check Redis
    redis_ok = await redis_client.ping() if redis_client.redis else False

    # Check databases
    db_status = await db_manager.check_connection()

    is_healthy = (
        redis_ok and db_status["main_db"] == "ok" and db_status["audit_db"] == "ok"
    )

    status_code = 200 if is_healthy else 503

    return JSONResponse(
        status_code=status_code,
        content={
            "status": "healthy" if is_healthy else "unhealthy",
            "services": {
                "redis": "ok" if redis_ok else "error",
                "main_database": db_status["main_db"],
                "audit_database": db_status["audit_db"],
            },
        },
    )


@app.post("/webhooks/telegram")
async def telegram_webhook(request: Request):
    """
    Telegram bot webhook endpoint
    Reference: docs/07-api_contracts.md
    """
    global bot_app

    if not bot_app:
        logger.error("Bot application not initialized")
        return JSONResponse(
            status_code=503, content={"status": "error", "message": "Bot not ready"}
        )

    try:
        # Parse update from Telegram
        data = await request.json()
        update = Update.de_json(data, bot_app.bot)

        # Process update
        await bot_app.process_update(update)

        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Telegram webhook error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500, content={"status": "error", "message": str(e)}
        )


@app.post("/webhooks/pakasir")
async def pakasir_webhook(request: Request):
    """
    Pakasir payment webhook endpoint - QRIS only
    Reference: docs/pakasir.md Section 4

    Expected payload from Pakasir:
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

    Status values: "completed", "pending", "expired"
    """
    try:
        data = await request.json()

        # Validate webhook signature if secret is configured
        signature = request.headers.get("X-Pakasir-Signature")
        if settings.pakasir_webhook_secret and signature:
            from src.integrations.pakasir import pakasir_client

            if not pakasir_client.validate_webhook_signature(signature, data):
                logger.error(
                    f"Invalid webhook signature for order {data.get('order_id')}"
                )
                return JSONResponse(
                    status_code=401,
                    content={"status": "error", "message": "Invalid signature"},
                )

        logger.info(f"Received Pakasir webhook: {data}")

        # Extract payment info (as per pakasir.md docs)
        order_id = data.get("order_id")
        status = data.get("status")
        amount = data.get("amount")
        payment_method = data.get("payment_method")
        completed_at = data.get("completed_at")
        metadata = data.get("metadata", {})

        if not order_id or not status or not amount:
            logger.error(f"Invalid webhook payload: {data}")
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Missing required fields"},
            )

        # Validate payment method (QRIS only)
        if payment_method and payment_method != "qris":
            logger.warning(f"Unexpected payment method: {payment_method}")

        # Process based on status
        if status == "completed":
            telegram_id = metadata.get("telegram_id")
            if not telegram_id:
                try:
                    telegram_id = int(order_id.split("-")[0].replace("tg", ""))
                except (ValueError, IndexError):
                    logger.error(f"Could not extract telegram_id from order_id: {order_id}")
                    return JSONResponse(status_code=400, content={"status": "error", "message": "Invalid order_id format"})

            logger.info(f"Processing successful payment for order_id: {order_id} and telegram_id: {telegram_id}")

            # Simulate database update
            logger.info(f"Updating order {order_id} to 'paid' in the database.")

            # Simulate product delivery
            if bot_app:
                message = (
                    f"🎉 Pesanan berhasil!\n"
                    f"📦 Produk: Premium Account\n"
                    f"🔢 Jumlah: 1\n"
                    f"🧾 Invoice: {order_id}\n"
                    f"Terima kasih telah berbelanja! Silakan cek detail produk di bawah ini. 😊"
                )
                await bot_app.bot.send_message(chat_id=telegram_id, text=message)
                logger.info(f"Sent confirmation message to telegram_id: {telegram_id}")

        elif status == "expired":
            logger.info(f"Processing expired payment for order_id: {order_id}")
            # Simulate database update
            logger.info(f"Updating order {order_id} to 'expired' in the database.")

        elif status == "pending":
            # Payment still pending (usually not sent via webhook, but handle it)
            logger.info(f"Payment pending: order_id={order_id}")

        else:
            logger.warning(f"Unknown payment status: {status} for order {order_id}")

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Pakasir webhook error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500, content={"status": "error", "message": str(e)}
        )


@app.get("/api/stats")
async def get_stats():
    """
    Get bot statistics (total users, transactions, etc.)
    For admin dashboard or monitoring
    """
    try:
        # TODO: Implement statistics gathering
        # - Total users from database
        # - Total transactions
        # - Revenue statistics
        # - Popular products

        return {
            "total_users": 0,
            "total_transactions": 0,
            "total_revenue": 0,
        }
    except Exception as e:
        logger.error(f"Stats error: {e}")
        return JSONResponse(
            status_code=500, content={"status": "error", "message": str(e)}
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )
