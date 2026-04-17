import os
import asyncio
from openai import AsyncOpenAI
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
import config
from ..logging import LOGGER

# OpenAI Setup
aio_client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)

class Userbot(Client):
    def __init__(self):
        # AI sirf pehle assistant (one) ke liye setup karenge
        self.one = Client(
            name="AnonXAss1",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING1),
            no_updates=False # Zaroori: Isse bot messages sun payega
        )
        self.two = self._create_client(config.STRING2, "AnonXAss2")
        self.three = self._create_client(config.STRING3, "AnonXAss3")
        self.four = self._create_client(config.STRING4, "AnonXAss4")
        self.five = self._create_client(config.STRING5, "AnonXAss5")

    def _create_client(self, string, name):
        if string:
            return Client(
                name=name,
                api_id=config.API_ID,
                api_hash=config.API_HASH,
                session_string=str(string),
                no_updates=True, # Baaki assistants updates nahi lenge
            )
        return None

    # --- AI REPLY FUNCTION ---
    async def get_ai_reply(self, text):
        try:
            response = await aio_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a sweet Indian girl. Talk in Hinglish. Reply shortly."},
                    {"role": "user", "content": text}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            LOGGER(__name__).error(f"OpenAI Error: {e}")
            return "Ji, kahiye? (API Not Responding)"

    async def _start_assistant(self, client, assistant_num):
        if not client:
            return
        try:
            await client.start()
            get_me = await client.get_me()
            client.id = get_me.id
            client.username = get_me.username
            client.mention = get_me.mention

            # --- AI LOGIC FOR ASSISTANT 1 ---
            if assistant_num == 1:
                # Is handler ko yahan register karna zaroori hai
                async def ai_handler(c, message):
                    if not message.text:
                        return

                    # Check karein agar bot ko tag kiya hai ya reply kiya hai
                    is_tagged = False
                    if message.mentioned:
                        is_tagged = True
                    elif message.reply_to_message and message.reply_to_message.from_user:
                        if message.reply_to_message.from_user.id == client.id:
                            is_tagged = True

                    if is_tagged:
                        print(f"DEBUG: AI active on message: {message.text}")
                        # Typing action
                        await c.send_chat_action(message.chat.id, "typing")
                        
                        # AI Jawab
                        reply = await self.get_ai_reply(message.text)
                        await message.reply_text(reply)
                        print(f"DEBUG: AI Replied: {reply}")

                # Handler ko Pyrogram mein add karein
                client.add_handler(MessageHandler(ai_handler, filters.group & filters.text))
                print(f"✅ AI Handler Registered for {get_me.first_name}")

            LOGGER(__name__).info(f"Assistant {assistant_num} Started as {get_me.first_name}")
        except Exception as e:
            LOGGER(__name__).error(f"Assistant {assistant_num} Failed: {e}")

    async def start(self):
        LOGGER(__name__).info("Starting Assistants...")
        if self.one: await self._start_assistant(self.one, 1)
        if self.two: await self._start_assistant(self.two, 2)
        if self.three: await self._start_assistant(self.three, 3)
        if self.four: await self._start_assistant(self.four, 4)
        if self.five: await self._start_assistant(self.five, 5)

    async def stop(self):
        if self.one: await self.one.stop()
        if self.two: await self.two.stop()
        # ... and so on
