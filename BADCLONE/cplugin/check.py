import asyncio
from BADCLONE import app
from pyrogram.types import ChatMemberUpdated, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.types import ChatJoinRequest, InlineKeyboardButton, InlineKeyboardMarkup
from pyrogram import filters, Client, enums
from logging import getLogger
from pyrogram import *
from pyrogram.types import *
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from BADCLONE.misc import SUDOERS
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import (
    ChatAdminRequired,
    InviteRequestSent,
    UserAlreadyParticipant,
    UserNotParticipant,
)

from BADCLONE.plugins.tools.clone import CLONES

TEMP_CLONES = set()

BOT_OFFICE = "-1003758847277"

# --------------------------------------------------------------------------------- #
# --------------------------------------------------------------------------------- #
# --------------------------------------------------------------------------------- #

async def get_all_member_ids(client: Client, chat_id: int) -> list:

    try:
        # Initialize an empty list to store member IDs
        member_ids = []

        # Fetch all chat members and store their IDs
        async for member in client.get_chat_members(chat_id):
            member_ids.append(member.user.id)

        # Return the list of member IDs
        return member_ids

    except Exception as e:
        # Handle any exceptions that may occur
        print(f"Error fetching member IDs: {e}")
        return []


# --------------------------------------------------------------------------------- #
# --------------------------------------------------------------------------------- #
# --------------------------------------------------------------------------------- #


LOGGER = getLogger(__name__)

@Client.on_chat_member_updated(filters.group, group=-3)
async def check_clones(client, member: ChatMemberUpdated):
    chat_id = member.chat.id
    user = member.new_chat_member.user if member.new_chat_member else member.from_user

    #IF BOT OFFICE
    if chat_id == int(BOT_OFFICE):
        return

    # Check if a new bot is added to the group
    if member.new_chat_member and not member.old_chat_member and member.new_chat_member.status != "kicked":
        try:
            bot_id = user.id
            member_ids = await get_all_member_ids(client, chat_id)
            member_ids_set = set(member_ids)

            # Update TEMP_CLONES with the latest CLONES data
            TEMP_CLONES.clear()
            TEMP_CLONES.update(CLONES)

            # Check if the bot is in CLONES
            if bot_id in CLONES:
                # Check if any other bot from CLONES is already in the group
                matching_ids = member_ids_set & TEMP_CLONES

                if len(matching_ids) > 1:  # More than one bot from CLONES in the group
                    await asyncio.sleep(1)
                    await client.send_message(chat_id, f"Lᴏᴏᴋs ʟɪᴋᴇ ᴏɴᴇ ᴏғ ᴍʏ ᴛᴇᴀᴍᴍᴀᴛᴇs ɪs ᴀʟʀᴇᴀᴅʏ ʜᴇʀᴇ! Oɴʟʏ ᴏɴᴇ ᴏғ ᴜs ᴄᴀɴ sᴛᴀʏ. I’ʟʟ ᴛᴀᴋᴇ ᴍʏ ʟᴇᴀᴠᴇ ɴᴏᴡ. ! ✨")
                    await client.leave_chat(chat_id)
                    return

        except Exception as e:
            LOGGER.error(f"Error: {e}")
