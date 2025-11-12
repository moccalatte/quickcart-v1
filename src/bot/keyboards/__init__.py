"""
Keyboard Utilities for QuickCart Bot
All keyboard builders for reply and inline keyboards
Reference: plans.md Section 2 - User Flows
"""

from .inline import (
    get_account_menu_keyboard,
    get_admin_confirmation_keyboard,
    get_back_to_main_keyboard,
    get_bestsellers_keyboard,
    get_broadcast_confirmation_keyboard,
    get_categories_keyboard,
    get_confirm_cancel_keyboard,
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
from .reply import (
    get_cancel_keyboard,
    get_main_menu_keyboard,
    get_skip_cancel_keyboard,
    remove_keyboard,
)

__all__ = [
    # Reply Keyboards
    "get_main_menu_keyboard",
    "get_cancel_keyboard",
    "get_skip_cancel_keyboard",
    "remove_keyboard",
    # Inline Keyboards - Main Menu
    "get_main_menu_inline",
    # Inline Keyboards - Product Browsing
    "get_categories_keyboard",
    "get_product_list_keyboard",
    "get_bestsellers_keyboard",
    "get_product_detail_keyboard",
    # Inline Keyboards - Payment
    "get_payment_method_keyboard",
    "get_qris_payment_keyboard",
    "get_payment_expired_keyboard",
    # Inline Keyboards - Account
    "get_account_menu_keyboard",
    "get_transaction_history_keyboard",
    # Inline Keyboards - Deposit
    "get_deposit_amount_keyboard",
    "get_deposit_qris_keyboard",
    # Inline Keyboards - Admin
    "get_admin_confirmation_keyboard",
    "get_broadcast_confirmation_keyboard",
    # Inline Keyboards - Generic
    "get_back_to_main_keyboard",
    "get_confirm_cancel_keyboard",
]
