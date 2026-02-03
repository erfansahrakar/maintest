"""
Migration: حذف ستون wallet_used از جدول orders
"""
import sqlite3
import shutil
from datetime import datetime

# بکاپ
backup_name = f'shop_bot_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
shutil.copy('shop_bot.db', backup_name)
print(f"✅ بکاپ ذخیره شد: {backup_name}")

conn = sqlite3.connect('shop_bot.db')
cursor = conn.cursor()

# ساخت جدول جدید بدون wallet_used
cursor.execute("""
    CREATE TABLE orders_new (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        items TEXT,
        total_price REAL,
        discount_amount REAL DEFAULT 0,
        final_price REAL,
        discount_code TEXT,
        status TEXT DEFAULT 'pending',
        receipt_photo TEXT,
        shipping_method TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )
""")

# کپی داده‌ها (بدون wallet_used)
cursor.execute("""
    INSERT INTO orders_new 
    (id, user_id, items, total_price, discount_amount, final_price, 
     discount_code, status, receipt_photo, shipping_method, created_at, expires_at)
    SELECT 
        id, user_id, items, total_price, discount_amount, final_price,
        discount_code, status, receipt_photo, shipping_method, created_at, expires_at
    FROM orders
""")

# حذف جدول قدیمی
cursor.execute("DROP TABLE orders")

# تغییر نام جدول جدید
cursor.execute("ALTER TABLE orders_new RENAME TO orders")

conn.commit()
conn.close()

print("✅ Migration تمام شد - ستون wallet_used حذف شد")
print("✅ دیتابیس الان 12 ستون داره")
