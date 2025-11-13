"""
Callback Query Handlers for QuickCart Bot
Reference: plans.md Section 2 - All inline button callbacks

Implements flexible navigation:
- Users can click any button at any time
- Session state is updated atomically
- No need to cancel before switching flows
"""

import logging
from decimal import Decimal

from telegram import Update
from telegram.ext import ContextTypes

from src.bot.keyboards.inline import (
    get_account_menu_keyboard,
    get_back_to_main_keyboard,
    get_bestsellers_keyboard,
    get_categories_keyboard,
    get_deposit_amount_keyboard,
    get_deposit_qris_keyboard,
    get_main_menu_inline,
    get_payment_expired_keyboard,
    get_payment_method_keyboard,
    get_product_detail_keyboard,
    get_product_list_keyboard,
    get_qris_payment_keyboard,
    get_transaction_history_keyboard,
)
from src.core.config import settings
from src.core.redis import get_session_manager
from src.repositories.order_repository import OrderRepository
from src.repositories.product_repository import ProductRepository
from src.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Main callback query router
    Routes callbacks based on prefix to appropriate handler
    """
    query = update.callback_query
    await query.answer()

    callback_data = query.data
    user = update.effective_user

    logger.info(f"Callback from user {user.id}: {callback_data}")

    try:
        # Route based on callback prefix
        if callback_data.startswith("menu:"):
            await handle_menu_callback(update, context)
        elif callback_data.startswith("cat:"):
            await handle_category_callback(update, context)
        elif callback_data.startswith("product:"):
            await handle_product_callback(update, context)
        elif callback_data.startswith("qty:"):
            await handle_quantity_callback(update, context)
        elif callback_data.startswith("checkout:"):
            await handle_checkout_callback(update, context)
        elif callback_data.startswith("pay:"):
            await handle_payment_callback(update, context)
        elif callback_data.startswith("payment:"):
            await handle_payment_status_callback(update, context)
        elif callback_data.startswith("account:"):
            await handle_account_callback(update, context)
        elif callback_data.startswith("deposit:"):
            await handle_deposit_callback(update, context)
        elif callback_data.startswith("page:"):
            await handle_pagination_callback(update, context)
        elif callback_data.startswith("stats:"):
            await handle_stats_callback(update, context)
        elif callback_data.startswith("order:"):
            await handle_order_action_callback(update, context)
        elif callback_data.startswith("action:"):
            await handle_generic_action_callback(update, context)
        else:
            await query.edit_message_text("⚠️ Tombol tidak dikenali. Silakan coba lagi.")

    except Exception as e:
        logger.error(f"Callback handler error: {e}", exc_info=True)
        await query.answer("❌ Terjadi kesalahan. Silakan coba lagi.", show_alert=True)


async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle main menu navigation callbacks"""
    query = update.callback_query
    user = update.effective_user
    action = query.data.split(":")[1]

    session_manager = await get_session_manager()
    product_repo = ProductRepository()

    if action == "main":
        # Return to main menu
        await session_manager.clear_session(user.id)
        await query.edit_message_text(
            "🏠 Kembali ke menu utama.\nSilakan gunakan tombol di bawah untuk navigasi.",
            reply_markup=get_main_menu_inline(),
        )

    elif action == "categories":
        # Show all categories
        categories = await product_repo.get_all_categories()

        if not categories:
            await query.edit_message_text(
                "📁 Belum ada kategori produk tersedia.",
                reply_markup=get_back_to_main_keyboard(),
            )
            return

        await session_manager.save_session(
            user.id, {"current_flow": "browsing", "current_step": "categories"}
        )

        await query.edit_message_text(
            "📁 **Pilih Kategori Produk:**\n\nKlik kategori untuk melihat produk di dalamnya.",
            parse_mode="Markdown",
            reply_markup=get_categories_keyboard(categories),
        )

    elif action == "bestsellers":
        # Show best selling products
        bestsellers = await product_repo.get_bestsellers(limit=10)

        if not bestsellers:
            await query.edit_message_text(
                "🔥 Belum ada produk terlaris.",
                reply_markup=get_back_to_main_keyboard(),
            )
            return

        await session_manager.save_session(
            user.id, {"current_flow": "browsing", "current_step": "bestsellers"}
        )

        text = "🔥 **Produk Terlaris**\n\nProduk paling laris di toko kami:\n\n"
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=get_bestsellers_keyboard(bestsellers),
        )

    elif action == "all_products":
        # Show all products with pagination
        page = 1
        products, total_pages = await product_repo.get_paginated(page=page, per_page=10)

        if not products:
            await query.edit_message_text(
                "📦 Belum ada produk tersedia.",
                reply_markup=get_back_to_main_keyboard(),
            )
            return

        await session_manager.save_session(
            user.id,
            {"current_flow": "browsing", "current_step": "all_products", "page": page},
        )

        await query.edit_message_text(
            "📦 **Semua Produk**\n\nPilih produk untuk melihat detail:",
            parse_mode="Markdown",
            reply_markup=get_product_list_keyboard(products, page, total_pages, "all"),
        )


