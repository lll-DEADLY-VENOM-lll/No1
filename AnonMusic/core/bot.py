from pyrogram import Client, errors, filters
from pyrogram.enums import ChatMemberStatus, ParseMode, ChatAction
from pyrogram.handlers import MessageHandler
from openai import AsyncOpenAI
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

    # --- AI BRAIN WITH MUSIC DETECTION ---
    async def get_ai_reply(self, text):
        try:
            # AI ko instruction di gayi hai ki song request par 'ACTION_PLAY:' likhe
            prompt = (
                "You are Aaru, a beautiful and sweet Indian girl. Talk in Hinglish. "
                "If the user asks to play a song or music, reply exactly in this format: "
                "'ACTION_PLAY: [song name]'. For example: 'ACTION_PLAY: Tum Hi Ho'. "
                "Otherwise, just chat sweetly."
            )
            
            response = await aio_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": prompt},
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

            # --- AI & MUSIC HANDLER ---
            async def main_bot_ai_handler(client, message):
                if not message.text:
                    return

                # Check if bot is tagged or replied to
                is_tagged = False
                if message.mentioned:
                    is_tagged = True
                elif message.reply_to_message and message.reply_to_message.from_user:
                    if message.reply_to_message.from_user.id == self.id:
                        is_tagged = True

                if is_tagged:
                    await client.send_chat_action(message.chat.id, ChatAction.TYPING)
                    ai_text = await self.get_ai_reply(message.text)

                    # Check agar AI ne gaana bajane ko kaha hai
                    if "ACTION_PLAY:" in ai_text:
                        song_name = ai_text.replace("ACTION_PLAY:", "").strip()
                        # User ko reply do
                        await message.reply_text(f"Theek hai ji, main aapke liye **{song_name}** play karti hoon... 🎶")
                        # Music bot ki command trigger karo
                        await client.send_message(message.chat.id, f"/play {song_name}")
                    else:
                        # Normal chat reply
                        await message.reply_text(ai_text)

            # Handler register karein
            self.add_handler(MessageHandler(main_bot_ai_handler, filters.group & filters.text))
            
            LOGGER(__name__).info(f"✅ AI & Music System Ready for @{self.username}")
            LOGGER(__name__).info(f"✅ Bot started successfully as {me.first_name}")

        except Exception as e:
            LOGGER(__name__).exception(f"❌ Failed to start bot: {e}")
            raise SystemExit(1)

    async def stop(self):
        try:
            await super().stop()
            LOGGER(__name__).info("🛑 Bot stopped successfully.")
        except Exception as e:
            LOGGER(__name__).exception(f"❌ Error during shutdown: {e}")
