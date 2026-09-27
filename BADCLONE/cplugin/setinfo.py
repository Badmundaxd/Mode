import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message
from BADCLONE import app
from BADCLONE.utils.decorators.language import language
from BADCLONE.utils.database.clonedb import (
    get_owner_id_from_db,
    get_cloned_support_chat,
    get_cloned_support_channel,
    check_bot_premium,
    set_clone_search_type,
    get_clone_search_type,
    set_clone_stream_caption,
    delete_clone_search_type,
    delete_clone_stream_caption,
)
from BADCLONE.utils.database import clonebotdb
from BADCLONE.core.mongo import mongodb
from config import SUPPORT_CHAT, OWNER_ID

cloneownerdb = mongodb.cloneownerdb

# --- Helper Function: Clean URL/Username ---
def clean_url_or_username(value):
    if "t.me/+" in value or "joinchat" in value or "https://" in value or "http://" in value:
        return value.strip()

    value = value.replace("https://", "").replace("http://", "")
    value = value.replace("t.me/", "").replace("telegram.me/", "")
    value = value.replace("@", "")
    return value.strip("/")

# --- Logging Helper Functions (Async Fixed) ---
async def get_logging_status(bot_id):
    bot_data = await clonebotdb.find_one({"bot_id": bot_id})
    if not bot_data:
        return True
    return bot_data.get("logging", True)

async def get_log_channel(bot_id):
    bot_data = await clonebotdb.find_one({"bot_id": bot_id})
    if not bot_data:
        return "-100"
    return bot_data.get("logchannel", "-100")


# --- Random-list helper (used by the /setplay* commands moved from customization.py) ---
async def add_to_random_list(bot_id, type_key, new_value):
    current_data = await get_clone_search_type(bot_id, type_key)

    if current_data:
        if new_value in current_data:
            return False
        final_value = f"{current_data}|||{new_value}"
    else:
        final_value = new_value

    await set_clone_search_type(bot_id, type_key, final_value)
    return True


# --- Random-list helper (used by the /setstart* commands moved from start.py) ---
async def add_start_content(bot_id, key, value):
    d = await clonebotdb.find_one({"bot_id": bot_id}) or {}
    current = d.get(key)

    if current:
        if isinstance(current, dict):
            current = f"{current['text']} - {current['url']}"
        if value in current:
            return False
        final_value = f"{current}|||{value}"
    else:
        final_value = value

    await clonebotdb.update_one({"bot_id": bot_id}, {"$set": {key: final_value}}, upsert=True)
    return True


# ==========================================================
#   SUPPORT CHAT / CHANNEL / BOT INFO  (unchanged from before)
# ==========================================================

#set clone bot support channel
@Client.on_message(filters.command("setchannel"))
@language
async def set_channel(client: Client, message: Message, _):

    bot = await client.get_me()
    bot_id = bot.id

    # premium check --------------
    # get owner info
    C_OWNER = await get_owner_id_from_db(bot_id)
    OWNERS = [OWNER_ID, C_OWNER]

    if message.from_user.id not in OWNERS:
        return await message.reply_text(_["NOT_C_OWNER"].format(SUPPORT_CHAT))

    # Check if bot has premium
    premium_status = await check_bot_premium(bot_id)
    if premium_status is None:
        return await message.reply_text(_["C_B_P_1"])
    elif not premium_status:
        if message.from_user.id != OWNER_ID:
            return await message.reply_text(_["C_B_P_2"])
        else:
            pass

    # premium check ---------------

    if len(message.command) != 2:
        await message.reply_text(_["C_P_I_2"])
        return

    channel = message.command[1]
    if channel.startswith("@"):
        channel = channel[1:]

    result = await clonebotdb.update_one({"bot_id": bot_id}, {"$set": {"channel": channel}})
    if result.modified_count > 0:
        await message.reply_text(_["C_P_I_4"].format(channel))
    else:
        await message.reply_text(_["C_P_I_6"])


#set clone bot support chat
@Client.on_message(filters.command("setsupport"))
@language
async def set_support(client: Client, message: Message, _):

    bot = await client.get_me()
    bot_id = bot.id

    # premium check --------------
    # get owner info
    C_OWNER = await get_owner_id_from_db(bot_id)
    OWNERS = [OWNER_ID, C_OWNER]

    if message.from_user.id not in OWNERS:
        return await message.reply_text(_["NOT_C_OWNER"].format(SUPPORT_CHAT))

    # Check if bot has premium
    premium_status = await check_bot_premium(bot_id)
    if premium_status is None:
        return await message.reply_text(_["C_B_P_1"])
    elif not premium_status:
        if message.from_user.id != OWNER_ID:
            return await message.reply_text(_["C_B_P_2"])
        else:
            pass

    # premium check ---------------

    if len(message.command) != 2:
        await message.reply_text(_["C_P_I_1"])
        return

    support = message.command[1]
    if support.startswith("@"):
        support = support[1:]

    result = await clonebotdb.update_one({"bot_id": bot_id}, {"$set": {"support": support}})
    if result.modified_count > 0:
        await message.reply_text(_["C_P_I_3"].format(support))
    else:
        await message.reply_text(_["C_P_I_5"])


