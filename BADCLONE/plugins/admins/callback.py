import asyncio
import html
import os
import random
import re
from telegram import CallbackQuery
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from BADCLONE import YouTube, app
from BADCLONE.core.call import Bad, get_thumb_safe, send_now_playing
from BADCLONE.misc import SUDOERS, db
from BADCLONE.utils.database import (
    get_active_chats,
    get_lang,
    get_upvote_count,
    is_active_chat,
    is_music_playing,
    get_loop,
    is_nonadmin_chat,
    music_off,
    music_on,
    set_loop,
)
from pyrogram.errors import (
    ChatAdminRequired,
    InviteRequestSent,
    UserAlreadyParticipant,
    UserNotParticipant,
)
from BADCLONE.utils.database import get_assistant
from BADCLONE.utils.decorators.language import languageCB
from BADCLONE.utils.formatters import seconds_to_min
from BADCLONE.utils.inline import (
    close_markup,
    more_markup,
    more_markup_timer,
    stream_markup,
    stream_markup_timer,
)
from BADCLONE.utils.stream.autoclear import auto_clean
from BADCLONE import app
from BADCLONE.utils.stream.autoplay import (
    autoplay_next,
    toggle_autoplay,
    user_can_control,
)
from BADCLONE.utils.stream.thumbnail import (
    toggle_thumbnail_status,
    get_thumbnail_status,
)

from BADCLONE.utils.inline.play import (
    stream_markup,
)
import config
from config import (
    BANNED_USERS,
    SOUNCLOUD_IMG_URL,
    STREAM_IMG_URL,
    TELEGRAM_AUDIO_URL,
    TELEGRAM_VIDEO_URL,
    adminlist,
    confirmer,
    votemode,
)
from strings import get_string
from pyrogram.enums import ButtonStyle


def random_style():
    return random.choice([
        ButtonStyle.SUCCESS,
        ButtonStyle.DANGER,
        ButtonStyle.PRIMARY
    ])


checker = {}
upvoters = {}


def _player_markup(_, chat_id: int, message_id: int):
    """Keyboard for the player message (main panel or 'More' panel), so a press refreshes it instantly."""
    playing = db.get(chat_id)
    if playing:
        cur = playing[0]
        mystic = cur.get("mystic")
        is_current = bool(mystic) and getattr(mystic, "id", None) == message_id
        more = is_current and cur.get("panel") == "more"
        try:
            if is_current and int(cur.get("seconds", 0)) > 0:
                builder = more_markup_timer if more else stream_markup_timer
                return builder(_, chat_id, seconds_to_min(cur["played"]), cur["dur"])
        except Exception:
            pass
        if more:
            return more_markup(_, chat_id)
    return stream_markup(_, chat_id)


async def _refresh_player_buttons(query, _, chat_id: int):
    try:
        markup = InlineKeyboardMarkup(_player_markup(_, chat_id, query.message.id))
        await query.message.edit_reply_markup(reply_markup=markup)
    except Exception:
        pass  # e.g. "message not modified" / message deleted


@app.on_callback_query(filters.regex("^THUMBTOGGLE") & ~BANNED_USERS)
@languageCB
async def thumbnail_toggle_callback(client, query: CallbackQuery, _):
    try:
        chat_id = int(query.data.split("|")[1])
    except Exception:
        return await query.answer()

    new_status = toggle_thumbnail_status(chat_id)

    status_text = (
        "🖼 ᴛʜᴜᴍʙɴᴀɪʟ ᴇɴᴀʙʟᴇᴅ ғᴏʀ ɴᴇxᴛ sᴏɴɢs"
        if new_status == "on"
        else "🖼 ᴛʜᴜᴍʙɴᴀɪʟ ᴅɪsᴀʙʟᴇᴅ ғᴏʀ ɴᴇxᴛ sᴏɴɢs"
    )
    try:
        await query.answer(status_text, show_alert=False)
    except Exception:
        pass
    await _refresh_player_buttons(query, _, chat_id)


