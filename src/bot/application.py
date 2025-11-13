"""
QuickCart Bot Application
Reference: plans.md - All user flows and commands
Creates and configures the Telegram bot with all handlers
"""

import logging

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from src.core.config import settings
from src.handlers.public.start import start as start_command
from src.handlers.callbacks.menu_callbacks import handle_menu_callback

logger = logging.getLogger(__name__)

# =============================================================================
# Conversation States (for multi-step flows)
# =============================================================================

# Onboarding states
ONBOARDING_NAME = 1
ONBOARDING_WHATSAPP = 2
ONBOARDING_EMAIL = 3

# Order flow states
ORDER_SELECT_PRODUCT = 10
ORDER_ADJUST_QUANTITY = 11
ORDER_SELECT_PAYMENT = 12

# Account edit states
ACCOUNT_EDIT_NAME = 20
ACCOUNT_EDIT_EMAIL = 21
ACCOUNT_EDIT_WHATSAPP = 22

# Deposit states
DEPOSIT_AMOUNT = 30

# Message to admin states
MESSAGE_TO_ADMIN = 40

# Admin broadcast states
ADMIN_BROADCAST = 50


# =============================================================================
# Handler Imports (to be implemented)
# =============================================================================

# We'll import handlers from separate modules for organization
# from .handlers import (
#     command_handlers,
#     callback_handlers,
#     message_handlers,
#     admin_handlers,
# )


# =============================================================================
# Placeholder Handlers (will be replaced with actual implementations)
# =============================================================================


async def help_command(update: Update, context):
    """Help command"""
    await update.message.reply_text(
        "QuickCart Bot - Digital Product Auto-Order System\n\n"
        "Commands:\n"
        "/start - Start the bot\n"
        "/stock - View available stock\n"
        "/order - Order guide\n"
        "/refund - Calculate refund\n"
    )


async def stock_command(update: Update, context):
    """
    /stock command - Show available products
    Reference: plans.md Section 3.1
    """
    await update.message.reply_text("📦 Stock list placeholder")


async def order_command(update: Update, context):
    """
    /order command - Order guide
    Reference: plans.md Section 3.1
    """
    await update.message.reply_text("📖 Order guide placeholder")


async def refund_command(update: Update, context):
    """
    /refund command - Calculate refund
    Reference: plans.md Section 3.1 & 6.1
    """
    await update.message.reply_text("💰 Refund calculation placeholder")


# =============================================================================
# Admin Command Handlers (Placeholder)
# =============================================================================


async def add_product_command(update: Update, context):
    """Admin: /add - Add new product"""
    user_id = update.effective_user.id
    if user_id not in settings.admin_ids:
        return  # Silent fail for non-admins per plans.md
    await update.message.reply_text("Admin: Add product placeholder")


async def addstock_command(update: Update, context):
    """Admin: /addstock - Add stock to product"""
    user_id = update.effective_user.id
    if user_id not in settings.admin_ids:
        return
    await update.message.reply_text("Admin: Add stock placeholder")


async def delete_product_command(update: Update, context):
    """Admin: /del - Delete product (soft delete)"""
    user_id = update.effective_user.id
    if user_id not in settings.admin_ids:
        return
    await update.message.reply_text("Admin: Delete product placeholder")


async def info_command(update: Update, context):
    """Admin: /info - Show user info"""
    user_id = update.effective_user.id
    if user_id not in settings.admin_ids:
        return
    await update.message.reply_text("Admin: User info placeholder")


async def broadcast_command(update: Update, context):
    """Admin: /broadcast - Broadcast to all users"""
    user_id = update.effective_user.id
    if user_id not in settings.admin_ids:
        return
    await update.message.reply_text("Admin: Broadcast placeholder")


async def version_command(update: Update, context):
    """Admin: /version - Show bot version"""
    user_id = update.effective_user.id
    if user_id not in settings.admin_ids:
        return
    await update.message.reply_text("QuickCart v1.0.0")


# =============================================================================
# Callback Query Handlers (Placeholder)
# =============================================================================


async def callback_query_handler(update: Update, context):
    """
    Handle all inline button callbacks
    Reference: plans.md Section 2 - All callback patterns
    """
    query = update.callback_query
    await query.answer()

    callback_data = query.data

    # Route to appropriate handler based on callback data prefix
    if callback_data.startswith("menu:"):
        await handle_menu_callback(update, context)
    else:
        await query.edit_message_text("Feature coming soon!")