#check bot info -------------------
@Client.on_message(filters.command("botinfo"))
@language
async def bot_info(client: Client, message: Message, _):

    bot = await client.get_me()
    bot_id = bot.id

    # premium check --------------
    # get owner info
    C_OWNER = await get_owner_id_from_db(bot_id)
    OWNERS = [OWNER_ID, C_OWNER]

    if message.from_user.id not in OWNERS:
        return await message.reply_text(_["NOT_C_OWNER"].format(SUPPORT_CHAT))

    # premium check ---------------

    channel = await get_cloned_support_channel(bot_id)
    support = await get_cloned_support_chat(bot_id)
    premium_status = await check_bot_premium(bot_id)
    if premium_status == True:
        bot_status = "Premium"
    else:
        bot_status = "Free"

     # Format and send the response
    await message.reply_text(
        f"**Bᴏᴛ Iɴғᴏ:**\n"
        f"➤ **Bᴏᴛ ID:** `{bot_id}`\n"
        f"➤ **Cʜᴀɴɴᴇʟ:** @{channel}\n"
        f"➤ **Sᴜᴘᴘᴏʀᴛ Cʜᴀᴛ:** @{support}\n"
        f"➤ **Bᴏᴛ Sᴛᴀᴛᴜs:** {bot_status}"
    )


@Client.on_message(filters.command("logstatus"))
@language
async def check_log_status(client: Client, message: Message, _):
    bot_id = client.me.id
    C_OWNER = await get_owner_id_from_db(bot_id)
    OWNERS = [OWNER_ID, C_OWNER]

    # Check if bot has premium
    premium_status = await check_bot_premium(bot_id)
    if premium_status is None:
        return await message.reply_text(_["C_B_P_1"])
    elif not premium_status:
        if message.from_user.id != OWNER_ID:
            return await message.reply_text(_["C_B_P_2"])
        else:
            pass

    # premium check ---------------

    if len(message.command) != 2:
        await message.reply_text(_["C_P_I_2"])
        return
    if message.from_user.id not in OWNERS:
        return await message.reply_text(_["NOT_C_OWNER"].format(SUPPORT_CHAT))

    logging_status = await get_logging_status(bot_id)
    log_channel = await get_log_channel(bot_id)

    C_LOGGER_STATUS = "Enabled" if logging_status else "Disabled"
    C_LOGGER_VALUE = log_channel if str(log_channel) != "-100" else "Not Set"

    text = f"**ʟᴏɢɢᴇʀ sᴛᴀᴛᴜs :**\n\n - sᴛᴀᴛᴜs : `{C_LOGGER_STATUS}`\n - ʟᴏɢɢᴇʀ ɪᴅ : `{C_LOGGER_VALUE}`"
    await message.reply_text(text)


@Client.on_message(filters.command("logger"))
@language
async def toggle_logging(client: Client, message: Message, _):
    bot = await client.get_me()
    bot_id = bot.id
    C_OWNER = await get_owner_id_from_db(bot_id)
    OWNERS = [OWNER_ID, C_OWNER]

    # Check if bot has premium
    premium_status = await check_bot_premium(bot_id)
    if premium_status is None:
        return await message.reply_text(_["C_B_P_1"])
    elif not premium_status:
        if message.from_user.id != OWNER_ID:
            return await message.reply_text(_["C_B_P_2"])
        else:
            pass

    # premium check ---------------

    if len(message.command) != 2:
        await message.reply_text(_["C_P_I_2"])
        return

    if message.from_user.id not in OWNERS:
        return await message.reply_text(_["NOT_C_OWNER"].format(SUPPORT_CHAT))

    if len(message.command) != 2 or message.command[1].lower() not in ["enable", "disable"]:
        return await message.reply_text("**ᴇxᴀᴍᴘʟᴇ :** \n/logger [ᴇɴᴀʙʟᴇ | ᴅɪsᴀʙʟᴇ]")

    logging_status = message.command[1].lower() == "enable"

    await clonebotdb.update_one(
        {"bot_id": bot_id},
        {"$set": {"logging": logging_status}},
        upsert=True
    )
    await message.reply_text(f"{'ᴇɴᴀʙʟᴇᴅ' if logging_status else 'ᴅɪsᴀʙʟᴇᴅ'} ʟᴏɢɢɪɴɢ.")


@Client.on_message(filters.command("setlogger"))
@language
async def set_log_channel(client: Client, message: Message, _):
    bot = await client.get_me()
    bot_id = bot.id
    C_OWNER = await get_owner_id_from_db(bot_id)
    OWNERS = [OWNER_ID, C_OWNER]
    # Check if bot has premium
    premium_status = await check_bot_premium(bot_id)
    if premium_status is None:
        return await message.reply_text(_["C_B_P_1"])
    elif not premium_status:
        if message.from_user.id != OWNER_ID:
            return await message.reply_text(_["C_B_P_2"])
        else:
            pass

    if message.from_user.id not in OWNERS:
        return await message.reply_text(_["NOT_C_OWNER"].format(SUPPORT_CHAT))

    if len(message.command) != 2:
        return await message.reply_text("**ᴇxᴀᴍᴘʟᴇ :** \n- `/setlogger -100xxxxxxxx`")

    try:
        group_id = int(message.command[1])
    except ValueError:
        return await message.reply_text("ɪɴᴠᴀʟɪᴅ ʟᴏɢɢᴇʀ ɪᴅ !!")

    if not str(group_id).startswith("-100"):
        return await message.reply_text("ɪɴᴠᴀʟɪᴅ ʟᴏɢɢᴇʀ ɪᴅ !!")

    try:
        await client.send_message(group_id, "ʙᴏᴛ ʟᴏɢɢɪɴɢ ᴇɴᴀʙʟᴇᴅ sᴜᴄᴄᴇssғᴜʟʟʏ!")
        await clonebotdb.update_one(
            {"bot_id": bot_id},
            {"$set": {"logchannel": group_id}},
            upsert=True
        )
        return await message.reply_text(f"ʟᴏɢɢɪɴɢ ᴇɴᴀʙʟᴇᴅ ғᴏʀ `{group_id}`.")
    except Exception:
        return await message.reply_text(f"ʙᴏᴛ ᴄᴀɴ'ᴛ sᴇɴᴅ ᴍᴇssᴀɢᴇs ɪɴ ᴛʜɪs ɢʀᴏᴜᴘ!")


