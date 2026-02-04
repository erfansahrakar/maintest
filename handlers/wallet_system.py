"""
سیستم مدیریت اعتبار (Wallet) نسخه 2.0 - با جداسازی اعتبار دائمی و موقت
✨ قابلیت‌های جدید:
- جداسازی کامل اعتبار دائمی و موقت
- مدیریت چند اعتبار موقت همزمان
- اولویت استفاده از اعتبار موقت (FIFO)
- حذف خودکار اعتبارهای منقضی شده
- گزارش جداگانه برای هر نوع اعتبار
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from datetime import datetime, timedelta
from typing import Optional, Tuple, List
import logging

logger = logging.getLogger(__name__)

# ==================== States ====================
WALLET_CHARGE_USER_ID = 100
WALLET_CHARGE_AMOUNT = 101
WALLET_GIFT_USER_ID = 102
WALLET_GIFT_TYPE = 103
WALLET_GIFT_VALUE = 104
WALLET_GIFT_EXPIRY = 105
WALLET_CASHBACK_PERCENT = 106
WALLET_CASHBACK_DATES = 107

# ==================== توابع Helper ====================

def format_price(price: float) -> str:
    """فرمت کردن قیمت به صورت فارسی"""
    return f"{price:,.0f}".replace(',', '٬')

def get_wallet_keyboard():
    """کیبورد منوی اعتبار"""
    keyboard = [
        [InlineKeyboardButton("💰 مشاهده موجودی", callback_data="wallet:view")],
        [InlineKeyboardButton("📋 تاریخچه تراکنش‌ها", callback_data="wallet:history")],
        [InlineKeyboardButton("🎁 اعتبار هدیه من", callback_data="wallet:gifts")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="wallet:back")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_admin_wallet_keyboard():
    """کیبورد مدیریت اعتبار برای ادمین"""
    keyboard = [
        [InlineKeyboardButton("💳 شارژ اعتبار دائمی", callback_data="wallet_admin:charge_permanent")],
        [InlineKeyboardButton("🎁 اعتبار هدیه موقت", callback_data="wallet_admin:gift_temp")],
        [InlineKeyboardButton("🎪 کمپین اعتباری", callback_data="campaign:menu")],
        [InlineKeyboardButton("💎 تنظیم کش‌بک", callback_data="wallet_admin:cashback")],
        [InlineKeyboardButton("📊 گزارش اعتبارها", callback_data="wallet_admin:report")],
        [InlineKeyboardButton("🧹 پاکسازی منقضی‌ها", callback_data="wallet_admin:cleanup")],
        [InlineKeyboardButton("🔙 بازگشت به منوی ادمین", callback_data="admin_back")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==================== توابع کاربر ====================

async def view_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش موجودی اعتبار کاربر با جداسازی دائمی و موقت"""
    query = update.callback_query
    if query:
        await query.answer()
        user_id = query.from_user.id
        message_func = query.message.reply_text
        
        # چک کردن اگر از سبد خرید اومده
        if "cart" in query.data:
            context.user_data['from_cart'] = True
    else:
        user_id = update.effective_user.id
        message_func = update.message.reply_text
    
    db = context.bot_data['db']
    
    # دریافت اعتبار دائمی
    permanent_balance = db.get_permanent_wallet(user_id)
    
    # دریافت اعتبارهای موقت فعال
    temp_wallets = db.get_active_temp_wallets(user_id)
    
    # محاسبه مجموع
    total_temp = sum([w[1] for w in temp_wallets])  # w[1] = balance
    total_balance = permanent_balance + total_temp
    
    text = "💰 **موجودی اعتبار شما**\n\n"
    
    if total_balance == 0:
        text += "موجودی فعلی: ۰ تومان\n\n"
        text += "⚠️ شما هنوز اعتباری ندارید.\n"
        text += "با خرید از فروشگاه، اعتبار کسب کنید!"
    else:
        text += f"💵 **مجموع کل:** {format_price(total_balance)} تومان\n\n"
        text += "━━━━━━━━━━━━━━━━\n\n"
        
        # نمایش اعتبار دائمی
        if permanent_balance > 0:
            text += f"🏦 **اعتبار دائمی:**\n"
            text += f"   💰 {format_price(permanent_balance)} تومان\n"
            text += f"   ♾ بدون تاریخ انقضا\n\n"
        
        # نمایش اعتبارهای موقت
        if temp_wallets:
            text += f"🎁 **اعتبار هدیه ({len(temp_wallets)} عدد):**\n"
            for idx, wallet in enumerate(temp_wallets, 1):
                wallet_id, balance, expires_at, description = wallet
                expiry = datetime.fromisoformat(expires_at)
                days_left = (expiry - datetime.now()).days
                
                text += f"   {idx}. {format_price(balance)} تومان"
                if days_left > 0:
                    text += f" - {days_left} روز مانده\n"
                    if description:
                        text += f"      📝 {description}\n"
                else:
                    text += f" - منقضی شده!\n"
            text += "\n"
        
        text += "━━━━━━━━━━━━━━━━\n\n"
        text += "💡 **نحوه استفاده:**\n"
        text += "• ابتدا اعتبار هدیه استفاده می‌شود\n"
        text += "• سپس اعتبار دائمی\n"
        text += "• اعتبار هدیه تاریخ انقضا دارد!"
    
    await message_func(text, parse_mode='Markdown', reply_markup=get_wallet_keyboard())