# =============================================================================
# Message Handlers (Placeholder)
# =============================================================================


async def text_message_handler(update: Update, context):
    """
    Handle text messages from users
    - Product ID input (numbers)
    - Onboarding flow responses
    - Admin message replies
    """
    text = update.message.text

    # Check if it's a number (product ID)
    if text.isdigit():
        product_id = int(text)
        await update.message.reply_text(
            f"You selected product #{product_id}\n(Full flow coming soon)"
        )
    else:
        await update.message.reply_text(
            "I don't understand. Please use the buttons or /help"
        )


# =============================================================================
# Error Handler
# =============================================================================


async def error_handler(update: Update, context):
    """Log errors caused by updates"""
    logger.error(f"Update {update} caused error {context.error}")

    if update and update.effective_message:
        await update.effective_message.reply_text(
            "An error occurred. Please try again or contact admin."
        )


# =============================================================================
# Application Factory
# =============================================================================


def create_bot_application() -> Application:
    """
    Create and configure the Telegram bot application
    with all handlers registered according to plans.md

    Returns:
        Configured Application instance
    """
    # Create application
    app = Application.builder().token(settings.telegram_bot_token).build()

    logger.info("Registering bot handlers...")

    # =============================================================================
    # Public Command Handlers (Section 3.1)
    # =============================================================================

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stock", stock_command))
    app.add_handler(CommandHandler("order", order_command))
    app.add_handler(CommandHandler("refund", refund_command))
    app.add_handler(CommandHandler("reff", refund_command))  # Alias

    # =============================================================================
    # Admin Command Handlers (Section 3.2)
    # =============================================================================

    # Product management
    app.add_handler(CommandHandler("add", add_product_command))
    app.add_handler(CommandHandler("addstock", addstock_command))
    app.add_handler(CommandHandler("del", delete_product_command))
    app.add_handler(CommandHandler("delstock", addstock_command))
    app.add_handler(CommandHandler("delallstock", addstock_command))
    app.add_handler(CommandHandler("editid", add_product_command))
    app.add_handler(CommandHandler("editcategory", add_product_command))
    app.add_handler(CommandHandler("editsold", add_product_command))
    app.add_handler(CommandHandler("disc", add_product_command))
    app.add_handler(CommandHandler("discat", add_product_command))
    app.add_handler(CommandHandler("priceress", add_product_command))
    app.add_handler(CommandHandler("exportstock", add_product_command))

    # User management
    app.add_handler(CommandHandler("info", info_command))
    app.add_handler(CommandHandler("pm", info_command))
    app.add_handler(CommandHandler("transfer", info_command))
    app.add_handler(CommandHandler("editbalance", info_command))
    app.add_handler(CommandHandler("ban", info_command))
    app.add_handler(CommandHandler("unban", info_command))
    app.add_handler(CommandHandler("addadmin", info_command))
    app.add_handler(CommandHandler("rmadmin", info_command))
    app.add_handler(CommandHandler("addreseller", info_command))
    app.add_handler(CommandHandler("rmress", info_command))

    # Group/notification management
    app.add_handler(CommandHandler("whitelist", info_command))
    app.add_handler(CommandHandler("rm", info_command))

    # Broadcast and system
    app.add_handler(CommandHandler("broadcast", broadcast_command))
    app.add_handler(CommandHandler("setformula", info_command))
    app.add_handler(CommandHandler("version", version_command))

    # =============================================================================
    # Callback Query Handlers (Section 2 - All inline buttons)
    # =============================================================================

    app.add_handler(CallbackQueryHandler(callback_query_handler))

    # =============================================================================
    # Message Handlers (Text, photos for admin messages, etc.)
    # =============================================================================

    # Text messages (product selection, onboarding, etc.)
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, text_message_handler)
    )

    # Photo messages (for user messages to admin)
    # app.add_handler(MessageHandler(filters.PHOTO, photo_message_handler))

    # =============================================================================
    # Error Handler
    # =============================================================================

    app.add_error_handler(error_handler)

    logger.info("✅ All bot handlers registered successfully")

    return app


# =============================================================================
# Application Entry Point (for testing)
# =============================================================================


async def main():
    """Run the bot in polling mode (for local testing)"""
    app = create_bot_application()

    logger.info("Starting QuickCart bot in polling mode...")
    await app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    import asyncio

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    asyncio.run(main())
