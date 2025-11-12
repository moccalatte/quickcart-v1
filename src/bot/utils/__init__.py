"""
Bot Utilities for QuickCart
Message formatters and helper functions
Reference: plans.md Section 4 - Notifications & Bot Responses
"""

from .messages import (
    format_account_info,
    format_admin_action_error,
    format_admin_action_success,
    format_balance_payment_confirmation,
    format_command_error,
    format_currency,
    format_datetime,
    format_deposit_expired_admin,
    format_deposit_expired_user,
    format_deposit_success_admin,
    format_deposit_success_user,
    format_error_message,
    format_insufficient_stock_message,
    format_maintenance_message,
    format_message_sent_confirmation,
    format_order_expired_admin,
    format_order_expired_user,
    format_order_guide,
    format_order_success_admin,
    format_order_success_user,
    format_order_summary,
    format_payment_expired_message,
    format_product_detail,
    format_qris_payment_message,
    format_refund_calculation,
    format_refund_guide,
    format_reseller_upgrade_admin,
    format_reseller_upgrade_user,
    format_stock_list,
    format_transaction_history,
    format_unauthorized_message,
    format_user_message_to_admin,
    format_welcome_message,
)

__all__ = [
    # Formatting utilities
    "format_currency",
    "format_datetime",
    # Welcome & Main Menu
    "format_welcome_message",
    # Product Information
    "format_product_detail",
    "format_stock_list",
    # Order & Checkout
    "format_order_summary",
    "format_qris_payment_message",
    "format_balance_payment_confirmation",
    # Order Success/Failure
    "format_order_success_user",
    "format_order_success_admin",
    "format_order_expired_user",
    "format_order_expired_admin",
    "format_payment_expired_message",
    # Deposit
    "format_deposit_success_user",
    "format_deposit_success_admin",
    "format_deposit_expired_user",
    "format_deposit_expired_admin",
    # Account Management
    "format_account_info",
    "format_transaction_history",
    # User Status Changes
    "format_reseller_upgrade_user",
    "format_reseller_upgrade_admin",
    # Admin Commands
    "format_command_error",
    "format_admin_action_success",
    "format_admin_action_error",
    # Public Commands Help
    "format_order_guide",
    "format_refund_guide",
    "format_refund_calculation",
    # User Messages
    "format_user_message_to_admin",
    "format_message_sent_confirmation",
    # System Messages
    "format_maintenance_message",
    "format_error_message",
    "format_insufficient_stock_message",
    "format_unauthorized_message",
]
