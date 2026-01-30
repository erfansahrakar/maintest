#!/usr/bin/env python3
"""
اسکریپت جادویی برای رفع کامل مشکل timezone و expires_at
این اسکریپت مستقیماً روی دیتابیس کار می‌کنه و همه چیز رو درست می‌کنه
"""

import sqlite3
from datetime import datetime, timedelta
import pytz

# مسیر دیتابیس - این رو تغییر بده
DB_PATH = "shop_bot.db"

# Timezone تهران
TEHRAN_TZ = pytz.timezone('Asia/Tehran')

def get_tehran_now():
    """دریافت زمان فعلی تهران"""
    return datetime.now(TEHRAN_TZ)

def fix_all_orders():
    """
    تصحیح همه سفارش‌ها:
    1. تبدیل created_at از UTC به تهران
    2. تنظیم expires_at به 1 ساعت بعد از created_at (با زمان تهران)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("🔧 شروع تصحیح همه سفارش‌ها...")
    print("=" * 60)
    
    # گرفتن همه سفارش‌ها
    cursor.execute("SELECT id, created_at, expires_at, status FROM orders")
    orders = cursor.fetchall()
    
    print(f"📊 تعداد کل سفارش‌ها: {len(orders)}\n")
    
    fixed_count = 0
    
    for order_id, created_at_str, expires_at_str, status in orders:
        try:
            # تبدیل created_at به datetime
            created_at_utc = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
            
            # اگر timezone نداره، فرض می‌کنیم UTC هست
            if created_at_utc.tzinfo is None:
                created_at_utc = pytz.UTC.localize(created_at_utc)
            
            # تبدیل به تهران
            created_at_tehran = created_at_utc.astimezone(TEHRAN_TZ)
            
            # محاسبه expires_at (1 ساعت بعد)
            expires_at_tehran = created_at_tehran + timedelta(hours=1)
            
            # آپدیت دیتابیس
            # تبدیل به naive datetime (بدون timezone) برای ذخیره در SQLite
            created_at_naive = created_at_tehran.replace(tzinfo=None)
            expires_at_naive = expires_at_tehran.replace(tzinfo=None)
            
            cursor.execute("""
                UPDATE orders 
                SET created_at = ?, expires_at = ?
                WHERE id = ?
            """, (created_at_naive, expires_at_naive, order_id))
            
            fixed_count += 1
            
            print(f"✅ سفارش #{order_id}:")
            print(f"   created_at: {created_at_tehran.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   expires_at: {expires_at_tehran.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   status: {status}")
            print()
            
        except Exception as e:
            print(f"❌ خطا در سفارش #{order_id}: {e}")
            print()
    
    conn.commit()
    conn.close()
    
    print("=" * 60)
    print(f"🎉 تمام! {fixed_count} سفارش تصحیح شد")
    print("\n⚠️  حالا ربات رو ریستارت کن تا تغییرات اعمال بشه")

def show_sample_orders():
    """نمایش نمونه سفارش‌ها بعد از تصحیح"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, created_at, expires_at, status 
        FROM orders 
        ORDER BY id DESC 
        LIMIT 3
    """)
    
    print("\n📋 نمونه آخرین سفارش‌ها:")
    print("-" * 60)
    
    for order_id, created_at, expires_at, status in cursor.fetchall():
        # محاسبه تفاوت
        try:
            created_dt = datetime.fromisoformat(created_at)
            expires_dt = datetime.fromisoformat(expires_at)
            diff_hours = (expires_dt - created_dt).total_seconds() / 3600
            
            print(f"سفارش #{order_id}:")
            print(f"  📅 ثبت: {created_at}")
            print(f"  ⏰ انقضا: {expires_at}")
            print(f"  ⏱️  تفاوت: {diff_hours:.2f} ساعت")
            print(f"  📊 وضعیت: {status}")
            print()
        except:
            pass
    
    conn.close()

if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════╗
║   🔧 اسکریپت تصحیح کامل تاریخ و زمان سفارش‌ها   ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    # چک کردن pytz
    try:
        import pytz
        print("✅ pytz نصب شده است")
    except ImportError:
        print("❌ pytz نصب نیست! لطفاً اجرا کنید: pip install pytz")
        exit(1)
    
    # تایید از کاربر
    print(f"\n⚠️  این اسکریپت همه سفارش‌های موجود در '{DB_PATH}' را تصحیح می‌کند.")
    response = input("آیا مطمئن هستید؟ (yes/no): ")
    
    if response.lower() in ['yes', 'y', 'بله']:
        fix_all_orders()
        show_sample_orders()
    else:
        print("❌ لغو شد")
