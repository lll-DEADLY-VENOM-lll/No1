import sys
from pyrogram import Client
from pyrogram.errors import (
    PeerIdInvalid,
    ChatIdInvalid,
    UserNotParticipant,
    UsernameNotOccupied,
    RPCError,
)

import config
from ..logging import LOGGER

assistants = []
assistantids = []


class Userbot(Client):
    def __init__(self):
        self.one = self._create_client(config.STRING1, "AnonXAss1")
        self.two = self._create_client(config.STRING2, "AnonXAss2")
        self.three = self._create_client(config.STRING3, "AnonXAss3")
        self.four = self._create_client(config.STRING4, "AnonXAss4")
        self.five = self._create_client(config.STRING5, "AnonXAss5")

    def _create_client(self, string, name):
        return Client(
            name=name,
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(string),
            no_updates=True,
        ) if string else None

    async def _start_assistant(self, client, assistant_num, session_string_name):
        if not client:
            return

        try:
            await client.start()
            
            try:
                await client.send_message(
                    config.LOGGER_ID,
                    f"Assistant {assistant_num} Started"
                )
            except Exception as e:
                LOGGER(__name__).error(
                    f"🚫 Assistant {assistant_num} ({session_string_name}) failed to send log message: {e}"
                )
                # We don't exit here anymore to let the bot try to continue

            client.id = client.me.id
            client.name = client.me.mention
            client.username = client.me.username

            # --- MODIFIED SECTION ---
            # Instead of exiting, we just log a warning if username is missing.
            if not client.username:
                LOGGER(__name__).warning(
                    f"⚠️ Assistant {assistant_num} ({session_string_name}) has no username set. The bot will continue anyway."
                )
            # ------------------------

            assistants.append(assistant_num)
            assistantids.append(client.id)
            LOGGER(__name__).info(f"✅ Assistant {assistant_num} Started as {client.name}")

        except UsernameNotOccupied:
            LOGGER(__name__).error(
                f"🚫 Assistant {assistant_num} ({session_string_name}) has no username set."
            )
        except RPCError as e:
            LOGGER(__name__).error(
                f"🚫 Assistant {assistant_num} ({session_string_name}) RPC error: {e}"
            )
        except Exception as e:
            LOGGER(__name__).error(
                f"🚫 Assistant {assistant_num} ({session_string_name}) unexpected error: {e}"
            )

    async def start(self):
        LOGGER(__name__).info("Starting Assistants...")
        await self._start_assistant(self.one, 1, "STRING1")
        await self._start_assistant(self.two, 2, "STRING2")
        await self._start_assistant(self.three, 3, "STRING3")
        await self._start_assistant(self.four, 4, "STRING4")
        await self._start_assistant(self.five, 5, "STRING5")

        if not assistants:
            LOGGER(__name__).error("🚫 No assistants were started. Exiting.")
            sys.exit(1)
        LOGGER(__name__).info(f"✅ {len(assistants)} assistant(s) started.")

    async def stop(self):
        LOGGER(__name__).info("Stopping Assistants...")
        try:
            if self.one: await self.one.stop()
            if self.two: await self.two.stop()
            if self.three: await self.three.stop()
            if self.four: await self.four.stop()
            if self.five: await self.five.stop()
            LOGGER(__name__).info("✅ All assistants stopped successfully.")
        except Exception as e:
            LOGGER(__name__).error(f"❌ Error stopping assistants: {e}")
