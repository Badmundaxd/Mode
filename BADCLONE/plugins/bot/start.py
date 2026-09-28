import time
import random
from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from youtubesearchpython.__future__ import VideosSearch

import config
from BADCLONE import app
from BADCLONE.misc import _boot_
from BADCLONE.plugins.sudo.sudoers import sudoers_list
from BADCLONE.utils.database import get_served_chats, get_served_users, get_sudoers
from BADCLONE.utils import bot_sys_stats
from BADCLONE.utils.database import (
    add_served_chat,
    add_served_user,
    blacklisted_chats,
    get_lang,
    is_banned_user,
    is_on_off,
)
from BADCLONE.utils.decorators.language import LanguageStart
from BADCLONE.utils.formatters import get_readable_time
from BADCLONE.utils.inline import help_pannel, private_panel, start_panel
from config import BANNED_USERS
from strings import get_string
from pyrogram.enums import ButtonStyle

from BADCLONE.utils.rich_ui import (
    rich_details,
    rich_esc,
    rich_heading,
    rich_img,
    rich_kv_table,
    rich_note,
    rich_send,
    rich_table,
    sanitize_display_name,
)


def random_style():
    return random.choice([
        ButtonStyle.SUCCESS,
        ButtonStyle.DANGER,
        ButtonStyle.PRIMARY
    ])


def _support_updates_pills() -> str:
    support = getattr(config, "SUPPORT_CHAT", None)
    updates = getattr(config, "SUPPORT_CHANNEL", None) or support
    pills = ""
    if support:
        pills += (
            f'<tg-button type="url" style="primary" url="{support}">'
            "🍬 sᴜᴘᴘᴏʀᴛ</tg-button> "
        )
    if updates:
        pills += (
            f'<tg-button type="url" style="success" url="{updates}">'
            "🍹 ᴜᴘᴅᴀᴛᴇs</tg-button>"
        )
    return f"<p>{pills}</p>" if pills else ""


def _bot_name() -> str:
    return rich_esc(getattr(app, "name", None) or getattr(config, "BOT_NAME", "Bot"))


def _onboarding_body(_: dict, uid: int, name: str) -> str:
    """Private /start menu (same layout as ShizuMusic)."""
    return (
        rich_note(
            _["onboarding_greeting"].format(uid, rich_esc(name))
            + _["onboarding_intro"].format(_bot_name())
        )
        + rich_details(
            _["onboarding_features_heading"],
            rich_table(_["onboarding_features_headers"], _["onboarding_features_rows"]),
            open=True,
        )
        + rich_details(
            _["onboarding_why_heading"],
            _["onboarding_why_body"],
            open=True,
        )
        + rich_note(_["onboarding_powered_by"])
        + _support_updates_pills()
    )


def _help_body(_: dict, uid: int, name: str, photo: str) -> str:
    return (
        rich_heading(_["help_pick_category_title"], level=3)
        + rich_img(photo)
        + rich_note(_["help_pick_category_note"].format(uid, rich_esc(name)))
        + rich_details(
            _["help_features_heading"],
            rich_table(["ғᴇᴀᴛᴜʀᴇ", "ᴅᴇᴛᴀɪʟs"], _["help_features_rows"]),
            open=True,
        )
        + rich_note(_["onboarding_powered_by"])
        + _support_updates_pills()
    )


def _group_body(_: dict, uid: int, name: str, chat_title: str, photo: str) -> str:
    mention = f'<a href="tg://user?id={uid}">{rich_esc(name)}</a>'
    return (
        rich_img(photo)
        + f"<p>{_['group_thanks_title'].format(mention, _bot_name())}</p>"
        + rich_note(_["group_thanks_note"].format(rich_esc(chat_title), _bot_name()))
        + _support_updates_pills()
    )