# ==========================================================
#   /play RANDOM CONTENT SETTINGS  (moved in from customization.py)
# ==========================================================

@Client.on_message(filters.command(["setplaytext", "addplaytext"]))
@language
async def set_play_text(client: Client, message: Message, _):
    bot = await client.get_me()
    bot_id = bot.id

    # premium check --------------
    C_OWNER = await get_owner_id_from_db(bot_id)
    OWNERS = [OWNER_ID, C_OWNER]
    if message.from_user.id not in OWNERS:
        return await message.reply_text(_["NOT_C_OWNER"].format(SUPPORT_CHAT))
    premium_status = await check_bot_premium(bot_id)
    if premium_status is None:
        return await message.reply_text(_["C_B_P_1"])
    elif not premium_status:
        if message.from_user.id != OWNER_ID:
            return await message.reply_text(_["C_B_P_2"])
        else:
            pass
    # premium check ---------------

    if len(message.command) < 2:
        return await message.reply_text("Usage: /setplaytext <Text/Emoji>")

    text = message.text.split(None, 1)[1]
    await add_to_random_list(bot_id, "text", text)
    await message.reply_text(f"✅ **Added to Random List:**\n\n{text}")


@Client.on_message(filters.command(["setplaysticker", "addplaysticker"]))
@language
async def set_play_sticker(client: Client, message: Message, _):
    bot = await client.get_me()
    bot_id = bot.id

    # premium check --------------
    C_OWNER = await get_owner_id_from_db(bot_id)
    OWNERS = [OWNER_ID, C_OWNER]
    if message.from_user.id not in OWNERS:
        return await message.reply_text(_["NOT_C_OWNER"].format(SUPPORT_CHAT))
    premium_status = await check_bot_premium(bot_id)
    if premium_status is None:
        return await message.reply_text(_["C_B_P_1"])
    elif not premium_status:
        if message.from_user.id != OWNER_ID:
            return await message.reply_text(_["C_B_P_2"])
        else:
            pass
    # premium check ---------------

    if not message.reply_to_message or not message.reply_to_message.sticker:
        return await message.reply_text("Usage: Reply to a Sticker with /setplaysticker")

    file_id = message.reply_to_message.sticker.file_id
    await add_to_random_list(bot_id, "sticker", file_id)
    await message.reply_text("✅ **Sticker Added to Random List!**")


@Client.on_message(filters.command(["setplayanimation", "addplayanimation"]))
@language
async def set_play_gif(client: Client, message: Message, _):
    bot = await client.get_me()
    bot_id = bot.id

    # premium check --------------
    C_OWNER = await get_owner_id_from_db(bot_id)
    OWNERS = [OWNER_ID, C_OWNER]
    if message.from_user.id not in OWNERS:
        return await message.reply_text(_["NOT_C_OWNER"].format(SUPPORT_CHAT))
    premium_status = await check_bot_premium(bot_id)
    if premium_status is None:
        return await message.reply_text(_["C_B_P_1"])
    elif not premium_status:
        if message.from_user.id != OWNER_ID:
            return await message.reply_text(_["C_B_P_2"])
        else:
            pass
    # premium check ---------------

    if not message.reply_to_message or not message.reply_to_message.animation:
        return await message.reply_text("Usage: Reply to a GIF with /setplayanimation")

    file_id = message.reply_to_message.animation.file_id
    await add_to_random_list(bot_id, "animation", file_id)

    current_text = await get_clone_search_type(bot_id, "text")
    if not current_text:
        await set_clone_search_type(bot_id, "text", "⠀")

    await message.reply_text("✅ **GIF Added to Random List!**")


@Client.on_message(filters.command(["setplayvideo", "addplayvideo"]))
@language
async def set_play_video(client: Client, message: Message, _):
    bot = await client.get_me()
    bot_id = bot.id

    # premium check --------------
    C_OWNER = await get_owner_id_from_db(bot_id)
    OWNERS = [OWNER_ID, C_OWNER]
    if message.from_user.id not in OWNERS:
        return await message.reply_text(_["NOT_C_OWNER"].format(SUPPORT_CHAT))
    premium_status = await check_bot_premium(bot_id)
    if premium_status is None:
        return await message.reply_text(_["C_B_P_1"])
    elif not premium_status:
        if message.from_user.id != OWNER_ID:
            return await message.reply_text(_["C_B_P_2"])
        else:
            pass
    # premium check ---------------

    if not message.reply_to_message or not message.reply_to_message.video:
        return await message.reply_text("Usage: Reply to a Video with /setplayvideo")

    file_id = message.reply_to_message.video.file_id
    await add_to_random_list(bot_id, "video", file_id)

    current_text = await get_clone_search_type(bot_id, "text")
    if not current_text:
        await set_clone_search_type(bot_id, "text", "⠀")

    await message.reply_text("✅ **Video Added to Random List!**\n(Searching text hidden automatically)")


