"""
Reply Keyboards for QuickCart Bot
Reference: plans.md Section 2.1 - Main Menu
All buttons in Bahasa Indonesia
"""

from telegram import KeyboardButton, ReplyKeyboardMarkup


def get_main_menu_keyboard(
    available_product_ids: list[int] = None,
) -> ReplyKeyboardMarkup:
    """
    Generate main menu keyboard with product quick access buttons

    Layout:
    [LIST PRODUK] [STOK]
    [AKUN] [KIRIM PESAN]
    [1] [2] [3] [4] [5] [6] [7] [8]
    [9] [10] [11] [12] [13] [14] [15] [16]
    [17] [18] [19] [20] [21] [22] [23] [24]

    Args:
        available_product_ids: List of product IDs with stock (sorted ascending)

    Returns:
        ReplyKeyboardMarkup with main menu buttons
    """
    # First two rows: main actions
    keyboard = [
        [
            KeyboardButton("📋 LIST PRODUK"),
            KeyboardButton("📦 STOK"),
        ],
        [
            KeyboardButton("👤 AKUN"),
            KeyboardButton("💬 KIRIM PESAN"),
        ],
    ]

    # Product quick access buttons (up to 24 products in 3 rows of 8)
    if available_product_ids:
        # Take first 24 products
        product_ids = available_product_ids[:24]

        # Build rows of 8 buttons each
        for i in range(0, len(product_ids), 8):
            row = []
            for product_id in product_ids[i : i + 8]:
                row.append(KeyboardButton(str(product_id)))
            keyboard.append(row)
    else:
        # Default layout with placeholders (will be disabled if no products)
        keyboard.extend(
            [
                [KeyboardButton(str(i)) for i in range(1, 9)],
                [KeyboardButton(str(i)) for i in range(9, 17)],
                [KeyboardButton(str(i)) for i in range(17, 25)],
            ]
        )

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """
    Simple keyboard with cancel button
    Used during multi-step flows
    """
    keyboard = [[KeyboardButton("❌ BATALKAN")]]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def get_skip_cancel_keyboard() -> ReplyKeyboardMarkup:
    """
    Keyboard with skip and cancel options
    Used during onboarding
    """
    keyboard = [[KeyboardButton("⏭️ LEWATI"), KeyboardButton("❌ BATALKAN")]]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def remove_keyboard():
    """
    Remove reply keyboard (return to chat input only)
    """
    from telegram import ReplyKeyboardRemove

    return ReplyKeyboardRemove()