YUMI_PICS = [
"https://graph.org/file/f76fd86d1936d45a63c64.jpg",
"https://graph.org/file/69ba894371860cd22d92e.jpg",
"https://graph.org/file/67fde88d8c3aa8327d363.jpg",
"https://graph.org/file/3a400f1f32fc381913061.jpg",
"https://graph.org/file/a0893f3a1e6777f6de821.jpg",
"https://graph.org/file/5a285fc0124657c7b7a0b.jpg",
"https://graph.org/file/25e215c4602b241b66829.jpg",
"https://graph.org/file/a13e9733afdad69720d67.jpg",
"https://graph.org/file/692e89f8fe20554e7a139.jpg",
"https://graph.org/file/db277a7810a3f65d92f22.jpg",
"https://graph.org/file/a00f89c5aa75735896e0f.jpg",
"https://graph.org/file/f86b71018196c5cfe7344.jpg",
"https://graph.org/file/a3db9af88f25bb1b99325.jpg",
"https://graph.org/file/5b344a55f3d5199b63fa5.jpg",
"https://graph.org/file/84de4b440300297a8ecb3.jpg",
"https://graph.org/file/84e84ff778b045879d24f.jpg",
"https://graph.org/file/a4a8f0e5c0e6b18249ffc.jpg",
"https://graph.org/file/ed92cada78099c9c3a4f7.jpg",
"https://graph.org/file/d6360613d0fa7a9d2f90b.jpg",
"https://graph.org/file/37248e7bdff70c662a702.jpg",
"https://graph.org/file/0bfe29d15e918917d1305.jpg",
"https://graph.org/file/16b1a2828cc507f8048bd.jpg",
"https://graph.org/file/e6b01f23f2871e128dad8.jpg",
"https://graph.org/file/cacbdddee77784d9ed2b7.jpg",
"https://graph.org/file/ddc5d6ec1c33276507b19.jpg",
"https://graph.org/file/39d7277189360d2c85b62.jpg",
"https://graph.org/file/5846b9214eaf12c3ed100.jpg",
"https://graph.org/file/ad4f9beb4d526e6615e18.jpg",
"https://graph.org/file/3514efaabe774e4f181f2.jpg",  
"https://graph.org/file/eaa3a2602e43844a488a5.jpg",
"https://graph.org/file/b129e98b6e5c4db81c15f.jpg",
"https://graph.org/file/3ccb86d7d62e8ee0a2e8b.jpg",
"https://graph.org/file/df11d8257613418142063.jpg",
"https://graph.org/file/9e23720fedc47259b6195.jpg",
"https://graph.org/file/826485f2d7db6f09db8ed.jpg",
"https://graph.org/file/ff3ad786da825b5205691.jpg",
"https://graph.org/file/52713c9fe9253ae668f13.jpg",
"https://graph.org/file/8f8516c86677a8c91bfb1.jpg",
"https://graph.org/file/6603c3740378d3f7187da.jpg",
"https://graph.org/file/66cb6ec40eea5c4670118.jpg",
"https://graph.org/file/2e3cf4327b169b981055e.jpg",   

]