@Client.on_message(filters.command(["setplayphoto", "addplayphoto"]))
@language
async def set_play_photo(client: Client, message: Message, _):
    bot = await client.get_me()
    bot_id = bot.id

    # premium check --------------
    C_OWNER = await get_owner_id_from_db(bot_id)
    OWNERS = [OWNER_ID, C_OWNER]
    if message.from_user.id not in OWNERS:
        return await message.reply_text(_["NOT_C_OWNER"].format(SUPPORT_CHAT))
    premium_status = await check_bot_premium(bot_id)
    if premium_status is None:
        return await message.reply_text(_["C_B_P_1"])
    elif not premium_status:
        if message.from_user.id != OWNER_ID:
            return await message.reply_text(_["C_B_P_2"])
        else:
            pass
    # premium check ---------------

    if not message.reply_to_message or not message.reply_to_message.photo:
        return await message.reply_text("Usage: Reply to a Photo with /setplayphoto")

    file_id = message.reply_to_message.photo.file_id
    await add_to_random_list(bot_id, "photo", file_id)

    current_text = await get_clone_search_type(bot_id, "text")
    if not current_text:
        await set_clone_search_type(bot_id, "text", "⠀")

    await message.reply_text("✅ **Photo Added to Random List!**")


@Client.on_message(filters.command("setstreamtext"))
@language
async def set_stream_text(client: Client, message: Message, _):
    bot = await client.get_me()
    bot_id = bot.id

    # premium check --------------
    C_OWNER = await get_owner_id_from_db(bot_id)
    OWNERS = [OWNER_ID, C_OWNER]
    if message.from_user.id not in OWNERS:
        return await message.reply_text(_["NOT_C_OWNER"].format(SUPPORT_CHAT))
    premium_status = await check_bot_premium(bot_id)
    if premium_status is None:
        return await message.reply_text(_["C_B_P_1"])
    elif not premium_status:
        if message.from_user.id != OWNER_ID:
            return await message.reply_text(_["C_B_P_2"])
        else:
            pass
    # premium check ---------------

    if len(message.command) < 2:
        return await message.reply_text(
            "**Usage:** /setstreamtext <Your Caption>\n\n"
            "**Available Variables:**\n"
            "`{1}` : Song Name\n"
            "`{2}` : Duration\n"
            "`{3}` : Requested By\n\n"
            "**Example:**\n"
            "`/setstreamtext 🎸 Playing: {1} | ⏳ Time: {2}`"
        )

    text = message.text.split(None, 1)[1]
    await set_clone_stream_caption(bot_id, text)
    await message.reply_text(f"✅ **Stream Caption Updated:**\n\n{text}")


@Client.on_message(filters.command(["delplay", "resetplay", "delplaymode"]))
@language
async def delete_play_mode(client: Client, message: Message, _):
    bot = await client.get_me()
    bot_id = bot.id

    # premium check --------------
    C_OWNER = await get_owner_id_from_db(bot_id)
    OWNERS = [OWNER_ID, C_OWNER]
    if message.from_user.id not in OWNERS:
        return await message.reply_text(_["NOT_C_OWNER"].format(SUPPORT_CHAT))
    premium_status = await check_bot_premium(bot_id)
    if premium_status is None:
        return await message.reply_text(_["C_B_P_1"])
    elif not premium_status:
        if message.from_user.id != OWNER_ID:
            return await message.reply_text(_["C_B_P_2"])
        else:
            pass
    # premium check ---------------

    await delete_clone_search_type(bot_id)
    await message.reply_text("🗑️ **Search Mode Reset!**\nAll saved random lists cleared.")


@Client.on_message(filters.command(["delstreamtext", "resetstreamtext"]))
@language
async def delete_stream_text_cmd(client: Client, message: Message, _):
    bot = await client.get_me()
    bot_id = bot.id

    # premium check --------------
    C_OWNER = await get_owner_id_from_db(bot_id)
    OWNERS = [OWNER_ID, C_OWNER]
    if message.from_user.id not in OWNERS:
        return await message.reply_text(_["NOT_C_OWNER"].format(SUPPORT_CHAT))
    premium_status = await check_bot_premium(bot_id)
    if premium_status is None:
        return await message.reply_text(_["C_B_P_1"])
    elif not premium_status:
        if message.from_user.id != OWNER_ID:
            return await message.reply_text(_["C_B_P_2"])
        else:
            pass
    # premium check ---------------

    await delete_clone_stream_caption(bot_id)
    await message.reply_text("🗑️ **Stream Caption Reset!**")


# ==========================================================
#   /start PANEL SETTINGS  (moved in from start.py)
# ==========================================================

