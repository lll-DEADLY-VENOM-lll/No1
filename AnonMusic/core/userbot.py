import sys
import asyncio
import os
from openai import AsyncOpenAI
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.errors import UserAlreadyParticipant
import config
from ..logging import LOGGER

# --- IMPORT ERROR FIX ---
assistants = []
assistantids = []
# ------------------------

aio_client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)

class Userbot(Client):
    def __init__(self):
        self.one = self._create_client(config.STRING1, "AnonXAss1", listen=True)
        self.two = self._create_client(config.STRING2, "AnonXAss2")
        self.three = self._create_client(config.STRING3, "AnonXAss3")
        self.four = self._create_client(config.STRING4, "AnonXAss4")
        self.five = self._create_client(config.STRING5, "AnonXAss5")

    def _create_client(self, string, name, listen=False):
        if string:
            return Client(
                name=name,
                api_id=config.API_ID,
                api_hash=config.API_HASH,
                session_string=str(string),
                no_updates=not listen,
            )
        return None

    # AI Brain
    async def get_ai_reply(self, text):
        try:
            response = await aio_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a beautiful Indian girl assistant. Talk sweetly in Hinglish. Short replies."},
                    {"role": "user", "content": text}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            LOGGER(__name__).error(f"OpenAI Error: {e}")
            return "Ji, kahiye?"

    async def _start_assistant(self, client, assistant_num):
        global assistants, assistantids
        if not client:
            return
        try:
            await client.start()
            
            get_me = await client.get_me()
            client.id = get_me.id
            client.name = get_me.mention
            client.username = get_me.username
            
            # Global lists update (Error fix)
            assistants.append(assistant_num)
            assistantids.append(client.id)

            # AI Logic sirf Assistant 1 ke liye
            if assistant_num == 1:
                async def ai_handler(c, message):
                    if not message.text: return
                    
                    # Agar bot ko tag kiya jaye ya bot ke message pe reply aaye
                    is_ai_needed = False
                    if message.mentioned:
                        is_ai_needed = True
                    elif message.reply_to_message and message.reply_to_message.from_user:
                        if message.reply_to_message.from_user.id == client.id:
                            is_ai_needed = True

                    if is_ai_needed:
                        await c.send_chat_action(message.chat.id, "typing")
                        ai_text = await self.get_ai_reply(message.text)
                        await message.reply_text(ai_text)

                client.add_handler(MessageHandler(ai_handler, filters.group & filters.text))

            if config.LOGGER_ID:
                try:
                    await client.join_chat(config.LOGGER_ID)
                except: pass

            LOGGER(__name__).info(f"✅ Assistant {assistant_num} Started as {client.name}")
        except Exception as e:
            LOGGER(__name__).error(f"🚫 Assistant {assistant_num} Error: {e}")

    async def start(self):
        LOGGER(__name__).info("Starting AI Assistants...")
        if self.one: await self._start_assistant(self.one, 1)
        if self.two: await self._start_assistant(self.two, 2)
        if self.three: await self._start_assistant(self.three, 3)
        if self.four: await self._start_assistant(self.four, 4)
        if self.five: await self._start_assistant(self.five, 5)

    async def stop(self):
        for ass in [self.one, self.two, self.three, self.four, self.five]:
            if ass: await ass.stop()