async def view_wallet_gifts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش جزئیات اعتبارهای هدیه"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    db = context.bot_data['db']
    
    temp_wallets = db.get_active_temp_wallets(user_id)
    
    if not temp_wallets:
        text = "🎁 **اعتبار هدیه شما**\n\n"
        text += "شما هیچ اعتبار هدیه‌ای ندارید.\n\n"
        text += "💡 اعتبار هدیه از طریق:\n"
        text += "• خرید در زمان‌های خاص\n"
        text += "• کمپین‌های تبلیغاتی\n"
        text += "• جوایز ویژه\n"
        text += "به شما داده می‌شود!"
    else:
        text = "🎁 **اعتبار هدیه شما**\n\n"
        text += f"📊 تعداد: {len(temp_wallets)} عدد\n"
        text += f"💰 مجموع: {format_price(sum([w[1] for w in temp_wallets]))} تومان\n\n"
        text += "━━━━━━━━━━━━━━━━\n\n"
        
        for idx, wallet in enumerate(temp_wallets, 1):
            wallet_id, balance, expires_at, description = wallet
            expiry = datetime.fromisoformat(expires_at)
            days_left = (expiry - datetime.now()).days
            
            text += f"**{idx}. اعتبار #{wallet_id}**\n"
            text += f"💰 مبلغ: {format_price(balance)} تومان\n"
            
            if days_left > 0:
                text += f"⏰ {days_left} روز مانده\n"
                text += f"📅 انقضا: {expiry.strftime('%Y/%m/%d')}\n"
            else:
                text += f"❌ منقضی شده!\n"
            
            if description:
                text += f"📝 {description}\n"
            
            text += "\n"
        
        text += "━━━━━━━━━━━━━━━━\n\n"
        text += "⚠️ **توجه:**\n"
        text += "هنگام خرید، ابتدا اعتبارهای هدیه با تاریخ انقضای نزدیک‌تر استفاده می‌شوند."
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="wallet:view")]]
    
    await query.message.reply_text(
        text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def view_wallet_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش تاریخچه تراکنش‌های اعتبار"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    db = context.bot_data['db']
    
    transactions = db.get_wallet_transactions(user_id, limit=15)
    
    if not transactions:
        text = "📋 **تاریخچه تراکنش‌ها**\n\n"
        text += "هنوز تراکنشی ثبت نشده است."
    else:
        text = "📋 **تاریخچه تراکنش‌ها**\n\n"
        text += "🔽 ۱۵ تراکنش اخیر:\n\n"
        
        for trans in transactions:
            trans_id, amount, trans_type, wallet_type, description, created_at = trans
            date = datetime.fromisoformat(created_at).strftime('%Y/%m/%d %H:%M')
            
            if amount > 0:
                emoji = "➕"
                sign = "+"
                color = "🟢"
            else:
                emoji = "➖"
                sign = ""
                color = "🔴"
            
            # نوع اعتبار
            if wallet_type == 'permanent':
                type_emoji = "🏦"
                type_text = "دائمی"
            else:
                type_emoji = "🎁"
                type_text = "هدیه"
            
            text += f"{color} {emoji} {sign}{format_price(abs(amount))} تومان\n"
            text += f"   {type_emoji} {type_text}\n"
            text += f"   📝 {description}\n"
            text += f"   🕐 {date}\n\n"
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="wallet:view")]]
    
    await query.message.reply_text(
        text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def use_wallet_in_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استفاده از اعتبار در پرداخت سفارش با اولویت اعتبار موقت"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    order_id = int(query.data.split(":")[1])
    
    db = context.bot_data['db']
    
    # دریافت اطلاعات سفارش
    order = db.get_order(order_id)
    if not order:
        await query.answer("❌ سفارش یافت نشد!", show_alert=True)
        return
    
    order_data = order
    final_price = order_data[5]  # final_price
    status = order_data[7]  # status
    
    if status not in ['pending', 'waiting_payment']:
        await query.answer("⚠️ این سفارش قابل پرداخت نیست!", show_alert=True)
        return
    
    # دریافت موجودی‌ها
    permanent_balance = db.get_permanent_wallet(user_id)
    temp_wallets = db.get_active_temp_wallets(user_id)
    total_balance = permanent_balance + sum([w[1] for w in temp_wallets])
    
    if total_balance <= 0:
        await query.answer("❌ موجودی اعتبار شما کافی نیست!", show_alert=True)
        return
    
    # محاسبه مبلغ قابل استفاده
    usable_amount = min(total_balance, final_price)
    remaining_to_pay = final_price - usable_amount
    
    # کسر به ترتیب اولویت: موقت (نزدیک‌ترین انقضا) → دائمی
    amount_to_deduct = usable_amount
    deductions = []
    
    # 1. اعتبارهای موقت (مرتب شده بر اساس تاریخ انقضا)
    for wallet in temp_wallets:
        if amount_to_deduct <= 0:
            break
        
        wallet_id, balance, expires_at, description = wallet
        deduct_from_this = min(balance, amount_to_deduct)
        
        success = db.deduct_temp_wallet(
            user_id=user_id,
            wallet_id=wallet_id,
            amount=deduct_from_this,
            description=f"پرداخت سفارش #{order_id}",
            order_id=order_id
        )
        
        if success:
            deductions.append(('temp', wallet_id, deduct_from_this))
            amount_to_deduct -= deduct_from_this
    
    # 2. اعتبار دائمی (اگه نیاز باشه)
    if amount_to_deduct > 0 and permanent_balance > 0:
        deduct_from_permanent = min(permanent_balance, amount_to_deduct)
        
        success = db.deduct_permanent_wallet(
            user_id=user_id,
            amount=deduct_from_permanent,
            description=f"پرداخت سفارش #{order_id}",
            order_id=order_id
        )
        
        if success:
            deductions.append(('permanent', None, deduct_from_permanent))
            amount_to_deduct -= deduct_from_permanent
    
    # به‌روزرسانی سفارش
    db.update_order_wallet_payment(order_id, usable_amount, remaining_to_pay)
    
    # پیام نتیجه
    if remaining_to_pay <= 0:
        # سفارش کاملاً با اعتبار پرداخت شد
        db.update_order_status(order_id, 'payment_confirmed')
        text = f"✅ **پرداخت موفق!**\n\n"
        text += f"💰 مبلغ کسر شده: {format_price(usable_amount)} تومان\n\n"
        
        # جزئیات کسر
        text += "📊 **جزئیات کسر:**\n"
        for wallet_type, wallet_id, amount in deductions:
            if wallet_type == 'temp':
                text += f"   🎁 اعتبار هدیه: {format_price(amount)} تومان\n"
            else:
                text += f"   🏦 اعتبار دائمی: {format_price(amount)} تومان\n"
        
        text += f"\n✨ سفارش شما تایید شد و به زودی ارسال می‌شود!"
    else:
        text = f"✅ **اعتبار اعمال شد!**\n\n"
        text += f"💰 مبلغ استفاده شده: {format_price(usable_amount)} تومان\n\n"
        
        # جزئیات کسر
        text += "📊 **جزئیات کسر:**\n"
        for wallet_type, wallet_id, amount in deductions:
            if wallet_type == 'temp':
                text += f"   🎁 اعتبار هدیه: {format_price(amount)} تومان\n"
            else:
                text += f"   🏦 اعتبار دائمی: {format_price(amount)} تومان\n"
        
        text += f"\n💵 مبلغ باقیمانده: {format_price(remaining_to_pay)} تومان\n\n"
        text += "لطفاً مبلغ باقیمانده را واریز کنید."
    
    await query.message.reply_text(text, parse_mode='Markdown')

# ==================== توابع ادمین ====================

async def admin_wallet_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """منوی مدیریت اعتبار برای ادمین"""
    query = update.callback_query if update.callback_query else None
    
    if query:
        await query.answer()
        message_func = query.message.reply_text
    else:
        message_func = update.message.reply_text
    
    text = "🏦 **مدیریت سیستم اعتبار**\n\n"
    text += "📌 **انواع اعتبار:**\n"
    text += "🏦 **دائمی:** بدون تاریخ انقضا\n"
    text += "🎁 **هدیه:** موقت با تاریخ انقضا\n\n"
    text += "━━━━━━━━━━━━━━━━\n\n"
    text += "از این بخش می‌توانید:\n"
    text += "• شارژ اعتبار دائمی مشتریان\n"
    text += "• اعتبار هدیه موقت بدهید\n"
    text += "• کش‌بک تنظیم کنید\n"
    text += "• گزارش‌ها را ببینید\n"
    text += "• اعتبارهای منقضی را پاک کنید"
    
    await message_func(text, parse_mode='Markdown', reply_markup=get_admin_wallet_keyboard())

async def admin_charge_permanent_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع شارژ اعتبار دائمی توسط ادمین"""
    query = update.callback_query
    await query.answer()
    
    from keyboards import cancel_keyboard
    
    await query.message.reply_text(
        "💳 **شارژ اعتبار دائمی**\n\n"
        "🏦 این اعتبار تاریخ انقضا ندارد.\n\n"
        "لطفاً User ID مشتری را وارد کنید:",
        parse_mode='Markdown',
        reply_markup=cancel_keyboard()
    )
    
    context.user_data['wallet_type'] = 'permanent'
    return WALLET_CHARGE_USER_ID

async def admin_gift_temp_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع اعتبار هدیه موقت توسط ادمین"""
    query = update.callback_query
    await query.answer()
    
    from keyboards import cancel_keyboard
    
    await query.message.reply_text(
        "🎁 **اعتبار هدیه موقت**\n\n"
        "⏰ این اعتبار تاریخ انقضا دارد.\n\n"
        "لطفاً User ID مشتری را وارد کنید:",
        parse_mode='Markdown',
        reply_markup=cancel_keyboard()
    )
    
    context.user_data['wallet_type'] = 'temp'
    return WALLET_GIFT_USER_ID

async def admin_charge_wallet_user_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت User ID برای شارژ"""
    if update.message.text == "❌ لغو":
        from handlers.admin import admin_start
        await admin_start(update, context)
        context.user_data.clear()
        return ConversationHandler.END
    
    try:
        user_id = int(update.message.text)
        context.user_data['wallet_charge_user_id'] = user_id
        
        from keyboards import cancel_keyboard
        
        wallet_type = context.user_data.get('wallet_type', 'permanent')
        type_text = "دائمی 🏦" if wallet_type == 'permanent' else "هدیه 🎁"
        
        await update.message.reply_text(
            f"✅ کاربر: {user_id}\n"
            f"📌 نوع: {type_text}\n\n"
            "💰 مبلغ را وارد کنید (به تومان):",
            reply_markup=cancel_keyboard()
        )
        
        if wallet_type == 'permanent':
            return WALLET_CHARGE_AMOUNT
        else:
            return WALLET_GIFT_VALUE
    
    except ValueError:
        await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کنید!")
        return WALLET_CHARGE_USER_ID

async def admin_charge_permanent_amount_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت مبلغ و شارژ اعتبار دائمی"""
    if update.message.text == "❌ لغو":
        from handlers.admin import admin_start
        await admin_start(update, context)
        context.user_data.clear()
        return ConversationHandler.END
    
    try:
        amount = float(update.message.text.replace(',', ''))
        user_id = context.user_data.get('wallet_charge_user_id')
        
        if amount <= 0:
            await update.message.reply_text("❌ مبلغ باید بیشتر از صفر باشد!")
            return WALLET_CHARGE_AMOUNT
        
        db = context.bot_data['db']
        success = db.add_permanent_wallet(
            user_id=user_id,
            amount=amount,
            description="شارژ دائمی توسط ادمین",
            admin_id=update.effective_user.id
        )
        
        if success:
            from keyboards import admin_main_keyboard
            
            await update.message.reply_text(
                f"✅ شارژ موفق!\n\n"
                f"👤 کاربر: {user_id}\n"
                f"🏦 نوع: اعتبار دائمی\n"
                f"💰 مبلغ: {format_price(amount)} تومان\n\n"
                f"♾ این اعتبار تاریخ انقضا ندارد.",
                reply_markup=admin_main_keyboard()
            )
            
            # اطلاع‌رسانی به کاربر
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"🎉 **اعتبار دائمی شما شارژ شد!**\n\n"
                         f"💰 مبلغ: {format_price(amount)} تومان\n"
                         f"♾ بدون تاریخ انقضا\n\n"
                         f"✨ از خرید بعدی خود می‌توانید استفاده کنید!",
                    parse_mode='Markdown'
                )
            except:
                pass
        else:
            await update.message.reply_text("❌ خطا در شارژ اعتبار!")
        
        context.user_data.clear()
        return ConversationHandler.END
    
    except ValueError:
        await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کنید!")
        return WALLET_CHARGE_AMOUNT

