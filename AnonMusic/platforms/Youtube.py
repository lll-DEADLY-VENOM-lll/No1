import asyncio
import os
import re
import logging
import aiohttp
import yt_dlp
from typing import Union, Optional, Tuple, List, Dict, Any
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch, Playlist
from AnonMusic.utils.formatters import time_to_seconds
from AnonMusic import LOGGER

# --- CONFIG & DIRECTORY ---
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)
API_URL = "https://shrutibots.site"

class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.listbase = "https://youtube.com/playlist?list="

    # Yeh method missing tha pichle code mein
    async def url(self, message: Message) -> Optional[str]:
        """Message ya Reply se YouTube URL extract karta hai"""
        for msg in [message, message.reply_to_message]:
            if not msg:
                continue
            text = msg.text or msg.caption
            if not text:
                continue
            
            # Entities se URL nikalna
            if msg.entities:
                for entity in msg.entities:
                    if entity.type == MessageEntityType.URL:
                        return text[entity.offset : entity.offset + entity.length]
            
            # Caption links se URL nikalna
            if msg.caption_entities:
                for entity in msg.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
            
            # Agar entity nahi hai toh simple regex search
            match = re.search(r"(https?://[^\s]+)", text)
            if match:
                return match.group(1)
        return None

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid: link = self.base + str(link)
        return bool(re.search(self.regex, link))

    async def details(self, link: str, videoid: Union[bool, str] = None) -> Optional[tuple]:
        if videoid: link = self.base + str(link)
        link = link.split("&")[0]
        try:
            results = VideosSearch(link, limit=1)
            res_data = await results.next()
            if not res_data or not res_data.get("result"):
                return None
            
            res = res_data["result"][0]
            return (
                res.get("title", "Unknown Title"),
                res.get("duration", "0:00"),
                int(time_to_seconds(res.get("duration", "0:00"))),
                res.get("thumbnails", [{}])[0].get("url", "").split("?")[0],
                res.get("id")
            )
        except Exception:
            return None

    async def track(self, link: str, videoid: Union[bool, str] = None):
        det = await self.details(link, videoid)
        if not det:
            return None, None
        track_details = {
            "title": det[0],
            "link": self.base + det[4] if det[4] else link,
            "vidid": det[4],
            "duration_min": det[1],
            "thumb": det[3],
        }
        return track_details, det[4]

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid: link = self.listbase + str(link)
        try:
            plist = await Playlist.get(link)
            return [v["id"] for v in plist.get("videos", [])[:limit] if v.get("id")]
        except:
            return []

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        **kwargs
    ) -> Tuple[Optional[str], bool]:
        if videoid: link = self.base + str(link)
        try:
            m_type = "video" if video else "audio"
            file_path = await api_downloader(link, m_type)
            return (file_path, True) if file_path else (None, False)
        except Exception:
            return None, False

# --- HELPER FUNCTIONS ---

async def api_downloader(link: str, media_type: str) -> Optional[str]:
    video_id = get_clean_id(link)
    if not video_id: return None

    ext = "mp3" if media_type == "audio" else "mp4"
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.{ext}")

    if os.path.exists(file_path):
        return file_path

    try:
        async with aiohttp.ClientSession() as session:
            # Step 1: Get Download Token
            async with session.get(f"{API_URL}/download", params={"url": link, "type": media_type}) as resp:
                if resp.status != 200: return None
                data = await resp.json()
                token = data.get("download_token")
            
            if not token: return None

            # Step 2: Download File
            stream_url = f"{API_URL}/stream/{video_id}?type={media_type}&token={token}"
            async with session.get(stream_url) as file_resp:
                if file_resp.status == 200:
                    with open(file_path, "wb") as f:
                        async for chunk in file_resp.content.iter_chunked(65536):
                            f.write(chunk)
                    return file_path
    except Exception as e:
        LOGGER.error(f"Download Error: {e}")
    return None

def get_clean_id(link: str) -> Optional[str]:
    if not link: return None
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(pattern, link)
    return match.group(1) if match else None

# Initialize Instance
YouTube = YouTubeAPI()
