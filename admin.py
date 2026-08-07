from aiogram import Router, types
from aiogram.filters import Command
from filters import IsAdmin
from database import update_chat_setting, get_chat_settings

router = Router()
router.message.filter(IsAdmin())

@router.message(Command("antispam"))
async def cmd_antispam(message: types.Message):
    args = message.text.split()[1:] if message.text else []
    if not args:
        await message.reply("Usage: /antispam <on|off|status>")
        return

    subcommand = args[0].lower()
    chat_id = message.chat.id

    if subcommand == "on":
        await update_chat_setting(chat_id, "antispam", 1)
        await message.reply("✅ AntiSpam protection activated.")
    elif subcommand == "off":
        await update_chat_setting(chat_id, "antispam", 0)
        await message.reply("❌ AntiSpam protection deactivated.")
    elif subcommand == "status":
        settings = await get_chat_settings(chat_id)
        status = "ON" if settings["antispam"] else "OFF"
        mode = settings["antispam_mode"]
        await message.reply(f"🛡️ **AntiSpam Status**: {status}\n⚙️ **Mode**: {mode.capitalize()}")
    else:
        await message.reply("Invalid subcommand. Use `on`, `off`, or `status`.")

@router.message(Command("antispammode"))
async def cmd_antispam_mode(message: types.Message):
    args = message.text.split()[1:] if message.text else []
    if not args or args[0].lower() not in ["normal", "strict", "aggressive"]:
        await message.reply("Usage: /antispammode <normal|strict|aggressive>")
        return

    mode = args[0].lower()
    await update_chat_setting(message.chat.id, "antispam_mode", mode)
    await message.reply(f"✅ AntiSpam mode updated to **{mode.capitalize()}**.")

@router.message(Command("antiflood"))
async def cmd_antiflood(message: types.Message):
    args = message.text.split()[1:] if message.text else []
    if not args:
        await message.reply("Usage: /antiflood <on|off>")
        return

    subcommand = args[0].lower()
    if subcommand == "on":
        await update_chat_setting(message.chat.id, "antiflood", 1)
        await message.reply("✅ AntiFlood protection activated.")
    elif subcommand == "off":
        await update_chat_setting(message.chat.id, "antiflood", 0)
        await message.reply("❌ AntiFlood protection deactivated.")

@router.message(Command("setflood"))
async def cmd_setflood(message: types.Message):
    args = message.text.split()[1:] if message.text else []
    if len(args) < 2 or not args[0].isdigit() or not args[1].isdigit():
        await message.reply("Usage: /setflood <message_limit> <time_in_seconds>\nExample: `/setflood 10 60`")
        return

    limit, seconds = int(args[0]), int(args[1])
    await update_chat_setting(message.chat.id, "flood_limit", limit)
    await update_chat_setting(message.chat.id, "flood_seconds", seconds)
    await message.reply(f"✅ AntiFlood set to **{limit} messages** per **{seconds} seconds**.")

@router.message(Command("nolinks"))
async def cmd_nolinks(message: types.Message):
    args = message.text.split()[1:] if message.text else []
    if not args:
        await message.reply("Usage: /nolinks <on|off>")
        return

    subcommand = args[0].lower()
    if subcommand == "on":
        await update_chat_setting(message.chat.id, "nolinks", 1)
        await message.reply("✅ Link filter enabled. Non-admins cannot send links.")
    elif subcommand == "off":
        await update_chat_setting(message.chat.id, "nolinks", 0)
        await message.reply("❌ Link filter disabled.")

@router.message(Command("nolocations"))
async def cmd_nolocations(message: types.Message):
    args = message.text.split()[1:] if message.text else []
    if not args:
        await message.reply("Usage: /nolocations <on|off>")
        return

    subcommand = args[0].lower()
    if subcommand == "on":
        await update_chat_setting(message.chat.id, "nolocations", 1)
        await message.reply("✅ Location filter enabled. Location shares will be deleted.")
    elif subcommand == "off":
        await update_chat_setting(message.chat.id, "nolocations", 0)
        await message.reply("❌ Location filter disabled.")
