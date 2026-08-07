import logging
import time
from collections import defaultdict
from urllib.parse import urlparse

from aiogram import Router, types, F
from aiogram.enums import ChatMemberStatus
from database import get_chat_settings, increment_user_activity, get_whitelisted_domains
from utils.spam_detector import is_spam

router = Router()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ModerationBot")

# In-memory storage for rate-limiting message histories per chat and user
user_message_timestamps = defaultdict(lambda: defaultdict(list))

async def is_user_admin(chat_id: int, user_id: int, bot) -> bool:
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]
    except Exception:
        return False

@router.message(F.chat.type.in_(["group", "supergroup"]))
async def process_moderation(message: types.Message):
    if not message.from_user or message.from_user.is_bot:
        return

    chat_id = message.chat.id
    user_id = message.from_user.id

    if await is_user_admin(chat_id, user_id, message.bot):
        return

    settings = await get_chat_settings(chat_id)
    msg_count = await increment_user_activity(chat_id, user_id)
    is_active = msg_count > 50

    # 1. Location Filter
    if settings["nolocations"] and message.location:
        try:
            await message.delete()
            logger.info(f"Deleted location message from user {user_id} in chat {chat_id}")
            return
        except Exception as e:
            logger.error(f"Failed to delete location message: {e}")

    text = message.text or message.caption or ""

    # 2. AntiSpam Check
    if settings["antispam"]:
        spam_detected, reason = is_spam(
            text=text,
            entities=message.entities or message.caption_entities,
            mode=settings["antispam_mode"],
            active_user=is_active
        )
        if spam_detected:
            try:
                await message.delete()
                logger.info(f"Deleted spam from {user_id} in {chat_id}: {reason}")
                warn_msg = await message.answer(f"⚠️ Message from @{message.from_user.username or user_id} deleted (Reason: {reason}).")
                return
            except Exception as e:
                logger.error(f"Failed to delete spam message: {e}")

    # 3. Link Filter Check
    if settings["nolinks"]:
        entities = message.entities or message.caption_entities or []
        has_link = any(e.type in ["url", "text_link"] for e in entities)
        
        if has_link:
            whitelisted_domains = await get_whitelisted_domains(chat_id)
            urls = [e.url for e in entities if e.url] + [text[e.offset:e.offset+e.length] for e in entities if e.type == "url"]
            
            allowed = True
            for url in urls:
                domain = urlparse(url if url.startswith("http") else f"http://{url}").netloc.lower()
                if not any(domain == w or domain.endswith("." + w) for w in whitelisted_domains):
                    allowed = False
                    break

            if not allowed:
                try:
                    await message.delete()
                    logger.info(f"Deleted unauthorized link from user {user_id} in chat {chat_id}")
                    return
                except Exception as e:
                    logger.error(f"Failed to delete link message: {e}")

    # 4. AntiFlood Check
    if settings["antiflood"]:
        now = time.time()
        window = settings["flood_seconds"]
        limit = settings["flood_limit"]
        
        timestamps = user_message_timestamps[chat_id][user_id]
        timestamps.append(now)
        
        # Remove timestamps outside the sliding window
        user_message_timestamps[chat_id][user_id] = [t for t in timestamps if now - t <= window]
        
        if len(user_message_timestamps[chat_id][user_id]) > limit:
            try:
                await message.delete()
                logger.info(f"Flooding detected from user {user_id} in chat {chat_id}. Message deleted.")
                return
            except Exception as e:
                logger.error(f"Failed to delete flood message: {e}")