async def handle_category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle category selection"""
    query = update.callback_query
    user = update.effective_user
    category = ":".join(query.data.split(":")[1:])  # Handle categories with colons

    session_manager = await get_session_manager()
    product_repo = ProductRepository()

    # Get products in category
    page = 1
    products, total_pages = await product_repo.get_by_category_paginated(
        category, page=page, per_page=10
    )

    if not products:
        await query.edit_message_text(
            f"📁 Kategori **{category}** belum memiliki produk.",
            parse_mode="Markdown",
            reply_markup=get_categories_keyboard(
                await product_repo.get_all_categories()
            ),
        )
        return

    await session_manager.save_session(
        user.id,
        {
            "current_flow": "browsing",
            "current_step": "category_products",
            "category": category,
            "page": page,
        },
    )

    await query.edit_message_text(
        f"📁 **Kategori: {category}**\n\nPilih produk untuk melihat detail:",
        parse_mode="Markdown",
        reply_markup=get_product_list_keyboard(
            products, page, total_pages, f"category:{category}"
        ),
    )


async def handle_product_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle product selection - show product details"""
    query = update.callback_query
    user = update.effective_user
    product_id = int(query.data.split(":")[1])

    session_manager = await get_session_manager()
    product_repo = ProductRepository()
    user_repo = UserRepository()

    # Get product details
    product = await product_repo.get_by_id(product_id)

    if not product:
        await query.answer("❌ Produk tidak ditemukan.", show_alert=True)
        return

    # Check stock
    stock_count = await product_repo.get_stock_count(product_id)

    if stock_count == 0:
        await query.answer("❌ Produk habis stok.", show_alert=True)
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

    # Save session with product selection
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

    await query.edit_message_text(
        product_text,
        parse_mode="Markdown",
        reply_markup=get_product_detail_keyboard(quantity=1),
    )


async def handle_quantity_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle quantity adjustment buttons"""
    query = update.callback_query
    user = update.effective_user
    parts = query.data.split(":")

    session_manager = await get_session_manager()
    session = await session_manager.get_session(user.id)

    if not session or session.get("current_flow") != "ordering":
        await query.answer("⚠️ Silakan pilih produk terlebih dahulu.", show_alert=True)
        return

    action = parts[1]
    current_qty = session.get("quantity", 1)
    product_id = session.get("product_id")

    # Get stock limit
    product_repo = ProductRepository()
    stock_count = await product_repo.get_stock_count(product_id)

    new_qty = current_qty

    if action == "decrease":
        new_qty = max(1, current_qty - 1)
    elif action == "increase":
        new_qty = min(stock_count, current_qty + 1)
    elif action == "add":
        increment = int(parts[2])
        new_qty = min(stock_count, current_qty + increment)
    elif action == "show":
        await query.answer(f"Jumlah saat ini: {current_qty}")
        return

    if new_qty == current_qty:
        if new_qty >= stock_count:
            await query.answer(
                "⚠️ Stok tidak mencukupi untuk jumlah lebih banyak.", show_alert=True
            )
        else:
            await query.answer("Jumlah minimal adalah 1.")
        return

    # Update session
    session["quantity"] = new_qty
    await session_manager.save_session(user.id, session)

    # Update keyboard
    try:
        await query.edit_message_reply_markup(
            reply_markup=get_product_detail_keyboard(quantity=new_qty)
        )
        await query.answer(f"Jumlah: {new_qty}")
    except Exception as e:
        logger.warning(f"Failed to update quantity keyboard: {e}")
        await query.answer(f"Jumlah diubah menjadi {new_qty}")


async def handle_checkout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle checkout - show payment method selection"""
    query = update.callback_query
    user = update.effective_user

    session_manager = await get_session_manager()
    session = await session_manager.get_session(user.id)

    if not session or session.get("current_flow") != "ordering":
        await query.answer("⚠️ Silakan pilih produk terlebih dahulu.", show_alert=True)
        return

    product_id = session.get("product_id")
    quantity = session.get("quantity", 1)
    unit_price = Decimal(str(session.get("price")))

    # Get product and user info
    product_repo = ProductRepository()
    user_repo = UserRepository()

    product = await product_repo.get_by_id(product_id)
    user_data = await user_repo.get_by_id(user.id)

    # Calculate totals
    subtotal = unit_price * quantity
    payment_fee = (subtotal * Decimal(str(settings.payment_fee_percentage))) + Decimal(
        str(settings.payment_fee_fixed)
    )
    total_bill = subtotal + payment_fee

    user_balance = (
        Decimal(str(user_data.get("account_balance", 0))) if user_data else Decimal(0)
    )

    # Update session
    session["current_step"] = "payment_selection"
    session["subtotal"] = float(subtotal)
    session["payment_fee"] = float(payment_fee)
    session["total_bill"] = float(total_bill)
    await session_manager.save_session(user.id, session)

    # Build order summary
    summary_text = (
        "🧾 **Ringkasan Pesanan**\n\n"
        f"📦 Produk: {product['name']}\n"
        f"🔢 Jumlah: {quantity}x\n"
        f"💵 Harga Satuan: Rp {unit_price:,.0f}\n"
        f"➖➖➖➖➖➖➖➖➖\n"
        f"Subtotal: Rp {subtotal:,.0f}\n"
        f"Biaya Transaksi: Rp {payment_fee:,.0f}\n"
        f"➖➖➖➖➖➖➖➖➖\n"
        f"**💰 Total: Rp {total_bill:,.0f}**\n\n"
        f"Saldo Anda: Rp {user_balance:,.0f}\n\n"
        "Pilih metode pembayaran:"
    )

    await query.edit_message_text(
        summary_text,
        parse_mode="Markdown",
        reply_markup=get_payment_method_keyboard(int(total_bill), int(user_balance)),
    )