async def admin_gift_temp_amount_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت مبلغ اعتبار هدیه"""
    if update.message.text == "❌ لغو":
        from handlers.admin import admin_start
        await admin_start(update, context)
        context.user_data.clear()
        return ConversationHandler.END
    
    try:
        amount = float(update.message.text.replace(',', ''))
        
        if amount <= 0:
            await update.message.reply_text("❌ مبلغ باید بیشتر از صفر باشد!")
            return WALLET_GIFT_VALUE
        
        context.user_data['wallet_gift_amount'] = amount
        
        from keyboards import cancel_keyboard
        
        await update.message.reply_text(
            f"💰 مبلغ: {format_price(amount)} تومان\n\n"
            "📅 چند روز اعتبار داشته باشد؟\n\n"
            "مثال: 30 (برای یک ماه)",
            reply_markup=cancel_keyboard()
        )
        
        return WALLET_GIFT_EXPIRY
    
    except ValueError:
        await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کنید!")
        return WALLET_GIFT_VALUE

async def admin_gift_temp_expiry_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت تعداد روز و ثبت اعتبار هدیه"""
    if update.message.text == "❌ لغو":
        from handlers.admin import admin_start
        await admin_start(update, context)
        context.user_data.clear()
        return ConversationHandler.END
    
    try:
        days = int(update.message.text)
        
        if days <= 0 or days > 365:
            await update.message.reply_text("❌ تعداد روز باید بین 1 تا 365 باشد!")
            return WALLET_GIFT_EXPIRY
        
        user_id = context.user_data.get('wallet_charge_user_id')
        amount = context.user_data.get('wallet_gift_amount')
        
        expires_at = datetime.now() + timedelta(days=days)
        
        db = context.bot_data['db']
        success = db.add_temp_wallet(
            user_id=user_id,
            amount=amount,
            expires_at=expires_at,
            description=f"هدیه {days} روزه",
            admin_id=update.effective_user.id
        )
        
        if success:
            from keyboards import admin_main_keyboard
            
            await update.message.reply_text(
                f"✅ اعتبار هدیه ثبت شد!\n\n"
                f"👤 کاربر: {user_id}\n"
                f"🎁 نوع: اعتبار هدیه\n"
                f"💰 مبلغ: {format_price(amount)} تومان\n"
                f"⏰ مدت: {days} روز\n"
                f"📅 انقضا: {expires_at.strftime('%Y/%m/%d')}\n\n"
                f"✅ اعتبار به کاربر اضافه شد.",
                reply_markup=admin_main_keyboard()
            )
            
            # اطلاع‌رسانی به کاربر
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"🎁 **اعتبار هدیه برای شما!**\n\n"
                         f"💰 مبلغ: {format_price(amount)} تومان\n"
                         f"⏰ مدت: {days} روز\n"
                         f"📅 انقضا: {expires_at.strftime('%Y/%m/%d')}\n\n"
                         f"⚠️ این اعتبار تاریخ انقضا دارد، زودتر استفاده کنید!",
                    parse_mode='Markdown'
                )
            except:
                pass
        else:
            await update.message.reply_text("❌ خطا در ثبت اعتبار!")
        
        context.user_data.clear()
        return ConversationHandler.END
    
    except ValueError:
        await update.message.reply_text("❌ لطفاً یک عدد وارد کنید!")
        return WALLET_GIFT_EXPIRY

