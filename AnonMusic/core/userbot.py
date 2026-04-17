import sys
import asyncio
import os
from openai import AsyncOpenAI # Updated
from pyrogram import Client, filters
from pyrogram.errors import UserAlreadyParticipant
import config
from ..logging import LOGGER

# OpenAI Async Client Setup
aio_client = AsyncOpenAI(api_key=config.OPENAI_API_KEY)

assistants = []
assistantids = []

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

    # --- AI BRAIN FUNCTION (ASYNCHRONOUS) ---
    async def get_ai_reply(self, text):
        try:
            prompt = f"You are a beautiful Indian girl assistant. Talk sweetly in Hinglish. If the user asks for a song, reply ONLY: 'ACTION_PLAY: [song name]'. Otherwise, chat nicely. User: {text}"
            response = await aio_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as e:
            LOGGER(__name__).error(f"AI Error: {e}")
            return "Ji, kahiye?"

    # --- VOICE GENERATION (TTS) ---
    async def get_voice_file(self, text):
        file_path = f"voice_{id(text)}.mp3"
        try:
            response = await aio_client.audio.speech.create(
                model="tts-1",
                voice="nova",
                input=text
            )
            # Save file asynchronously
            await response.atransform_to_file(file_path)
            return file_path
        except Exception as e:
            LOGGER(__name__).error(f"TTS Error: {e}")
            return None

    async def _start_assistant(self, client, assistant_num):
        if not client:
            return
        try:
            await client.start()
            
            # AI logic setup
            if assistant_num == 1:
                @client.on_message(filters.mentioned & filters.group)
                async def ai_handler(c, message):
                    # Typing action dikhane ke liye
                    ai_text = await self.get_ai_reply(message.text)
                    
                    if "ACTION_PLAY:" in ai_text:
                        song = ai_text.replace("ACTION_PLAY:", "").strip()
                        await message.reply(f"Theek hai, main aapke liye **{song}** play karti hoon... 🎶")
                        await c.send_message(message.chat.id, f"/play {song}")
                    else:
                        voice = await self.get_voice_file(ai_text)
                        if voice:
                            await message.reply_voice(voice)
                            if os.path.exists(voice):
                                os.remove(voice)
                        else:
                            await message.reply(ai_text)

            if config.LOGGER_ID:
                try:
                    await client.join_chat(config.LOGGER_ID)
                except:
                    pass

            get_me = await client.get_me()
            client.id = get_me.id
            client.name = get_me.mention
            client.username = get_me.username
            assistants.append(assistant_num)
            assistantids.append(client.id)
            LOGGER(__name__).info(f"✅ Assistant {assistant_num} AI Active as {client.username}")
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
        LOGGER(__name__).info("Stopping Assistants...")
        for assistant in [self.one, self.two, self.three, self.four, self.five]:
            if assistant: await assistant.stop()