async def handle_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle payment method selection"""
    query = update.callback_query
    user = update.effective_user
    payment_method = query.data.split(":")[1]

    session_manager = await get_session_manager()
    session = await session_manager.get_session(user.id)

    if not session or session.get("current_flow") != "ordering":
        await query.answer(
            "⚠️ Sesi tidak valid. Silakan mulai pesanan baru.", show_alert=True
        )
        return

    if payment_method == "qris":
        await handle_qris_payment(update, context, session)
    elif payment_method == "balance":
        await handle_balance_payment(update, context, session)
    elif payment_method == "balance_insufficient":
        await query.answer(
            "❌ Saldo tidak mencukupi. Silakan deposit atau gunakan QRIS.",
            show_alert=True,
        )


async def handle_qris_payment(
    update: Update, context: ContextTypes.DEFAULT_TYPE, session: dict
):
    """Handle QRIS payment flow"""
    query = update.callback_query
    user = update.effective_user

    # TODO: Integrate with Pakasir API to create payment
    # For now, show placeholder
    await query.edit_message_text(
        "🔳 **Pembayaran QRIS**\n\n"
        "Fitur pembayaran QRIS sedang dalam pengembangan.\n"
        "Silakan gunakan metode pembayaran lain atau hubungi admin.\n\n"
        "Implementasi akan mencakup:\n"
        "• QR code dari Pakasir\n"
        "• Invoice ID unik\n"
        "• Timer 10 menit\n"
        "• Auto-delivery setelah pembayaran",
        reply_markup=get_back_to_main_keyboard(),
    )


async def handle_balance_payment(
    update: Update, context: ContextTypes.DEFAULT_TYPE, session: dict
):
    """Handle account balance payment flow"""
    query = update.callback_query
    user = update.effective_user

    # TODO: Implement balance payment
    # - Verify user has sufficient balance
    # - Create order in database
    # - Deduct balance
    # - Deliver product
    # - Send confirmation

    await query.edit_message_text(
        "💰 **Pembayaran Saldo**\n\n"
        "Fitur pembayaran saldo sedang dalam pengembangan.\n\n"
        "Implementasi akan mencakup:\n"
        "• Konfirmasi pembayaran\n"
        "• Pengurangan saldo otomatis\n"
        "• Pengiriman produk instant\n"
        "• Riwayat transaksi",
        reply_markup=get_back_to_main_keyboard(),
    )


async def handle_payment_status_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handle payment status check"""
    query = update.callback_query
    parts = query.data.split(":")
    action = parts[1]
    invoice_id = parts[2] if len(parts) > 2 else None

    if action == "status":
        # TODO: Check payment status from Pakasir
        await query.answer("🔍 Memeriksa status pembayaran...", show_alert=True)
    elif action == "cancel":
        # TODO: Cancel payment/order
        await query.answer("Pembayaran dibatalkan.", show_alert=True)
        await query.edit_message_text(
            "❌ Pembayaran dibatalkan.\n\nSilakan buat pesanan baru jika masih diperlukan.",
            reply_markup=get_back_to_main_keyboard(),
        )


