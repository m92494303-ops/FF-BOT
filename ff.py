import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.filters import CommandStart
from aiogram.exceptions import TelegramForbiddenError
from functools import wraps

TOKEN = "8432697594:AAFeIMSAAAuoKCVONYPF7Y91lhYER080R-Q"
CHANNELS = [
    "@azimboyev_blog",
    "@CyberLearnUz"
    "@comment_bIog"
]
ADMIN_ID = 7815632054

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_data = {}

# ================= DB =================
db = sqlite3.connect("bot.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS stats (
    key TEXT PRIMARY KEY,
    value INTEGER
)
""")

cursor.execute("INSERT OR IGNORE INTO stats VALUES ('auto_calc', 0)")
db.commit()


def save_user(user_id: int):
    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id) VALUES (?)",
        (user_id,)
    )
    db.commit()


@dp.message(F.from_user.id == ADMIN_ID, F.text == "/admin")
async def admin_panel(message: Message):
    await safe_send(
        message.answer,
        "👑 *ADMIN PANEL*\n\n"
        "📊 /stats – Statistika\n"
        "📨 /xabar <matn> – Hammaga xabar\n",
        parse_mode="Markdown"
    )



def get_all_users():
    cursor.execute("SELECT user_id FROM users")
    return [row[0] for row in cursor.fetchall()]


def inc_stat(key: str):
    cursor.execute(
        "UPDATE stats SET value = value + 1 WHERE key=?",
        (key,)
    )
    db.commit()


def get_stat(key):
    cursor.execute("SELECT value FROM stats WHERE key=?", (key,))
    return cursor.fetchone()[0]


def get_users_count():
    cursor.execute("SELECT COUNT(*) FROM users")
    return cursor.fetchone()[0]


# ================= SAFE SEND =================
async def safe_send(func, *args, **kwargs):
    try:
        return await func(*args, **kwargs)
    except TelegramForbiddenError:
        return


# ================= SUB CHECK =================
async def check_sub(user_id: int):
    try:
        for channel in CHANNELS:
            member = await bot.get_chat_member(channel, user_id)
            if member.status not in ["member", "administrator", "creator"]:
                return False
        return True
    except:
        return False



def subscription_required(handler):
    @wraps(handler)
    async def wrapper(event, *args, **kwargs):
        user_id = event.from_user.id
        if not await check_sub(user_id):
            if isinstance(event, Message):
                await safe_send(
                    event.answer,
                    "❌ Kanalga obuna bo‘lmagansiz!",
                    reply_markup=sub_menu()
                )
            elif isinstance(event, CallbackQuery):
                await safe_send(
                    event.message.edit_text,
                    "❌ Kanalga obuna bo‘lmagansiz!",
                    reply_markup=sub_menu()
                )
            return
        return await handler(event, *args, **kwargs)
    return wrapper


# ================= LOGIC =================
def auto_calc_sens(ram: int, dpi: int, fps: int):
    base = 180
    if ram <= 3: base -= 15
    elif ram >= 6: base += 10
    if dpi <= 320: base += 10
    elif dpi == 400: base -= 10
    elif dpi >= 440: base -= 20
    if fps <= 30: base -= 15
    elif fps >= 60: base += 10
    base = max(120, min(200, base))
    return {
        "General": base,
        "Red Dot": base - 10,
        "2x": base - 20,
        "4x": base - 35,
        "AWM": base - 55,
        "Free Look": base - 30
    }


# ================= MENUS =================
def sub_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 1-kanalga obuna", url="https://t.me/azimboyev_blog")],
        [InlineKeyboardButton(text="📢 2-kanalga obuna", url="https://t.me/CyberLearnUz")],
        [InlineKeyboardButton(text="📢 3-kanalga obuna", url="https://t.me/comment_bIog")],
        [InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")]
    ])



def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 AUTO SENSITIVITY", callback_data="auto")]
    ])


def ram_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 2–3GB RAM", callback_data="ram_3")],
        [InlineKeyboardButton(text="📱 4GB RAM", callback_data="ram_4")],
        [InlineKeyboardButton(text="📱 6–8GB RAM", callback_data="ram_6")]
    ])


def dpi_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="320 DPI", callback_data="dpi_320")],
        [InlineKeyboardButton(text="360 DPI", callback_data="dpi_360")],
        [InlineKeyboardButton(text="400 DPI", callback_data="dpi_400")],
        [InlineKeyboardButton(text="440 DPI", callback_data="dpi_440")]
    ])


def fps_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="30 FPS", callback_data="fps_30")],
        [InlineKeyboardButton(text="45 FPS", callback_data="fps_45")],
        [InlineKeyboardButton(text="60 FPS", callback_data="fps_60")]
    ])


# ================= HANDLERS =================
@dp.message(CommandStart())
async def start(message: Message):
    save_user(message.from_user.id)

    if not await check_sub(message.from_user.id):
        await safe_send(message.answer, "❌ Obuna bo‘ling!", reply_markup=sub_menu())
        return

    await safe_send(
        message.answer,
        "🔥 *FF PRO Settings*\n\n🎯 AUTO-CALC tizimga xush kelibsiz!",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )


@dp.callback_query(F.data == "check_sub")
async def recheck(callback: CallbackQuery):
    if await check_sub(callback.from_user.id):
        await safe_send(callback.message.edit_text, "✅ Obuna tasdiqlandi!", reply_markup=main_menu())
    else:
        await callback.answer("❌ Hali obuna emassiz!", show_alert=True)


@dp.callback_query(F.data == "auto")
@subscription_required
async def auto_start(callback: CallbackQuery):
    user_data[callback.from_user.id] = {}
    await safe_send(callback.message.edit_text, "📱 RAM tanlang:", reply_markup=ram_menu())


@dp.callback_query(F.data.startswith("ram_"))
@subscription_required
async def set_ram(callback: CallbackQuery):
    user_data[callback.from_user.id]["ram"] = int(callback.data.split("_")[1])
    await safe_send(callback.message.edit_text, "🧩 DPI tanlang:", reply_markup=dpi_menu())


@dp.callback_query(F.data.startswith("dpi_"))
@subscription_required
async def set_dpi(callback: CallbackQuery):
    user_data[callback.from_user.id]["dpi"] = int(callback.data.split("_")[1])
    await safe_send(callback.message.edit_text, "⚡ FPS tanlang:", reply_markup=fps_menu())


@dp.callback_query(F.data.startswith("fps_"))
@subscription_required
async def set_fps(callback: CallbackQuery):
    fps = int(callback.data.split("_")[1])
    data = user_data[callback.from_user.id]
    sens = auto_calc_sens(data["ram"], data["dpi"], fps)
    inc_stat("auto_calc")

    text = (
        "🎯 *AUTO-CALC SENSITIVITY*\n\n"
        f"RAM: {data['ram']}GB\nDPI: {data['dpi']}\nFPS: {fps}\n\n"
        f"General: {sens['General']}\n"
        f"Red Dot: {sens['Red Dot']}\n"
        f"2x: {sens['2x']}\n"
        f"4x: {sens['4x']}\n"
        f"AWM: {sens['AWM']}\n"
        f"Free Look: {sens['Free Look']}"
    )

    await safe_send(callback.message.edit_text, text, parse_mode="Markdown")


# ================= ADMIN =================
@dp.message(F.from_user.id == ADMIN_ID, F.text.startswith("/xabar"))
async def admin_broadcast(message: Message):
    text = message.text.replace("/xabar", "").strip()
    if not text:
        await safe_send(message.answer, "❌ Xabar yozing!\n/xabar Salom")
        return

    users = get_all_users()
    sent = blocked = 0

    for uid in users:
        try:
            await bot.send_message(uid, text)
            sent += 1
            await asyncio.sleep(0.05)
        except TelegramForbiddenError:
            blocked += 1
            cursor.execute("DELETE FROM users WHERE user_id=?", (uid,))
            db.commit()

    await safe_send(
        message.answer,
        f"✅ Yuborildi: {sent}\n⛔ Block: {blocked}"
    )


@dp.message(F.from_user.id == ADMIN_ID, F.text == "/stats")
async def admin_stats(message: Message):
    await safe_send(
        message.answer,
        f"👥 Userlar: {get_users_count()}\n🎯 Auto-calc: {get_stat('auto_calc')}"
    )


# ================= RUN =================
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
