"""
Message Formatters for QuickCart Bot
Reference: plans.md Section 4 - Notifications & Bot Responses
All bot messages in English (buttons in Bahasa Indonesia)
"""

from datetime import datetime
from typing import Optional


def format_currency(amount: int) -> str:
    """Format amount as Rupiah currency"""
    return f"Rp {amount:,}"


def format_datetime(dt: datetime) -> str:
    """Format datetime in readable format"""
    return dt.strftime("%d %b %Y, %H:%M WIB")


# =============================================================================
# Main Menu & Welcome (Section 2.1)
# =============================================================================


def format_welcome_message(
    user_name: str,
    store_name: str,
    total_users: int,
    total_transactions: int,
    documentation_url: str,
) -> str:
    """
    Format welcome message for /start command
    Reference: plans.md Section 2.1
    """
    return f"""ᯓ Halo **{user_name}** 👋🏻
Selamat datang di **{store_name}**

⤷ **Total Pengguna: {total_users} Orang**
⤷ **Total Transaksi: {total_transactions}x**

Dokumentasi: [Baca Disini]({documentation_url})
Silakan tombol dibawah ini untuk melihat produk yang tersedia."""


# =============================================================================
# Product Information (Section 2.2)
# =============================================================================


def format_product_detail(
    product_id: int,
    product_name: str,
    description: str,
    price: int,
    stock: int,
    sold_count: int,
    category: str = "Uncategorized",
    discount: Optional[int] = None,
) -> str:
    """
    Format product detail message with stock and pricing info
    """
    discount_text = ""
    if discount and discount > 0:
        original_price = price + discount
        discount_text = f"~~{format_currency(original_price)}~~ 🔥 DISKON!"

    return f"""📦 **Product Details**

**ID:** {product_id}
**Name:** {product_name}
**Category:** {category}
**Price:** {format_currency(price)} {discount_text}
**Stock:** {stock} available
**Sold:** {sold_count}x

**Description:**
{description or "No description available."}

Use the buttons below to select quantity and proceed to checkout."""


def format_stock_list(products: list[dict]) -> str:
    """
    Format stock list for /stock command
    """
    if not products:
        return "❌ No products available at the moment."

    lines = ["📦 **Available Stock:**\n"]
    for product in products:
        product_id = product["id"]
        name = product["name"]
        stock = product.get("stock", 0)
        price = product.get("customer_price", 0)

        stock_emoji = "✅" if stock > 0 else "❌"
        lines.append(
            f"{stock_emoji} **{product_id}.** {name} - {format_currency(price)} ({stock} stock)"
        )

    return "\n".join(lines)


# =============================================================================
# Order & Checkout (Section 2.2)
# =============================================================================


def format_order_summary(
    product_name: str,
    quantity: int,
    price_per_unit: int,
    subtotal: int,
    fee: int,
    total: int,
) -> str:
    """
    Format order summary before payment method selection
    """
    return f"""🛒 **Order Summary**

**Product:** {product_name}
**Quantity:** {quantity}x
**Price per unit:** {format_currency(price_per_unit)}
**Subtotal:** {format_currency(subtotal)}
**Payment Fee:** {format_currency(fee)} (0.7% + Rp310)
**Total Bill:** {format_currency(total)}

Please select your payment method below."""


def format_qris_payment_message(
    invoice_id: str,
    total_bill: int,
    expiry_time: datetime,
    qr_url: str,
) -> str:
    """
    Format QRIS payment message with QR code and instructions
    """
    return f"""💳 **QRIS Payment**

**Invoice ID:** `{invoice_id}`
**Amount:** {format_currency(total_bill)}
**Expires:** {format_datetime(expiry_time)} (10 minutes)

**Payment Instructions:**
1. Open your e-wallet app (GoPay, OVO, Dana, ShopeePay, etc.)
2. Scan the QR code above
3. Confirm payment
4. Wait for confirmation (automatic)

⚠️ **Important:** Payment must be completed within 10 minutes. After expiry, the invoice will be cancelled automatically.

If you accidentally pay after expiry, the payment will be refunded (minus transaction fee)."""


def format_balance_payment_confirmation(
    product_name: str,
    quantity: int,
    total_bill: int,
    current_balance: int,
    remaining_balance: int,
) -> str:
    """
    Format balance payment confirmation message
    """
    return f"""💰 **Balance Payment Confirmation**

**Product:** {product_name}
**Quantity:** {quantity}x
**Total Bill:** {format_currency(total_bill)}

**Current Balance:** {format_currency(current_balance)}
**After Payment:** {format_currency(remaining_balance)}

Are you sure you want to proceed with this payment?"""


# =============================================================================
# Order Success/Failure (Section 4)
# =============================================================================


def format_order_success_user(
    product_name: str,
    quantity: int,
    invoice_id: str,
    product_contents: list[str],
) -> str:
    """
    Format order success message for user
    Reference: plans.md Section 4 - Order Success
    """
    content_text = "\n".join(
        [f"**{i + 1}.** `{content}`" for i, content in enumerate(product_contents)]
    )

    return f"""🎉 **Order Successful!**

📦 **Product:** {product_name}
🔢 **Quantity:** {quantity}
🧾 **Invoice:** `{invoice_id}`

**Your Products:**
{content_text}

Thank you for shopping! Please check your product details above. 😊

Need help? Use the [💬 KIRIM PESAN] button to contact admin."""


