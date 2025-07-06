import asyncio
import sqlite3
from datetime import datetime, timezone

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.types import Message

API_TOKEN = 'YOUR_API_TOKEN'
MAIN_CHANNEL = -1002699957905
SECRET_CHANNEL = -1002520692350
ADMIN_IDS = [7715403070, 7618825755]

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

conn = sqlite3.connect("users.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    invited_at TEXT,
    invite_link TEXT
)
""")
conn.commit()

@router.message(Command("start"))
async def handle_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or "unknown"

    print(f"DEBUG: from_user.id = {user_id}")
    print(f"DEBUG: ADMIN_IDS = {ADMIN_IDS}")

    if user_id in ADMIN_IDS:
        await message.answer(
            "🔐 Welcome, Admin!\nUse /stats or /users to manage the user list."
        )
        return

    try:
        member = await bot.get_chat_member(MAIN_CHANNEL, user_id)
        if member.status in ['left', 'kicked']:
            await message.answer("🚫 Please subscribe to the main channel first.")
            return
    except Exception as e:
        print(f"⚠️ Could not check subscription: {e}")
        await message.answer("⚠️ Failed to check your subscription. Please try again later.")
        return

    cursor.execute("SELECT invite_link FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    if result and result[0]:
        await message.answer("✅ You already have an invite link:\n" + result[0])
        return

    try:
        invite = await bot.create_chat_invite_link(
            chat_id=SECRET_CHANNEL,
            member_limit=1,
            creates_join_request=False
        )

        cursor.execute(
            "INSERT OR REPLACE INTO users (user_id, username, invited_at, invite_link) VALUES (?, ?, ?, ?)",
            (user_id, username, datetime.now(timezone.utc).isoformat(), invite.invite_link)
        )
        conn.commit()

        await message.answer(f"👋 Hello, @{username}!\nHere is your private invite link:\n\n{invite.invite_link}")

    except Exception as e:
        print(f"❌ Error creating invite link: {e}")
        await message.answer("❌ Failed to create your invite link. Please contact support.")

@router.message(Command("myid"))
async def my_id(message: Message):
    await message.answer(f"🆔 Your Telegram ID: {message.from_user.id}")

@router.message(Command("stats"))
async def admin_stats(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]
    await message.answer(f"📊 Total users in the database: {total}")

@router.message(Command("users"))
async def admin_users(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    cursor.execute("SELECT username, invited_at FROM users")
    rows = cursor.fetchall()
    if not rows:
        await message.answer("There are no users yet.")
        return
    text = "👥 Users:\n" + "\n".join(
        [f"@{u or 'unknown'} — {d[:10]}" for u, d in rows]
    )
    await message.answer(text)

async def check_unsubscribed():
    while True:
        cursor.execute("SELECT user_id FROM users")
        all_users = cursor.fetchall()

        for (user_id,) in all_users:
            try:
                member = await bot.get_chat_member(MAIN_CHANNEL, user_id)
                if member.status in ['left', 'kicked']:
                    print(f"❌ {user_id} unsubscribed — removing from secret channel")

                    cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
                    conn.commit()

                    try:
                        await bot.ban_chat_member(SECRET_CHANNEL, user_id)
                        await bot.unban_chat_member(SECRET_CHANNEL, user_id)
                    except Exception as e:
                        print(f"⚠️ Error kicking {user_id}: {e}")

            except Exception as e:
                print(f"⚠️ Error checking {user_id}: {e}")
        await asyncio.sleep(60)

async def main():
    asyncio.create_task(check_unsubscribed())
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
