import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.exceptions import TelegramForbiddenError
from functools import wraps

TOKEN = "8432697594:AAFeIMSAAAuoKCVONYPF7Y91lhYER080R-Q"
ADMIN_ID = 7815632054
PROMO_CODE = "FFPRO"

CHANNELS = [
    "@azimboyev_blog",
    "@CyberLearnUz",
    "@comment_bIog"
]

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_data = {}

# ================= DATABASE =================
db = sqlite3.connect("bot.db")
cursor = db.cursor()

cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
cursor.execute("CREATE TABLE IF NOT EXISTS bans (user_id INTEGER PRIMARY KEY)")

cursor.execute("""
CREATE TABLE IF NOT EXISTS profiles (
    user_id INTEGER PRIMARY KEY,
    uses INTEGER DEFAULT 0,
    promo_used INTEGER DEFAULT 0,
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 1
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    ram INTEGER,
    dpi INTEGER,
    fps INTEGER,
    date TEXT
)
""")

db.commit()

# ================= UTILS =================
def save_user(uid):
    cursor.execute("INSERT OR IGNORE INTO users VALUES (?)", (uid,))
    cursor.execute("INSERT OR IGNORE INTO profiles (user_id) VALUES (?)", (uid,))
    db.commit()

def is_banned(uid):
    cursor.execute("SELECT 1 FROM bans WHERE user_id=?", (uid,))
    return cursor.fetchone() is not None

async def safe_send(func, *args, **kwargs):
    try:
        return await func(*args, **kwargs)
    except TelegramForbiddenError:
        return

# ================= SUB CHECK =================
async def check_sub(uid):
    not_sub = []
    for ch in CHANNELS:
        try:
            m = await bot.get_chat_member(ch, uid)
            if m.status not in ["member", "administrator", "creator"]:
                not_sub.append(ch)
        except:
            not_sub.append(ch)
    return not_sub

def subscription_required(handler):
    @wraps(handler)
    async def wrapper(event, *args, **kwargs):
        uid = event.from_user.id

        if is_banned(uid):
            await event.answer("🚫 Siz botdan bloklangansiz.")
            return

        not_sub = await check_sub(uid)
        if not_sub:
            text = "❌ *Quyidagi kanallarga obuna emassiz:*\n\n"
            text += "\n".join([f"• {c}" for c in not_sub])
            await safe_send(
                event.message.edit_text if isinstance(event, CallbackQuery) else event.answer,
                text,
                reply_markup=sub_menu(),
                parse_mode="Markdown"
            )
            return
        return await handler(event, *args, **kwargs)
    return wrapper

# ================= MENUS =================
def sub_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 1-kanal", url="https://t.me/azimboyev_blog")],
        [InlineKeyboardButton(text="📢 2-kanal", url="https://t.me/CyberLearnUz")],
        [InlineKeyboardButton(text="📢 3-kanal", url="https://t.me/comment_bIog")],
        [InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_sub")]
    ])

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎯 AUTO SENSITIVITY", callback_data="auto")]
    ])

def ram_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="2–3GB", callback_data="ram_3")],
        [InlineKeyboardButton(text="4GB", callback_data="ram_4")],
        [InlineKeyboardButton(text="6–8GB", callback_data="ram_6")]
    ])

def dpi_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="320", callback_data="dpi_320")],
        [InlineKeyboardButton(text="360", callback_data="dpi_360")],
        [InlineKeyboardButton(text="400", callback_data="dpi_400")],
        [InlineKeyboardButton(text="440", callback_data="dpi_440")]
    ])

def fps_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="30", callback_data="fps_30")],
        [InlineKeyboardButton(text="45", callback_data="fps_45")],
        [InlineKeyboardButton(text="60", callback_data="fps_60")]
    ])

# ================= LOGIC =================
def auto_calc(ram, dpi, fps):
    base = 180
    if ram <= 3: base -= 15
    if ram >= 6: base += 10
    if dpi <= 320: base += 10
    if dpi >= 440: base -= 20
    if fps <= 30: base -= 15
    if fps >= 60: base += 10
    base = max(120, min(200, base))
    return {k: base - v for k, v in {
        "General": 0, "Red Dot": 10, "2x": 20,
        "4x": 35, "AWM": 55, "Free Look": 30
    }.items()}

def calc_level(xp): return xp // 100 + 1

async def add_xp(uid, amount, msg):
    cursor.execute("SELECT xp, level FROM profiles WHERE user_id=?", (uid,))
    xp, lvl = cursor.fetchone()
    xp += amount
    new_lvl = calc_level(xp)
    cursor.execute("UPDATE profiles SET xp=?, level=? WHERE user_id=?", (xp, new_lvl, uid))
    db.commit()
    if new_lvl > lvl:
        await msg.answer(f"🎉 LEVEL UP! {lvl} → {new_lvl}")

