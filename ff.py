import asyncio
import sqlite3
from functools import wraps
from typing import List

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
    LabeledPrice, PreCheckoutQuery
)
from aiogram.filters import CommandStart
from aiogram.client.default import DefaultBotProperties

# ================== CONFIG ==================
TOKEN = "8432697594:AAFeIMSAAAuoKCVONYPF7Y91lhYER080R-Q"
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
                await event.answer(
                    "✅ Tasdiqlandi\n🔓 *BANDAN CHIQDINGIZ*",
                    show_alert=True
                )

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
    kb = [
        [InlineKeyboardButton(text="🎯 AUTO SENSITIVITY", callback_data="auto")]
    ]
    if is_vip(uid):
        kb.append(
            [InlineKeyboardButton(text="🔥 VIP EXTREME HS", callback_data="vip_extreme")]
        )
    else:
        kb.append(
            [InlineKeyboardButton(text="⭐ VIP PRO (5⭐)", callback_data="vip_buy")]
        )
    return InlineKeyboardMarkup(inline_keyboard=kb)

def back_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back", callback_data="back")]
    ])

def admin_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Statistika", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📢 Broadcast", callback_data="admin_broadcast")]
    ])

# ================== TEXT =====================
AUTO_TEXT = (
    "🎯 *AUTO SENSITIVITY (FREE)*\n\n"
    "🎯 Taxminiy HEADSHOT: *~80%*\n\n"
    "General: 170\n"
    "Red Dot: 165\n"
    "2x: 150\n"
    "4x: 130\n"
    "AWM: 110\n\n"
    "🟡 Oddiy o‘yinchilar uchun\n"
    "🆓 Bepul nastroyka"
)

VIP_TEXT = (
    "🔥 *VIP EXTREME HEADSHOT (PRO)*\n\n"
    "🎯 Taxminiy HEADSHOT: *~95%*\n\n"
    "General: 195\n"
    "Red Dot: 190\n"
    "2x: 175\n"
    "4x: 150\n"
    "AWM: 130\n\n"
    "⚡ PRO o‘yinchilar uchun\n"
    "⭐ 5 Telegram Stars bilan ochiladi"
)

# ================== START ====================
@dp.message(CommandStart())
async def start(msg: Message):
    save_user(msg.from_user.id)
    if not await check_sub(msg.from_user.id):
        await msg.answer(
            "🔥 *FF PRO SETTINGS*",
            reply_markup=main_menu(msg.from_user.id)
        )
    else:
        await msg.answer("❌ Avval obuna bo‘ling", reply_markup=sub_menu())

# ================== NAV ======================
@dp.callback_query(F.data == "back")
async def back(cb: CallbackQuery):
    await cb.message.edit_text(
        "🔥 *FF PRO SETTINGS*",
        reply_markup=main_menu(cb.from_user.id)
    )

@dp.callback_query(F.data == "check_sub")
async def check_sub_btn(cb: CallbackQuery):
    uid = cb.from_user.id
    if not await check_sub(uid):
        unban(uid)
        await cb.message.edit_text(
            "🔥 *FF PRO SETTINGS*",
            reply_markup=main_menu(uid)
        )
    else:
        await cb.answer("❌ Hali obuna to‘liq emas", show_alert=True)

# ================== AUTO =====================
@dp.callback_query(F.data == "auto")
@subscription_required
async def auto(cb: CallbackQuery):
    await cb.message.edit_text(AUTO_TEXT, reply_markup=back_menu())

# ================== VIP BUY (⭐ STARS) ==================
@dp.callback_query(F.data == "vip_buy")
@subscription_required
async def vip_buy(cb: CallbackQuery):
    prices = [
        LabeledPrice(
            label="VIP PRO (5 ⭐ Telegram Stars)",
            amount=5
        )
    ]

    await bot.send_invoice(
        chat_id=cb.from_user.id,
        title="⭐ VIP PRO",
        description="VIP EXTREME HEADSHOT ochish",
        payload="vip_5stars",
        currency="XTR",
        prices=prices,
        provider_token=""
    )

@dp.pre_checkout_query()
async def pre_checkout(pre: PreCheckoutQuery):
    await pre.answer(ok=True)

@dp.message(F.successful_payment)
async def successful_payment(msg: Message):
    if msg.successful_payment.invoice_payload != "vip_5stars":
        return

    uid = msg.from_user.id
    cur.execute("INSERT OR IGNORE INTO vip VALUES (?)", (uid,))
    db.commit()

    stars = msg.successful_payment.total_amount

    await msg.answer(
        "🎉 *To‘lov muvaffaqiyatli!*\n\n"
        f"⭐ To‘langan: {stars} Stars\n"
        "👑 *VIP PRO faollashtirildi!*"
    )

# ================== VIP ONLY =================
@dp.callback_query(F.data == "vip_extreme")
@subscription_required
async def vip_only(cb: CallbackQuery):
    if not is_vip(cb.from_user.id):
        await cb.answer("❌ Siz VIP emassiz", show_alert=True)
        return
    await cb.message.edit_text(VIP_TEXT, reply_markup=back_menu())

# ================== ADMIN ====================
@dp.message(F.from_user.id == ADMIN_ID, F.text == "/admin")
async def admin(msg: Message):
    await msg.answer("👑 *ADMIN PANEL*", reply_markup=admin_menu())

@dp.callback_query(F.data == "admin_stats", F.from_user.id == ADMIN_ID)
async def admin_stats(cb: CallbackQuery):
    cur.execute("SELECT COUNT(*) FROM users")
    users = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM vip")
    vips = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM bans")
    bans = cur.fetchone()[0]
    await cb.message.answer(
        f"👤 Userlar: {users}\n⭐ VIP: {vips}\n🚫 BAN: {bans}"
    )

# ================== BROADCAST =================
@dp.callback_query(F.data == "admin_broadcast", F.from_user.id == ADMIN_ID)
async def bc_info(cb: CallbackQuery):
    await cb.message.answer(
        "📢 *Broadcast*\n\n"
        "Keyingi yuborgan xabaringiz BARCHA userlarga ketadi."
    )

@dp.message(F.from_user.id == ADMIN_ID)
async def broadcast(msg: Message):
    if msg.text and msg.text.startswith("/"):
        return

    cur.execute("SELECT user_id FROM users")
    users = [u[0] for u in cur.fetchall()]

    for uid in users:
        try:
            await msg.copy_to(uid)
            await asyncio.sleep(0.05)
        except:
            pass

    await msg.answer("✅ Broadcast tugadi")

# ================== RUN ======================
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
