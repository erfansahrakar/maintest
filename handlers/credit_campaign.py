"""
🎁 سیستم کمپین اعتباری پیشرفته
✨ قابلیت‌ها:
- اعطای گروهی اعتبار به کاربران با فیلترهای مختلف
- فیلتر بر اساس تاریخ ثبت فاکتور
- فیلتر بر اساس مبلغ خرید
- درصدی از مبلغ فاکتور به عنوان اعتبار
- تعیین تاریخ انقضا برای اعتبار
- پیش‌نمایش کاربران واجد شرایط قبل از اعطا
- گزارش کامل از کمپین
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

# ==================== States ====================
CAMPAIGN_START_DATE = 300
CAMPAIGN_END_DATE = 301
CAMPAIGN_MIN_AMOUNT = 302
CAMPAIGN_MAX_AMOUNT = 303
CAMPAIGN_CREDIT_PERCENT = 304
CAMPAIGN_CREDIT_EXPIRY = 305
CAMPAIGN_CONFIRM = 306

# ==================== توابع Helper ====================

def format_price(price: float) -> str:
    """فرمت کردن قیمت"""
    return f"{price:,.0f}".replace(',', '٬')

def parse_persian_date(date_str: str) -> datetime:
    """
    تبدیل تاریخ فارسی به datetime
    فرمت: 1403/12/15 یا 1403-12-15
    """
    from datetime import datetime
    import jdatetime
    
    date_str = date_str.strip().replace('/', '-')
    parts = date_str.split('-')
    
    if len(parts) != 3:
        raise ValueError("فرمت تاریخ باید 1403/12/15 باشه")
    
    year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
    j_date = jdatetime.date(year, month, day)
    g_date = j_date.togregorian()
    
    return datetime.combine(g_date, datetime.min.time())

def get_campaign_keyboard():
    """کیبورد منوی کمپین اعتباری"""
    keyboard = [
        [InlineKeyboardButton("🎁 ایجاد کمپین جدید", callback_data="campaign:new")],
        [InlineKeyboardButton("📊 لیست کمپین‌ها", callback_data="campaign:list")],
        [InlineKeyboardButton("🔙 بازگشت", callback_data="wallet_admin:menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==================== توابع اصلی ====================

async def campaign_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """منوی اصلی کمپین اعتباری"""
    query = update.callback_query if update.callback_query else None
    
    if query:
        await query.answer()
        message_func = query.message.reply_text
    else:
        message_func = update.message.reply_text
    
    text = "🎁 **سیستم کمپین اعتباری**\n\n"
    text += "از این بخش می‌توانید:\n\n"
    text += "✅ به دسته‌ای از کاربران یکجا اعتبار بدهید\n"
    text += "📅 فیلتر بر اساس تاریخ خرید\n"
    text += "💰 فیلتر بر اساس مبلغ خرید\n"
    text += "📊 درصدی از خرید به عنوان اعتبار\n"
    text += "⏰ تعیین تاریخ انقضا\n\n"
    text += "💡 **مثال کاربردی:**\n"
    text += "به همه کسایی که از 1 دی تا 15 دی\n"
    text += "بیشتر از 500 هزار تومان خرید کردن،\n"
    text += "10% خریدشون رو به صورت اعتبار 30 روزه بده!"
    
    await message_func(text, parse_mode='Markdown', reply_markup=get_campaign_keyboard())

async def campaign_new_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع ساخت کمپین جدید"""
    query = update.callback_query
    await query.answer()
    
    # ریست کردن اطلاعات کمپین قبلی
    context.user_data['campaign_data'] = {}
    
    from keyboards import cancel_keyboard
    
    text = "📅 **تاریخ شروع بازه**\n\n"
    text += "فاکتورهایی که از این تاریخ به بعد ثبت شدن رو در نظر بگیریم؟\n\n"
    text += "💡 فرمت: 1403/12/01\n"
    text += "یا بزن: `همه` برای تمام فاکتورها\n"
    text += "یا بزن: `امروز` برای امروز\n"
    text += "یا بزن: `هفته` برای هفته اخیر\n"
    text += "یا بزن: `ماه` برای ماه اخیر"
    
    await query.message.reply_text(
        text,
        parse_mode='Markdown',
        reply_markup=cancel_keyboard()
    )
    
    return CAMPAIGN_START_DATE

