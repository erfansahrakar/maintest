"""
اسکریپت چک کردن ساختار دیتابیس
"""
import sqlite3

conn = sqlite3.connect('shop_bot.db')
cursor = conn.cursor()

# چک کردن ستون‌های جدول orders
cursor.execute("PRAGMA table_info(orders)")
columns = cursor.fetchall()

print("ستون‌های جدول orders:")
for col in columns:
    print(f"  {col[0]}: {col[1]} ({col[2]})")

print(f"\nتعداد کل: {len(columns)} ستون")

# تست یه سفارش
cursor.execute("SELECT * FROM orders LIMIT 1")
order = cursor.fetchone()
if order:
    print(f"\nتعداد فیلدهای یک سفارش: {len(order)}")
else:
    print("\nهیچ سفارشی وجود ندارد")

conn.close()
