import asyncio
import sqlite3
from functools import wraps
from typing import List

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    LabeledPrice, PreCheckoutQuery, Update
)
from aiogram.filters import CommandStart
from aiogram.client.default import DefaultBotProperties

from fastapi import FastAPI, Request
import uvicorn

# ================== CONFIG ==================
TOKEN = "8432697594:AAFeIMSAAAuoKCVONYPF7Y91lhYER080R-Q"

WEBHOOK_URL = "ff-bot-production.up.railway.app"  # 🔴 SHUNI ALMASHTIR
WEBHOOK_PATH = "/webhook"

ADMIN_ID = 7815632054

REQUIRED_CHATS = [
    "@azimboyev_blog",
    "@CyberLearnUz",
    "@comment_bIog"
]

# ================== BOT =====================
bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode="Markdown")
)
dp = Dispatcher()
app = FastAPI()

# ================== DATABASE =================
db = sqlite3.connect("bot.db", check_same_thread=False)
cur = db.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
cur.execute("CREATE TABLE IF NOT EXISTS vip (user_id INTEGER PRIMARY KEY)")
cur.execute("CREATE TABLE IF NOT EXISTS bans (user_id INTEGER PRIMARY KEY)")
db.commit()

# ================== UTILS ===================
def save_user(uid: int):
    cur.execute("INSERT OR IGNORE INTO users VALUES (?)", (uid,))
    db.commit()

def is_vip(uid: int) -> bool:
    cur.execute("SELECT 1 FROM vip WHERE user_id=?", (uid,))
    return cur.fetchone() is not None

def is_banned(uid: int) -> bool:
    cur.execute("SELECT 1 FROM bans WHERE user_id=?", (uid,))
    return cur.fetchone() is not None

def ban(uid: int):
    cur.execute("INSERT OR IGNORE INTO bans VALUES (?)", (uid,))
    db.commit()

def unban(uid: int):
    cur.execute("DELETE FROM bans WHERE user_id=?", (uid,))
    db.commit()

# ================== SUB CHECK =================
async def check_sub(uid: int) -> List[str]:
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
            ban(uid)
            text = (
                "❌ *Siz kanaldan chiqqaningiz uchun BAN oldingiz*\n\n"
                "📢 Qayta obuna bo‘ling:\n" +
                "\n".join(f"• {c}" for c in not_joined) +
                "\n\n✅ Obuna bo‘lgach *Tekshirish* ni bosing"
            )
            if isinstance(event, CallbackQuery):
                await event.message.edit_text(text, reply_markup=sub_menu())
            else:
                await event.answer(text, reply_markup=sub_menu())
            return

        if is_banned(uid):
            unban(uid)
            if isinstance(event, CallbackQuery):
                await event.answer("✅ Tasdiqlandi\n🔓 *BANDAN CHIQDINGIZ*", show_alert=True)

        return await handler(event, *args, **kwargs)
    return wrapper

# ================== MENUS ====================
def sub_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Kanal 1", url="https://t.me/azimboyev_blog")],
        [InlineKeyboardButton(text="📢 Kanal 2", url="https://t.me/CyberLearnUz")],
        [InlineKeyboardButton(text="💬 Guruh", url="https://t.me/comment_bIog")],
        [InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")]
    ])

def main_menu(uid: int):
    kb = [[InlineKeyboardButton(text="🎯 AUTO SENSITIVITY", callback_data="auto")]]
    if is_vip(uid):
        kb.append([InlineKeyboardButton(text="🔥 VIP EXTREME HS", callback_data="vip_extreme")])
    else:
        kb.append([InlineKeyboardButton(text="⭐ VIP PRO (5⭐)", callback_data="vip_buy")])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def back_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back", callback_data="back")]
    ])

# ================== TEXT =====================
AUTO_TEXT = (
    "🎯 *AUTO SENSITIVITY (FREE)*\n\n"
    "🎯 ~80% HEADSHOT\n\n"
    "General: 170\nRed Dot: 165\n2x: 150\n4x: 130\nAWM: 110"
)

VIP_TEXT = (
    "🔥 *VIP EXTREME HEADSHOT (PRO)*\n\n"
    "🎯 ~95% HEADSHOT\n\n"
    "General: 195\nRed Dot: 190\n2x: 175\n4x: 150\nAWM: 130"
)

# ================== HANDLERS =================
@dp.message(CommandStart())
async def start(msg: Message):
    save_user(msg.from_user.id)
    if not await check_sub(msg.from_user.id):
        await msg.answer("🔥 *FF PRO SETTINGS*", reply_markup=main_menu(msg.from_user.id))
    else:
        await msg.answer("❌ Avval obuna bo‘ling", reply_markup=sub_menu())

@dp.callback_query(F.data == "check_sub")
async def check_sub_btn(cb: CallbackQuery):
    uid = cb.from_user.id
    if not await check_sub(uid):
        unban(uid)
        await cb.message.edit_text("🔥 *FF PRO SETTINGS*", reply_markup=main_menu(uid))
    else:
        await cb.answer("❌ Hali obuna to‘liq emas", show_alert=True)

@dp.callback_query(F.data == "auto")
@subscription_required
async def auto(cb: CallbackQuery):
    await cb.message.edit_text(AUTO_TEXT, reply_markup=back_menu())

@dp.callback_query(F.data == "vip_extreme")
@subscription_required
async def vip_extreme(cb: CallbackQuery):
    if not is_vip(cb.from_user.id):
        await cb.answer("❌ Siz VIP emassiz", show_alert=True)
        return
    await cb.message.edit_text(VIP_TEXT, reply_markup=back_menu())

# ================== WEBHOOK ==================
@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL + WEBHOOK_PATH)

@app.post(WEBHOOK_PATH)
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update(**data)
    await dp.feed_update(bot, update)
    return {"ok": True}

# ================== RUN ======================
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
