import random
import time

from youtubesearchpython.__future__ import VideosSearch
from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

import config
from AnonMusic import app
from AnonMusic.misc import _boot_
from AnonMusic.plugins.sudo.sudoers import sudoers_list
from AnonMusic.utils.database import (
    add_served_chat,
    add_served_user,
    blacklisted_chats,
    get_lang,
    is_banned_user,
    is_on_off,
)
from AnonMusic.utils.decorators.language import LanguageStart
from AnonMusic.utils.formatters import get_readable_time
from AnonMusic.utils.inline import help_pannel, private_panel, start_panel
from config import BANNED_USERS
from strings import get_string

# 🎆 Latest Message Effects IDs (Only for latest Pyrogram)
EFFECT_ID = [
    5104841245755180586,
    5107584321108051014,
    5104841245755180586,
    5107584321108051014,
]

# 🌄 Random Start Images
Kanha = [
    "https://files.catbox.moe/v00l7e.jpg",
    "https://files.catbox.moe/uow54p.jpg",
    "https://files.catbox.moe/z0t6l3.jpg",
    "https://files.catbox.moe/jdw0il.jpg",
    "https://files.catbox.moe/izfi0y.jpg",
    "https://files.catbox.moe/7wx3ha.jpg",
    "https://files.catbox.moe/2u0srm.jpg",
    "https://files.catbox.moe/tqwy0q.jpg",
    "https://files.catbox.moe/vbgrx1.jpg"
]

# 🍓 Random Reactions
REACTIONS = ["🍓", "🔥", "❤️", "⚡", "🎉", "🥰", "👏", "💫", "🎶", "🌟", "💩", "👍", "👎"]


@app.on_message(filters.command(["start"]) & filters.private & ~BANNED_USERS)
@LanguageStart
async def start_pm(client, message: Message, _):
    await add_served_user(message.from_user.id)

    # 🍓 Random reaction with big=True
    try:
        await message.react(random.choice(REACTIONS), big=True)
    except:
        pass

    if len(message.text.split()) > 1:
        name = message.text.split(None, 1)[1]

        if name.startswith("help"):
            keyboard = help_pannel(_)
            return await message.reply_photo(
                photo=random.choice(Kanha),  
                caption=_["help_1"].format(config.SUPPORT_CHAT),
                reply_markup=keyboard,
            )

        if name.startswith("sud"):
            await sudoers_list(client=client, message=message, _=_)
            return

        if name.startswith("inf"):
            m = await message.reply_text("🔎 Searching...")
            query = name.replace("info_", "", 1)
            query = f"https://www.youtube.com/watch?v={query}"
            results = VideosSearch(query, limit=1)
            data = (await results.next())["result"][0]
            
            # Info track logic
            searched_text = _["start_6"].format(
                data["title"], data["duration"], data["viewCount"]["short"], 
                data["publishedTime"], data["channel"]["link"], data["channel"]["name"], app.mention
            )
            key = InlineKeyboardMarkup([[InlineKeyboardButton(_["S_B_8"], url=data["link"]), InlineKeyboardButton(_["S_B_9"], url=config.SUPPORT_CHAT)]])
            
            await m.delete()
            # Latest Features Enabled here
            await app.send_photo(
                chat_id=message.chat.id,
                photo=data["thumbnails"][0]["url"].split("?")[0],
                has_spoiler=True,
                protect_content=True,
                caption=searched_text,
                reply_markup=key,
            )
            return

    # 🌄 Normal Start with Effects & Protection
    out = private_panel(_)

    await message.reply_photo(
        photo=random.choice(Kanha),
        has_spoiler=True,
        protect_content=True,
        message_effect_id=random.choice(EFFECT_ID),
        caption=_["start_2"].format(message.from_user.mention, app.mention),
        reply_markup=InlineKeyboardMarkup(out),
    )

@app.on_message(filters.command(["start"]) & filters.group & ~BANNED_USERS)
@LanguageStart
async def start_gp(client, message: Message, _):
    out = start_panel(_)
    uptime = int(time.time() - _boot_)
    
    # Latest Features for Group
    await message.reply_photo(
        photo=config.START_IMG_URL,
        has_spoiler=True,
        protect_content=True,
        caption=_["start_1"].format(app.mention, get_readable_time(uptime)),
        reply_markup=InlineKeyboardMarkup(out),
    )
    await add_served_chat(message.chat.id)
