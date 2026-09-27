import asyncio
import os
from datetime import datetime, timedelta
from typing import Union

from ntgcalls import ConnectionNotFound, TelegramServerError
from pyrogram import Client
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from pytgcalls import PyTgCalls, exceptions, types
from pytgcalls.pytgcalls_session import PyTgCallsSession

import config
from BADCLONE import LOGGER, YouTube, app
from BADCLONE.misc import db
from BADCLONE.utils.database import (
    add_active_chat,
    add_active_video_chat,
    get_lang,
    get_loop,
    group_assistant,
    is_autoend,
    music_on,
    remove_active_chat,
    remove_active_video_chat,
    set_loop,
)
from BADCLONE.utils.exceptions import AssistantErr
from BADCLONE.utils.formatters import check_duration, seconds_to_min, speed_converter
from BADCLONE.utils.inline.play import stream_markup
from BADCLONE.utils.stream.autoclear import auto_clean
from BADCLONE.utils.stream.autoplay import autoplay_next, schedule_prefetch
from BADCLONE.utils.stream.thumbnail import get_thumbnail_status

from BADCLONE.utils.thumbnails import get_thumb
from strings import get_string
import random
from pyrogram.enums import ButtonStyle


def random_style():
    return random.choice([
        ButtonStyle.SUCCESS,
        ButtonStyle.DANGER,
        ButtonStyle.PRIMARY
    ])



async def delete_old_message(chat_id: int):
    try:
        old = db.get(chat_id, [{}])[0].get("mystic")
        if old:
            await old.delete()
    except:
        pass


autoend = {}
counter = {}


async def get_thumb_safe(videoid: str):
    """Generated thumbnail; falls back to the default image if it can't be made."""
    try:
        return await get_thumb(videoid)
    except Exception:
        return config.STREAM_IMG_URL


async def send_now_playing(chat_id, use_photo: bool, photo, caption: str, buttons):
    """
    Thumbnail ON  -> photo + caption
    Thumbnail OFF -> plain text message (same as /play does)
    """
    markup = InlineKeyboardMarkup(buttons)
    if use_photo and photo:
        try:
            return await app.send_photo(
                chat_id=chat_id,
                photo=photo,
                has_spoiler=True,
                caption=caption,
                reply_markup=markup,
            )
        except Exception:
            pass  # bad photo -> fall back to text so the song info is never lost
    try:
        return await app.send_message(
            chat_id=chat_id,
            text=caption,
            reply_markup=markup,
            disable_web_page_preview=True,
        )
    except TypeError:  # newer Kurigram dropped this argument
        return await app.send_message(chat_id=chat_id, text=caption, reply_markup=markup)


async def _clear_(chat_id: int):
    db[chat_id] = []
    await remove_active_video_chat(chat_id)
    await remove_active_chat(chat_id)


