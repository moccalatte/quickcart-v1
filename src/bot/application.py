"""
QuickCart Bot Application
Reference: plans.md - All user flows and commands

Creates and configures the Telegram bot with all handlers.
Implements flexible navigation using Redis session state (not ConversationHandler).
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

from src.bot.handlers.callback_handlers import handle_callback_query
from src.bot.handlers.command_handlers import (
    help_command,
    order_command,
    refund_command,
    skip_command,
    start_command,
    stock_command,
)
from src.bot.handlers.message_handlers import (
    handle_photo_message,
    handle_text_message,
)
from src.core.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# Admin Command Handlers (Placeholder - to be implemented)
# =============================================================================


async def add_product_command(update: Update, context):
    """
    Admin: /add - Add new product
    Usage: /add <id> <name> <price_customer> [price_reseller] [category] [description]
    """
    user_id = update.effective_user.id
    if user_id not in settings.admin_ids:
        return  # Silent fail for non-admins per plans.md

    await update.message.reply_text(
        "⚙️ **Admin: Tambah Produk**\n\n"
        "Format:\n"
        "`/add <id> <nama> <harga_customer> [harga_reseller] [kategori] [deskripsi]`\n\n"
        "Contoh:\n"
        "`/add 1 Tutorial Premium 50000 40000 Tutorial Lengkap banget`\n\n"
        "Fitur ini sedang dalam pengembangan.",
        parse_mode="Markdown",
    )


async def addstock_command(update: Update, context):
    """
    Admin: /addstock - Add stock to product
    Usage: /addstock <product_id> <content1> | <content2> | <content3>
    """
    user_id = update.effective_user.id
    if user_id not in settings.admin_ids:
        return

    await update.message.reply_text(
        "⚙️ **Admin: Tambah Stok**\n\n"
        "Format:\n"
        "`/addstock <product_id> <konten1> | <konten2> | <konten3>`\n\n"
        "Contoh:\n"
        "`/addstock 1 AKUN001 | AKUN002 | AKUN003`\n\n"
        "Fitur ini sedang dalam pengembangan.",
        parse_mode="Markdown",
    )


async def delete_product_command(update: Update, context):
    """Admin: /del - Delete product (soft delete)"""
    user_id = update.effective_user.id
    if user_id not in settings.admin_ids:
        return

    await update.message.reply_text(
        "⚙️ **Admin: Hapus Produk**\n\n"
        "Format: `/del <product_id>`\n\n"
        "Fitur ini sedang dalam pengembangan.",
        parse_mode="Markdown",
    )


async def info_command(update: Update, context):
    """Admin: /info - Show user info"""
    user_id = update.effective_user.id
    if user_id not in settings.admin_ids:
        return

    await update.message.reply_text(
        "⚙️ **Admin: Info User**\n\n"
        "Format: `/info <user_id>`\n\n"
        "Fitur ini sedang dalam pengembangan.",
        parse_mode="Markdown",
    )


async def broadcast_command(update: Update, context):
    """Admin: /broadcast - Broadcast to all users"""
    user_id = update.effective_user.id
    if user_id not in settings.admin_ids:
        return

    await update.message.reply_text(
        "⚙️ **Admin: Broadcast**\n\n"
        "Format: `/broadcast <pesan>`\n\n"
        "Fitur ini sedang dalam pengembangan.",
        parse_mode="Markdown",
    )


async def version_command(update: Update, context):
    """Admin: /version - Show bot version"""
    user_id = update.effective_user.id
    if user_id not in settings.admin_ids:
        return

    await update.message.reply_text(
        f"🤖 **{settings.bot_name}**\n\n"
        f"Store: {settings.store_name}\n"
        "Version: 1.1.0\n"
        "Environment: " + settings.environment + "\n"
        "Python Telegram Bot: v22.5"
    )


# =============================================================================
# Error Handler
# =============================================================================


async def error_handler(update: Update, context):
    """Log errors caused by updates"""
    logger.error(
        f"Update {update} caused error {context.error}", exc_info=context.error
    )

    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "❌ Terjadi kesalahan sistem.\n"
                "Silakan coba lagi atau hubungi admin jika masalah berlanjut."
            )
        except Exception as e:
            logger.error(f"Failed to send error message to user: {e}")


# =============================================================================
# Application Factory
# =============================================================================


def create_bot_application() -> Application:
    """
    Create and configure the Telegram bot application
    with all handlers registered according to plans.md

    Uses flexible navigation - no ConversationHandler
    Session state managed via Redis

    Returns:
        Configured Application instance
    """
    # Create application
    app = Application.builder().token(settings.telegram_bot_token).build()

    logger.info("🔧 Registering bot handlers...")

    # =============================================================================
    # Public Command Handlers (Section 3.1)
    # =============================================================================

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stock", stock_command))
    app.add_handler(CommandHandler("order", order_command))
    app.add_handler(CommandHandler("refund", refund_command))
    app.add_handler(CommandHandler("reff", refund_command))  # Alias
    app.add_handler(CommandHandler("skip", skip_command))  # For onboarding

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

    # Single handler routes all callbacks based on prefix
    # This supports flexible navigation - users can click any button anytime
    app.add_handler(CallbackQueryHandler(handle_callback_query))

    # =============================================================================
    # Message Handlers (Text, photos for admin messages, etc.)
    # =============================================================================

    # Text messages (product selection, onboarding, etc.)
    # This handler supports flexible navigation by checking session state
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message)
    )

    # Photo messages (for user messages to admin)
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo_message))

    # =============================================================================
    # Error Handler
    # =============================================================================

    app.add_error_handler(error_handler)

    logger.info("✅ All bot handlers registered successfully")
    logger.info("🎯 Flexible navigation enabled - no ConversationHandler")
    logger.info("💾 Session state managed via Redis")

    return app


# =============================================================================
# Application Entry Point (for testing)
# =============================================================================


async def main():
    """Run the bot in polling mode (for local testing)"""
    app = create_bot_application()

    logger.info(f"🚀 Starting {settings.bot_name} in polling mode...")
    await app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    import asyncio

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    asyncio.run(main())