def format_order_success_admin(
    user_name: str,
    user_id: int,
    product_name: str,
    quantity: int,
    invoice_id: str,
) -> str:
    """
    Format order success notification for admin
    Reference: plans.md Section 4 - Order Success
    """
    return f"""🆕 **New Order Received!**

👤 **User:** {user_name} (ID: `{user_id}`)
📦 **Product:** {product_name}
🔢 **Quantity:** {quantity}
🧾 **Invoice:** `{invoice_id}`"""


def format_order_expired_user(invoice_id: str) -> str:
    """
    Format order expired/cancelled message for user
    Reference: plans.md Section 4 - Order Failed/Expired
    """
    return f"""⏰ **Order Cancelled or Expired**

🧾 **Invoice:** `{invoice_id}`

If you have already made payment, the funds will be returned (minus transaction fee).
Please try again or contact admin if you encounter any issues. 🙏"""


def format_order_expired_admin(invoice_id: str, user_name: str) -> str:
    """
    Format order expired notification for admin
    Reference: plans.md Section 4 - Order Failed/Expired
    """
    return f"""⚠️ **Order Expired/Unpaid**

🧾 **Invoice:** `{invoice_id}`
👤 **User:** {user_name}"""


def format_payment_expired_message() -> str:
    """
    Format payment expired message (replaces QR message after 10 minutes)
    Reference: plans.md Section 4 - QR Payment Expiry Logic
    """
    return """⌛ **Invoice Expired**

Payment is no longer accepted for this invoice.

If you have already paid, the funds will be returned (minus transaction fee).

Please create a new order/deposit if still needed."""


# =============================================================================
# Deposit (Section 2.5 & 4)
# =============================================================================


def format_deposit_success_user(amount: int, new_balance: int) -> str:
    """
    Format deposit success message for user
    Reference: plans.md Section 4 - Deposit Success
    """
    return f"""💰 **Deposit Successful!**

Your balance has been increased by {format_currency(amount)} (after fee).

**New Balance:** {format_currency(new_balance)}

Please check your balance in the [👤 AKUN] menu. 🎯"""


def format_deposit_success_admin(user_name: str, amount: int) -> str:
    """
    Format deposit success notification for admin
    Reference: plans.md Section 4 - Deposit Success
    """
    return f"""💸 **User Deposit Successful**

👤 **User:** {user_name}
💰 **Amount:** {format_currency(amount)}"""


def format_deposit_expired_user() -> str:
    """
    Format deposit expired message for user
    Reference: plans.md Section 4 - Deposit Expired
    """
    return """⌛️ **Deposit Invoice Expired**

Please create a new deposit if still needed. 🔄"""


def format_deposit_expired_admin(invoice_id: str) -> str:
    """
    Format deposit expired notification for admin
    Reference: plans.md Section 4 - Deposit Expired
    """
    return f"""🚫 **Deposit Expired**

🧾 **Invoice:** `{invoice_id}`"""


# =============================================================================
# Account Management (Section 2.3)
# =============================================================================


def format_account_info(
    user_id: int,
    name: str,
    username: Optional[str],
    email: Optional[str],
    whatsapp: Optional[str],
    balance: int,
    bank_id: str,
    member_status: str,
) -> str:
    """
    Format account information display
    Reference: plans.md Section 2.3
    """
    username_text = f"@{username}" if username else "Not set"
    email_text = email or "Not set"
    whatsapp_text = whatsapp or "Not set"

    status_emoji = {
        "customer": "👤",
        "reseller": "⭐",
        "admin": "👑",
    }.get(member_status, "👤")

    return f"""👤 **Account Information**

**User ID:** `{user_id}`
**Name:** {name}
**Username:** {username_text}
**Email:** {email_text}
**WhatsApp:** {whatsapp_text}
**Balance:** {format_currency(balance)}
**Bank ID:** `{bank_id}`
**Status:** {status_emoji} {member_status.upper()}

Use the buttons below to manage your account."""


def format_transaction_history(
    transactions: list[dict], page: int, total_pages: int
) -> str:
    """
    Format transaction history list
    """
    if not transactions:
        return "📜 **Transaction History**\n\nNo transactions yet."

    lines = [f"📜 **Transaction History** (Page {page}/{total_pages})\n"]

    for txn in transactions:
        invoice_id = txn["invoice_id"]
        created_at = format_datetime(txn["created_at"])
        total_bill = format_currency(txn["total_bill"])
        status = txn["status"]
        status_emoji = (
            "✅" if status == "paid" else "⏳" if status == "pending" else "❌"
        )

        lines.append(f"{status_emoji} `{invoice_id}` - {total_bill} ({created_at})")

    return "\n".join(lines)


# =============================================================================
# User Status Changes (Section 4)
# =============================================================================