@Client.on_message(filters.command(["transfer", "transferowner"]))
@language
async def transfer_owner(client: Client, message: Message, _):
    bot = await client.get_me()
    bot_id = bot.id

    # premium check --------------
    C_OWNER = await get_owner_id_from_db(bot_id)
    OWNERS = [OWNER_ID, C_OWNER]
    if message.from_user.id not in OWNERS:
        return await message.reply_text(_["NOT_C_OWNER"].format(SUPPORT_CHAT))
    premium_status = await check_bot_premium(bot_id)
    if premium_status is None:
        return await message.reply_text(_["C_B_P_1"])
    elif not premium_status:
        if message.from_user.id != OWNER_ID:
            return await message.reply_text(_["C_B_P_2"])
        else:
            pass
    # premium check ---------------

    user = message.from_user
    new_owner = None
    if message.reply_to_message:
        new_owner = message.reply_to_message.from_user
    elif len(message.command) > 1:
        try:
            new_owner = await client.get_users(message.command[1])
        except Exception:
            return await message.reply_text("❌ User not found! Check Username or ID.")
    else:
        return await message.reply_text("❌ **Usage:**\nReply to a user or type `/transfer @username`.")

    if new_owner.is_bot:
        return await message.reply_text("❌ You cannot make a bot the owner.")
    if new_owner.id == user.id:
        return await message.reply_text("❌ You are already the owner.")

    await clonebotdb.update_one({"bot_id": bot_id}, {"$set": {"user_id": new_owner.id}})
    await cloneownerdb.update_one({"bot_id": bot_id}, {"$set": {"user_id": new_owner.id}}, upsert=True)

    await message.reply_text(f"✅ **Ownership Transferred!**\n👑 New Owner: {new_owner.mention}")


@Client.on_message(filters.command("viewstartsettings"))
@language
async def view_start_settings(client: Client, message: Message, _):
    bot = await client.get_me()
    bot_id = bot.id

    # premium check --------------
    C_OWNER = await get_owner_id_from_db(bot_id)
    OWNERS = [OWNER_ID, C_OWNER]
    if message.from_user.id not in OWNERS:
        return await message.reply_text(_["NOT_C_OWNER"].format(SUPPORT_CHAT))
    premium_status = await check_bot_premium(bot_id)
    if premium_status is None:
        return await message.reply_text(_["C_B_P_1"])
    elif not premium_status:
        if message.from_user.id != OWNER_ID:
            return await message.reply_text(_["C_B_P_2"])
        else:
            pass
    # premium check ---------------

    d = await clonebotdb.find_one({"bot_id": bot_id}) or {}
    pos = d.get("start_btn_pos", "TOP")
    await message.reply_text(f"⚙️ **Settings Viewed**\nButton Position: `{pos}`")


@Client.on_message(filters.command("resetstartsetting"))
@language
async def reset_start_settings(client: Client, message: Message, _):
    bot = await client.get_me()
    bot_id = bot.id

    # premium check --------------
    C_OWNER = await get_owner_id_from_db(bot_id)
    OWNERS = [OWNER_ID, C_OWNER]
    if message.from_user.id not in OWNERS:
        return await message.reply_text(_["NOT_C_OWNER"].format(SUPPORT_CHAT))
    premium_status = await check_bot_premium(bot_id)
    if premium_status is None:
        return await message.reply_text(_["C_B_P_1"])
    elif not premium_status:
        if message.from_user.id != OWNER_ID:
            return await message.reply_text(_["C_B_P_2"])
        else:
            pass
    # premium check ---------------

    await clonebotdb.update_one({"bot_id": bot_id}, {"$unset": {
        "start_image": "", "start_video": "", "start_sticker": "",
        "start_animation": "", "start_caption": "", "start_button": "",
        "start_btn_pos": "", "start_reaction": "", "start_effect": ""
    }})
    await message.reply_text("🔄 All Start Settings Reset!")


@Client.on_message(filters.command(["setstartreaction", "addstartreaction"]))
@language
async def set_start_reaction_cmd(client: Client, message: Message, _):
    bot = await client.get_me()
    bot_id = bot.id

    # premium check --------------
    C_OWNER = await get_owner_id_from_db(bot_id)
    OWNERS = [OWNER_ID, C_OWNER]
    if message.from_user.id not in OWNERS:
        return await message.reply_text(_["NOT_C_OWNER"].format(SUPPORT_CHAT))
    premium_status = await check_bot_premium(bot_id)
    if premium_status is None:
        return await message.reply_text(_["C_B_P_1"])
    elif not premium_status:
        if message.from_user.id != OWNER_ID:
            return await message.reply_text(_["C_B_P_2"])
        else:
            pass
    # premium check ---------------

    if len(message.command) < 2:
        return await message.reply_text("❌ **Usage:** `/setstartreaction 🔥`\nYou can add multiple.")

    emoji = message.command[1]
    await add_start_content(bot_id, "start_reaction", emoji)
    await message.reply_text(f"✅ Start Reaction Added: {emoji}")


@Client.on_message(filters.command(["delstartreaction", "resetstartreaction"]))
@language
async def del_start_reaction_cmd(client: Client, message: Message, _):
    bot = await client.get_me()
    bot_id = bot.id

    # premium check --------------
    C_OWNER = await get_owner_id_from_db(bot_id)
    OWNERS = [OWNER_ID, C_OWNER]
    if message.from_user.id not in OWNERS:
        return await message.reply_text(_["NOT_C_OWNER"].format(SUPPORT_CHAT))
    premium_status = await check_bot_premium(bot_id)
    if premium_status is None:
        return await message.reply_text(_["C_B_P_1"])
    elif not premium_status:
        if message.from_user.id != OWNER_ID:
            return await message.reply_text(_["C_B_P_2"])
        else:
            pass
    # premium check ---------------

    await clonebotdb.update_one({"bot_id": bot_id}, {"$unset": {"start_reaction": ""}})
    await message.reply_text("✅ Start Reaction Deleted (Default Random will be used)!")


