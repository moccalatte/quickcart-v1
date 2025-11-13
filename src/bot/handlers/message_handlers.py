"""
Message Handlers for QuickCart Bot
Reference: plans.md Section 2 - User flows

Handles all text and media messages from users:
- Product ID input (numbers)
- Onboarding flow responses
- Reply keyboard button presses
- Admin message forwarding
"""

import logging
from typing import Optional

from telegram import Update
from telegram.ext import ContextTypes

from src.bot.keyboards.inline import (
    get_account_menu_keyboard,
    get_main_menu_inline,
    get_product_detail_keyboard,
)
from src.bot.keyboards.reply import get_main_menu_keyboard
from src.core.config import settings
from src.core.redis import get_session_manager
from src.repositories.product_repository import ProductRepository
from src.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Main text message handler
    Routes messages based on context and content
    """
    user = update.effective_user
    text = update.message.text.strip()

    logger.info(f"Text message from user {user.id}: {text}")

    session_manager = await get_session_manager()
    session = await session_manager.get_session(user.id)

    # Check if user is in a specific flow
    if session and session.get("current_flow"):
        current_flow = session.get("current_flow")

        if current_flow == "onboarding":
            await handle_onboarding_input(update, context, session)
            return
        elif current_flow == "messaging_admin":
            await handle_admin_message_input(update, context, session)
            return
        elif (
            current_flow == "deposit" and session.get("current_step") == "custom_amount"
        ):
            await handle_deposit_custom_amount(update, context, session)
            return

    # Handle reply keyboard buttons
    if text in ["📋 LIST PRODUK", "📦 STOK", "👤 AKUN", "💬 KIRIM PESAN"]:
        await handle_reply_keyboard_button(update, context, text)
        return

    # Check if it's a product ID
    if text.isdigit():
        await handle_product_id_input(update, context, int(text))
        return

    # Default: guide user
    await update.message.reply_text(
        "❓ Saya tidak mengerti pesan tersebut.\n\n"
        "Gunakan:\n"
        "• Tombol di bawah untuk navigasi\n"
        "• /help untuk bantuan\n"
        "• /start untuk kembali ke menu utama"
    )


async def handle_reply_keyboard_button(
    update: Update, context: ContextTypes.DEFAULT_TYPE, button_text: str
):
    """Handle reply keyboard button presses"""
    user = update.effective_user
    session_manager = await get_session_manager()

    if button_text == "📋 LIST PRODUK":
        # Show product list inline menu
        await session_manager.save_session(
            user.id, {"current_flow": "browsing", "current_step": "menu"}
        )
        await update.message.reply_text(
            "📋 **Daftar Produk**\n\nPilih kategori atau lihat semua produk:",
            parse_mode="Markdown",
            reply_markup=get_main_menu_inline(),
        )

    elif button_text == "📦 STOK":
        # Show stock list
        product_repo = ProductRepository()
        products = await product_repo.get_all_with_stock()

        if not products:
            await update.message.reply_text(
                "📦 Belum ada produk yang tersedia.\nSilakan cek lagi nanti!"
            )
            return

        stock_text = "📦 **Ketersediaan Stok Produk**\n\n"

        for product in products[:30]:  # Limit to 30 to avoid message too long
            product_id = product["id"]
            name = product["name"]
            stock = product["stock_count"]
            price = product["customer_price"]

            stock_emoji = "✅" if stock > 0 else "❌"
            stock_text += (
                f"{stock_emoji} **{product_id}. {name}**\n"
                f"   Stok: {stock} | Harga: Rp {price:,.0f}\n\n"
            )

        await update.message.reply_text(stock_text, parse_mode="Markdown")

    elif button_text == "👤 AKUN":
        # Show account info
        user_repo = UserRepository()
        user_data = await user_repo.get_by_id(user.id)

        if not user_data:
            await update.message.reply_text(
                "❌ Data pengguna tidak ditemukan.\nSilakan /start untuk membuat akun."
            )
            return

        account_text = (
            "👤 **Informasi Akun**\n\n"
            f"🆔 User ID: `{user_data['id']}`\n"
            f"👤 Nama: {user_data['name']}\n"
            f"📱 Username: @{user_data.get('username', 'Tidak ada')}\n"
            f"📧 Email: {user_data.get('email', 'Tidak ada')}\n"
            f"📞 WhatsApp: {user_data.get('whatsapp_number', 'Tidak ada')}\n"
            f"💰 Saldo: Rp {user_data.get('account_balance', 0):,.0f}\n"
            f"🏦 Bank ID: {user_data.get('bank_id', 'N/A')}\n"
            f"⭐️ Status: {user_data.get('member_status', 'customer').title()}\n\n"
            "Pilih aksi di bawah:"
        )

        await update.message.reply_text(
            account_text,
            parse_mode="Markdown",
            reply_markup=get_account_menu_keyboard(),
        )

    elif button_text == "💬 KIRIM PESAN":
        # Start admin message flow
        await session_manager.save_session(
            user.id,
            {"current_flow": "messaging_admin", "current_step": "awaiting_message"},
        )
        await update.message.reply_text(
            "💬 **Kirim Pesan ke Admin**\n\n"
            "Silakan ketik pesan Anda (bisa dengan 1 foto).\n"
            "Pesan akan diteruskan ke semua admin.\n\n"
            "Ketik /cancel untuk membatalkan."
        )


async def handle_product_id_input(
    update: Update, context: ContextTypes.DEFAULT_TYPE, product_id: int
):
    """
    Handle product ID input from user
    Reference: plans.md Section 2.2 - Order Flow
    """
    user = update.effective_user
    session_manager = await get_session_manager()
    product_repo = ProductRepository()
    user_repo = UserRepository()

    # Get product details
    product = await product_repo.get_by_id(product_id)

    if not product:
        await update.message.reply_text(
            f"❌ Produk dengan ID {product_id} tidak ditemukan.\n"
            "Gunakan /stock untuk melihat daftar produk tersedia."
        )
        return

    # Check if product is active
    if not product.get("is_active"):
        await update.message.reply_text(
            f"⚠️ Produk **{product['name']}** sedang tidak tersedia.\n"
            "Silakan pilih produk lain.",
            parse_mode="Markdown",
        )
        return

    # Check stock
    stock_count = await product_repo.get_stock_count(product_id)

    if stock_count == 0:
        await update.message.reply_text(
            f"❌ Produk **{product['name']}** habis stok.\n"
            "Silakan pilih produk lain atau tunggu restock.",
            parse_mode="Markdown",
        )
        return

    # Get user to determine pricing
    user_data = await user_repo.get_by_id(user.id)
    member_status = (
        user_data.get("member_status", "customer") if user_data else "customer"
    )

    # Determine price based on member status
    if member_status == "reseller" and product.get("reseller_price"):
        price = product["reseller_price"]
        price_label = "Harga Reseller"
    else:
        price = product["customer_price"]
        price_label = "Harga"

    # Save session with product selection (flexible navigation - clear any previous flow)
    await session_manager.save_session(
        user.id,
        {
            "current_flow": "ordering",
            "current_step": "product_selected",
            "product_id": product_id,
            "quantity": 1,
            "price": float(price),
        },
    )

    # Build product detail message
    product_text = (
        f"📦 **{product['name']}**\n\n"
        f"🆔 ID Produk: {product['id']}\n"
        f"📊 Stok: {stock_count} tersedia\n"
        f"💰 {price_label}: Rp {price:,.0f}\n"
        f"📈 Terjual: {product.get('sold_count', 0)}x\n\n"
    )

    if product.get("description"):
        product_text += f"📝 Deskripsi:\n{product['description']}\n\n"

    product_text += "Gunakan tombol di bawah untuk mengatur jumlah pesanan:"

    await update.message.reply_text(
        product_text,
        parse_mode="Markdown",
        reply_markup=get_product_detail_keyboard(quantity=1),
    )


async def handle_onboarding_input(
    update: Update, context: ContextTypes.DEFAULT_TYPE, session: dict
):
    """
    Handle user input during onboarding flow
    Reference: plans.md Section 2.1
    """
    user = update.effective_user
    text = update.message.text.strip()
    session_manager = await get_session_manager()

    current_step = session.get("current_step")

    if current_step == "name":
        # Validate and save name
        if len(text) > 100:
            await update.message.reply_text(
                "❌ Nama terlalu panjang. Maksimal 100 karakter.\n"
                "Silakan masukkan nama yang lebih pendek:"
            )
            return

        session["name"] = text
        session["current_step"] = "whatsapp"
        await session_manager.save_session(user.id, session)

        await update.message.reply_text(
            "✅ Nama tersimpan!\n\n"
            "📱 Masukkan nomor **WhatsApp** Anda:\n"
            "(Atau ketik /skip untuk melewati)",
            parse_mode="Markdown",
        )

    elif current_step == "whatsapp":
        # Validate and save WhatsApp number
        if len(text) > 20:
            await update.message.reply_text(
                "❌ Nomor WhatsApp tidak valid.\nSilakan masukkan nomor yang benar:"
            )
            return

        session["whatsapp"] = text
        session["current_step"] = "email"
        await session_manager.save_session(user.id, session)

        await update.message.reply_text(
            "✅ Nomor WhatsApp tersimpan!\n\n"
            "📧 Masukkan **email** Anda:\n"
            "(Atau ketik /skip untuk melewati)",
            parse_mode="Markdown",
        )

    elif current_step == "email":
        # Simple email validation
        if "@" not in text or "." not in text:
            await update.message.reply_text(
                "❌ Format email tidak valid.\n"
                "Silakan masukkan email yang benar (atau /skip):"
            )
            return

        session["email"] = text
        await complete_onboarding(update, context, session)


async def complete_onboarding(
    update: Update, context: ContextTypes.DEFAULT_TYPE, session: dict
):
    """Complete onboarding and create user account"""
    from src.bot.handlers.command_handlers import show_main_menu
    from src.services.user_service import UserService

    user = update.effective_user
    session_manager = await get_session_manager()
    user_service = UserService()

    try:
        # Create user account
        new_user = await user_service.create_user(
            telegram_id=user.id,
            name=session.get("name", "Anonymous"),
            username=session.get("telegram_username"),
            email=session.get("email"),
            whatsapp_number=session.get("whatsapp"),
        )

        # Clear onboarding session
        await session_manager.clear_session(user.id)

        await update.message.reply_text(
            f"✅ Akun Anda berhasil dibuat!\n\n"
            f"Selamat datang, **{new_user['name']}**! 🎉",
            parse_mode="Markdown",
        )

        # Show main menu
        await show_main_menu(update, context, new_user)

    except Exception as e:
        logger.error(f"Failed to complete onboarding for user {user.id}: {e}")
        await update.message.reply_text(
            "❌ Terjadi kesalahan saat membuat akun.\nSilakan coba lagi dengan /start"
        )


async def handle_admin_message_input(
    update: Update, context: ContextTypes.DEFAULT_TYPE, session: dict
):
    """
    Handle message to admin input
    Reference: plans.md Section 2.4
    """
    user = update.effective_user
    session_manager = await get_session_manager()
    user_repo = UserRepository()

    # Get user data
    user_data = await user_repo.get_by_id(user.id)
    user_name = user_data.get("name", user.first_name) if user_data else user.first_name

    # Build admin notification message
    admin_message = (
        f"💬 **Pesan Baru dari User**\n\n"
        f"👤 Nama: {user_name}\n"
        f"🆔 User ID: `{user.id}`\n"
        f"📱 Username: @{user.username or 'Tidak ada'}\n\n"
        f"**Pesan:**\n{update.message.text}"
    )

    # Send to all admins
    sent_count = 0
    for admin_id in settings.admin_ids:
        try:
            await context.bot.send_message(
                chat_id=admin_id,
                text=admin_message,
                parse_mode="Markdown",
            )
            sent_count += 1
        except Exception as e:
            logger.error(f"Failed to send message to admin {admin_id}: {e}")

    # Clear session
    await session_manager.clear_session(user.id)

    if sent_count > 0:
        await update.message.reply_text(
            "✅ Pesan Anda telah dikirim ke admin.\n"
            "Admin akan menghubungi Anda segera.\n\n"
            "Terima kasih! 🙏"
        )
    else:
        await update.message.reply_text(
            "❌ Gagal mengirim pesan ke admin.\n"
            "Silakan coba lagi nanti atau hubungi kami melalui kontak lain."
        )


async def handle_deposit_custom_amount(
    update: Update, context: ContextTypes.DEFAULT_TYPE, session: dict
):
    """Handle custom deposit amount input"""
    user = update.effective_user
    text = update.message.text.strip()
    session_manager = await get_session_manager()

    try:
        amount = int(text.replace(".", "").replace(",", ""))

        if amount < 10000:
            await update.message.reply_text(
                "❌ Jumlah deposit minimal adalah Rp 10.000.\n"
                "Silakan masukkan jumlah yang lebih besar:"
            )
            return

        if amount > 10000000:
            await update.message.reply_text(
                "❌ Jumlah deposit maksimal adalah Rp 10.000.000.\n"
                "Silakan masukkan jumlah yang lebih kecil:"
            )
            return

        # TODO: Process deposit with amount
        await update.message.reply_text(
            f"💰 Memproses deposit Rp {amount:,}...\n\n"
            "Fitur deposit sedang dalam pengembangan.\n"
            "Silakan hubungi admin untuk deposit manual."
        )

        # Clear session
        await session_manager.clear_session(user.id)

    except ValueError:
        await update.message.reply_text(
            "❌ Format tidak valid. Silakan masukkan angka saja.\nContoh: 50000"
        )


async def handle_photo_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle photo messages (for admin messages with images)
    Reference: plans.md Section 2.4
    """
    user = update.effective_user
    session_manager = await get_session_manager()
    session = await session_manager.get_session(user.id)

    # Only handle photos in admin message flow
    if not session or session.get("current_flow") != "messaging_admin":
        await update.message.reply_text(
            "📸 Untuk mengirim foto ke admin, gunakan tombol [KIRIM PESAN] terlebih dahulu."
        )
        return

    user_repo = UserRepository()
    user_data = await user_repo.get_by_id(user.id)
    user_name = user_data.get("name", user.first_name) if user_data else user.first_name

    # Get caption or use default
    caption = update.message.caption or "(Tanpa keterangan)"

    # Build admin notification
    admin_message = (
        f"💬 **Pesan Baru dari User (dengan foto)**\n\n"
        f"👤 Nama: {user_name}\n"
        f"🆔 User ID: `{user.id}`\n"
        f"📱 Username: @{user.username or 'Tidak ada'}\n\n"
        f"**Pesan:**\n{caption}"
    )

    # Get largest photo
    photo = update.message.photo[-1]

    # Send to all admins
    sent_count = 0
    for admin_id in settings.admin_ids:
        try:
            await context.bot.send_photo(
                chat_id=admin_id,
                photo=photo.file_id,
                caption=admin_message,
                parse_mode="Markdown",
            )
            sent_count += 1
        except Exception as e:
            logger.error(f"Failed to send photo message to admin {admin_id}: {e}")

    # Clear session
    await session_manager.clear_session(user.id)

    if sent_count > 0:
        await update.message.reply_text(
            "✅ Pesan dan foto Anda telah dikirim ke admin.\n"
            "Admin akan menghubungi Anda segera.\n\n"
            "Terima kasih! 🙏"
        )
    else:
        await update.message.reply_text(
            "❌ Gagal mengirim pesan ke admin.\nSilakan coba lagi nanti."
        )