async def handle_account_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle account management callbacks"""
    query = update.callback_query
    user = update.effective_user
    action = query.data.split(":")[1]

    session_manager = await get_session_manager()
    user_repo = UserRepository()

    if action == "menu":
        # Show account menu
        user_data = await user_repo.get_by_id(user.id)

        if not user_data:
            await query.answer("❌ Data pengguna tidak ditemukan.", show_alert=True)
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

        await query.edit_message_text(
            account_text,
            parse_mode="Markdown",
            reply_markup=get_account_menu_keyboard(),
        )

    elif action == "edit":
        field = query.data.split(":")[2]
        # TODO: Implement account editing
        await query.answer(
            f"Fitur ubah {field} sedang dalam pengembangan.", show_alert=True
        )

    elif action == "history":
        page = int(query.data.split(":")[2]) if len(query.data.split(":")) > 2 else 1
        # TODO: Implement transaction history
        await query.edit_message_text(
            f"📜 **Riwayat Transaksi** (Halaman {page})\n\n"
            "Fitur riwayat transaksi sedang dalam pengembangan.\n\n"
            "Akan menampilkan:\n"
            "• Semua transaksi Anda\n"
            "• Status pembayaran\n"
            "• Detail produk\n"
            "• Tanggal dan waktu",
            parse_mode="Markdown",
            reply_markup=get_transaction_history_keyboard(page, 1),
        )


async def handle_deposit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle deposit callbacks"""
    query = update.callback_query
    user = update.effective_user
    action = query.data.split(":")[1]

    session_manager = await get_session_manager()

    if action == "start":
        # Show deposit amount selection
        await session_manager.save_session(
            user.id, {"current_flow": "deposit", "current_step": "amount_selection"}
        )

        await query.edit_message_text(
            "💰 **Deposit Saldo**\n\n"
            "Pilih jumlah deposit atau masukkan jumlah custom:\n\n"
            "Biaya transaksi akan diterapkan sesuai metode pembayaran.",
            parse_mode="Markdown",
            reply_markup=get_deposit_amount_keyboard(),
        )

    elif action == "amount":
        amount = int(query.data.split(":")[2])
        # TODO: Process deposit with Pakasir
        await query.answer(f"Memproses deposit Rp {amount:,}...", show_alert=True)

    elif action == "custom":
        # TODO: Prompt for custom amount
        await query.answer(
            "Fitur custom amount sedang dalam pengembangan.", show_alert=True
        )


async def handle_pagination_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handle pagination for product lists"""
    query = update.callback_query
    user = update.effective_user
    parts = query.data.split(":")

    context_type = parts[1]
    page = int(parts[2])

    product_repo = ProductRepository()

    if context_type == "all":
        products, total_pages = await product_repo.get_paginated(page=page, per_page=10)
        await query.edit_message_reply_markup(
            reply_markup=get_product_list_keyboard(products, page, total_pages, "all")
        )
    elif context_type.startswith("category"):
        category = ":".join(parts[1:-1]).replace("category:", "")
        products, total_pages = await product_repo.get_by_category_paginated(
            category, page=page, per_page=10
        )
        await query.edit_message_reply_markup(
            reply_markup=get_product_list_keyboard(
                products, page, total_pages, f"category:{category}"
            )
        )


async def handle_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle statistics callbacks"""
    query = update.callback_query
    action = query.data.split(":")[1]

    if action == "top_buyers":
        # TODO: Implement top buyers leaderboard
        await query.edit_message_text(
            "👥 **Top Buyers**\n\n"
            "Fitur leaderboard pembeli sedang dalam pengembangan.\n\n"
            "Akan menampilkan:\n"
            "• Top 10 pembeli terbanyak\n"
            "• Total transaksi\n"
            "• Badge spesial",
            parse_mode="Markdown",
            reply_markup=get_back_to_main_keyboard(),
        )


async def handle_order_action_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handle order-related actions"""
    query = update.callback_query
    user = update.effective_user
    action = query.data.split(":")[1]

    session_manager = await get_session_manager()

    if action == "cancel":
        # Clear session and go back to main menu
        await session_manager.clear_session(user.id)
        await query.edit_message_text(
            "❌ Pesanan dibatalkan.\n\nSilakan gunakan menu utama untuk memulai pesanan baru.",
            reply_markup=get_main_menu_inline(),
        )
    elif action == "back_to_product":
        # Go back to product detail
        session = await session_manager.get_session(user.id)
        if session and session.get("product_id"):
            # Re-trigger product callback
            query.data = f"product:{session['product_id']}"
            await handle_product_callback(update, context)
        else:
            await query.answer("Sesi tidak valid.", show_alert=True)


async def handle_generic_action_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """Handle generic action callbacks"""
    query = update.callback_query
    action = query.data.split(":")[1]

    session_manager = await get_session_manager()

    if action == "cancel":
        # Generic cancel - clear session
        await session_manager.clear_session(update.effective_user.id)
        await query.edit_message_text(
            "❌ Aksi dibatalkan.",
            reply_markup=get_back_to_main_keyboard(),
        )
