from pyrogram import filters
from pyrogram.types import Message

from BADCLONE import app
from BADCLONE.utils.database import (
    get_autoplay_lang,
    get_autoplay_mood,
    is_autoplay,
    set_autoplay_lang,
    set_autoplay_mood,
)
from BADCLONE.utils.decorators.language import language
from BADCLONE.utils.inline import close_markup
from BADCLONE.utils.stream.autoplay import (
    AUTOPLAY_LANGS,
    AUTOPLAY_MOODS,
    set_autoplay,
    user_can_control,
)
from config import BANNED_USERS

USAGE = (
    "<b>♬ ᴀᴜᴛᴏᴘʟᴀʏ</b>\n\n"
    "<code>/autoplay on</code> • <code>/autoplay off</code>\n"
    "<code>/autoplay lang hindi</code> (ᴏʀ <code>auto</code>)\n"
    "<code>/autoplay mood sad</code> (ᴏʀ <code>any</code>)\n\n"
    "<b>ʟᴀɴɢs:</b> {langs}\n"
    "<b>ᴍᴏᴏᴅs:</b> {moods}"
)


async def _status(chat_id: int) -> str:
    on = await is_autoplay(chat_id)
    lang = await get_autoplay_lang(chat_id)
    mood = await get_autoplay_mood(chat_id)
    return (
        f"<b>♬ ᴀᴜᴛᴏᴘʟᴀʏ :</b> {'ᴏɴ ✅' if on else 'ᴏғғ ❌'}\n"
        f"<b>ʟᴀɴɢᴜᴀɢᴇ :</b> <code>{lang}</code>\n"
        f"<b>ᴍᴏᴏᴅ :</b> <code>{mood}</code>\n\n"
    )


@app.on_message(filters.command(["autoplay"]) & filters.group & ~BANNED_USERS)
@language
async def autoplay_command(client, message: Message, _):
    if not message.from_user:
        return
    chat_id = message.chat.id
    args = [a.lower() for a in message.command[1:]]
    usage = USAGE.format(
        langs=", ".join(f"<code>{x}</code>" for x in AUTOPLAY_LANGS),
        moods=", ".join(f"<code>{x}</code>" for x in AUTOPLAY_MOODS),
    )

    # /autoplay  -> just show the current settings
    if not args:
        return await message.reply_text(
            await _status(chat_id) + usage, reply_markup=close_markup(_)
        )

    if not await user_can_control(message.from_user.id, chat_id):
        return await message.reply_text(_["admin_14"], reply_markup=close_markup(_))

    action = args[0]
    who = message.from_user.mention

    if action in ("on", "enable", "start"):
        await set_autoplay(chat_id, True)
        return await message.reply_text(
            f"<b>♬ ᴀᴜᴛᴏᴘʟᴀʏ ᴇɴᴀʙʟᴇᴅ ʙʏ</b> {who}\n"
            "ᴡʜᴇɴ ᴛʜᴇ ǫᴜᴇᴜᴇ ᴇɴᴅs, ʀᴇʟᴀᴛᴇᴅ sᴏɴɢs ᴡɪʟʟ ᴋᴇᴇᴘ ᴘʟᴀʏɪɴɢ.",
            reply_markup=close_markup(_),
        )

    if action in ("off", "disable", "stop"):
        await set_autoplay(chat_id, False)
        return await message.reply_text(
            f"<b>♬ ᴀᴜᴛᴏᴘʟᴀʏ ᴅɪsᴀʙʟᴇᴅ ʙʏ</b> {who}",
            reply_markup=close_markup(_),
        )

    if action in ("lang", "language") and len(args) >= 2:
        if args[1] not in AUTOPLAY_LANGS:
            return await message.reply_text(usage, reply_markup=close_markup(_))
        await set_autoplay_lang(chat_id, args[1])
        return await message.reply_text(
            f"<b>♬ ᴀᴜᴛᴏᴘʟᴀʏ ʟᴀɴɢᴜᴀɢᴇ :</b> <code>{args[1]}</code>",
            reply_markup=close_markup(_),
        )

    if action == "mood" and len(args) >= 2:
        if args[1] not in AUTOPLAY_MOODS:
            return await message.reply_text(usage, reply_markup=close_markup(_))
        await set_autoplay_mood(chat_id, args[1])
        return await message.reply_text(
            f"<b>♬ ᴀᴜᴛᴏᴘʟᴀʏ ᴍᴏᴏᴅ :</b> <code>{args[1]}</code>",
            reply_markup=close_markup(_),
        )

    return await message.reply_text(usage, reply_markup=close_markup(_))