@Client.on_message(filters.command(["setstarteffect", "addstarteffect"]))
@language
async def set_start_effect_cmd(client: Client, message: Message, _):
    bot = await client.get_me()
    bot_id = bot.id

    # premium check --------------
    C_OWNER = await get_owner_id_from_db(bot_id)
    OWNERS = [OWNER_ID, C_OWNER]
    if message.from_user.id not in OWNERS:
        return await message.reply_text(_["NOT_C_OWNER"].format(SUPPORT_CHAT))
    premium_status = await check_bot_premium(bot_id)
    if premium_status is None:
        return await message.reply_text(_["C_B_P_1"])
    elif not premium_status:
        if message.from_user.id != OWNER_ID:
            return await message.reply_text(_["C_B_P_2"])
        else:
            pass
    # premium check ---------------

    if len(message.command) < 2:
        return await message.reply_text("❌ **Usage:** `/setstarteffect 🔥` or ID\n\nSupported: 🔥, 👍, 👎, ❤️, 🎉, 💩")

    EFFECT_MAP = {
        "🔥": "5104841245755180586",
        "👍": "5107584321108051014",
        "👎": "5104858069142078462",
        "❤️": "5044134455711629726",
        "🎉": "5046509860389126442",
        "💩": "5046589136895476101"
    }

    arg = message.command[1]
    effect_id = EFFECT_MAP.get(arg, arg)

    await add_start_content(bot_id, "start_effect", effect_id)
    await message.reply_text("✅ Start Effect Added!")


@Client.on_message(filters.command(["delstarteffect", "resetstarteffect"]))
@language
async def del_start_effect_cmd(client: Client, message: Message, _):
    bot = await client.get_me()
    bot_id = bot.id

    # premium check --------------
    C_OWNER = await get_owner_id_from_db(bot_id)
    OWNERS = [OWNER_ID, C_OWNER]
    if message.from_user.id not in OWNERS:
        return await message.reply_text(_["NOT_C_OWNER"].format(SUPPORT_CHAT))
    premium_status = await check_bot_premium(bot_id)
    if premium_status is None:
        return await message.reply_text(_["C_B_P_1"])
    elif not premium_status:
        if message.from_user.id != OWNER_ID:
            return await message.reply_text(_["C_B_P_2"])
        else:
            pass
    # premium check ---------------

    await clonebotdb.update_one({"bot_id": bot_id}, {"$unset": {"start_effect": ""}})
    await message.reply_text("✅ Start Effect Deleted (Default Random will be used)!")


@Client.on_message(filters.command(["setstartimg", "addstartimg"]))
@language
async def set_start_image_cmd(client: Client, message: Message, _):
    bot = await client.get_me()
    bot_id = bot.id

    # premium check --------------
    C_OWNER = await get_owner_id_from_db(bot_id)
    OWNERS = [OWNER_ID, C_OWNER]
    if message.from_user.id not in OWNERS:
        return await message.reply_text(_["NOT_C_OWNER"].format(SUPPORT_CHAT))
    premium_status = await check_bot_premium(bot_id)
    if premium_status is None:
        return await message.reply_text(_["C_B_P_1"])
    elif not premium_status:
        if message.from_user.id != OWNER_ID:
            return await message.reply_text(_["C_B_P_2"])
        else:
            pass
    # premium check ---------------

    if message.reply_to_message and message.reply_to_message.photo:
        await add_start_content(bot_id, "start_image", message.reply_to_message.photo.file_id)
        await message.reply_text("✅ Start Image Added to Random List!")
    else:
        await message.reply_text("Reply to a photo.")


@Client.on_message(filters.command(["delstartimg", "resetstartimg"]))
@language
async def del_start_image_cmd(client: Client, message: Message, _):
    bot = await client.get_me()
    bot_id = bot.id

    # premium check --------------
    C_OWNER = await get_owner_id_from_db(bot_id)
    OWNERS = [OWNER_ID, C_OWNER]
    if message.from_user.id not in OWNERS:
        return await message.reply_text(_["NOT_C_OWNER"].format(SUPPORT_CHAT))
    premium_status = await check_bot_premium(bot_id)
    if premium_status is None:
        return await message.reply_text(_["C_B_P_1"])
    elif not premium_status:
        if message.from_user.id != OWNER_ID:
            return await message.reply_text(_["C_B_P_2"])
        else:
            pass
    # premium check ---------------

    await clonebotdb.update_one({"bot_id": bot_id}, {"$unset": {"start_image": ""}})
    await message.reply_text("✅ Start Images Deleted!")


@Client.on_message(filters.command(["setstartvideo", "addstartvideo"]))
@language
async def set_start_video_cmd(client: Client, message: Message, _):
    bot = await client.get_me()
    bot_id = bot.id

    # premium check --------------
    C_OWNER = await get_owner_id_from_db(bot_id)
    OWNERS = [OWNER_ID, C_OWNER]
    if message.from_user.id not in OWNERS:
        return await message.reply_text(_["NOT_C_OWNER"].format(SUPPORT_CHAT))
    premium_status = await check_bot_premium(bot_id)
    if premium_status is None:
        return await message.reply_text(_["C_B_P_1"])
    elif not premium_status:
        if message.from_user.id != OWNER_ID:
            return await message.reply_text(_["C_B_P_2"])
        else:
            pass
    # premium check ---------------

    if message.reply_to_message and message.reply_to_message.video:
        await add_start_content(bot_id, "start_video", message.reply_to_message.video.file_id)
        await message.reply_text("✅ Start Video Added to Random List!")
    else:
        await message.reply_text("Reply to a video.")


