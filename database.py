"""
مدیریت دیتابیس با SQLite
"""
import sqlite3
import json
from datetime import datetime
from config import DATABASE_NAME


class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DATABASE_NAME, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()
    
    def create_tables(self):
        """ایجاد جداول دیتابیس"""
        
        # جدول محصولات
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                photo_id TEXT,
                channel_message_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # جدول پک‌ها
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS packs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                price REAL NOT NULL,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )
        """)
        
        # جدول کاربران
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                full_name TEXT,
                phone TEXT,
                landline_phone TEXT,
                address TEXT,
                shop_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # جدول سبد خرید
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS cart (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product_id INTEGER,
                pack_id INTEGER,
                quantity INTEGER DEFAULT 1,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (product_id) REFERENCES products(id),
                FOREIGN KEY (pack_id) REFERENCES packs(id)
            )
        """)
        
        # جدول سفارشات
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
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
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # جدول کد تخفیف
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS discount_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                type TEXT NOT NULL,
                value REAL NOT NULL,
                min_purchase REAL DEFAULT 0,
                max_discount REAL,
                usage_limit INTEGER,
                used_count INTEGER DEFAULT 0,
                start_date TIMESTAMP,
                end_date TIMESTAMP,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # جدول استفاده از کد تخفیف
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS discount_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                discount_code TEXT,
                order_id INTEGER,
                used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (order_id) REFERENCES orders(id)
            )
        """)
        
        self.conn.commit()
    
    # ==================== محصولات ====================
    
    def add_product(self, name, description, photo_id):
        """افزودن محصول جدید"""
        self.cursor.execute(
            "INSERT INTO products (name, description, photo_id) VALUES (?, ?, ?)",
            (name, description, photo_id)
        )
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_product(self, product_id):
        """دریافت اطلاعات یک محصول"""
        self.cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        return self.cursor.fetchone()
    
    def get_all_products(self):
        """دریافت تمام محصولات"""
        self.cursor.execute("SELECT * FROM products ORDER BY created_at DESC")
        return self.cursor.fetchall()
    
    def update_product_name(self, product_id, name):
        """ویرایش نام محصول"""
        self.cursor.execute(
            "UPDATE products SET name = ? WHERE id = ?",
            (name, product_id)
        )
        self.conn.commit()
    
    def update_product_description(self, product_id, description):
        """ویرایش توضیحات محصول"""
        self.cursor.execute(
            "UPDATE products SET description = ? WHERE id = ?",
            (description, product_id)
        )
        self.conn.commit()
    
    def update_product_photo(self, product_id, photo_id):
        """ویرایش عکس محصول"""
        self.cursor.execute(
            "UPDATE products SET photo_id = ? WHERE id = ?",
            (photo_id, product_id)
        )
        self.conn.commit()
    
    def save_channel_message_id(self, product_id, message_id):
        """ذخیره شناسه پیام کانال"""
        self.cursor.execute(
            "UPDATE products SET channel_message_id = ? WHERE id = ?",
            (message_id, product_id)
        )
        self.conn.commit()
    
    def delete_product(self, product_id):
        """حذف محصول"""
        self.cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        self.cursor.execute("DELETE FROM packs WHERE product_id = ?", (product_id,))
        self.conn.commit()
    
    # ==================== پک‌ها ====================
    
    def add_pack(self, product_id, name, quantity, price):
        """افزودن پک به محصول"""
        self.cursor.execute(
            "INSERT INTO packs (product_id, name, quantity, price) VALUES (?, ?, ?, ?)",
            (product_id, name, quantity, price)
        )
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_packs(self, product_id):
        """دریافت پک‌های یک محصول"""
        self.cursor.execute("SELECT * FROM packs WHERE product_id = ?", (product_id,))
        return self.cursor.fetchall()
    
    def get_pack(self, pack_id):
        """دریافت اطلاعات یک پک"""
        self.cursor.execute("SELECT * FROM packs WHERE id = ?", (pack_id,))
        return self.cursor.fetchone()
    
    def update_pack(self, pack_id, name, quantity, price):
        """ویرایش پک"""
        self.cursor.execute(
            "UPDATE packs SET name = ?, quantity = ?, price = ? WHERE id = ?",
            (name, quantity, price, pack_id)
        )
        self.conn.commit()
    
    def delete_pack(self, pack_id):
        """حذف پک"""
        self.cursor.execute("DELETE FROM packs WHERE id = ?", (pack_id,))
        self.conn.commit()
    
    # ==================== کاربران ====================
    
    def add_user(self, user_id, username, first_name):
        """افزودن کاربر جدید"""
        self.cursor.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
            (user_id, username, first_name)
        )
        self.conn.commit()
    
    def update_user_info(self, user_id, phone=None, landline_phone=None, address=None, full_name=None, shop_name=None):
        """بروزرسانی اطلاعات کاربر"""
        if phone:
            self.cursor.execute("UPDATE users SET phone = ? WHERE user_id = ?", (phone, user_id))
        if landline_phone:
            self.cursor.execute("UPDATE users SET landline_phone = ? WHERE user_id = ?", (landline_phone, user_id))
        if address:
            self.cursor.execute("UPDATE users SET address = ? WHERE user_id = ?", (address, user_id))
        if full_name:
            self.cursor.execute("UPDATE users SET full_name = ? WHERE user_id = ?", (full_name, user_id))
        if shop_name:
            self.cursor.execute("UPDATE users SET shop_name = ? WHERE user_id = ?", (shop_name, user_id))
        self.conn.commit()
    
    def get_user(self, user_id):
        """دریافت اطلاعات کاربر"""
        self.cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return self.cursor.fetchone()
    
    def get_all_users(self):
        """دریافت همه کاربران"""
        self.cursor.execute("SELECT * FROM users")
        return self.cursor.fetchall()
    
    # ==================== سبد خرید ====================
    
    def add_to_cart(self, user_id, product_id, pack_id, quantity=1):
        """افزودن به سبد خرید"""
        self.cursor.execute(
            "SELECT id, quantity FROM cart WHERE user_id = ? AND product_id = ? AND pack_id = ?",
            (user_id, product_id, pack_id)
        )
        existing = self.cursor.fetchone()
        
        if existing:
            new_quantity = existing[1] + quantity
            self.cursor.execute(
                "UPDATE cart SET quantity = ? WHERE id = ?",
                (new_quantity, existing[0])
            )
        else:
            self.cursor.execute(
                "INSERT INTO cart (user_id, product_id, pack_id, quantity) VALUES (?, ?, ?, ?)",
                (user_id, product_id, pack_id, quantity)
            )
        self.conn.commit()
    
    def get_cart(self, user_id):
        """دریافت سبد خرید کاربر"""
        self.cursor.execute("""
            SELECT c.id, p.name, pk.name, pk.quantity, pk.price, c.quantity
            FROM cart c
            JOIN products p ON c.product_id = p.id
            JOIN packs pk ON c.pack_id = pk.id
            WHERE c.user_id = ?
        """, (user_id,))
        return self.cursor.fetchall()
    
    def clear_cart(self, user_id):
        """خالی کردن سبد خرید"""
        self.cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
        self.conn.commit()
    
    def remove_from_cart(self, cart_id):
        """حذف آیتم از سبد"""
        self.cursor.execute("DELETE FROM cart WHERE id = ?", (cart_id,))
        self.conn.commit()
    
    # ==================== سفارشات ====================
    
    def create_order(self, user_id, items, total_price, discount_amount=0, final_price=None, discount_code=None):
        """ایجاد سفارش جدید"""
        items_json = json.dumps(items, ensure_ascii=False)
        if final_price is None:
            final_price = total_price - discount_amount
        
        self.cursor.execute(
            "INSERT INTO orders (user_id, items, total_price, discount_amount, final_price, discount_code) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, items_json, total_price, discount_amount, final_price, discount_code)
        )
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_order(self, order_id):
        """دریافت اطلاعات سفارش"""
        self.cursor.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        return self.cursor.fetchone()
    
    def update_order_status(self, order_id, status):
        """بروزرسانی وضعیت سفارش"""
        self.cursor.execute(
            "UPDATE orders SET status = ? WHERE id = ?",
            (status, order_id)
        )
        self.conn.commit()
    
    def add_receipt(self, order_id, photo_id):
        """افزودن رسید به سفارش"""
        self.cursor.execute(
            "UPDATE orders SET receipt_photo = ?, status = 'receipt_sent' WHERE id = ?",
            (photo_id, order_id)
        )
        self.conn.commit()
    
    def update_shipping_method(self, order_id, method):
        """بروزرسانی نحوه ارسال"""
        self.cursor.execute(
            "UPDATE orders SET shipping_method = ? WHERE id = ?",
            (method, order_id)
        )
        self.conn.commit()
    
    def get_pending_orders(self):
        """دریافت سفارشات در انتظار تایید"""
        self.cursor.execute("SELECT * FROM orders WHERE status = 'pending' ORDER BY created_at DESC")
        return self.cursor.fetchall()
    
    def get_waiting_payment_orders(self):
        """دریافت سفارشات در انتظار پرداخت"""
        self.cursor.execute("SELECT * FROM orders WHERE status = 'waiting_payment' ORDER BY created_at DESC")
        return self.cursor.fetchall()
    
    def get_user_orders(self, user_id):
        """دریافت سفارشات یک کاربر"""
        self.cursor.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        return self.cursor.fetchall()
    
    # ==================== تخفیف ====================
    
    def create_discount(self, code, type, value, min_purchase=0, max_discount=None, usage_limit=None, start_date=None, end_date=None):
        """ایجاد کد تخفیف"""
        self.cursor.execute(
            "INSERT INTO discount_codes (code, type, value, min_purchase, max_discount, usage_limit, start_date, end_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (code, type, value, min_purchase, max_discount, usage_limit, start_date, end_date)
        )
        self.conn.commit()
        return self.cursor.lastrowid
    
    def get_discount(self, code):
        """دریافت اطلاعات کد تخفیف"""
        self.cursor.execute("SELECT * FROM discount_codes WHERE code = ? AND is_active = 1", (code,))
        return self.cursor.fetchone()
    
    def get_all_discounts(self):
        """دریافت همه کدهای تخفیف"""
        self.cursor.execute("SELECT * FROM discount_codes ORDER BY created_at DESC")
        return self.cursor.fetchall()
    
    def use_discount(self, user_id, discount_code, order_id):
        """ثبت استفاده از کد تخفیف"""
        self.cursor.execute(
            "INSERT INTO discount_usage (user_id, discount_code, order_id) VALUES (?, ?, ?)",
            (user_id, discount_code, order_id)
        )
        self.cursor.execute(
            "UPDATE discount_codes SET used_count = used_count + 1 WHERE code = ?",
            (discount_code,)
        )
        self.conn.commit()
    
    def toggle_discount(self, discount_id):
        """فعال/غیرفعال کردن کد تخفیف"""
        self.cursor.execute(
            "UPDATE discount_codes SET is_active = 1 - is_active WHERE id = ?",
            (discount_id,)
        )
        self.conn.commit()
    
    def delete_discount(self, discount_id):
        """حذف کد تخفیف"""
        self.cursor.execute("DELETE FROM discount_codes WHERE id = ?", (discount_id,))
        self.conn.commit()
    
    # ==================== آمار ====================
    
    def get_statistics(self):
        """دریافت آمار کلی"""
        stats = {}
        
        # تعداد کل سفارشات
        self.cursor.execute("SELECT COUNT(*) FROM orders")
        stats['total_orders'] = self.cursor.fetchone()[0]
        
        # تعداد سفارشات امروز
        self.cursor.execute("SELECT COUNT(*) FROM orders WHERE DATE(created_at) = DATE('now')")
        stats['today_orders'] = self.cursor.fetchone()[0]
        
        # تعداد سفارشات این هفته
        self.cursor.execute("SELECT COUNT(*) FROM orders WHERE DATE(created_at) >= DATE('now', '-7 days')")
        stats['week_orders'] = self.cursor.fetchone()[0]
        
        # درآمد کل (فقط سفارشات تایید شده)
        self.cursor.execute("SELECT SUM(final_price) FROM orders WHERE status IN ('confirmed', 'payment_confirmed')")
        total_income = self.cursor.fetchone()[0]
        stats['total_income'] = total_income if total_income else 0
        
        # درآمد امروز
        self.cursor.execute("SELECT SUM(final_price) FROM orders WHERE status IN ('confirmed', 'payment_confirmed') AND DATE(created_at) = DATE('now')")
        today_income = self.cursor.fetchone()[0]
        stats['today_income'] = today_income if today_income else 0
        
        # درآمد این هفته
        self.cursor.execute("SELECT SUM(final_price) FROM orders WHERE status IN ('confirmed', 'payment_confirmed') AND DATE(created_at) >= DATE('now', '-7 days')")
        week_income = self.cursor.fetchone()[0]
        stats['week_income'] = week_income if week_income else 0
        
        # تعداد کاربران
        self.cursor.execute("SELECT COUNT(*) FROM users")
        stats['total_users'] = self.cursor.fetchone()[0]
        
        # کاربران جدید این هفته
        self.cursor.execute("SELECT COUNT(*) FROM users WHERE DATE(created_at) >= DATE('now', '-7 days')")
        stats['week_new_users'] = self.cursor.fetchone()[0]
        
        # تعداد محصولات
        self.cursor.execute("SELECT COUNT(*) FROM products")
        stats['total_products'] = self.cursor.fetchone()[0]
        
        # تعداد سفارشات در انتظار
        self.cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'pending'")
        stats['pending_orders'] = self.cursor.fetchone()[0]
        
        # محبوب‌ترین محصول
        self.cursor.execute("""
            SELECT items FROM orders 
            WHERE status IN ('confirmed', 'payment_confirmed')
        """)
        product_counts = {}
        for row in self.cursor.fetchall():
            items = json.loads(row[0])
            for item in items:
                product_name = item.get('product', '')
                product_counts[product_name] = product_counts.get(product_name, 0) + item.get('quantity', 0)
        
        if product_counts:
            stats['most_popular'] = max(product_counts.items(), key=lambda x: x[1])[0]
        else:
            stats['most_popular'] = "هنوز داده‌ای نیست"
        
        return stats
    
    def close(self):
        """بستن اتصال"""
        self.conn.close()