async def campaign_start_date_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت تاریخ شروع"""
    if update.message.text == "❌ لغو":
        await campaign_menu(update, context)
        return ConversationHandler.END
    
    text = update.message.text.strip()
    
    try:
        if text == "همه":
            start_date = datetime(2020, 1, 1)
        elif text == "امروز":
            start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        elif text == "هفته":
            start_date = datetime.now() - timedelta(days=7)
        elif text == "ماه":
            start_date = datetime.now() - timedelta(days=30)
        else:
            start_date = parse_persian_date(text)
        
        context.user_data['campaign_data']['start_date'] = start_date
        
        from keyboards import cancel_keyboard
        
        text = "📅 **تاریخ پایان بازه**\n\n"
        text += "فاکتورها تا چه تاریخی؟\n\n"
        text += "💡 فرمت: 1403/12/15\n"
        text += "یا بزن: `الان` برای الان\n"
        text += "یا بزن: `امروز` برای امروز"
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=cancel_keyboard()
        )
        
        return CAMPAIGN_END_DATE
    
    except Exception as e:
        await update.message.reply_text(
            f"❌ خطا در تاریخ!\n\n{str(e)}\n\n"
            "لطفاً دوباره وارد کنید:"
        )
        return CAMPAIGN_START_DATE

async def campaign_end_date_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت تاریخ پایان"""
    if update.message.text == "❌ لغو":
        await campaign_menu(update, context)
        return ConversationHandler.END
    
    text = update.message.text.strip()
    
    try:
        if text == "الان" or text == "امروز":
            end_date = datetime.now()
        else:
            end_date = parse_persian_date(text)
            end_date = end_date.replace(hour=23, minute=59, second=59)
        
        start_date = context.user_data['campaign_data']['start_date']
        
        if end_date <= start_date:
            await update.message.reply_text(
                "❌ تاریخ پایان باید بعد از تاریخ شروع باشه!\n"
                "لطفاً دوباره وارد کنید:"
            )
            return CAMPAIGN_END_DATE
        
        context.user_data['campaign_data']['end_date'] = end_date
        
        from keyboards import cancel_keyboard
        
        text = "💰 **حداقل مبلغ خرید**\n\n"
        text += "فقط فاکتورهایی که حداقل چقدر باشن؟\n\n"
        text += "💡 مثال: 500000 (پانصد هزار تومان)\n"
        text += "یا بزن: `0` برای همه مبالغ"
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=cancel_keyboard()
        )
        
        return CAMPAIGN_MIN_AMOUNT
    
    except Exception as e:
        await update.message.reply_text(
            f"❌ خطا در تاریخ!\n\n{str(e)}\n\n"
            "لطفاً دوباره وارد کنید:"
        )
        return CAMPAIGN_END_DATE

async def campaign_min_amount_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت حداقل مبلغ"""
    if update.message.text == "❌ لغو":
        await campaign_menu(update, context)
        return ConversationHandler.END
    
    try:
        min_amount = float(update.message.text.strip().replace(',', ''))
        
        if min_amount < 0:
            await update.message.reply_text("❌ مبلغ نمی‌تونه منفی باشه!")
            return CAMPAIGN_MIN_AMOUNT
        
        context.user_data['campaign_data']['min_amount'] = min_amount
        
        from keyboards import cancel_keyboard
        
        text = "💰 **حداکثر مبلغ خرید**\n\n"
        text += "فقط فاکتورهایی که حداکثر چقدر باشن؟\n\n"
        text += "💡 مثال: 2000000 (دو میلیون تومان)\n"
        text += "یا بزن: `0` برای نامحدود"
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=cancel_keyboard()
        )
        
        return CAMPAIGN_MAX_AMOUNT
    
    except ValueError:
        await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کنید!")
        return CAMPAIGN_MIN_AMOUNT

async def campaign_max_amount_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت حداکثر مبلغ"""
    if update.message.text == "❌ لغو":
        await campaign_menu(update, context)
        return ConversationHandler.END
    
    try:
        max_amount = float(update.message.text.strip().replace(',', ''))
        
        if max_amount < 0:
            await update.message.reply_text("❌ مبلغ نمی‌تونه منفی باشه!")
            return CAMPAIGN_MAX_AMOUNT
        
        min_amount = context.user_data['campaign_data']['min_amount']
        
        if max_amount > 0 and max_amount < min_amount:
            await update.message.reply_text(
                "❌ حداکثر باید بیشتر از حداقل باشه!"
            )
            return CAMPAIGN_MAX_AMOUNT
        
        context.user_data['campaign_data']['max_amount'] = max_amount if max_amount > 0 else None
        
        from keyboards import cancel_keyboard
        
        text = "📊 **درصد اعتبار**\n\n"
        text += "چند درصد مبلغ فاکتور به عنوان اعتبار بدیم؟\n\n"
        text += "💡 مثال:\n"
        text += "• 10 → 10% مبلغ فاکتور\n"
        text += "• 5 → 5% مبلغ فاکتور\n"
        text += "• 100 → کل مبلغ فاکتور!\n\n"
        text += "عدد بین 1 تا 100 وارد کنید:"
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=cancel_keyboard()
        )
        
        return CAMPAIGN_CREDIT_PERCENT
    
    except ValueError:
        await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کنید!")
        return CAMPAIGN_MAX_AMOUNT

