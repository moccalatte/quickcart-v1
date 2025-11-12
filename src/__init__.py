"""
QuickCart Application Package
Version: 1.0.0
Reference: Complete documentation suite in docs/ directory (01-20)

This package contains the complete QuickCart Telegram bot implementation
for automated digital product sales with QRIS payment integration.
"""

__version__ = "1.0.0"
__author__ = "Senior Lead Engineer"
__description__ = "QuickCart - Automated Telegram Bot for Digital Product Sales"

from src.core.config import settings

__all__ = [
    "settings",
    "__version__",
    "__author__",
    "__description__",
]
