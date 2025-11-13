"""
Public Command Handlers for QuickCart Bot
Reference: plans.md Section 3.1 - Public Commands

These handlers implement flexible navigation using Redis session state.
Users can execute any command at any time without needing to cancel previous operations.
"""

import logging

from telegram import ReplyKeyboardMarkup, Update
from telegram.ext import ContextTypes

from src.bot.keyboards.inline import get_main_menu_inline
from src.bot.keyboards.reply import get_main_menu_keyboard
from src.core.config import settings
from src.core.redis import get_cache_manager, get_session_manager
from src.repositories.product_repository import ProductRepository
from src.repositories.user_repository import UserRepository
from src.services.user_service import UserService

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /start - Welcome message and onboarding
    Reference: plans.md Section 2.1

    Flow:
    1. Send welcome sticker
    2. Check if user exists in database
    3. If new user: start onboarding (name, whatsapp, email)
    4. If existing user: show main menu
    """
    user = update.effective_user
    session_manager = await get_session_manager()

    # Clear any existing session state (flexible navigation)
    await session_manager.clear_session(user.id)

    # Send welcome sticker
    try:
        await update.message.reply_sticker(settings.telegram_welcome_sticker)
    except Exception as e:
        logger.warning(f"Failed to send welcome sticker: {e}")

    # Check if user exists
    user_repo = UserRepository()
    existing_user = await user_repo.get_by_id(user.id)

    if existing_user:
        # Existing user - show main menu
        await show_main_menu(update, context, existing_user)
    else:
        # New user - start onboarding
        await start_onboarding(update, context)


async def start_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start onboarding process for new users"""
    user = update.effective_user
    session_manager = await get_session_manager()

    # Set session state
    await session_manager.save_session(
        user.id,
        {
            "current_flow": "onboarding",
            "current_step": "name",
            "telegram_username": user.username,
        },
    )

    welcome_text = (
        f"👋 Selamat datang di **{settings.store_name}**!\n\n"
        "Mari kita atur akun Anda terlebih dahulu.\n\n"
        "Silakan masukkan **nama lengkap** Anda:\n"
        "(Atau ketik /skip untuk melewati)"
    )

    await update.message.reply_text(welcome_text, parse_mode="Markdown")


