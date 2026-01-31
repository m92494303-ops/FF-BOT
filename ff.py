import asyncio
import os
import sqlite3
from functools import wraps

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.filters import CommandStart
from aiogram.exceptions import TelegramForbiddenError

# ================= CONFIG =================
TOKEN = os.getenv("8432697594:AAFeIMSAAAuoKCVONYPF7Y91lhYER080R-Q")  # BOT_TOKEN
ADMIN_ID = 7815632054

REQUIRED_CHATS = [
    "@azimboyev_blog",
    "@CyberLearnUz",
    "@comment_bIog"
]

bot = Bot(token=TOKEN, parse_mode="Markdown")
dp = Dispatcher()

# ================= DATABASE =================
db = sqlite3.connect("./bot.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
cursor.execute("CREATE TABLE IF NOT EXISTS bans (user_id INTEGER PRIMARY KEY)")
cursor.execute("CREATE TABLE IF NOT EXISTS vip (user_id INTEGER PRIMARY KEY)")
db.commit()

# ================= UTILS =================
def save_user(uid):
    cursor.execute("INSERT OR IGNORE INTO users VALUES (?)", (uid,))
    db.commit()

def is_banned(uid):
    cursor.execute("SELECT 1 FROM bans WHERE user_id=?", (uid,))
    return cursor.fetchone() is not None

def is_vip(uid):
    cursor.execute("SELECT 1 FROM vip WHERE user_id=?", (uid,))
    return cursor.fetchone() is not None

async def safe_send(func, *args, **kwargs):
    try:
        return await func(*args, **kwargs)
    except TelegramForbiddenError:
        return

# ================= SUB CHECK =================
async def check_sub(uid):
    not_joined = []
    for chat in REQUIRED_CHATS:
        try:
            m = await bot.get_chat_member(chat, uid)
            if m.status in ("left", "kicked"):
                not_joined.append(chat)
        except:
            not_joined.append(chat)
    return not_joined

def subscription_required(handler):
    @wraps(handler)
    async def wrapper(event, *args, **kwargs):
        uid = event.from_user.id
        not_joined = await check_sub(uid)

        if not_joined:
            text = (
                "❌ *Avval obuna bo‘ling:*\n\n" +
                "\n".join(f"• {c}" for c in not_joined)
            )
            if isinstance(event, CallbackQuery):
                await safe_send(event.message.edit_text, text, reply_markup=sub_menu())
            else:
                await event.answer(text, reply_markup=sub_menu())
            return
        return await handler(event, *args, **kwargs)
    return wrapper

# ================= MENUS =================
def sub_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("📢 Kanal 1", url="https://t.me/azimboyev_blog")],
        [InlineKeyboardButton("📢 Kanal 2", url="https://t.me/CyberLearnUz")],
        [InlineKeyboardButton("💬 Guruh", url="https://t.me/comment_bIog")],
        [InlineKeyboardButton("🔄 Tekshirish", callback_data="back")]
    ])

def main_menu(uid):
    kb = [
        [InlineKeyboardButton("🎯 AUTO SENSITIVITY", callback_data="auto")]
    ]
    if is_vip(uid):
        kb.append([InlineKeyboardButton("🔥 VIP EXTREME HS", callback_data="vip_extreme")])
    else:
        kb.append([InlineKeyboardButton("⭐ VIP PRO", callback_data="vip_info")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def back_menu(uid):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ])

def admin_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("📊 VIP statistikasi", callback_data="admin_vip_stats")]
    ])

# ================= TEXT =================
AUTO_TEXT = (
    "🎯 *AUTO SENSITIVITY*\n\n"
    "General: 182\nRed Dot: 176\n2x: 162\n4x: 138\nAWM: 118\n\n"
    "🔥 200 MAX HS"
)

VIP_TEXT = (
    "🔥 *VIP EXTREME HEADSHOT*\n\n"
    "General: 188\nRed Dot: 182\n2x: 168\n4x: 142\nAWM: 120\n\n"
    "⚡ PRO ONLY"
)

VIP_INFO = (
    "⭐ *VIP PRO*\n\n"
    "VIP faqat *ADMIN* orqali beriladi.\n"
    "Agar sotib olmoqchi bo‘lsangiz — admin bilan bog‘laning."
)

# ================= START =================
@dp.message(CommandStart())
async def start(msg: Message):
    save_user(msg.from_user.id)
    if not await check_sub(msg.from_user.id):
        await msg.answer("🔥 *FF PRO SETTINGS*", reply_markup=main_menu(msg.from_user.id))
    else:
        await msg.answer("❌ Avval obuna bo‘ling", reply_markup=sub_menu())

# ================= NAV =================
@dp.callback_query(F.data == "back")
async def back(cb: CallbackQuery):
    await cb.message.edit_text(
        "🔥 *FF PRO SETTINGS*",
        reply_markup=main_menu(cb.from_user.id)
    )

# ================= AUTO =================
@dp.callback_query(F.data == "auto")
@subscription_required
async def auto(cb: CallbackQuery):
    await cb.message.edit_text(
        AUTO_TEXT,
        reply_markup=back_menu(cb.from_user.id)
    )

# ================= VIP INFO =================
@dp.callback_query(F.data == "vip_info")
@subscription_required
async def vip_info(cb: CallbackQuery):
    await cb.message.edit_text(
        VIP_INFO,
        reply_markup=back_menu(cb.from_user.id)
    )

# ================= VIP ONLY =================
@dp.callback_query(F.data == "vip_extreme")
@subscription_required
async def vip_only(cb: CallbackQuery):
    if not is_vip(cb.from_user.id):
        await cb.answer("❌ Siz VIP emassiz", show_alert=True)
        return
    await cb.message.edit_text(
        VIP_TEXT,
        reply_markup=back_menu(cb.from_user.id)
    )

# ================= ADMIN =================
@dp.message(F.from_user.id == ADMIN_ID, F.text == "/admin")
async def admin(msg: Message):
    await msg.answer("👑 *ADMIN PANEL*", reply_markup=admin_menu())

@dp.callback_query(F.data == "admin_vip_stats", F.from_user.id == ADMIN_ID)
async def vip_stats(cb: CallbackQuery):
    cursor.execute("SELECT COUNT(*) FROM vip")
    v = cursor.fetchone()[0]
    await cb.message.answer(f"⭐ VIP userlar: {v}")

# ================= ADMIN COMMANDS =================
@dp.message(F.from_user.id == ADMIN_ID, F.text.startswith("/addvip"))
async def add_vip(msg: Message):
    parts = msg.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await msg.answer("❌ Foydalanish: `/addvip user_id`")
        return
    uid = int(parts[1])
    cursor.execute("INSERT OR IGNORE INTO vip VALUES (?)", (uid,))
    db.commit()
    await msg.answer(f"✅ VIP berildi: `{uid}`")

@dp.message(F.from_user.id == ADMIN_ID, F.text.startswith("/delvip"))
async def del_vip(msg: Message):
    parts = msg.text.split()
    if len(parts) != 2 or not parts[1].isdigit():
        await msg.answer("❌ Foydalanish: `/delvip user_id`")
        return
    uid = int(parts[1])
    cursor.execute("DELETE FROM vip WHERE user_id=?", (uid,))
    db.commit()
    await msg.answer(f"🗑 VIP olib tashlandi: `{uid}`")

# ================= RUN =================
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
