import sys
import asyncio
import os
from openai import AsyncOpenAI
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
import config
from ..logging import LOGGER

# OpenAI Setup
aio_client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)

assistants = []
assistantids = []

class Userbot(Client):
    def __init__(self):
        # Yahan humne listen=True rakha hai Assistant 1 ke liye
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

    async def get_ai_reply(self, text):
        try:
            # Check karein agar API Key sahi hai
            response = await aio_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": "You are a helpful Indian girl."},
                          {"role": "user", "content": text}]
            )
            return response.choices[0].message.content
        except Exception as e:
            LOGGER(__name__).error(f"OpenAI API Error: {e}")
            return "Ji, main sun rahi hoon. (API Error)"

    async def _start_assistant(self, client, assistant_num):
        if not client:
            return
        try:
            await client.start()
            get_me = await client.get_me()
            
            # --- AI LOGIC START ---
            if assistant_num == 1:
                # Bot ka username le rahe hain taaki mention check kar sakein
                bot_username = get_me.username if get_me.username else ""

                async def ai_handler(c, message):
                    # AGAR MESSAGE MEIN BOT KA USERNAME YA USKA NAAM HAI TOH REPLY KAREGA
                    # Ya agar aap use tag karein
                    if f"@{bot_username}" in message.text or get_me.first_name in message.text:
                        print(f"DEBUG: Message received from {message.from_user.first_name}: {message.text}")
                        
                        # AI se jawab mangna
                        reply_text = await self.get_ai_reply(message.text)
                        await message.reply(reply_text) # Pehle simple text reply check karte hain
                        print(f"DEBUG: Replied with: {reply_text}")

                # Saare groups ke text messages sunne ke liye handler
                client.add_handler(MessageHandler(ai_handler, filters.group & filters.text))
                LOGGER(__name__).info(f"✅ Assistant 1 (AI) is listening for mentions of @{bot_username}")
            # --- AI LOGIC END ---

            client.id = get_me.id
            client.name = get_me.mention
            client.username = get_me.username
            assistants.append(assistant_num)
            assistantids.append(client.id)
            LOGGER(__name__).info(f"✅ Assistant {assistant_num} Started as {client.name}")
        except Exception as e:
            LOGGER(__name__).error(f"🚫 Assistant {assistant_num} Error: {e}")

    async def start(self):
        if self.one: await self._start_assistant(self.one, 1)
        if self.two: await self._start_assistant(self.two, 2)
        if self.three: await self._start_assistant(self.three, 3)
        if self.four: await self._start_assistant(self.four, 4)
        if self.five: await self._start_assistant(self.five, 5)

    async def stop(self):
        for ass in [self.one, self.two, self.three, self.four, self.five]:
            if ass: await ass.stop()