def format_reseller_upgrade_user() -> str:
    """
    Format reseller upgrade notification for user
    Reference: plans.md Section 4 - Reseller Upgrade
    """
    return """🎊 **Congratulations!**

Your status has been upgraded to **RESELLER**.

Enjoy special pricing and additional features! 🏅"""


def format_reseller_upgrade_admin(user_name: str) -> str:
    """
    Format reseller upgrade notification for admin
    Reference: plans.md Section 4 - Reseller Upgrade
    """
    return f"""⭐️ **User Upgraded to Reseller**

👤 **User:** {user_name}"""


# =============================================================================
# Admin Commands
# =============================================================================


def format_command_error(command: str, correct_format: str, example: str) -> str:
    """
    Format command error message with correct usage
    Reference: plans.md Section 3.2 - Command Error Handling
    """
    return f"""❌ **Format salah.**

**Contoh penggunaan yang benar:**
`{example}`

**Format:** `{correct_format}`"""


def format_admin_action_success(action: str, details: str = "") -> str:
    """
    Format generic admin action success message
    """
    return (
        f"✅ **{action} berhasil!**\n\n{details}"
        if details
        else f"✅ **{action} berhasil!**"
    )


def format_admin_action_error(action: str, error: str) -> str:
    """
    Format generic admin action error message
    """
    return f"❌ **{action} gagal:**\n\n{error}"


# =============================================================================
# Public Commands Help
# =============================================================================


def format_order_guide() -> str:
    """
    Format /order command help message
    Reference: plans.md Section 3.1
    """
    return """📖 **How to Order**

**Method 1:** Click product number buttons on main menu (1-24)

**Method 2:** Click [📋 LIST PRODUK] → Browse → Select product

**Method 3:** Send product ID directly (e.g., type "5" to order product #5)

**Steps:**
1. Select product
2. Adjust quantity using +/- buttons
3. Click [💳 Lanjut ke pembayaran]
4. Choose payment method (QRIS or Balance)
5. Complete payment
6. Receive your product instantly!

Need help? Click [💬 KIRIM PESAN] to contact admin."""


def format_refund_guide() -> str:
    """
    Format /refund command usage guide
    """
    return """💰 **Refund Calculation**

**Usage:** `/refund <invoice_id>`
**Example:** `/refund TRX123456`

This command calculates the refund amount based on:
- Days used (from purchase date)
- Number of warranty claims
- Current refund formula

The refund will be credited to your account balance (minus transaction fee).

**Formula:**
refund = (purchase_price × (30 - days_used) / 30) × fee_multiplier

**Fee Multipliers:**
- 0.8 = used < 7 days
- 0.7 = used ≥ 7 days
- 0.6 = 1-2 warranty claims
- 0.5 = 3 claims
- 0.4 = >3 claims"""


def format_refund_calculation(
    invoice_id: str,
    purchase_price: int,
    days_used: int,
    warranty_claims: int,
    refund_amount: int,
    fee_multiplier: float,
) -> str:
    """
    Format refund calculation result
    """
    return f"""💰 **Refund Calculation**

**Invoice ID:** `{invoice_id}`
**Purchase Price:** {format_currency(purchase_price)}
**Days Used:** {days_used} days
**Warranty Claims:** {warranty_claims}
**Fee Multiplier:** {fee_multiplier}

**Refund Amount:** {format_currency(refund_amount)}

To request refund, please contact admin via [💬 KIRIM PESAN]."""


# =============================================================================
# User Message to Admin (Section 2.4)
# =============================================================================


def format_user_message_to_admin(
    user_id: int,
    user_name: str,
    username: Optional[str],
    message: str,
) -> str:
    """
    Format user message notification for admins
    Reference: plans.md Section 2.4
    """
    username_text = f"@{username}" if username else "No username"

    return f"""💬 **New Message from User**

👤 **From:** {user_name} ({username_text})
🆔 **User ID:** `{user_id}`

**Message:**
{message}

Reply directly to this message to respond to the user."""


def format_message_sent_confirmation() -> str:
    """
    Confirm user message has been sent to admin
    """
    return """✅ **Message Sent!**

Your message has been forwarded to all admins.
They will respond to you shortly.

Thank you for contacting us! 🙏"""


# =============================================================================
# System Messages
# =============================================================================


def format_maintenance_message() -> str:
    """
    System maintenance message
    """
    return """🔧 **System Maintenance**

The bot is currently under maintenance.
Please try again later.

We apologize for the inconvenience."""


def format_error_message(error_code: Optional[str] = None) -> str:
    """
    Generic error message
    """
    code_text = f" (Error: {error_code})" if error_code else ""
    return f"""❌ **An error occurred**{code_text}

Please try again. If the problem persists, contact admin via [💬 KIRIM PESAN]."""


def format_insufficient_stock_message(product_name: str, available: int) -> str:
    """
    Insufficient stock error message
    """
    return f"""❌ **Insufficient Stock**

**Product:** {product_name}
**Available:** {available} units

Please reduce quantity or check back later."""


def format_unauthorized_message() -> str:
    """
    Unauthorized access message
    """
    return """🔒 **Access Denied**

You don't have permission to use this command.

This command is only available to administrators."""
