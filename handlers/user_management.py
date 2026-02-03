"""
مدیریت اطلاعات کاربران برای ادمین
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

async def view_users_list(update: Update, context: ContextTypes.DEFAULT_TYPE, page: int = 0):
    """نمایش لیست کاربران با pagination"""
    query = update.callback_query if update.callback_query else None
    
    if query:
        await query.answer()
        message_func = query.edit_message_text
    else:
        message_func = update.message.reply_text
    
    db = context.bot_data['db']
    all_users = db.get_all_users()
    
    if not all_users:
        await message_func("👥 هیچ کاربری در ربات ثبت نشده است.")
        return
    
    # تنظیمات pagination
    USERS_PER_PAGE = 5
    total_users = len(all_users)
    total_pages = (total_users + USERS_PER_PAGE - 1) // USERS_PER_PAGE
    
    if page >= total_pages:
        page = total_pages - 1
    if page < 0:
        page = 0
    
    start_idx = page * USERS_PER_PAGE
    end_idx = min(start_idx + USERS_PER_PAGE, total_users)
    
    users_on_page = all_users[start_idx:end_idx]
    
    text = f"👥 **لیست کاربران** (صفحه {page + 1} از {total_pages})\n\n"
    text += f"📊 کل کاربران: {total_users}\n\n"
    text += "━━━━━━━━━━━━━━━━\n\n"
    
    for idx, user in enumerate(users_on_page, start=start_idx + 1):
        user_id, username, first_name, full_name, phone, _, address, shop_name, created_at = user
        
        text += f"**{idx}. کاربر**\n"
        text += f"🆔 ID: `{user_id}`\n"
        text += f"👤 نام: {first_name or 'نامشخص'}\n"
        
        if full_name:
            text += f"📝 نام کامل: {full_name}\n"
        
        if username:
            text += f"🔗 @{username}\n"
        else:
            text += f"🔗 بدون یوزرنیم\n"
        
        if shop_name:
            text += f"🏪 فروشگاه: {shop_name}\n"
        
        if phone:
            text += f"📱 تلفن: {phone}\n"
        
        if address:
            text += f"📍 آدرس: {address[:50]}...\n" if len(address) > 50 else f"📍 آدرس: {address}\n"
        
        # لینک چت (فقط برای کاربران بدون username)
        if not username:
            text += f"💬 [ارسال پیام](tg://user?id={user_id})\n"
        
        text += "\n"
    
    # ساخت کیبورد pagination
    keyboard = []
    nav_buttons = []
    
    if page > 0:
        nav_buttons.append(InlineKeyboardButton("◀️ قبلی", callback_data=f"users_page:{page - 1}"))
    
    nav_buttons.append(InlineKeyboardButton(f"📄 {page + 1}/{total_pages}", callback_data="users_page:current"))
    
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton("بعدی ▶️", callback_data=f"users_page:{page + 1}"))
    
    keyboard.append(nav_buttons)
    keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="admin_back")])
    
    await message_func(
        text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard),
        disable_web_page_preview=True
    )


async def handle_users_pagination(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت pagination کاربران"""
    query = update.callback_query
    await query.answer()
    
    page_data = query.data.split(":")
    if len(page_data) < 2:
        return
    
    if page_data[1] == "current":
        return
    
    try:
        page = int(page_data[1])
        await view_users_list(update, context, page)
    except ValueError:
        await query.answer("❌ خطا در صفحه‌بندی!")
