from pyrogram import Client, errors, filters
from pyrogram.enums import ChatMemberStatus, ParseMode, ChatAction # ChatAction add kiya
from pyrogram.handlers import MessageHandler
from openai import AsyncOpenAI
import config
from ..logging import LOGGER

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

    async def get_ai_reply(self, text):
        try:
            response = await aio_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a sweet Indian girl named Aaru. Talk in Hinglish."},
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
            self.username = me.username
            self.mention = me.mention

            async def main_bot_ai_handler(client, message):
                if not message.text: return
                is_tagged = False
                if message.mentioned:
                    is_tagged = True
                elif message.reply_to_message and message.reply_to_message.from_user:
                    if message.reply_to_message.from_user.id == self.id:
                        is_tagged = True

                if is_tagged:
                    # FIX: Yahan ChatAction.TYPING use kiya hai
                    await client.send_chat_action(message.chat.id, ChatAction.TYPING)
                    reply = await self.get_ai_reply(message.text)
                    await message.reply_text(reply)

            self.add_handler(MessageHandler(main_bot_ai_handler, filters.group & filters.text))
            LOGGER(__name__).info(f"✅ AI System Ready for @{self.username}")

        except Exception as e:
            LOGGER(__name__).exception(f"❌ Failed to start bot: {e}")
            raise SystemExit(1)

    async def stop(self):
        await super().stop()
