# src/handlers/public/start.py
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /start command."""
    user = update.effective_user

    # Send welcome sticker
    await context.bot.send_sticker(chat_id=update.effective_chat.id, sticker="CAACAgIAAxkBAAIDbWkLZHuqPRCqCqmL9flozT9YJdWOAAIZUAAC4KOCB7lIn3OKexieNgQ")

    # Main menu text
    main_menu_text = (
        f"ᯓ Halo **{user.first_name}** 👋🏻\n"
        "Selamat datang di **QuickCart**\n\n"
        "⤷ **Total Pengguna: 100 Orang**\n"
        "⤷ **Total Transaksi: 500x**\n\n"
        "Dokumentasi: [Baca Disini](https://notion.so/blabla)\n"
        "Silakan tombol dibawah ini untuk melihat produk yang tersedia."
    )

    # Inline keyboard buttons
    inline_keyboard = [
        [
            InlineKeyboardButton("Kategori", callback_data="menu:kategori"),
            InlineKeyboardButton("Terlaris", callback_data="menu:terlaris"),
            InlineKeyboardButton("Semua Produk", callback_data="menu:semua_produk"),
        ]
    ]
    inline_markup = InlineKeyboardMarkup(inline_keyboard)

    # Reply keyboard buttons
    reply_keyboard = [
        ["LIST PRODUK", "STOK"],
        ["AKUN", "KIRIM PESAN"],
    ]
    reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)

    await update.message.reply_text(
        main_menu_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

    await update.message.reply_text(
        "Pilih salah satu opsi:",
        reply_markup=inline_markup
    )