class Call(PyTgCalls):
    def __init__(self):
        PyTgCallsSession.notice_displayed = True

        self.userbot1 = Client(
            name="BADMUSIC1",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING1),
        )
        self.one = PyTgCalls(self.userbot1, cache_duration=100)

        self.userbot2 = Client(
            name="BADMUSIC2",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING2),
        )
        self.two = PyTgCalls(self.userbot2, cache_duration=100)

        self.userbot3 = Client(
            name="BADMUSIC3",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING3),
        )
        self.three = PyTgCalls(self.userbot3, cache_duration=100)

        self.userbot4 = Client(
            name="BADMUSIC4",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING4),
        )
        self.four = PyTgCalls(self.userbot4, cache_duration=100)

        self.userbot5 = Client(
            name="BADMUSIC5",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING5),
        )
        self.five = PyTgCalls(self.userbot5, cache_duration=100)

    def _build_stream(
        self,
        source: str,
        video: bool,
        ffmpeg: str | None = None,
    ) -> types.MediaStream:
        return types.MediaStream(
            media_path=source,
            audio_parameters=types.AudioQuality.HIGH,
            video_parameters=types.VideoQuality.HD_720p,
            audio_flags=types.MediaStream.Flags.REQUIRED,
            video_flags=(
                types.MediaStream.Flags.AUTO_DETECT
                if video
                else types.MediaStream.Flags.IGNORE
            ),
            ffmpeg_parameters=ffmpeg,
        )

    async def _play_on_assistant(
        self,
        client: PyTgCalls,
        chat_id: int,
        stream: types.MediaStream,
    ):
        try:
            await client.play(
                chat_id=chat_id,
                stream=stream,
                config=types.GroupCallConfig(auto_start=False),
            )
        except exceptions.NoActiveGroupCall:
            raise
        except exceptions.NoAudioSourceFound:
            raise
        except (ConnectionNotFound, TelegramServerError):
            raise
        except Exception:
            raise

    
    async def pause_stream(self, chat_id: int):
        await delete_old_message(chat_id)
        assistant = await group_assistant(self, chat_id)
        await assistant.pause(chat_id)

  
    async def resume_stream(self, chat_id: int):
        await delete_old_message(chat_id)
        assistant = await group_assistant(self, chat_id)
        await assistant.resume(chat_id)

    
    async def stop_stream(self, chat_id: int):
        await delete_old_message(chat_id)
        assistant = await group_assistant(self, chat_id)
        try:
            await _clear_(chat_id)
            await assistant.leave_call(chat_id, close=False)
        except Exception:
            pass


    async def stop_stream_force(self, chat_id: int):
        for string, client in [
            (config.STRING1, self.one),
            (config.STRING2, self.two),
            (config.STRING3, self.three),
            (config.STRING4, self.four),
            (config.STRING5, self.five),
        ]:
            if not string:
                continue
            try:
                await client.leave_call(chat_id, close=False)
            except Exception:
                pass
        try:
            await _clear_(chat_id)
        except Exception:
            pass

  
    async def speedup_stream(self, chat_id: int, file_path, speed, playing):
        assistant = await group_assistant(self, chat_id)
        if str(speed) != "1.0":
            base = os.path.basename(file_path)
            chatdir = os.path.join(os.getcwd(), "playback", str(speed))
            if not os.path.isdir(chatdir):
                os.makedirs(chatdir)
            out = os.path.join(chatdir, base)
            if not os.path.isfile(out):
                if str(speed) == "0.5":
                    vs = 2.0
                elif str(speed) == "0.75":
                    vs = 1.35
                elif str(speed) == "1.5":
                    vs = 0.68
                elif str(speed) == "2.0":
                    vs = 0.5
                else:
                    vs = 1.0
                proc = await asyncio.create_subprocess_shell(
                    cmd=(
                        "ffmpeg "
                        "-i "
                        f"{file_path} "
                        "-filter:v "
                        f"setpts={vs}*PTS "
                        "-filter:a "
                        f"atempo={speed} "
                        f"{out}"
                    ),
                    stdin=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                await proc.communicate()
        else:
            out = file_path
        dur = await asyncio.get_event_loop().run_in_executor(None, check_duration, out)
        dur = int(dur)
        played, con_seconds = speed_converter(playing[0]["played"], speed)
        duration = seconds_to_min(dur)
        xx = f"-ss {played} -to {duration}"
        video_mode = playing[0]["streamtype"] == "video"
        stream = self._build_stream(out, video=video_mode, ffmpeg=xx)
        if str(db[chat_id][0]["file"]) == str(file_path):
            await self._play_on_assistant(assistant, chat_id, stream)
        else:
            raise AssistantErr("Ufff")
        if str(db[chat_id][0]["file"]) == str(file_path):
            exis = (playing[0]).get("old_dur")
            if not exis:
                db[chat_id][0]["old_dur"] = db[chat_id][0]["dur"]
                db[chat_id][0]["old_second"] = db[chat_id][0]["seconds"]
            db[chat_id][0]["played"] = con_seconds
            db[chat_id][0]["dur"] = duration
            db[chat_id][0]["seconds"] = dur
            db[chat_id][0]["speed_path"] = out
            db[chat_id][0]["speed"] = speed

    async def force_stop_stream(self, chat_id: int):
        await delete_old_message(chat_id)
        assistant = await group_assistant(self, chat_id)
        try:
            check = db.get(chat_id)
            check.pop(0)
        except Exception:
            pass
        await remove_active_video_chat(chat_id)
        await remove_active_chat(chat_id)
        try:
            await assistant.leave_call(chat_id, close=False)
        except Exception:
            pass

  
    async def skip_stream(
        self,
        chat_id: int,
        link: str,
        video: Union[bool, str] = None,
        image: Union[bool, str] = None,
    ):
        assistant = await group_assistant(self, chat_id)
        stream = self._build_stream(link, video=bool(video))
        await self._play_on_assistant(assistant, chat_id, stream)
        current = db.get(chat_id)
        if current:
            schedule_prefetch(chat_id, current[0])

  
    async def seek_stream(self, chat_id, file_path, to_seek, duration, mode):
        assistant = await group_assistant(self, chat_id)
        ffmpeg = f"-ss {to_seek} -to {duration}"
        video_mode = mode == "video"
        stream = self._build_stream(
            file_path,
            video=video_mode,
            ffmpeg=ffmpeg,
        )
        await self._play_on_assistant(assistant, chat_id, stream)

    
    async def stream_call(self, link):
        assistant = await group_assistant(self, config.LOGGER_ID)
        stream = self._build_stream(link, video=True)
        await self._play_on_assistant(assistant, config.LOGGER_ID, stream)
        await asyncio.sleep(0.2)
        try:
            await assistant.leave_call(config.LOGGER_ID, close=False)
        except Exception:
            pass

    
    async def join_call(
        self,
        chat_id: int,
        original_chat_id: int,
        link,
        video: Union[bool, str] = None,
        image: Union[bool, str] = None,
    ):
        assistant = await group_assistant(self, chat_id)
        language = await get_lang(chat_id)
        _ = get_string(language)
        stream = self._build_stream(link, video=bool(video))
        try:
            await self._play_on_assistant(assistant, chat_id, stream)
        except exceptions.NoActiveGroupCall:
            raise AssistantErr(_["call_8"])
        except exceptions.NoAudioSourceFound:
            raise AssistantErr(_["call_10"])
        except (ConnectionNotFound, TelegramServerError):
            raise AssistantErr(_["call_10"])
        except Exception:
            raise AssistantErr(_["call_10"])
        await add_active_chat(chat_id)
        await music_on(chat_id)
        if video:
            await add_active_video_chat(chat_id)
        if await is_autoend():
            counter[chat_id] = {}
            users = len(await assistant.get_participants(chat_id))
            if users == 1:
                autoend[chat_id] = datetime.now() + timedelta(minutes=1)

  
    async def _queue_finished(self, client: PyTgCalls, chat_id: int, _):
        """Queue is over (and autoplay had nothing to add): clean up and leave."""
        try:
            await _clear_(chat_id)
        except Exception:
            pass
        try:
            buttons = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "✙ ʌᴅᴅ ϻє вᴧʙʏ ✙",
                            url=f"https://t.me/{app.username}?startgroup=true",
                         style=random_style()),
                        InlineKeyboardButton("⋞ ᴄʟᴏsє ⋟", callback_data="close", style=random_style()),
                    ],
                    [
                        InlineKeyboardButton(
                            "⌯ ᴅєᴠєʟᴏᴘєꝛ ⌯",
                            url=f"https://t.me/{config.OWNER_USERNAME}",
                         style=random_style()),
                    ],
                ]
            )
            await app.send_message(
                chat_id,
                "<b>🎵 𝐓ʜᴇ 𝐐ᴜᴇᴜᴇ 𝐇ᴀs 𝐅ɪɴɪsʜᴇᴅ. 𝐔sᴇ /play 𝐓ᴏ 𝐀ᴅᴅ 𝐌ᴏʀᴇ 𝐒ᴏɴɢs!!</b>",
                reply_markup=buttons,
            )
        except Exception:
            pass
        try:
            return await client.leave_call(chat_id, close=False)
        except Exception:
            return

    async def autoplay_recover(self, chat_id: int):
        """An autoplay song failed to start (skip button / command): pick another one."""
        assistant = await group_assistant(self, chat_id)
        return await self.change_stream(assistant, chat_id)

    async def change_stream(self, client: PyTgCalls, chat_id: int, _retry: int = 0):
        await delete_old_message(chat_id)
        try:
            language = await get_lang(chat_id)
            _ = get_string(language)
        except Exception:
            _ = get_string("en")

        check = db.get(chat_id)
        popped = None
        loop = await get_loop(chat_id)
        try:
            if loop == 0:
                popped = check.pop(0)
            elif loop > 0:
                loop = loop - 1
                await set_loop(chat_id, loop)
            # loop < 0: repeat button is on -> keep playing the same song
            await auto_clean(popped)
            if not check:
                # queue is empty: autoplay (if ON) adds a related song, else we finish
                if not await autoplay_next(chat_id, popped):
                    return await self._queue_finished(client, chat_id, _)
                check = db.get(chat_id)
        except Exception:
            return await self._queue_finished(client, chat_id, _)

        queued = check[0]["file"]
        title = (check[0]["title"]).title()
        user = check[0].get("by")

        if not user or str(user).strip() in ["", "None", "null", "-"]:
            try:
                member = await app.get_users(check[0]["user_id"])
                user = member.first_name
            except:
                user = "Unknown"
        original_chat_id = check[0]["chat_id"]
        streamtype = check[0]["streamtype"]
        videoid = check[0]["vidid"]
        db[chat_id][0]["played"] = 0
        exis = (check[0]).get("old_dur")
        if exis:
            db[chat_id][0]["dur"] = exis
            db[chat_id][0]["seconds"] = check[0]["old_second"]
            db[chat_id][0]["speed_path"] = None
            db[chat_id][0]["speed"] = 1.0
        video = True if str(streamtype) == "video" else False

        # same switch the Thumb button and /play use, so ON/OFF applies to the next song too
        thumb_on = get_thumbnail_status(chat_id) == "on"

        # autoplay: start getting suggestions ready while this song plays
        schedule_prefetch(chat_id, check[0])

        if "live_" in queued:
            n, link = await YouTube.video(videoid, True)
            if n == 0:
                return await app.send_message(
                    original_chat_id,
                    text=_["call_6"],
                )

            stream = self._build_stream(link, video=video)

            try:
                await self._play_on_assistant(client, chat_id, stream)
            except Exception:
                return await app.send_message(
                    original_chat_id,
                    text=_["call_6"],
                )

            img = await get_thumb_safe(videoid) if thumb_on else None
            button = stream_markup(_, chat_id)

            run = await send_now_playing(
                original_chat_id,
                thumb_on,
                img,
                _["stream_1"].format(
                    f"https://t.me/{app.username}?start=info_{videoid}",
                    title[:23],
                    check[0]["dur"],
                    user,
                ),
                button,
            )

            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"

        elif "vid_" in queued:
            mystic = await app.send_message(original_chat_id, _["call_7"])

            try:
                file_path, direct = await YouTube.download(
                    videoid,
                    mystic,
                    videoid=True,
                    video=video,
                )
            except Exception:
                file_path = None

            autoplay_song = str(check[0].get("by")) == "Autoplay"

            if not file_path:
                if autoplay_song and _retry < 3:
                    # autoplay's pick can't be downloaded: drop it and pick another
                    try:
                        await mystic.delete()
                    except Exception:
                        pass
                    return await self.change_stream(client, chat_id, _retry + 1)
                return await mystic.edit_text(_["call_6"])

            stream = self._build_stream(file_path, video=video)

            try:
                await self._play_on_assistant(client, chat_id, stream)
            except Exception:
                if autoplay_song and _retry < 3:
                    try:
                        await mystic.delete()
                    except Exception:
                        pass
                    return await self.change_stream(client, chat_id, _retry + 1)
                return await app.send_message(
                    original_chat_id,
                    text=_["call_6"],
                )

            img = await get_thumb_safe(videoid) if thumb_on else None
            button = stream_markup(_, chat_id)

            await mystic.delete()

            run = await send_now_playing(
                original_chat_id,
                thumb_on,
                img,
                _["stream_1"].format(
                    f"https://t.me/{app.username}?start=info_{videoid}",
                    title[:23],
                    check[0]["dur"],
                    user,
                ),
                button,
            )

            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "stream"

        elif "index_" in queued:
            stream = self._build_stream(videoid, video=video)

            try:
                await self._play_on_assistant(client, chat_id, stream)
            except Exception:
                return await app.send_message(
                    original_chat_id,
                    text=_["call_6"],
                )

            button = stream_markup(_, chat_id)

            run = await send_now_playing(
                original_chat_id,
                thumb_on,
                config.STREAM_IMG_URL,
                _["stream_2"].format(user),
                button,
            )

            db[chat_id][0]["mystic"] = run
            db[chat_id][0]["markup"] = "tg"

        else:
            stream = self._build_stream(queued, video=video)

            try:
                await self._play_on_assistant(client, chat_id, stream)
            except Exception:
                return await app.send_message(
                    original_chat_id,
                    text=_["call_6"],
                )

            if videoid == "telegram":
                button = stream_markup(_, chat_id)

                run = await send_now_playing(
                    original_chat_id,
                    thumb_on,
                    (
                        config.TELEGRAM_AUDIO_URL
                        if str(streamtype) == "audio"
                        else config.TELEGRAM_VIDEO_URL
                    ),
                    _["stream_1"].format(
                        config.SUPPORT_CHAT,
                        title[:23],
                        check[0]["dur"],
                        user,
                    ),
                    button,
                )

                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "tg"

            elif videoid == "soundcloud":
                button = stream_markup(_, chat_id)

                run = await send_now_playing(
                    original_chat_id,
                    thumb_on,
                    config.SOUNCLOUD_IMG_URL,
                    _["stream_1"].format(
                        config.SUPPORT_CHAT,
                        title[:23],
                        check[0]["dur"],
                        user,
                    ),
                    button,
                )

                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "tg"

            else:
                img = await get_thumb_safe(videoid) if thumb_on else None
                button = stream_markup(_, chat_id)

                run = await send_now_playing(
                    original_chat_id,
                    thumb_on,
                    img,
                    _["stream_1"].format(
                        f"https://t.me/{app.username}?start=info_{videoid}",
                        title[:23],
                        check[0]["dur"],
                        user,
                    ),
                    button,
                )

                db[chat_id][0]["mystic"] = run
                db[chat_id][0]["markup"] = "stream"

    async def ping(self):
        pings = []
        if config.STRING1:
            pings.append(self.one.ping)
        if config.STRING2:
            pings.append(self.two.ping)
        if config.STRING3:
            pings.append(self.three.ping)
        if config.STRING4:
            pings.append(self.four.ping)
        if config.STRING5:
            pings.append(self.five.ping)
        return str(round(sum(pings) / len(pings), 3)) if pings else "0"

    
    async def start(self):
        LOGGER(__name__).info("Starting PyTgCalls Client...\n")
        if config.STRING1:
            await self.one.start()
        if config.STRING2:
            await self.two.start()
        if config.STRING3:
            await self.three.start()
        if config.STRING4:
            await self.four.start()
        if config.STRING5:
            await self.five.start()

    
    async def decorators(self):
        for string, client in [
            (config.STRING1, self.one),
            (config.STRING2, self.two),
            (config.STRING3, self.three),
            (config.STRING4, self.four),
            (config.STRING5, self.five),
        ]:
            if not string:
                continue

            @client.on_update()
            async def _update_handler(_, update: types.Update, _client=client):
                if isinstance(update, types.StreamEnded):
                    if update.stream_type == types.StreamEnded.Type.AUDIO:
                        await self.change_stream(_client, update.chat_id)
                elif isinstance(update, types.ChatUpdate):
                    if update.status in [
                        types.ChatUpdate.Status.KICKED,
                        types.ChatUpdate.Status.LEFT_GROUP,
                        types.ChatUpdate.Status.CLOSED_VOICE_CHAT,
                    ]:
                        await self.stop_stream(update.chat_id)


Bad = Call()
