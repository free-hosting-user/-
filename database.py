import aiosqlite
from config import DB_PATH

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS chat_settings (
                chat_id INTEGER PRIMARY KEY,
                antispam INTEGER DEFAULT 1,
                antispam_mode TEXT DEFAULT 'normal',
                antiflood INTEGER DEFAULT 1,
                flood_limit INTEGER DEFAULT 5,
                flood_seconds INTEGER DEFAULT 10,
                nolinks INTEGER DEFAULT 0,
                nolocations INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_activity (
                chat_id INTEGER,
                user_id INTEGER,
                message_count INTEGER DEFAULT 0,
                PRIMARY KEY (chat_id, user_id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS domain_whitelist (
                chat_id INTEGER,
                domain TEXT,
                PRIMARY KEY (chat_id, domain)
            )
        """)
        await db.commit()

async def get_chat_settings(chat_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM chat_settings WHERE chat_id = ?", (chat_id,)) as cursor:
            row = await cursor.fetchone()
            if not row:
                await db.execute(
                    "INSERT INTO chat_settings (chat_id) VALUES (?)", (chat_id,)
                )
                await db.commit()
                return {
                    "chat_id": chat_id,
                    "antispam": 1,
                    "antispam_mode": "normal",
                    "antiflood": 1,
                    "flood_limit": 5,
                    "flood_seconds": 10,
                    "nolinks": 0,
                    "nolocations": 0,
                }
            return dict(row)

async def update_chat_setting(chat_id: int, key: str, value: str | int):
    await get_chat_settings(chat_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE chat_settings SET {key} = ? WHERE chat_id = ?", (value, chat_id))
        await db.commit()

async def increment_user_activity(chat_id: int, user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT message_count FROM user_activity WHERE chat_id = ? AND user_id = ?",
            (chat_id, user_id),
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                count = row[0] + 1
                await db.execute(
                    "UPDATE user_activity SET message_count = ? WHERE chat_id = ? AND user_id = ?",
                    (count, chat_id, user_id),
                )
            else:
                count = 1
                await db.execute(
                    "INSERT INTO user_activity (chat_id, user_id, message_count) VALUES (?, ?, ?)",
                    (chat_id, user_id, count),
                )
        await db.commit()
        return count

async def get_whitelisted_domains(chat_id: int) -> list[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT domain FROM domain_whitelist WHERE chat_id = ?", (chat_id,)) as cursor:
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