@app.on_callback_query(filters.regex("^autoplay_from_player") & ~BANNED_USERS)
@languageCB
async def autoplay_toggle_callback(client, query: CallbackQuery, _):
    try:
        chat_id = int(query.data.split("|")[1])
    except Exception:
        return await query.answer()

    if not await user_can_control(query.from_user.id, query.message.chat.id):
        return await query.answer(_["admin_14"], show_alert=True)

    enabled = await toggle_autoplay(chat_id)
    status_text = (
        "♬ ᴀᴜᴛᴏᴘʟᴀʏ ᴏɴ — ʀᴇʟᴀᴛᴇᴅ sᴏɴɢs ᴡɪʟʟ ᴋᴇᴇᴘ ᴘʟᴀʏɪɴɢ"
        if enabled
        else "♬ ᴀᴜᴛᴏᴘʟᴀʏ ᴏғғ"
    )
    try:
        await query.answer(status_text, show_alert=False)
    except Exception:
        pass
    await _refresh_player_buttons(query, _, chat_id)


def _chat_id_from(data: str, index: int = -1):
    try:
        return int(data.split("|")[index])
    except Exception:
        return None


def _is_current_player(query, chat_id: int) -> bool:
    playing = db.get(chat_id)
    if not playing:
        return False
    mystic = playing[0].get("mystic")
    return bool(mystic) and getattr(mystic, "id", None) == query.message.id


@app.on_callback_query(filters.regex("^PLAYERMORE") & ~BANNED_USERS)
@languageCB
async def player_more_callback(client, query: CallbackQuery, _):
    chat_id = _chat_id_from(query.data)
    if chat_id is None:
        return await query.answer()
    if not _is_current_player(query, chat_id):
        return await query.answer("⛔ ᴛʜɪs ᴘʟᴀʏᴇʀ ɪs ᴏʟᴅ, ᴜsᴇ ᴛʜᴇ ʟᴀᴛᴇsᴛ ᴏɴᴇ", show_alert=True)
    db[chat_id][0]["panel"] = "more"
    try:
        await query.answer()
    except Exception:
        pass
    await _refresh_player_buttons(query, _, chat_id)


@app.on_callback_query(filters.regex("^PLAYERBACK") & ~BANNED_USERS)
@languageCB
async def player_back_callback(client, query: CallbackQuery, _):
    chat_id = _chat_id_from(query.data)
    if chat_id is None:
        return await query.answer()
    if db.get(chat_id):
        db[chat_id][0]["panel"] = None
    try:
        await query.answer()
    except Exception:
        pass
    await _refresh_player_buttons(query, _, chat_id)


_seek_locks = {}


@app.on_callback_query(filters.regex("^PLAYERSEEK") & ~BANNED_USERS)
@languageCB
async def player_seek_callback(client, query: CallbackQuery, _):
    try:
        _tag, direction, chat_id = query.data.split("|")
        chat_id = int(chat_id)
    except Exception:
        return await query.answer()
    if not await user_can_control(query.from_user.id, query.message.chat.id):
        return await query.answer(_["admin_14"], show_alert=True)
    playing = db.get(chat_id)
    if not playing:
        return await query.answer(_["queue_2"], show_alert=True)
    cur = playing[0]
    duration_seconds = int(cur.get("seconds", 0))
    if duration_seconds == 0:
        return await query.answer(_["admin_22"], show_alert=True)

    lock = _seek_locks.setdefault(chat_id, asyncio.Lock())
    if lock.locked():
        return await query.answer("⏳ ᴡᴀɪᴛ...")
    async with lock:
        step = 20
        played = int(cur["played"])
        if direction == "b":
            if played - step <= 10:
                return await query.answer("⛔ ᴄᴀɴ'ᴛ ɢᴏ ʙᴀᴄᴋ ᴍᴏʀᴇ", show_alert=True)
            to_seek = played - step + 1
        else:
            if duration_seconds - (played + step) <= 10:
                return await query.answer("⛔ ᴛᴏᴏ ᴄʟᴏsᴇ ᴛᴏ ᴛʜᴇ ᴇɴᴅ", show_alert=True)
            to_seek = played + step + 1

        await query.answer("⏪ -20s" if direction == "b" else "⏩ +20s")

        file_path = cur["file"]
        if "vid_" in file_path:
            file_path, _ok = await YouTube.download(
                cur["vidid"],
                None,
                videoid=True,
                video=(str(cur["streamtype"]) == "video"),
            )
            if not file_path:
                return await query.message.reply_text(_["admin_22"])
        if cur.get("speed_path"):
            file_path = cur["speed_path"]
        if "index_" in str(file_path):
            file_path = cur["vidid"]
        try:
            await Bad.seek_stream(
                chat_id,
                file_path,
                seconds_to_min(to_seek),
                cur["dur"],
                cur["streamtype"],
            )
        except Exception:
            return await query.message.reply_text(_["admin_26"])

        now = db.get(chat_id)
        if now and now[0] is cur:  # same song still playing
            cur["played"] = played - step if direction == "b" else played + step
    await _refresh_player_buttons(query, _, chat_id)


