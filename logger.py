"""
سیستم Logging حرفه‌ای برای ربات
🔴 مرحله 3: Logging
✅ ثبت رویدادها، خطاها، و عملیات مهم
"""
import logging
import os
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime
from functools import wraps
from typing import Optional


# ==================== تنظیمات ====================

LOG_FOLDER = "logs"
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# سایز حداکثر هر فایل لاگ (10 MB)
MAX_LOG_SIZE = 10 * 1024 * 1024
# تعداد backup فایل‌ها
BACKUP_COUNT = 5


# ==================== ایجاد پوشه لاگ ====================

def setup_log_folder():
    """ایجاد پوشه logs اگر وجود نداشته باشد"""
    if not os.path.exists(LOG_FOLDER):
        os.makedirs(LOG_FOLDER)
        print(f"✅ پوشه {LOG_FOLDER} ایجاد شد")


# ==================== تنظیم Logger اصلی ====================

def setup_logger(
    name: str = "bot",
    level: int = logging.INFO,
    log_to_console: bool = True,
    log_to_file: bool = True
) -> logging.Logger:
    """
    ایجاد و تنظیم logger
    
    Args:
        name: نام logger
        level: سطح لاگ (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_console: لاگ در کنسول
        log_to_file: لاگ در فایل
    
    Returns:
        logger تنظیم شده
    """
    setup_log_folder()
    
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # جلوگیری از duplicate handlers
    if logger.handlers:
        return logger
    
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    
    # ==================== Console Handler ====================
    if log_to_console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    # ==================== File Handler - All Logs ====================
    if log_to_file:
        # لاگ همه چیز (با rotation بر اساس سایز)
        all_logs_file = os.path.join(LOG_FOLDER, "bot_all.log")
        all_handler = RotatingFileHandler(
            all_logs_file,
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT,
            encoding='utf-8'
        )
        all_handler.setLevel(logging.DEBUG)
        all_handler.setFormatter(formatter)
        logger.addHandler(all_handler)
        
        # ==================== File Handler - Errors Only ====================
        # فایل جداگانه برای خطاها
        error_logs_file = os.path.join(LOG_FOLDER, "bot_errors.log")
        error_handler = RotatingFileHandler(
            error_logs_file,
            maxBytes=MAX_LOG_SIZE,
            backupCount=BACKUP_COUNT,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        logger.addHandler(error_handler)
        
        # ==================== File Handler - Daily Rotation ====================
        # لاگ روزانه (یه فایل برای هر روز)
        daily_logs_file = os.path.join(LOG_FOLDER, "bot_daily.log")
        daily_handler = TimedRotatingFileHandler(
            daily_logs_file,
            when='midnight',
            interval=1,
            backupCount=30,  # نگه‌داری 30 روز
            encoding='utf-8'
        )
        daily_handler.setLevel(logging.INFO)
        daily_handler.setFormatter(formatter)
        daily_handler.suffix = "%Y-%m-%d"  # فرمت: bot_daily.log.2024-12-25
        logger.addHandler(daily_handler)
    
    return logger


# ==================== Logger سراسری ====================

bot_logger = setup_logger("bot")


# ==================== Decorator برای لاگ کردن توابع ====================

def log_function_call(logger: Optional[logging.Logger] = None):
    """
    Decorator برای لاگ کردن فراخوانی توابع
    
    مثال:
        @log_function_call()
        async def my_handler(update, context):
            ...
    """
    if logger is None:
        logger = bot_logger
    
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            func_name = func.__name__
            logger.info(f"📞 فراخوانی تابع: {func_name}")
            
            try:
                result = await func(*args, **kwargs)
                logger.info(f"✅ تابع {func_name} با موفقیت اجرا شد")
                return result
            except Exception as e:
                logger.error(f"❌ خطا در تابع {func_name}: {e}", exc_info=True)
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            func_name = func.__name__
            logger.info(f"📞 فراخوانی تابع: {func_name}")
            
            try:
                result = func(*args, **kwargs)
                logger.info(f"✅ تابع {func_name} با موفقیت اجرا شد")
                return result
            except Exception as e:
                logger.error(f"❌ خطا در تابع {func_name}: {e}", exc_info=True)
                raise
        
        # تشخیص async یا sync
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# ==================== توابع کمکی برای لاگ ====================

def log_user_action(user_id: int, action: str, details: str = ""):
    """لاگ عملیات کاربر"""
    bot_logger.info(f"👤 کاربر {user_id} | عملیات: {action} | {details}")


def log_order(order_id: int, user_id: int, status: str, amount: float):
    """لاگ سفارش"""
    bot_logger.info(
        f"📦 سفارش #{order_id} | کاربر: {user_id} | "
        f"وضعیت: {status} | مبلغ: {amount:,.0f} تومان"
    )


def log_payment(order_id: int, user_id: int, status: str):
    """لاگ پرداخت"""
    bot_logger.info(f"💳 پرداخت سفارش #{order_id} | کاربر: {user_id} | وضعیت: {status}")


def log_discount_usage(user_id: int, code: str, amount: float):
    """لاگ استفاده از کد تخفیف"""
    bot_logger.info(f"🎁 کاربر {user_id} | کد تخفیف: {code} | مبلغ: {amount:,.0f} تومان")


def log_database_operation(operation: str, table: str, record_id: Optional[int] = None):
    """لاگ عملیات دیتابیس"""
    if record_id:
        bot_logger.debug(f"💾 دیتابیس | {operation} | جدول: {table} | ID: {record_id}")
    else:
        bot_logger.debug(f"💾 دیتابیس | {operation} | جدول: {table}")


def log_rate_limit(user_id: int, action: str, remaining_time: int):
    """لاگ محدودیت درخواست"""
    bot_logger.warning(
        f"⚠️ Rate Limit | کاربر: {user_id} | عملیات: {action} | "
        f"زمان باقیمانده: {remaining_time}s"
    )


def log_error(error_type: str, error_message: str, user_id: Optional[int] = None):
    """لاگ خطا"""
    if user_id:
        bot_logger.error(f"❌ {error_type} | کاربر: {user_id} | {error_message}")
    else:
        bot_logger.error(f"❌ {error_type} | {error_message}")


def log_admin_action(admin_id: int, action: str, details: str = ""):
    """لاگ عملیات ادمین"""
    bot_logger.info(f"👨‍💼 ادمین {admin_id} | {action} | {details}")


def log_broadcast(admin_id: int, success: int, failed: int, total: int):
    """لاگ پیام همگانی"""
    bot_logger.info(
        f"📢 پیام همگانی | ادمین: {admin_id} | "
        f"موفق: {success} | ناموفق: {failed} | کل: {total}"
    )


def log_backup(status: str, filename: str = "", error: str = ""):
    """لاگ بکاپ"""
    if status == "success":
        bot_logger.info(f"💾 بکاپ موفق | فایل: {filename}")
    else:
        bot_logger.error(f"❌ بکاپ ناموفق | خطا: {error}")


def log_startup():
    """لاگ شروع ربات"""
    bot_logger.info("=" * 50)
    bot_logger.info("🚀 ربات شروع به کار کرد")
    bot_logger.info(f"📅 تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    bot_logger.info("=" * 50)


def log_shutdown():
    """لاگ خاموش شدن ربات"""
    bot_logger.info("=" * 50)
    bot_logger.info("🛑 ربات متوقف شد")
    bot_logger.info(f"📅 تاریخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    bot_logger.info("=" * 50)


# ==================== Context Manager برای لاگ بخش‌های کد ====================

class LogSection:
    """
    Context manager برای لاگ کردن یک بخش از کد
    
    مثال:
        with LogSection("پردازش سفارش"):
            # کد...
            pass
    """
    def __init__(self, section_name: str, logger: Optional[logging.Logger] = None):
        self.section_name = section_name
        self.logger = logger or bot_logger
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.info(f"▶️ شروع: {self.section_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        
        if exc_type is None:
            self.logger.info(f"✅ پایان: {self.section_name} ({duration:.2f}s)")
        else:
            self.logger.error(
                f"❌ خطا در {self.section_name} ({duration:.2f}s): {exc_val}",
                exc_info=True
            )
        
        return False  # اجازه propagate شدن exception


# ==================== نمونه استفاده ====================

if __name__ == "__main__":
    # تست سیستم logging
    
    print("🧪 تست سیستم Logging:\n")
    
    # لاگ‌های مختلف
    bot_logger.debug("🔍 پیام DEBUG")
    bot_logger.info("ℹ️ پیام INFO")
    bot_logger.warning("⚠️ پیام WARNING")
    bot_logger.error("❌ پیام ERROR")
    bot_logger.critical("🔥 پیام CRITICAL")
    
    print("\n" + "="*50 + "\n")
    
    # لاگ عملیات
    log_user_action(12345, "افزودن به سبد", "محصول: مانتو مشکی")
    log_order(101, 12345, "pending", 250000)
    log_payment(101, 12345, "confirmed")
    log_discount_usage(12345, "SUMMER2024", 25000)
    log_rate_limit(12345, "order", 30)
    
    print("\n" + "="*50 + "\n")
    
    # تست decorator
    @log_function_call()
    def test_function(x, y):
        return x + y
    
    result = test_function(5, 3)
    print(f"نتیجه: {result}")
    
    print("\n" + "="*50 + "\n")
    
    # تست context manager
    with LogSection("پردازش تست"):
        import time
        time.sleep(0.5)
        print("در حال انجام کار...")
    
    print("\n✅ لاگ‌ها در پوشه 'logs' ذخیره شدند!")