async def admin_wallet_cleanup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """پاکسازی اعتبارهای منقضی شده"""
    query = update.callback_query
    await query.answer()
    
    db = context.bot_data['db']
    cleaned_count = db.cleanup_expired_wallets()
    
    text = "🧹 **پاکسازی انجام شد**\n\n"
    text += f"🗑 تعداد حذف شده: {cleaned_count} اعتبار منقضی\n\n"
    
    if cleaned_count > 0:
        text += "✅ اعتبارهای منقضی شده پاک شدند."
    else:
        text += "✨ هیچ اعتبار منقضی‌ای یافت نشد!"
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="wallet_admin:menu")]]
    
    await query.message.reply_text(
        text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def admin_wallet_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """گزارش کلی اعتبارهای کاربران با جداسازی"""
    query = update.callback_query
    await query.answer()
    
    db = context.bot_data['db']
    report = db.get_wallet_statistics_v2()
    
    text = "📊 **گزارش سیستم اعتبار**\n\n"
    
    text += "🏦 **اعتبار دائمی:**\n"
    text += f"   👥 کاربران: {report['permanent_users']}\n"
    text += f"   💰 مجموع: {format_price(report['permanent_total'])} تومان\n"
    text += f"   💵 میانگین: {format_price(report['permanent_avg'])} تومان\n\n"
    
    text += "🎁 **اعتبار هدیه:**\n"
    text += f"   👥 کاربران: {report['temp_users']}\n"
    text += f"   📦 تعداد: {report['temp_count']} عدد\n"
    text += f"   💰 مجموع: {format_price(report['temp_total'])} تومان\n"
    text += f"   ⚠️ منقضی شده: {report['expired_count']} عدد\n\n"
    
    text += "━━━━━━━━━━━━━━━━\n\n"
    
    text += f"💎 **کل سیستم:**\n"
    text += f"   💰 مجموع: {format_price(report['grand_total'])} تومان\n\n"
    
    text += f"📈 **امروز:**\n"
    text += f"   📊 تراکنش‌ها: {report['today_transactions']}\n"
    text += f"   ➕ شارژ: {format_price(report['today_charges'])} تومان\n"
    text += f"   ➖ برداشت: {format_price(report['today_withdrawals'])} تومان"
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="wallet_admin:menu")]]
    
    await query.message.reply_text(
        text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def wallet_back_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت بازگشت از wallet به منوی قبلی"""
    query = update.callback_query
    await query.answer()
    
    # بررسی اینکه از کجا اومده (سبد خرید یا منوی اصلی)
    message_text = query.message.text if query.message else ""
    
    if "سبد خرید" in message_text or context.user_data.get('from_cart'):
        # بازگشت به سبد خرید
        user_id = update.effective_user.id
        db = context.bot_data['db']
        cart = db.get_cart(user_id)
        
        if not cart:
            await query.edit_message_text("🛒 سبد خرید شما خالی است!")
            context.user_data.pop('from_cart', None)
            return
        
        text = "🛒 سبد خرید شما:\n\n"
        total_price = 0
        
        for item in cart:
            cart_id, product_name, pack_name, pack_qty, pack_price, item_qty = item
            
            unit_price = pack_price / pack_qty
            item_total = unit_price * item_qty
            total_price += item_total
            
            text += f"🏷 {product_name}\n"
            text += f"📦 {pack_name} ({item_qty} عدد)\n"
            text += f"💰 {item_total:,.0f} تومان\n\n"
        
        text += f"💳 جمع کل: {total_price:,.0f} تومان"
        
        from keyboards import cart_keyboard
        await query.edit_message_text(
            text,
            reply_markup=cart_keyboard(cart)
        )
        context.user_data.pop('from_cart', None)
    else:
        # بازگشت به منوی اصلی کاربر
        from keyboards import user_main_keyboard
        await query.message.delete()


async def use_credit_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """استفاده از اعتبار در سبد خرید"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    db = context.bot_data['db']
    
    # دریافت سبد خرید
    cart = db.get_cart(user_id)
    if not cart:
        await query.edit_message_text("سبد خرید شما خالی است!")
        return
    
    # محاسبه مجموع سبد
    total_price = 0
    for item in cart:
        cart_id, product_name, pack_name, pack_qty, pack_price, item_qty = item
        unit_price = pack_price / pack_qty
        item_total = unit_price * item_qty
        total_price += item_total
    
    # دریافت اعتبار
    permanent_balance = db.get_permanent_wallet(user_id)
    temp_wallets = db.get_active_temp_wallets(user_id)
    total_temp = sum([w[1] for w in temp_wallets])
    total_credit = permanent_balance + total_temp
    
    if total_credit == 0:
        await query.answer("⚠️ شما اعتباری ندارید!", show_alert=True)
        return
    
    # محاسبه مقدار قابل استفاده
    usable_credit = min(total_credit, total_price)
    
    # ذخیره در context
    context.user_data['applied_credit'] = usable_credit
    context.user_data['credit_discount_amount'] = usable_credit
    
    text = f"💳 **استفاده از اعتبار**\n\n"
    text += f"💰 اعتبار شما: {format_price(total_credit)} تومان\n"
    text += f"🛒 مجموع سبد: {format_price(total_price)} تومان\n\n"
    text += f"✅ مقدار استفاده شده: {format_price(usable_credit)} تومان\n"
    text += f"💳 مبلغ قابل پرداخت: {format_price(total_price - usable_credit)} تومان\n\n"
    text += "💡 اعتبار شما در هنگام نهایی کردن سفارش کسر می‌شود."
    
    from keyboards import cart_keyboard
    await query.edit_message_text(
        text,
        parse_mode='Markdown',
        reply_markup=cart_keyboard(cart)
    )

