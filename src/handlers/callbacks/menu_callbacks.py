# src/handlers/callbacks/menu_callbacks.py
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

async def handle_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles menu callbacks."""
    query = update.callback_query
    await query.answer()

    # Data callback is in format "menu:action"
    action = query.data.split(":")[1]

    if action == "kategori":
        await show_categories(update, context)
    elif action == "terlaris":
        await show_bestsellers(update, context)
    elif action == "semua_produk":
        await show_all_products(update, context)

async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays product categories."""
    query = update.callback_query
    keyboard = [
        [InlineKeyboardButton("Tanpa Kategori", callback_data="category:uncategorized")],
        [InlineKeyboardButton("Kategori 1", callback_data="category:1")],
        [InlineKeyboardButton("Kategori 2", callback_data="category:2")],
        [InlineKeyboardButton("Kembali", callback_data="menu:kembali")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Please select a category:", reply_markup=reply_markup)

async def show_bestsellers(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays best-selling products."""
    query = update.callback_query
    keyboard = [
        [InlineKeyboardButton("Kembali", callback_data="menu:kembali")],
        [InlineKeyboardButton("Top Buyers", callback_data="menu:top_buyers")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Here are the best-selling products:", reply_markup=reply_markup)

async def show_all_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays all products."""
    query = update.callback_query
    keyboard = [
        [InlineKeyboardButton("KEMBALI", callback_data="menu:kembali")],
        [InlineKeyboardButton("SELANJUTNYA 1/5", callback_data="page:2")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text("Here are all the products:", reply_markup=reply_markup)