@Client.on_message(filters.command(["delstartvideo", "resetstartvideo"]))
@language
async def del_start_video_cmd(client: Client, message: Message, _):
    bot = await client.get_me()
    bot_id = bot.id

    # premium check --------------
    C_OWNER = await get_owner_id_from_db(bot_id)
    OWNERS = [OWNER_ID, C_OWNER]
    if message.from_user.id not in OWNERS:
        return await message.reply_text(_["NOT_C_OWNER"].format(SUPPORT_CHAT))
    premium_status = await check_bot_premium(bot_id)
    if premium_status is None:
        return await message.reply_text(_["C_B_P_1"])
    elif not premium_status:
        if message.from_user.id != OWNER_ID:
            return await message.reply_text(_["C_B_P_2"])
        else:
            pass
    # premium check ---------------

    await clonebotdb.update_one({"bot_id": bot_id}, {"$unset": {"start_video": ""}})
    await message.reply_text("✅ Start Videos Deleted!")


@Client.on_message(filters.command(["setstartsticker", "addstartsticker"]))
@language
async def set_start_sticker_cmd(client: Client, message: Message, _):
    bot = await client.get_me()
    bot_id = bot.id

    # premium check --------------
    C_OWNER = await get_owner_id_from_db(bot_id)
    OWNERS = [OWNER_ID, C_OWNER]
    if message.from_user.id not in OWNERS:
        return await message.reply_text(_["NOT_C_OWNER"].format(SUPPORT_CHAT))
    premium_status = await check_bot_premium(bot_id)
    if premium_status is None:
        return await message.reply_text(_["C_B_P_1"])
    elif not premium_status:
        if message.from_user.id != OWNER_ID:
            return await message.reply_text(_["C_B_P_2"])
        else:
            pass
    # premium check ---------------

    if message.reply_to_message and message.reply_to_message.sticker:
        await add_start_content(bot_id, "start_sticker", message.reply_to_message.sticker.file_id)
        await message.reply_text("✅ Sticker Added to Random List!")
    else:
        await message.reply_text("Reply to a sticker.")


@Client.on_message(filters.command(["delstartsticker", "resetstartsticker"]))
@language
async def del_start_sticker_cmd(client: Client, message: Message, _):
    bot = await client.get_me()
    bot_id = bot.id

    # premium check --------------
    C_OWNER = await get_owner_id_from_db(bot_id)
    OWNERS = [OWNER_ID, C_OWNER]
    if message.from_user.id not in OWNERS:
        return await message.reply_text(_["NOT_C_OWNER"].format(SUPPORT_CHAT))
    premium_status = await check_bot_premium(bot_id)
    if premium_status is None:
        return await message.reply_text(_["C_B_P_1"])
    elif not premium_status:
        if message.from_user.id != OWNER_ID:
            return await message.reply_text(_["C_B_P_2"])
        else:
            pass
    # premium check ---------------

    await clonebotdb.update_one({"bot_id": bot_id}, {"$unset": {"start_sticker": ""}})
    await message.reply_text("✅ Stickers Deleted!")


@Client.on_message(filters.command(["setstartanimation", "addstartanimation"]))
@language
async def set_start_animation_cmd(client: Client, message: Message, _):
    bot = await client.get_me()
    bot_id = bot.id

    # premium check --------------
    C_OWNER = await get_owner_id_from_db(bot_id)
    OWNERS = [OWNER_ID, C_OWNER]
    if message.from_user.id not in OWNERS:
        return await message.reply_text(_["NOT_C_OWNER"].format(SUPPORT_CHAT))
    premium_status = await check_bot_premium(bot_id)
    if premium_status is None:
        return await message.reply_text(_["C_B_P_1"])
    elif not premium_status:
        if message.from_user.id != OWNER_ID:
            return await message.reply_text(_["C_B_P_2"])
        else:
            pass
    # premium check ---------------

    if message.reply_to_message and message.reply_to_message.animation:
        await add_start_content(bot_id, "start_animation", message.reply_to_message.animation.file_id)
        await message.reply_text("✅ Animation Added to Random List!")
    else:
        await message.reply_text("Reply to a GIF.")


@Client.on_message(filters.command(["delstartanimation", "resetstartanimation"]))
@language
async def del_start_animation_cmd(client: Client, message: Message, _):
    bot = await client.get_me()
    bot_id = bot.id

    # premium check --------------
    C_OWNER = await get_owner_id_from_db(bot_id)
    OWNERS = [OWNER_ID, C_OWNER]
    if message.from_user.id not in OWNERS:
        return await message.reply_text(_["NOT_C_OWNER"].format(SUPPORT_CHAT))
    premium_status = await check_bot_premium(bot_id)
    if premium_status is None:
        return await message.reply_text(_["C_B_P_1"])
    elif not premium_status:
        if message.from_user.id != OWNER_ID:
            return await message.reply_text(_["C_B_P_2"])
        else:
            pass
    # premium check ---------------

    await clonebotdb.update_one({"bot_id": bot_id}, {"$unset": {"start_animation": ""}})
    await message.reply_text("✅ Animations Deleted!")


