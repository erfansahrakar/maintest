"""
Handler modules for the Telegram bot
این فایل پوشه handlers را به یک Python package تبدیل می‌کند
"""

# Import کردن ماژول‌های handler برای دسترسی راحت‌تر
from . import admin
from . import user  
from . import order
from . import wallet_system
from . import admin_invoice

__all__ = [
    'admin',
    'user',
    'order', 
    'wallet_system',
    'admin_invoice'
]