# ================= HANDLERS =================
@dp.message(CommandStart())
async def start(msg: Message):
    save_user(msg.from_user.id)
    if await check_sub(msg.from_user.id):
        await msg.answer("🔥 *FF PRO SETTINGS*", reply_markup=main_menu(), parse_mode="Markdown")
    else:
        await msg.answer("❌ Obuna bo‘ling", reply_markup=sub_menu())

@dp.callback_query(F.data == "check_sub")
async def recheck(cb: CallbackQuery):
    if not await check_sub(cb.from_user.id):
        await cb.message.edit_text("❌ Hali obuna emassiz", reply_markup=sub_menu())
    else:
        await cb.message.edit_text("✅ Obuna tasdiqlandi", reply_markup=main_menu())

@dp.callback_query(F.data == "auto")
@subscription_required
async def auto_start(cb: CallbackQuery):
    user_data[cb.from_user.id] = {}
    await cb.message.edit_text("RAM tanlang:", reply_markup=ram_menu())

@dp.callback_query(F.data.startswith("ram_"))
@subscription_required
async def set_ram(cb: CallbackQuery):
    user_data[cb.from_user.id]["ram"] = int(cb.data.split("_")[1])
    await cb.message.edit_text("DPI tanlang:", reply_markup=dpi_menu())

@dp.callback_query(F.data.startswith("dpi_"))
@subscription_required
async def set_dpi(cb: CallbackQuery):
    user_data[cb.from_user.id]["dpi"] = int(cb.data.split("_")[1])
    await cb.message.edit_text("FPS tanlang:", reply_markup=fps_menu())

@dp.callback_query(F.data.startswith("fps_"))
@subscription_required
async def set_fps(cb: CallbackQuery):
    fps = int(cb.data.split("_")[1])
    d = user_data[cb.from_user.id]
    sens = auto_calc(d["ram"], d["dpi"], fps)

    cursor.execute(
        "INSERT INTO history (user_id, ram, dpi, fps, date) VALUES (?, ?, ?, ?, datetime('now'))",
        (cb.from_user.id, d["ram"], d["dpi"], fps)
    )
    cursor.execute("UPDATE profiles SET uses=uses+1 WHERE user_id=?", (cb.from_user.id,))
    db.commit()

    await add_xp(cb.from_user.id, 20, cb.message)

    text = "🎯 *AUTO SENSITIVITY*\n\n"
    for k, v in sens.items():
        text += f"{k}: {v}\n"

    await cb.message.edit_text(text, parse_mode="Markdown")

# ================= USER =================
@dp.message(F.text == "/profile")
@subscription_required
async def profile(msg: Message):
    cursor.execute("SELECT uses, xp, level FROM profiles WHERE user_id=?", (msg.from_user.id,))
    u, xp, lvl = cursor.fetchone()
    await msg.answer(
        f"👤 Profil\n🎯 Hisoblashlar: {u}\n⚡ XP: {xp}\n🏆 Level: {lvl}"
    )

@dp.message(F.text == "/history")
@subscription_required
async def history_cmd(msg: Message):
    cursor.execute("SELECT ram,dpi,fps FROM history WHERE user_id=? ORDER BY id DESC LIMIT 5", (msg.from_user.id,))
    rows = cursor.fetchall()
    if not rows:
        await msg.answer("📭 Tarix yo‘q")
        return
    text = "📜 OXIRGI SOZLAMALAR:\n"
    for r in rows:
        text += f"• {r[0]}GB | {r[1]} DPI | {r[2]} FPS\n"
    await msg.answer(text)

# ================= ADMIN =================
@dp.message(F.from_user.id == ADMIN_ID, F.text == "/level_stats")
async def level_stats(msg: Message):
    cursor.execute("SELECT COUNT(*) FROM profiles")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT AVG(level) FROM profiles")
    avg = cursor.fetchone()[0] or 0
    cursor.execute("SELECT MAX(level) FROM profiles")
    mx = cursor.fetchone()[0] or 0
    cursor.execute("SELECT user_id, level FROM profiles ORDER BY level DESC LIMIT 5")
    top = cursor.fetchall()

    text = f"📊 LEVEL STAT\n👥 Userlar: {total}\n🏆 O‘rtacha: {avg:.1f}\n🔥 Max: {mx}\n\nTOP 5:\n"
    for u in top:
        text += f"• {u[0]} — L{u[1]}\n"
    await msg.answer(text)

# ================= RUN =================
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