async def show_main_menu(
    update: Update, context: ContextTypes.DEFAULT_TYPE, user_data: dict = None
):
    """
    Show main menu with stats and product quick access
    Reference: plans.md Section 2.1
    """
    user = update.effective_user
    cache_manager = await get_cache_manager()

    # Get user data if not provided
    if not user_data:
        user_repo = UserRepository()
        user_data = await user_repo.get_by_id(user.id)

    # Get statistics (cached)
    total_users = await cache_manager.get_stats("total_users")
    total_transactions = await cache_manager.get_stats("total_transactions")

    if not total_users:
        user_repo = UserRepository()
        total_users = await user_repo.count_all()
        await cache_manager.set_stats("total_users", total_users, ttl=600)

    if not total_transactions:
        # TODO: Implement transaction count
        total_transactions = 0
        await cache_manager.set_stats("total_transactions", total_transactions, ttl=600)

    # Get available products for keyboard
    product_repo = ProductRepository()
    available_products = await product_repo.get_available_product_ids()

    # Build main menu message
    user_name = user_data.get("name", "Anonymous") if user_data else user.first_name

    menu_text = (
        f"ᯓ Halo **{user_name}** 👋🏻\n"
        f"Selamat datang di **{settings.store_name}**\n\n"
        f"⤷ **Total Pengguna: {total_users} Orang**\n"
        f"⤷ **Total Transaksi: {total_transactions}x**\n\n"
        f"Dokumentasi: [Baca Disini]({settings.documentation_url})\n"
        "Silakan gunakan tombol di bawah ini untuk melihat produk yang tersedia."
    )

    # Reply keyboard with product quick access
    reply_keyboard = get_main_menu_keyboard(available_products)

    # Inline keyboard for main actions
    inline_keyboard = get_main_menu_inline()

    await update.message.reply_text(
        menu_text,
        parse_mode="Markdown",
        reply_markup=reply_keyboard,
        disable_web_page_preview=True,
    )

    # Send inline menu separately
    await update.message.reply_text(
        "Pilih kategori atau lihat semua produk:",
        reply_markup=inline_keyboard,
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /help - Show help message with available commands
    Reference: plans.md Section 3.1
    """
    help_text = (
        f"🤖 **{settings.bot_name} - Panduan Penggunaan**\n\n"
        "**Perintah Tersedia:**\n"
        "/start - Mulai bot atau kembali ke menu utama\n"
        "/stock - Lihat ketersediaan stok produk\n"
        "/order - Panduan cara memesan\n"
        "/refund - Kalkulator pengembalian dana\n"
        "/help - Tampilkan pesan ini\n\n"
        "**Cara Memesan:**\n"
        "1. Pilih produk dari menu atau ketik nomor produk\n"
        "2. Atur jumlah pesanan\n"
        "3. Pilih metode pembayaran (QRIS/Saldo)\n"
        "4. Selesaikan pembayaran dalam 10 menit\n"
        "5. Produk akan dikirim otomatis setelah pembayaran\n\n"
        "**Butuh Bantuan?**\n"
        "Gunakan tombol [KIRIM PESAN] untuk menghubungi admin.\n\n"
        f"📚 Dokumentasi Lengkap: {settings.documentation_url}"
    )

    await update.message.reply_text(
        help_text, parse_mode="Markdown", disable_web_page_preview=True
    )


async def stock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /stock - Show all products with stock count
    Reference: plans.md Section 3.1
    """
    product_repo = ProductRepository()
    products = await product_repo.get_all_with_stock()

    if not products:
        await update.message.reply_text(
            "📦 Belum ada produk yang tersedia.\nSilakan cek lagi nanti!"
        )
        return

    stock_text = "📦 **Ketersediaan Stok Produk**\n\n"

    for product in products:
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


async def order_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /order - Show order guide
    Reference: plans.md Section 3.1
    """
    order_guide = (
        f"📖 **Panduan Pemesanan {settings.store_name}**\n\n"
        "**Langkah-langkah:**\n\n"
        "1️⃣ **Pilih Produk**\n"
        "   • Ketik nomor produk (contoh: 1)\n"
        "   • Atau gunakan tombol [LIST PRODUK]\n\n"
        "2️⃣ **Atur Jumlah**\n"
        "   • Gunakan tombol [-] [+] untuk mengatur\n"
        "   • Atau langsung tambah dengan [+2] [+5] [+10]\n\n"
        "3️⃣ **Pilih Pembayaran**\n"
        "   • **QRIS**: Scan QR code (berlaku 10 menit)\n"
        "   • **SALDO**: Gunakan saldo akun Anda\n\n"
        "4️⃣ **Selesaikan Pembayaran**\n"
        "   • Bayar sebelum waktu habis\n"
        "   • Produk dikirim otomatis setelah pembayaran\n\n"
        "**⚠️ Penting:**\n"
        "• Invoice QRIS berlaku 10 menit\n"
        "• Jika expired, buat pesanan baru\n"
        "• Pembayaran setelah expired akan dikembalikan (dipotong fee)\n\n"
        "**💡 Tips:**\n"
        "• Anda bisa klik tombol apa saja kapan saja\n"
        "• Tidak perlu batalkan pesanan untuk mulai yang baru\n"
        "• Sistem akan otomatis menyesuaikan dengan pilihan terakhir\n\n"
        "Butuh bantuan? Gunakan [KIRIM PESAN] untuk hubungi admin."
    )

    await update.message.reply_text(order_guide, parse_mode="Markdown")


async def refund_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /refund or /reff - Calculate refund amount
    Reference: plans.md Section 6.1

    Usage: /refund <amount> <days_since_purchase> <total_claims>
    Example: /refund 100000 3 0
    """
    if not context.args or len(context.args) < 3:
        help_text = (
            "💰 **Kalkulator Pengembalian Dana**\n\n"
            "**Format:**\n"
            "`/refund <jumlah> <hari_sejak_beli> <total_klaim>`\n\n"
            "**Contoh:**\n"
            "`/refund 100000 3 0`\n"
            "↳ Menghitung refund untuk pembelian Rp100.000 yang dibeli 3 hari lalu, belum pernah klaim.\n\n"
            "**Ketentuan Refund:**\n"
            "• < 7 hari: 80% dari total\n"
            "• ≥ 7 hari: 70% dari total\n"
            "• 1-2 klaim: 60% dari total\n"
            "• 3 klaim: 50% dari total\n"
            "• > 3 klaim: 40% dari total\n\n"
            "Catatan: Refund dipotong biaya transaksi."
        )
        await update.message.reply_text(help_text, parse_mode="Markdown")
        return

    try:
        amount = float(context.args[0])
        days_since_purchase = int(context.args[1])
        total_claims = int(context.args[2])

        # Calculate refund based on rules (plans.md Section 6.1)
        if days_since_purchase < 7:
            multiplier = settings.refund_multiplier_under_7_days
        else:
            multiplier = settings.refund_multiplier_7_plus_days

        # Adjust for claims
        if total_claims >= 1 and total_claims <= 2:
            multiplier = min(multiplier, settings.refund_multiplier_1_2_claims)
        elif total_claims == 3:
            multiplier = settings.refund_multiplier_3_claims
        elif total_claims > 3:
            multiplier = settings.refund_multiplier_over_3_claims

        refund_amount = amount * multiplier

        # Calculate fee (same as payment fee)
        fee = (amount * settings.payment_fee_percentage) + settings.payment_fee_fixed
        final_refund = refund_amount - fee

        result_text = (
            "💰 **Hasil Perhitungan Refund**\n\n"
            f"Jumlah Pembelian: Rp {amount:,.0f}\n"
            f"Hari Sejak Beli: {days_since_purchase} hari\n"
            f"Total Klaim Sebelumnya: {total_claims}x\n\n"
            f"Multiplier: {multiplier * 100}%\n"
            f"Refund Sebelum Fee: Rp {refund_amount:,.0f}\n"
            f"Biaya Transaksi: Rp {fee:,.0f}\n\n"
            f"**💵 Refund Akhir: Rp {final_refund:,.0f}**\n\n"
            "Catatan: Ini adalah estimasi. Refund aktual mungkin berbeda."
        )

        await update.message.reply_text(result_text, parse_mode="Markdown")

    except (ValueError, IndexError) as e:
        await update.message.reply_text(
            "❌ Format tidak valid. Gunakan: `/refund <jumlah> <hari> <klaim>`\n"
            "Contoh: `/refund 100000 3 0`",
            parse_mode="Markdown",
        )


async def skip_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /skip - Skip current step (mainly for onboarding)
    """
    user = update.effective_user
    session_manager = await get_session_manager()
    session = await session_manager.get_session(user.id)

    if not session or session.get("current_flow") != "onboarding":
        await update.message.reply_text("Tidak ada yang bisa dilewati saat ini.")
        return

    # Handle skip in onboarding
    current_step = session.get("current_step")

    if current_step == "name":
        session["name"] = "Anonymous"
        session["current_step"] = "whatsapp"
        await session_manager.save_session(user.id, session)
        await update.message.reply_text(
            "📱 Masukkan nomor **WhatsApp** Anda:\n(Atau ketik /skip untuk melewati)",
            parse_mode="Markdown",
        )
    elif current_step == "whatsapp":
        session["whatsapp"] = None
        session["current_step"] = "email"
        await session_manager.save_session(user.id, session)
        await update.message.reply_text(
            "📧 Masukkan **email** Anda:\n(Atau ketik /skip untuk melewati)",
            parse_mode="Markdown",
        )
    elif current_step == "email":
        session["email"] = None
        await complete_onboarding(update, context, session)
    else:
        await update.message.reply_text("Tidak ada yang bisa dilewati saat ini.")


async def complete_onboarding(
    update: Update, context: ContextTypes.DEFAULT_TYPE, session: dict
):
    """Complete onboarding and create user account"""
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
            f"Selamat datang, **{new_user['name']}**! 🎉"
        )

        # Show main menu
        await show_main_menu(update, context, new_user)

    except Exception as e:
        logger.error(f"Failed to complete onboarding for user {user.id}: {e}")
        await update.message.reply_text(
            "❌ Terjadi kesalahan saat membuat akun.\nSilakan coba lagi dengan /start"
        )
