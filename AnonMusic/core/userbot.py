import sys
import asyncio
import os
from openai import AsyncOpenAI
from pyrogram import Client, filters
from pyrogram.enums import ChatAction # ChatAction add kiya
from pyrogram.handlers import MessageHandler
import config
from ..logging import LOGGER

assistants = []
assistantids = []
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
                name=name, api_id=config.API_ID, api_hash=config.API_HASH,
                session_string=str(string), no_updates=not listen,
            )
        return None

    async def get_ai_reply(self, text):
        try:
            response = await aio_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a sweet Indian girl. Talk in Hinglish."},
                    {"role": "user", "content": text}
                ]
            )
            return response.choices[0].message.content
        except: return "Ji, kahiye?"

    async def _start_assistant(self, client, assistant_num):
        global assistants, assistantids
        if not client: return
        try:
            await client.start()
            get_me = await client.get_me()
            client.id = get_me.id
            assistants.append(assistant_num)
            assistantids.append(client.id)

            if assistant_num == 1:
                async def assistant_ai_logic(c, message):
                    if not message.text: return
                    if message.mentioned or (message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.from_user.id == client.id):
                        # FIX: Yahan ChatAction.TYPING use kiya hai
                        await c.send_chat_action(message.chat.id, ChatAction.TYPING)
                        reply = await self.get_ai_reply(message.text)
                        await message.reply_text(reply)
                client.add_handler(MessageHandler(assistant_ai_logic, filters.group & filters.text))

            LOGGER(__name__).info(f"✅ Assistant {assistant_num} Ready")
        except Exception as e:
            LOGGER(__name__).error(f"Error: {e}")

    async def start(self):
        if self.one: await self._start_assistant(self.one, 1)
        if self.two: await self._start_assistant(self.two, 2)
        if self.three: await self._start_assistant(self.three, 3)
        if self.four: await self._start_assistant(self.four, 4)
        if self.five: await self._start_assistant(self.five, 5)

    async def stop(self):
        for ass in [self.one, self.two, self.three, self.four, self.five]:
            if ass: await ass.stop()
