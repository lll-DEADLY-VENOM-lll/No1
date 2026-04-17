from pyrogram import Client, errors, filters # filters add kiya
from pyrogram.enums import ChatMemberStatus, ParseMode
from pyrogram.types import Chat
from pyrogram.handlers import MessageHandler # Handler add kiya
from openai import AsyncOpenAI # AI add kiya
import os
import config
from ..logging import LOGGER

# OpenAI Setup
aio_client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)

class Anony(Client):
    def __init__(self):
        LOGGER(__name__).info("🈵 Initializing bot client")
        super().__init__(
            name="AnonMusic",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            bot_token=config.BOT_TOKEN,
            in_memory=True,
            parse_mode=ParseMode.HTML,
            max_concurrent_transmissions=7,
        )

    # --- AI BRAIN FUNCTION ---
    async def get_ai_reply(self, text):
        try:
            response = await aio_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a beautiful Indian girl named Aaru. Talk sweetly in Hinglish. Be friendly and helpful. Keep replies short."},
                    {"role": "user", "content": text}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            LOGGER(__name__).error(f"AI Error: {e}")
            return "Ji, kahiye? 😊"

    async def start(self):
        try:
            await super().start()
            me = await self.get_me()
            self.id = me.id
            self.name = f"{me.first_name} {(me.last_name or '')}".strip()
            self.username = me.username
            self.mention = me.mention

            # --- AI HANDLER REGISTRATION ---
            async def main_bot_ai_handler(client, message):
                if not message.text:
                    return

                # Condition: Agar bot ko tag kiya jaye ya bot ke message par reply ho
                is_tagged = False
                if message.mentioned:
                    is_tagged = True
                elif message.reply_to_message and message.reply_to_message.from_user:
                    if message.reply_to_message.from_user.id == self.id:
                        is_tagged = True

                if is_tagged:
                    await client.send_chat_action(message.chat.id, "typing")
                    reply = await self.get_ai_reply(message.text)
                    await message.reply_text(reply)

            # Is handler ko register karna
            self.add_handler(MessageHandler(main_bot_ai_handler, filters.group & filters.text))
            LOGGER(__name__).info(f"✅ AI Chat System Active for {self.name}")
            # -------------------------------

            LOGGER(__name__).info(f"✅ Bot logged in as {self.name} (@{self.username})")

            # Try sending a startup message
            try:
                await self.send_message(
                    chat_id=config.LOGGER_ID,
                    text=(
                        f"<u><b>» {self.mention} ʙᴏᴛ sᴛᴀʀᴛᴇᴅ :</b></u>\n\n"
                        f"🆔 ɪᴅ : <code>{self.id}</code>\n"
                        f"📛 ɴᴀᴍᴇ : {self.name}\n"
                        f"🔰 ᴜsᴇʀɴᴀᴍᴇ : @{self.username}"
                    ),
                )
            except Exception as e:
                LOGGER(__name__).error(f"❌ Startup log failed: {e}")

            LOGGER(__name__).info("✅ Bot started successfully.")

        except Exception as e:
            LOGGER(__name__).exception(f"❌ Failed to start bot: {e}")
            raise SystemExit(1)

    async def stop(self):
        try:
            await super().stop()
            LOGGER(__name__).info("🛑 Bot stopped successfully.")
        except Exception as e:
            LOGGER(__name__).exception(f"❌ Error during shutdown: {e}")
