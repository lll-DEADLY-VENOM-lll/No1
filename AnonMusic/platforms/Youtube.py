import asyncio
import os
import re
import logging
import aiohttp
import yt_dlp
from typing import Union, Optional, Tuple, List
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch, Playlist
from AnonMusic.utils.formatters import time_to_seconds
from AnonMusic import LOGGER

# IMPORTANT: Credentials hamesha config se hi aane chahiye
try:
    from config import API_ID, BOT_TOKEN, MONGO_DB_URI
except ImportError:
    LOGGER.error("Config file not found! Ensure API_ID, BOT_TOKEN and MONGO_DB_URI are set.")

# --- SECURITY: SENSITIVE DATA REDACTION FILTER ---
class SensitiveDataFilter(logging.Filter):
    """Logs se sensitive info (Tokens, MongoURI) ko remove karne ke liye filter"""
    def filter(self, record):
        msg = str(record.msg)
        # Regex for Bot Token, MongoURI, and Session Strings
        patterns = [
            r"\d{8,10}:[a-zA-Z0-9_-]{35,}",  # Telegram Bot Token
            r"mongodb\+srv://\S+",           # Mongo DB URI
            r"session[a-zA-Z0-9]{50,}",      # String Session
        ]
        for pattern in patterns:
            msg = re.sub(pattern, "[PROTECTED]", msg)
        record.msg = msg
        return True

# Logger par security filter apply karein
logging.getLogger().addFilter(SensitiveDataFilter())

# --- CONFIGURATION ---
API_URL = "https://shrutibots.site"
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# --- UTILS ---
def get_clean_id(link: str) -> Optional[str]:
    """Video ID ko sanitize karta hai taaki path traversal attack na ho"""
    if "v=" in link:
        video_id = link.split('v=')[-1].split('&')[0]
    elif "youtu.be/" in link:
        video_id = link.split('youtu.be/')[-1].split('?')[0]
    else:
        video_id = link
    
    clean_id = re.sub(r'[^a-zA-Z0-9_-]', '', video_id)
    return clean_id if 5 <= len(clean_id) <= 15 else None

async def api_downloader(link: str, media_type: str) -> Optional[str]:
    """Audio/Video download karne wala core function"""
    video_id = get_clean_id(link)
    if not video_id:
        return None

    ext = "mp3" if media_type == "audio" else "mp4"
    file_path = os.path.abspath(os.path.join(DOWNLOAD_DIR, f"{video_id}.{ext}"))

    # Security: Ensure path escapes na hon
    if not file_path.startswith(os.path.abspath(DOWNLOAD_DIR)):
        return None

    if os.path.exists(file_path):
        return file_path

    try:
        # aiohttp automatically redirects handle karta hai
        timeout = aiohttp.ClientTimeout(total=600) 
        async with aiohttp.ClientSession(headers={"User-Agent": "ShrutiMusicBot/1.0"}, timeout=timeout) as session:
            # Step 1: Token prapt karein
            async with session.get(f"{API_URL}/download", params={"url": video_id, "type": media_type}) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                token = data.get("download_token")
                if not token: return None

            # Step 2: Stream aur save karein
            stream_url = f"{API_URL}/stream/{video_id}?type={media_type}&token={token}"
            async with session.get(stream_url) as file_resp:
                if file_resp.status == 200:
                    with open(file_path, "wb") as f:
                        async for chunk in file_resp.content.iter_chunked(65536):
                            f.write(chunk)
                    
                    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                        return file_path
    except Exception:
        # Security: Exception 'e' ko log na karein, usme system path ya token ho sakta hai
        LOGGER.error(f"Download Error for Video ID: {video_id}")
        if os.path.exists(file_path):
            try: os.remove(file_path)
            except: pass
    return None

class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.listbase = "https://youtube.com/playlist?list="

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid: link = self.base + link
        return bool(re.search(self.regex, link))

    async def url(self, message: Message) -> Optional[str]:
        """Message se YouTube URL extract karne ke liye"""
        for msg in [message, message.reply_to_message]:
            if not msg: continue
            text = msg.text or msg.caption
            if msg.entities:
                for entity in msg.entities:
                    if entity.type == MessageEntityType.URL:
                        return text[entity.offset : entity.offset + entity.length]
            if msg.caption_entities:
                for entity in msg.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        return None

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid: link = self.base + link
        link = link.split("&")[0]
        try:
            results = VideosSearch(link, limit=1)
            res = (await results.next())["result"][0]
            return (
                res["title"],
                res["duration"],
                int(time_to_seconds(res["duration"])),
                res["thumbnails"][0]["url"].split("?")[0],
                res["id"]
            )
        except Exception:
            return None

    async def title(self, link: str, videoid: Union[bool, str] = None):
        det = await self.details(link, videoid)
        return det[0] if det else "Unknown Title"

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid: link = self.base + link
        file = await api_downloader(link, "video")
        return (1, file) if file else (0, "Download Failed")

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid: link = self.listbase + link
        try:
            plist = await Playlist.get(link)
            return [v["id"] for v in plist.get("videos", [])[:limit] if v.get("id")]
        except:
            return []

    async def track(self, link: str, videoid: Union[bool, str] = None):
        det = await self.details(link, videoid)
        if not det: return None, None
        track_details = {
            "title": det[0],
            "link": self.base + det[4],
            "vidid": det[4],
            "duration_min": det[1],
            "thumb": det[3],
        }
        return track_details, det[4]

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid: link = self.base + link
        link = link.split("&")[0]
        
        # yt-dlp Settings for maximum security
        ytdl_opts = {
            "quiet": True,
            "no_warnings": True,
            "nocheckcertificate": True,
            "no_color": True,
            "logger": logging.getLogger("dummy"), 
        }
        
        def fetch_info():
            with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
                return ydl.extract_info(link, download=False)

        try:
            info = await asyncio.to_thread(fetch_info)
            formats_available = []
            for f in info.get("formats", []):
                if f.get("format_id"):
                    formats_available.append({
                        "format": f.get("format", "N/A"),
                        "filesize": f.get("filesize"),
                        "format_id": f["format_id"],
                        "ext": f.get("ext", "mp4"),
                        "format_note": f.get("format_note", ""),
                        "yturl": link,
                    })
            return formats_available, link
        except Exception:
            return [], link

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        **kwargs
    ) -> Tuple[Optional[str], bool]:
        if videoid: link = self.base + link
        
        try:
            file_path = await (api_downloader(link, "video") if video else api_downloader(link, "audio"))
            return (file_path, True) if file_path else (None, False)
        except Exception:
            return None, False


# Initialize Instance
YouTube = YouTubeAPI()
