from aiogram.filters import Filter
from aiogram.types import Message
from aiogram.enums import ChatMemberStatus

class IsAdmin(Filter):
    async def __call__(self, message: Message) -> bool:
        if message.chat.type in ["private"]:
            return True
        member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
        return member.status in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]
