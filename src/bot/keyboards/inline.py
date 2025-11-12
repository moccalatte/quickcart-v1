"""
Inline Keyboards for QuickCart Bot
Reference: plans.md Section 2 - User Flows
All buttons in Bahasa Indonesia
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# =============================================================================
# Main Menu Inline Buttons (Section 2.1)
# =============================================================================


def get_main_menu_inline() -> InlineKeyboardMarkup:
    """
    Main menu inline buttons below welcome message
    [Kategori] [Terlaris] [Semua Produk]
    """
    keyboard = [
        [
            InlineKeyboardButton("🏷️ Kategori", callback_data="menu:categories"),
            InlineKeyboardButton("🔥 Terlaris", callback_data="menu:bestsellers"),
            InlineKeyboardButton("📦 Semua Produk", callback_data="menu:all_products"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


# =============================================================================
# Product Browsing (Section 2.2)
# =============================================================================


def get_categories_keyboard(categories: list[str]) -> InlineKeyboardMarkup:
    """
    Category selection keyboard
    Shows all available categories + back button
    """
    keyboard = []

    # Add category buttons (2 per row)
    for i in range(0, len(categories), 2):
        row = []
        for category in categories[i : i + 2]:
            callback_data = f"cat:{category}"
            row.append(
                InlineKeyboardButton(f"📁 {category}", callback_data=callback_data)
            )
        keyboard.append(row)

    # Back button
    keyboard.append([InlineKeyboardButton("🔙 Kembali", callback_data="menu:main")])

    return InlineKeyboardMarkup(keyboard)


def get_product_list_keyboard(
    products: list[dict],
    page: int = 1,
    total_pages: int = 1,
    context: str = "all",
) -> InlineKeyboardMarkup:
    """
    Product list with pagination
    Shows products with [KEMBALI] [SELANJUTNYA 1/{total_page}]

    Args:
        products: List of product dicts with id and name
        page: Current page number
        total_pages: Total number of pages
        context: 'all', 'category:NAME', or 'bestsellers'
    """
    keyboard = []

    # Product buttons (one per row)
    for product in products:
        product_id = product["id"]
        product_name = product["name"]
        stock = product.get("stock", 0)

        # Show stock indicator
        stock_emoji = "✅" if stock > 0 else "❌"
        callback_data = f"product:{product_id}"

        button_text = f"{stock_emoji} {product_id}. {product_name} ({stock})"
        keyboard.append(
            [InlineKeyboardButton(button_text, callback_data=callback_data)]
        )

    # Pagination buttons
    nav_buttons = []

    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                "⬅️ Sebelumnya", callback_data=f"page:{context}:{page - 1}"
            )
        )

    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(
                f"➡️ Selanjutnya {page}/{total_pages}",
                callback_data=f"page:{context}:{page + 1}",
            )
        )

    if nav_buttons:
        keyboard.append(nav_buttons)

    # Back button
    if context.startswith("category:"):
        keyboard.append(
            [InlineKeyboardButton("🔙 Kembali", callback_data="menu:categories")]
        )
    else:
        keyboard.append([InlineKeyboardButton("🔙 Kembali", callback_data="menu:main")])

    return InlineKeyboardMarkup(keyboard)


def get_bestsellers_keyboard(products: list[dict]) -> InlineKeyboardMarkup:
    """
    Bestsellers list with Top Buyers button
    """
    keyboard = []

    # Top products
    for idx, product in enumerate(products, 1):
        product_id = product["id"]
        product_name = product["name"]
        sold = product.get("sold_count", 0)

        button_text = f"🏆 {idx}. {product_name} ({sold} terjual)"
        keyboard.append(
            [InlineKeyboardButton(button_text, callback_data=f"product:{product_id}")]
        )

    # Navigation buttons
    keyboard.append(
        [
            InlineKeyboardButton("🔙 Kembali", callback_data="menu:main"),
            InlineKeyboardButton("👥 Top Buyers", callback_data="stats:top_buyers"),
        ]
    )

    return InlineKeyboardMarkup(keyboard)


# =============================================================================
# Product Detail & Order (Section 2.2)
# =============================================================================


def get_product_detail_keyboard(quantity: int = 1) -> InlineKeyboardMarkup:
    """
    Product detail with quantity adjustment
    [-] [Qty: X] [+] [+2] [+5] [+10]
    [Lanjut ke pembayaran] [Batalkan]
    """
    keyboard = [
        [
            InlineKeyboardButton("➖", callback_data=f"qty:decrease:{quantity}"),
            InlineKeyboardButton(f"🔢 {quantity}", callback_data="qty:show"),
            InlineKeyboardButton("➕", callback_data=f"qty:increase:{quantity}"),
        ],
        [
            InlineKeyboardButton("+2", callback_data=f"qty:add:2:{quantity}"),
            InlineKeyboardButton("+5", callback_data=f"qty:add:5:{quantity}"),
            InlineKeyboardButton("+10", callback_data=f"qty:add:10:{quantity}"),
        ],
        [
            InlineKeyboardButton(
                "💳 Lanjut ke pembayaran",
                callback_data=f"checkout:{quantity}",
            )
        ],
        [InlineKeyboardButton("❌ Batalkan", callback_data="order:cancel")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_payment_method_keyboard(
    total_bill: int, user_balance: int
) -> InlineKeyboardMarkup:
    """
    Payment method selection
    [QRIS] [SALDO] [KEMBALI] [BATALKAN]
    """
    keyboard = []

    # QRIS always available
    keyboard.append([InlineKeyboardButton("🔳 QRIS", callback_data="pay:qris")])

    # SALDO only if sufficient balance
    if user_balance >= total_bill:
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"💰 SALDO (Rp {user_balance:,})", callback_data="pay:balance"
                )
            ]
        )
    else:
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"💰 SALDO (Tidak Cukup: Rp {user_balance:,})",
                    callback_data="pay:balance_insufficient",
                )
            ]
        )

    # Navigation
    keyboard.append(
        [
            InlineKeyboardButton("🔙 Kembali", callback_data="order:back_to_product"),
            InlineKeyboardButton("❌ Batalkan", callback_data="order:cancel"),
        ]
    )

    return InlineKeyboardMarkup(keyboard)


def get_qris_payment_keyboard(
    invoice_id: str, checkout_url: str
) -> InlineKeyboardMarkup:
    """
    QRIS payment screen buttons
    [Checkout Page] [Status Pembayaran] [Batalkan]
    """
    keyboard = [
        [InlineKeyboardButton("🌐 Checkout Page", url=checkout_url)],
        [
            InlineKeyboardButton(
                "🔍 Status Pembayaran", callback_data=f"payment:status:{invoice_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "❌ Batalkan", callback_data=f"payment:cancel:{invoice_id}"
            )
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_payment_expired_keyboard() -> InlineKeyboardMarkup:
    """
    Expired payment screen - only back button
    """
    keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="menu:main")]]
    return InlineKeyboardMarkup(keyboard)


# =============================================================================
# Account Management (Section 2.3)
# =============================================================================


def get_account_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Account management menu
    [Ubah Nama] [Ubah Email] [Ubah Whatsapp]
    [Riwayat Transaksi] [Deposit]
    [Kembali]
    """
    keyboard = [
        [
            InlineKeyboardButton("✏️ Ubah Nama", callback_data="account:edit:name"),
            InlineKeyboardButton("📧 Ubah Email", callback_data="account:edit:email"),
        ],
        [
            InlineKeyboardButton(
                "📱 Ubah WhatsApp", callback_data="account:edit:whatsapp"
            ),
        ],
        [
            InlineKeyboardButton(
                "📜 Riwayat Transaksi", callback_data="account:history:1"
            ),
        ],
        [
            InlineKeyboardButton("💰 Deposit", callback_data="deposit:start"),
        ],
        [
            InlineKeyboardButton("🔙 Kembali", callback_data="menu:main"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_transaction_history_keyboard(
    page: int = 1, total_pages: int = 1
) -> InlineKeyboardMarkup:
    """
    Transaction history pagination
    """
    keyboard = []

    # Navigation buttons
    nav_buttons = []
    if page > 1:
        nav_buttons.append(
            InlineKeyboardButton(
                "⬅️ Sebelumnya", callback_data=f"account:history:{page - 1}"
            )
        )
    if page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(
                f"➡️ Selanjutnya {page}/{total_pages}",
                callback_data=f"account:history:{page + 1}",
            )
        )

    if nav_buttons:
        keyboard.append(nav_buttons)

    # Back button
    keyboard.append([InlineKeyboardButton("🔙 Kembali", callback_data="account:menu")])

    return InlineKeyboardMarkup(keyboard)


# =============================================================================
# Deposit Flow (Section 2.5)
# =============================================================================


def get_deposit_amount_keyboard() -> InlineKeyboardMarkup:
    """
    Quick deposit amount selection
    """
    keyboard = [
        [
            InlineKeyboardButton("Rp 10.000", callback_data="deposit:amount:10000"),
            InlineKeyboardButton("Rp 25.000", callback_data="deposit:amount:25000"),
        ],
        [
            InlineKeyboardButton("Rp 50.000", callback_data="deposit:amount:50000"),
            InlineKeyboardButton("Rp 100.000", callback_data="deposit:amount:100000"),
        ],
        [
            InlineKeyboardButton("Rp 250.000", callback_data="deposit:amount:250000"),
            InlineKeyboardButton("Rp 500.000", callback_data="deposit:amount:500000"),
        ],
        [
            InlineKeyboardButton("💭 Jumlah Lain", callback_data="deposit:custom"),
        ],
        [
            InlineKeyboardButton("🔙 Kembali", callback_data="account:menu"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_deposit_qris_keyboard(
    invoice_id: str, checkout_url: str
) -> InlineKeyboardMarkup:
    """
    Deposit QRIS payment screen
    Same as order QRIS but for deposit
    """
    keyboard = [
        [InlineKeyboardButton("🌐 Checkout Page", url=checkout_url)],
        [
            InlineKeyboardButton(
                "🔍 Status Pembayaran", callback_data=f"deposit:status:{invoice_id}"
            )
        ],
        [
            InlineKeyboardButton(
                "❌ Batalkan", callback_data=f"deposit:cancel:{invoice_id}"
            )
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


# =============================================================================
# Admin Utilities
# =============================================================================


def get_admin_confirmation_keyboard(
    action: str, target_id: str
) -> InlineKeyboardMarkup:
    """
    Generic confirmation keyboard for admin actions
    """
    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Konfirmasi", callback_data=f"admin:confirm:{action}:{target_id}"
            ),
            InlineKeyboardButton("❌ Batalkan", callback_data="admin:cancel"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_broadcast_confirmation_keyboard() -> InlineKeyboardMarkup:
    """
    Broadcast confirmation
    """
    keyboard = [
        [
            InlineKeyboardButton(
                "✅ Kirim Broadcast", callback_data="broadcast:confirm"
            ),
            InlineKeyboardButton("❌ Batalkan", callback_data="broadcast:cancel"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


# =============================================================================
# Generic Utilities
# =============================================================================


def get_back_to_main_keyboard() -> InlineKeyboardMarkup:
    """
    Simple back to main menu button
    """
    keyboard = [[InlineKeyboardButton("🔙 Kembali ke Menu", callback_data="menu:main")]]
    return InlineKeyboardMarkup(keyboard)


def get_confirm_cancel_keyboard(confirm_data: str) -> InlineKeyboardMarkup:
    """
    Generic confirm/cancel keyboard
    """
    keyboard = [
        [
            InlineKeyboardButton("✅ Konfirmasi", callback_data=confirm_data),
            InlineKeyboardButton("❌ Batalkan", callback_data="action:cancel"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)