@app.on_callback_query(filters.regex("^PLAYERSHUFFLE") & ~BANNED_USERS)
@languageCB
async def player_shuffle_callback(client, query: CallbackQuery, _):
    chat_id = _chat_id_from(query.data)
    if chat_id is None:
        return await query.answer()
    if not await user_can_control(query.from_user.id, query.message.chat.id):
        return await query.answer(_["admin_14"], show_alert=True)
    playing = db.get(chat_id)
    if not playing or len(playing) < 3:
        return await query.answer(
            "🔀 ᴀᴅᴅ ᴀᴛ ʟᴇᴀsᴛ 2 ᴍᴏʀᴇ sᴏɴɢs ᴛᴏ sʜᴜғғʟᴇ", show_alert=True
        )
    upcoming = playing[1:]
    random.shuffle(upcoming)
    playing[1:] = upcoming
    await query.answer("🔀 ǫᴜᴇᴜᴇ sʜᴜғғʟᴇᴅ")


@app.on_callback_query(filters.regex("^PLAYERREPEAT") & ~BANNED_USERS)
@languageCB
async def player_repeat_callback(client, query: CallbackQuery, _):
    chat_id = _chat_id_from(query.data)
    if chat_id is None:
        return await query.answer()
    if not await user_can_control(query.from_user.id, query.message.chat.id):
        return await query.answer(_["admin_14"], show_alert=True)
    if await get_loop(chat_id) != 0:
        await set_loop(chat_id, 0)
        text = "🔁 ʀᴇᴘᴇᴀᴛ ᴏғғ"
    else:
        await set_loop(chat_id, -1)  # -1 = repeat until switched off
        text = "🔁 ʀᴇᴘᴇᴀᴛ ᴏɴ: ᴛʜɪs sᴏɴɢ ᴋᴇᴇᴘs ᴘʟᴀʏɪɴɢ ᴜɴᴛɪʟ ʏᴏᴜ ᴛᴜʀɴ ɪᴛ ᴏғғ"
    try:
        await query.answer(text, show_alert=False)
    except Exception:
        pass
    await _refresh_player_buttons(query, _, chat_id)


_downloading = set()
_YT_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")


def _file_in_use(vidid: str, kind: str) -> bool:
    """True if a queue is playing / waiting for exactly this file (then we must not delete it)."""
    for items in db.values():
        for item in items:
            if item.get("vidid") == vidid and str(item.get("streamtype")) == kind:
                return True
    return False


@app.on_callback_query(filters.regex(r"^download(audio|video) ") & ~BANNED_USERS)
@languageCB
async def player_download_callback(client, query: CallbackQuery, _):
    kind = "video" if query.data.startswith("downloadvideo") else "audio"
    vidid = query.data.split(" ", 1)[1].strip()
    if not _YT_ID.match(vidid):
        return await query.answer("⛔ ɴᴏᴛ ᴀᴠᴀɪʟᴀʙʟᴇ ғᴏʀ ᴛʜɪs ᴛʀᴀᴄᴋ", show_alert=True)
    key = (vidid, kind)
    if key in _downloading:
        return await query.answer("⏳ ᴀʟʀᴇᴀᴅʏ ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ, ᴡᴀɪᴛ...", show_alert=True)
    _downloading.add(key)
    chat_id = query.message.chat.id
    status = None
    path = None
    try:
        await query.answer("📥 ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ, ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ...")
        status = await app.send_message(chat_id, f"📥 Downloading {kind}...")
        try:
            title, _dur_min, dur_sec, _thumb, _vid = await YouTube.details(vidid, True)
        except Exception:
            title, dur_sec = vidid, 0
        path, _direct = await YouTube.download(
            vidid, status, video=(kind == "video"), videoid=True
        )
        if not path:
            return await status.edit_text("❌ Download failed, please try again.")
        await status.edit_text("📤 Uploading...")
        caption = f"<b>{html.escape(str(title))}</b>\n\n📥 {html.escape(query.from_user.first_name or '')}"
        try:
            if kind == "audio":
                await app.send_audio(
                    chat_id,
                    audio=path,
                    caption=caption,
                    title=str(title)[:64],
                    duration=int(dur_sec or 0),
                    reply_markup=close_markup(_),
                )
            else:
                await app.send_video(
                    chat_id,
                    video=path,
                    caption=caption,
                    duration=int(dur_sec or 0),
                    supports_streaming=True,
                    reply_markup=close_markup(_),
                )
        except Exception:
            return await status.edit_text(
                "❌ Couldn't send the file (it may be too big for Telegram)."
            )
        await status.delete()
        status = None
    finally:
        _downloading.discard(key)
        # temporary files only: never delete what the player is using
        if path and not _file_in_use(vidid, kind):
            try:
                os.remove(path)
            except Exception:
                pass