async def campaign_credit_percent_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت درصد اعتبار"""
    if update.message.text == "❌ لغو":
        await campaign_menu(update, context)
        return ConversationHandler.END
    
    try:
        percent = float(update.message.text.strip())
        
        if percent <= 0 or percent > 100:
            await update.message.reply_text("❌ درصد باید بین 1 تا 100 باشه!")
            return CAMPAIGN_CREDIT_PERCENT
        
        context.user_data['campaign_data']['credit_percent'] = percent
        
        from keyboards import cancel_keyboard
        
        text = "⏰ **مدت اعتبار**\n\n"
        text += "این اعتبار چند روز اعتبار داشته باشه؟\n\n"
        text += "💡 مثال:\n"
        text += "• 30 → 30 روز\n"
        text += "• 60 → دو ماه\n"
        text += "• 0 → بدون انقضا (دائمی)\n\n"
        text += "عدد وارد کنید:"
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=cancel_keyboard()
        )
        
        return CAMPAIGN_CREDIT_EXPIRY
    
    except ValueError:
        await update.message.reply_text("❌ لطفاً یک عدد معتبر وارد کنید!")
        return CAMPAIGN_CREDIT_PERCENT

async def campaign_credit_expiry_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت مدت اعتبار و نمایش پیش‌نمایش"""
    if update.message.text == "❌ لغو":
        await campaign_menu(update, context)
        return ConversationHandler.END
    
    try:
        expiry_days = int(update.message.text.strip())
        
        if expiry_days < 0:
            await update.message.reply_text("❌ تعداد روز نمی‌تونه منفی باشه!")
            return CAMPAIGN_CREDIT_EXPIRY
        
        context.user_data['campaign_data']['expiry_days'] = expiry_days
        
        # محاسبه کاربران واجد شرایط
        db = context.bot_data['db']
        campaign = context.user_data['campaign_data']
        
        eligible_users = get_eligible_users(db, campaign)
        
        if not eligible_users:
            await update.message.reply_text(
                "⚠️ **هیچ کاربری واجد شرایط نیست!**\n\n"
                "با این فیلترها هیچ فاکتوری پیدا نشد.\n"
                "لطفاً دوباره تلاش کنید.",
                reply_markup=get_campaign_keyboard()
            )
            return ConversationHandler.END
        
        # نمایش پیش‌نمایش
        import jdatetime
        
        start_j = jdatetime.datetime.fromgregorian(datetime=campaign['start_date'])
        end_j = jdatetime.datetime.fromgregorian(datetime=campaign['end_date'])
        
        text = "📊 **پیش‌نمایش کمپین**\n\n"
        text += "🎯 **فیلترهای اعمال شده:**\n\n"
        text += f"📅 بازه زمانی: {start_j.strftime('%Y/%m/%d')} تا {end_j.strftime('%Y/%m/%d')}\n"
        text += f"💰 حداقل مبلغ: {format_price(campaign['min_amount'])} تومان\n"
        
        if campaign.get('max_amount'):
            text += f"💰 حداکثر مبلغ: {format_price(campaign['max_amount'])} تومان\n"
        
        text += f"📊 درصد اعتبار: {campaign['credit_percent']}%\n"
        
        if expiry_days > 0:
            text += f"⏰ اعتبار: {expiry_days} روزه\n"
        else:
            text += f"⏰ اعتبار: دائمی\n"
        
        text += f"\n✅ **کاربران واجد شرایط: {len(eligible_users)} نفر**\n\n"
        
        total_credit = 0
        for user_data in eligible_users[:5]:  # نمایش 5 نفر اول
            user_id, total_orders, credit_amount = user_data
            total_credit += credit_amount
            text += f"• کاربر {user_id}: {format_price(credit_amount)} تومان\n"
        
        if len(eligible_users) > 5:
            text += f"\n... و {len(eligible_users) - 5} نفر دیگر\n"
        
        text += f"\n💵 **جمع کل اعتبار: {format_price(total_credit)} تومان**\n\n"
        text += "آیا مطمئنید می‌خواهید این کمپین را اجرا کنید؟"
        
        keyboard = [
            [
                InlineKeyboardButton("✅ بله، اجرا کن", callback_data="campaign:confirm"),
                InlineKeyboardButton("❌ خیر، لغو", callback_data="campaign:cancel")
            ]
        ]
        
        await update.message.reply_text(
            text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        
        return CAMPAIGN_CONFIRM
    
    except ValueError:
        await update.message.reply_text("❌ لطفاً یک عدد صحیح وارد کنید!")
        return CAMPAIGN_CREDIT_EXPIRY

def get_eligible_users(db, campaign):
    """
    پیدا کردن کاربران واجد شرایط
    Returns: List[(user_id, total_orders_amount, credit_amount)]
    """
    start_date = campaign['start_date']
    end_date = campaign['end_date']
    min_amount = campaign['min_amount']
    max_amount = campaign.get('max_amount')
    credit_percent = campaign['credit_percent'] / 100
    
    query = """
        SELECT 
            user_id,
            SUM(final_price) as total_amount
        FROM orders
        WHERE created_at >= ? AND created_at <= ?
        AND status = 'confirmed'
        AND final_price >= ?
    """
    
    params = [start_date, end_date, min_amount]
    
    if max_amount:
        query += " AND final_price <= ?"
        params.append(max_amount)
    
    query += " GROUP BY user_id"
    
    cursor = db.conn.cursor()
    cursor.execute(query, params)
    results = cursor.fetchall()
    
    eligible_users = []
    for user_id, total_amount in results:
        credit_amount = total_amount * credit_percent
        eligible_users.append((user_id, total_amount, credit_amount))
    
    return eligible_users

async def campaign_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تایید و اجرای کمپین"""
    query = update.callback_query
    await query.answer()
    
    await query.message.reply_text("⏳ در حال اجرای کمپین...")
    
    db = context.bot_data['db']
    campaign = context.user_data['campaign_data']
    
    eligible_users = get_eligible_users(db, campaign)
    expiry_days = campaign['expiry_days']
    
    success_count = 0
    total_credit = 0
    
    for user_id, total_orders, credit_amount in eligible_users:
        try:
            # افزودن اعتبار
            if expiry_days > 0:
                # اعتبار موقت
                expiry_date = datetime.now() + timedelta(days=expiry_days)
                db.add_wallet_credit(user_id, credit_amount, expiry_date=expiry_date, credit_type='campaign')
            else:
                # اعتبار دائمی
                db.add_wallet_credit(user_id, credit_amount, credit_type='campaign')
            
            success_count += 1
            total_credit += credit_amount
            
            # ارسال نوتیف به کاربر
            try:
                expiry_text = f"{expiry_days} روزه" if expiry_days > 0 else "دائمی"
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"🎉 **تبریک!**\n\n"
                         f"شما {format_price(credit_amount)} تومان اعتبار {expiry_text} دریافت کردید!\n\n"
                         f"این اعتبار بابت خریدهای شما در کمپین ویژه اعطا شده است.\n\n"
                         f"💰 موجودی شما: {format_price(db.get_wallet_balance(user_id))} تومان",
                    parse_mode='Markdown'
                )
            except:
                pass
        
        except Exception as e:
            logger.error(f"خطا در اعطای اعتبار به {user_id}: {e}")
    
    # گزارش نهایی
    text = f"✅ **کمپین با موفقیت اجرا شد!**\n\n"
    text += f"👥 تعداد کاربران: {success_count} نفر\n"
    text += f"💵 جمع اعتبار اعطا شده: {format_price(total_credit)} تومان\n\n"
    text += f"📊 میانگین اعتبار هر نفر: {format_price(total_credit/success_count if success_count > 0 else 0)} تومان"
    
    await query.message.reply_text(
        text,
        parse_mode='Markdown',
        reply_markup=get_campaign_keyboard()
    )
    
    # پاک کردن داده‌های کمپین
    context.user_data.pop('campaign_data', None)
    
    return ConversationHandler.END

async def campaign_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """لغو کمپین"""
    query = update.callback_query
    await query.answer()
    
    await query.message.reply_text(
        "❌ کمپین لغو شد.",
        reply_markup=get_campaign_keyboard()
    )
    
    context.user_data.pop('campaign_data', None)
    
    return ConversationHandler.END