@Client.on_message(filters.command(["setstartcaption", "addstartcaption"]))
@language
async def set_start_caption_cmd(client: Client, message: Message, _):
    bot = await client.get_me()
    bot_id = bot.id

    # premium check --------------
    C_OWNER = await get_owner_id_from_db(bot_id)
    OWNERS = [OWNER_ID, C_OWNER]
    if message.from_user.id not in OWNERS:
        return await message.reply_text(_["NOT_C_OWNER"].format(SUPPORT_CHAT))
    premium_status = await check_bot_premium(bot_id)
    if premium_status is None:
        return await message.reply_text(_["C_B_P_1"])
    elif not premium_status:
        if message.from_user.id != OWNER_ID:
            return await message.reply_text(_["C_B_P_2"])
        else:
            pass
    # premium check ---------------

    if message.reply_to_message:
        text = message.reply_to_message.text.html if message.reply_to_message.text else message.reply_to_message.caption.html
        await add_start_content(bot_id, "start_caption", text)
        await message.reply_text("✅ Caption Added to Random List!")
    else:
        await message.reply_text("Reply to a text to add as Caption.")


@Client.on_message(filters.command(["delstartcaption", "resetstartcaption"]))
@language
async def del_start_caption_cmd(client: Client, message: Message, _):
    bot = await client.get_me()
    bot_id = bot.id

    # premium check --------------
    C_OWNER = await get_owner_id_from_db(bot_id)
    OWNERS = [OWNER_ID, C_OWNER]
    if message.from_user.id not in OWNERS:
        return await message.reply_text(_["NOT_C_OWNER"].format(SUPPORT_CHAT))
    premium_status = await check_bot_premium(bot_id)
    if premium_status is None:
        return await message.reply_text(_["C_B_P_1"])
    elif not premium_status:
        if message.from_user.id != OWNER_ID:
            return await message.reply_text(_["C_B_P_2"])
        else:
            pass
    # premium check ---------------

    await clonebotdb.update_one({"bot_id": bot_id}, {"$unset": {"start_caption": ""}})
    await message.reply_text("✅ Captions Deleted!")


@Client.on_message(filters.command(["setstartbutton", "addstartbutton"]))
@language
async def set_start_button_cmd(client: Client, message: Message, _):
    bot = await client.get_me()
    bot_id = bot.id

    # premium check --------------
    C_OWNER = await get_owner_id_from_db(bot_id)
    OWNERS = [OWNER_ID, C_OWNER]
    if message.from_user.id not in OWNERS:
        return await message.reply_text(_["NOT_C_OWNER"].format(SUPPORT_CHAT))
    premium_status = await check_bot_premium(bot_id)
    if premium_status is None:
        return await message.reply_text(_["C_B_P_1"])
    elif not premium_status:
        if message.from_user.id != OWNER_ID:
            return await message.reply_text(_["C_B_P_2"])
        else:
            pass
    # premium check ---------------

    data = message.text.split(None, 1)[1] if len(message.command) > 1 else None

    if not data or "-" not in data:
        return await message.reply_text("Format: `/addstartbutton Text - URL`")

    txt, url = data.split("-", 1)
    btn_str = f"{txt.strip()} - {url.strip()}"

    await add_start_content(bot_id, "start_button", btn_str)
    await message.reply_text("✅ Button Added to Random List!")


@Client.on_message(filters.command(["delstartbutton", "resetstartbutton"]))
@language
async def del_start_button_cmd(client: Client, message: Message, _):
    bot = await client.get_me()
    bot_id = bot.id

    # premium check --------------
    C_OWNER = await get_owner_id_from_db(bot_id)
    OWNERS = [OWNER_ID, C_OWNER]
    if message.from_user.id not in OWNERS:
        return await message.reply_text(_["NOT_C_OWNER"].format(SUPPORT_CHAT))
    premium_status = await check_bot_premium(bot_id)
    if premium_status is None:
        return await message.reply_text(_["C_B_P_1"])
    elif not premium_status:
        if message.from_user.id != OWNER_ID:
            return await message.reply_text(_["C_B_P_2"])
        else:
            pass
    # premium check ---------------

    await clonebotdb.update_one({"bot_id": bot_id}, {"$unset": {"start_button": ""}})
    await message.reply_text("✅ Custom Buttons Deleted!")


@Client.on_message(filters.command("setbtnpos"))
@language
async def set_btn_pos_cmd(client: Client, message: Message, _):
    bot = await client.get_me()
    bot_id = bot.id

    # premium check --------------
    C_OWNER = await get_owner_id_from_db(bot_id)
    OWNERS = [OWNER_ID, C_OWNER]
    if message.from_user.id not in OWNERS:
        return await message.reply_text(_["NOT_C_OWNER"].format(SUPPORT_CHAT))
    premium_status = await check_bot_premium(bot_id)
    if premium_status is None:
        return await message.reply_text(_["C_B_P_1"])
    elif not premium_status:
        if message.from_user.id != OWNER_ID:
            return await message.reply_text(_["C_B_P_2"])
        else:
            pass
    # premium check ---------------

    if len(message.command) < 2:
        return await message.reply_text("Usage: `/setbtnpos [UP/DOWN/MID]`")

    raw_pos = message.command[1].upper()
    valid_pos = ["UP", "TOP", "DOWN", "BOTTOM", "MID", "MIDDLE", "LEFT", "RIGHT"]

    if raw_pos in valid_pos:
        if raw_pos == "TOP": raw_pos = "UP"
        if raw_pos == "BOTTOM": raw_pos = "DOWN"
        if raw_pos == "MIDDLE": raw_pos = "MID"

        await clonebotdb.update_one({"bot_id": bot_id}, {"$set": {"start_btn_pos": raw_pos}}, upsert=True)
        await message.reply_text(f"✅ Button Position: **{raw_pos}**")
    else:
        await message.reply_text("❌ Invalid! Use: UP, DOWN, MID")