@app.on_message(filters.command(["start"]) & filters.private & ~BANNED_USERS)
@LanguageStart
async def start_pm(client, message: Message, _):
    await add_served_user(message.from_user.id)
    if len(message.text.split()) > 1:
        name = message.text.split(None, 1)[1]
        if name[0:4] == "help":
            keyboard = help_pannel(_)
            name_ = sanitize_display_name(message.from_user.first_name)
            return await rich_send(
                app,
                message.chat.id,
                _help_body(_, message.from_user.id, name_, random.choice(YUMI_PICS)),
                reply_markup=keyboard,
            )
        if name[0:3] == "sud":
            await sudoers_list(client=client, message=message, _=_)
            if await is_on_off(2):
                return await app.send_message(
                    chat_id=config.LOGGER_ID,
                    text=f"✦ {message.from_user.mention} ᴊᴜsᴛ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ᴄʜᴇᴄᴋ <b>sᴜᴅᴏʟɪsᴛ</b>.\n\n<b>✦ ᴜsᴇʀ ɪᴅ ➠</b> <code>{message.from_user.id}</code>\n<b>✦ ᴜsᴇʀɴᴀᴍᴇ ➠</b> @{message.from_user.username}",
                )
            return
        if name[0:3] == "inf":
            m = await message.reply_text("🔎")
            query = (str(name)).replace("info_", "", 1)
            query = f"https://www.youtube.com/watch?v={query}"
            results = VideosSearch(query, limit=1)
            for result in (await results.next())["result"]:
                title = result["title"]
                duration = result["duration"]
                views = result["viewCount"]["short"]
                thumbnail = result["thumbnails"][0]["url"].split("?")[0]
                channellink = result["channel"]["link"]
                channel = result["channel"]["name"]
                link = result["link"]
                published = result["publishedTime"]
            searched_text = _["start_6"].format(
                title, duration, views, published, channellink, channel, app.mention
            )
            key = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text=_["S_B_8"], url=link, style=random_style()),
                        InlineKeyboardButton(text=_["S_B_9"], url=config.SUPPORT_CHAT, style=random_style()),
                    ],
                ]
            )
            await m.delete()
            await app.send_photo(
                chat_id=message.chat.id,
                photo=thumbnail,
                caption=searched_text,
                reply_markup=key,
            )
            if await is_on_off(2):
                return await app.send_message(
                    chat_id=config.LOGGER_ID,
                    text=f"✦ {message.from_user.mention} ᴊᴜsᴛ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ᴄʜᴇᴄᴋ <b>ᴛʀᴀᴄᴋ ɪɴғᴏʀᴍᴀᴛɪᴏɴ</b>.\n\n✦ <b>ᴜsᴇʀ ɪᴅ ➠</b> <code>{message.from_user.id}</code>\n✦ <b>ᴜsᴇʀɴᴀᴍᴇ ➠</b> @{message.from_user.username}",
                )
    else:
        out = private_panel(_)
        name_ = sanitize_display_name(message.from_user.first_name)
        await rich_send(
            app,
            message.chat.id,
            rich_img(random.choice(YUMI_PICS))
            + _onboarding_body(_, message.from_user.id, name_),
            reply_markup=InlineKeyboardMarkup(out),
        )
        if await is_on_off(2):
            return await app.send_message(
                chat_id=config.LOGGER_ID,
                text=f"✦ {message.from_user.mention} ᴊᴜsᴛ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ.\n\n✦ <b>ᴜsᴇʀ ɪᴅ ➠</b> <code>{message.from_user.id}</code>\n✦ <b>ᴜsᴇʀɴᴀᴍᴇ ➠</b> @{message.from_user.username}",
            )


@app.on_message(filters.command(["start"]) & filters.group & ~BANNED_USERS)
@LanguageStart
async def start_gp(client, message: Message, _):
    out = start_panel(_)
    uptime = int(time.time() - _boot_)
    uid = message.from_user.id if message.from_user else 0
    name_ = sanitize_display_name(message.from_user.first_name) if message.from_user else "User"
    body = _group_body(
        _, uid, name_, message.chat.title or "this chat", random.choice(YUMI_PICS)
    ) + rich_note(f"❍ ᴜᴘᴛɪᴍᴇ : {rich_esc(get_readable_time(uptime))}")
    await rich_send(
        app,
        message.chat.id,
        body,
        reply_markup=InlineKeyboardMarkup(out),
    )
    return await add_served_chat(message.chat.id)


@app.on_message(filters.new_chat_members, group=-1)
async def welcome(client, message: Message):
    for member in message.new_chat_members:
        try:
            language = await get_lang(message.chat.id)
            _ = get_string(language)
            if await is_banned_user(member.id):
                try:
                    await message.chat.ban_member(member.id)
                except:
                    pass
            if member.id == app.id:
                if message.chat.type != ChatType.SUPERGROUP:
                    await message.reply_text(_["start_4"])
                    return await app.leave_chat(message.chat.id)
                if message.chat.id in await blacklisted_chats():
                    await message.reply_text(
                        _["start_5"].format(
                            app.mention,
                            f"https://t.me/{app.username}?start=sudolist",
                            config.SUPPORT_CHAT,
                        ),
                        disable_web_page_preview=True,
                    )
                    return await app.leave_chat(message.chat.id)

                out = start_panel(_)
                adder = message.from_user
                adder_id = adder.id if adder else 0
                adder_name = sanitize_display_name(adder.first_name) if adder else "User"
                await rich_send(
                    app,
                    message.chat.id,
                    _group_body(
                        _, adder_id, adder_name, message.chat.title or "this chat",
                        random.choice(YUMI_PICS),
                    ),
                    reply_markup=InlineKeyboardMarkup(out),
                )
                try:
                    await rich_send(
                        app,
                        message.chat.id,
                        rich_heading(_["group_admin_request_title"], level=2)
                        + rich_note(_["group_admin_request_note1"])
                        + rich_note(_["group_admin_request_note2"]),
                    )
                except Exception:
                    pass
                await add_served_chat(message.chat.id)
                await message.stop_propagation()
        except Exception as ex:
            print(ex)
            