@app.on_callback_query(filters.regex("unban_assistant"))
async def unban_assistant(_, callback: CallbackQuery):
    chat_id = callback.message.chat.id
    userbot = await get_assistant(chat_id)
    
    try:
        await app.unban_chat_member(chat_id, userbot.id)
        await callback.answer("My assistant id unbanned successfully\n\nNow you can play song🔉\n\nThank you", show_alert=True)
    except Exception as e:
        await callback.answer(f"Failed to unban my assistant because i don't have ban power\n\nPlease provide me ban power so that i can unban my assistant id", show_alert=True)


@app.on_callback_query(filters.regex("ADMIN") & ~BANNED_USERS)
@languageCB
async def del_back_playlist(client, CallbackQuery, _):
    callback_data = CallbackQuery.data.strip()
    callback_request = callback_data.split(None, 1)[1]
    command, chat = callback_request.split("|")
    if "_" in str(chat):
        bet = chat.split("_")
        chat = bet[0]
        counter = bet[1]
    chat_id = int(chat)
    if not await is_active_chat(chat_id):
        return await CallbackQuery.answer(_["general_5"], show_alert=True)
    mention = CallbackQuery.from_user.mention
    if command == "UpVote":
        if chat_id not in votemode:
            votemode[chat_id] = {}
        if chat_id not in upvoters:
            upvoters[chat_id] = {}

        voters = (upvoters[chat_id]).get(CallbackQuery.message.id)
        if not voters:
            upvoters[chat_id][CallbackQuery.message.id] = []

        vote = (votemode[chat_id]).get(CallbackQuery.message.id)
        if not vote:
            votemode[chat_id][CallbackQuery.message.id] = 0

        if CallbackQuery.from_user.id in upvoters[chat_id][CallbackQuery.message.id]:
            (upvoters[chat_id][CallbackQuery.message.id]).remove(
                CallbackQuery.from_user.id
            )
            votemode[chat_id][CallbackQuery.message.id] -= 1
        else:
            (upvoters[chat_id][CallbackQuery.message.id]).append(
                CallbackQuery.from_user.id
            )
            votemode[chat_id][CallbackQuery.message.id] += 1
        upvote = await get_upvote_count(chat_id)
        get_upvotes = int(votemode[chat_id][CallbackQuery.message.id])
        if get_upvotes >= upvote:
            votemode[chat_id][CallbackQuery.message.id] = upvote
            try:
                exists = confirmer[chat_id][CallbackQuery.message.id]
                current = db[chat_id][0]
            except:
                return await CallbackQuery.edit_message_text(f"ғᴀɪʟᴇᴅ.")
            try:
                if current["vidid"] != exists["vidid"]:
                    return await CallbackQuery.edit_message.text(_["admin_35"])
                if current["file"] != exists["file"]:
                    return await CallbackQuery.edit_message.text(_["admin_35"])
            except:
                return await CallbackQuery.edit_message_text(_["admin_36"])
            try:
                await CallbackQuery.edit_message_text(_["admin_37"].format(upvote))
            except:
                pass
            command = counter
            mention = "ᴜᴘᴠᴏᴛᴇs"
        else:
            if (
                CallbackQuery.from_user.id
                in upvoters[chat_id][CallbackQuery.message.id]
            ):
                await CallbackQuery.answer(_["admin_38"], show_alert=True)
            else:
                await CallbackQuery.answer(_["admin_39"], show_alert=True)
            upl = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text=f"👍 {get_upvotes}",
                            callback_data=f"ADMIN  UpVote|{chat_id}_{counter}",
                         style=random_style())
                    ]
                ]
            )
            await CallbackQuery.answer(_["admin_40"], show_alert=True)
            return await CallbackQuery.edit_message_reply_markup(reply_markup=upl)
    else:
        is_non_admin = await is_nonadmin_chat(CallbackQuery.message.chat.id)
        if not is_non_admin:
            if CallbackQuery.from_user.id not in SUDOERS:
                admins = adminlist.get(CallbackQuery.message.chat.id)
                if not admins:
                    return await CallbackQuery.answer(_["admin_13"], show_alert=True)
                else:
                    if CallbackQuery.from_user.id not in admins:
                        return await CallbackQuery.answer(
                            _["admin_14"], show_alert=True
                        )
    if command == "Pause":
        if not await is_music_playing(chat_id):
            return await CallbackQuery.answer(_["admin_1"], show_alert=True)
        await CallbackQuery.answer()
        await music_off(chat_id)
        await Bad.pause_stream(chat_id)
        await CallbackQuery.message.reply_text(
            _["admin_2"].format(mention), reply_markup=close_markup(_)
        )
    elif command == "Resume":
        if await is_music_playing(chat_id):
            return await CallbackQuery.answer(_["admin_3"], show_alert=True)
        await CallbackQuery.answer()
        await music_on(chat_id)
        await Bad.resume_stream(chat_id)
        await CallbackQuery.message.reply_text(
            _["admin_4"].format(mention), reply_markup=close_markup(_)
        )
    elif command == "Stop" or command == "End":
        await CallbackQuery.answer()
        await Bad.stop_stream(chat_id)
        await set_loop(chat_id, 0)
        await CallbackQuery.message.reply_text(
            _["admin_5"].format(mention), reply_markup=close_markup(_)
        )
        await CallbackQuery.message.delete()
    elif command == "Skip" or command == "Replay":
        try:
            await CallbackQuery.answer()  # answer first: finding the next song can take a few seconds
        except Exception:
            pass
        check = db.get(chat_id)
        if command == "Skip":
            txt = f"{mention}\n Skiped"
            popped = None
            try:
                popped = check.pop(0)
                if popped:
                    await auto_clean(popped)
                if not check and not await autoplay_next(chat_id, popped):
                    await CallbackQuery.edit_message_text(
                        f"{mention}\n Skiped"
                    )
                    await CallbackQuery.message.reply_text(
                        text=_["admin_6"].format(
                            mention, CallbackQuery.message.chat.title
                        ),
                        reply_markup=close_markup(_),
                    )
                    try:
                        return await Bad.stop_stream(chat_id)
                    except:
                        return
                check = db.get(chat_id)
            except:
                try:
                    await CallbackQuery.edit_message_text(
                        f"{mention}\n Skiped"
                    )
                    await CallbackQuery.message.reply_text(
                        text=_["admin_6"].format(
                            mention, CallbackQuery.message.chat.title
                        ),
                        reply_markup=close_markup(_),
                    )
                    return await Bad.stop_stream(chat_id)
                except:
                    return
        else:
            txt = f"{mention}\n playing"
        queued = check[0]["file"]
        title = (check[0]["title"]).title()
        user = check[0]["by"]
        duration = check[0]["dur"]
        streamtype = check[0]["streamtype"]
        videoid = check[0]["vidid"]
        thumb_on = get_thumbnail_status(chat_id) == "on"
        status = True if str(streamtype) == "video" else None
        db[chat_id][0]["played"] = 0
        exis = (check[0]).get("old_dur")
        if exis:
            db[chat_id][0]["dur"] = exis
            db[chat_id][0]["seconds"] = check[0]["old_second"]
            db[chat_id][0]["speed_path"] = None
            db[chat_id][0]["speed"] = 1.0
        if "live_" in queued:
            n, link = await YouTube.video(videoid, True)
            if n == 0:
                return await CallbackQuery.message.reply_text(
                    text=_["admin_7"].format(title),
                    reply_markup=close_markup(_),
                )
            try:
                image = await YouTube.thumbnail(videoid, True)
            except:
                image = None
            try:
                await Bad.skip_stream(chat_id, link, video=status, image=image)
            except:
                return await CallbackQuery.message.reply_text(_["call_6"])
            button = stream_markup(_, chat_id)
            run = await send_now_playing(
                CallbackQuery.message.chat.id,
                thumb_on,
                await get_thumb_safe(videoid) if thumb_on else None,
                _["stream_1"].format(
                    f"https://t.me/{app.username}?start=info_{videoid}",
                    title[:23],
                    duration,
                    user,
                ),
                button,
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
            await CallbackQuery.edit_message_text(txt, reply_markup=close_markup(_))
        elif "vid_" in queued:
            mystic = await CallbackQuery.message.reply_text(
                _["call_7"]
            )
            try:
                file_path, direct = await YouTube.download(
                    videoid,
                    mystic,
                    videoid=True,
                    video=status,
                )
            except:
                file_path = None
            if not file_path:
                if str(user) == "Autoplay":
                    await mystic.delete()
                    return await Bad.autoplay_recover(chat_id)
                return await mystic.edit_text(_["call_6"])
            try:
                image = await YouTube.thumbnail(videoid, True)
            except:
                image = None
            try:
                await Bad.skip_stream(chat_id, file_path, video=status, image=image)
            except:
                if str(user) == "Autoplay":
                    await mystic.delete()
                    return await Bad.autoplay_recover(chat_id)
                return await mystic.edit_text(_["call_6"])
            button = stream_markup(_, chat_id)
            run = await send_now_playing(
                CallbackQuery.message.chat.id,
                thumb_on,
                await get_thumb_safe(videoid) if thumb_on else None,
                _["stream_1"].format(
                    f"https://t.me/{app.username}?start=info_{videoid}",
                    title[:23],
                    duration,
                    user,
                ),
                button,
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "stream"
            await CallbackQuery.edit_message_text(txt, reply_markup=close_markup(_))
            await mystic.delete()
        elif "index_" in queued:
            try:
                await Bad.skip_stream(chat_id, videoid, video=status)
            except:
                return await CallbackQuery.message.reply_text(_["call_6"])
            button = stream_markup(_, chat_id)
            run = await send_now_playing(
                CallbackQuery.message.chat.id,
                thumb_on,
                STREAM_IMG_URL,
                _["stream_2"].format(user),
                button,
            )
            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"
            await CallbackQuery.edit_message_text(txt, reply_markup=close_markup(_))
        else:
            if videoid == "telegram":
                image = None
            elif videoid == "soundcloud":
                image = None
            else:
                try:
                    image = await YouTube.thumbnail(videoid, True)
                except:
                    image = None
            try:
                await Bad.skip_stream(chat_id, queued, video=status, image=image)
            except:
                return await CallbackQuery.message.reply_text(_["call_6"])
            if videoid == "telegram":
                button = stream_markup(_, chat_id)
                run = await send_now_playing(
                    CallbackQuery.message.chat.id,
                    thumb_on,
                    TELEGRAM_AUDIO_URL
                    if str(streamtype) == "audio"
                    else TELEGRAM_VIDEO_URL,
                    _["stream_1"].format(
                        config.SUPPORT_CHAT, title[:23], duration, user
                    ),
                    button,
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "tg"
            elif videoid == "soundcloud":
                button = stream_markup(_, chat_id)
                run = await send_now_playing(
                    CallbackQuery.message.chat.id,
                    thumb_on,
                    SOUNCLOUD_IMG_URL
                    if str(streamtype) == "audio"
                    else TELEGRAM_VIDEO_URL,
                    _["stream_1"].format(
                        config.SUPPORT_CHAT, title[:23], duration, user
                    ),
                    button,
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "tg"
            else:
                button = stream_markup(_, chat_id)
                run = await send_now_playing(
                    CallbackQuery.message.chat.id,
                    thumb_on,
                    await get_thumb_safe(videoid) if thumb_on else None,
                    _["stream_1"].format(
                        f"https://t.me/{app.username}?start=info_{videoid}",
                        title[:23],
                        duration,
                        user,
                    ),
                    button,
                )
                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"
            await CallbackQuery.edit_message_text(txt, reply_markup=close_markup(_))


async def markup_timer():
    while not await asyncio.sleep(7):
        active_chats = await get_active_chats()
        for chat_id in active_chats:
            try:
                if not await is_music_playing(chat_id):
                    continue
                playing = db.get(chat_id)
                if not playing:
                    continue
                duration_seconds = int(playing[0]["seconds"])
                if duration_seconds == 0:
                    continue
                try:
                    mystic = playing[0]["mystic"]
                except:
                    continue
                try:
                    check = checker[chat_id][mystic.id]
                    if check is False:
                        continue
                except:
                    pass
                try:
                    language = await get_lang(chat_id)
                    _ = get_string(language)
                except:
                    _ = get_string("en")
                try:
                    builder = (
                        more_markup_timer
                        if playing[0].get("panel") == "more"
                        else stream_markup_timer
                    )
                    buttons = builder(
                        _,
                        chat_id,
                        seconds_to_min(playing[0]["played"]),
                        playing[0]["dur"],
                    )
                    await mystic.edit_reply_markup(
                        reply_markup=InlineKeyboardMarkup(buttons)
                    )
                except:
                    continue
            except:
                continue


asyncio.create_task(markup_timer())
