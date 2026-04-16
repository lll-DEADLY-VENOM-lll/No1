import asyncio
import os
import re
import logging
import aiohttp
import yt_dlp
from pathlib import Path
from typing import Union, Optional, Tuple, List
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from py_yt import VideosSearch, Playlist
from AnonMusic.utils.formatters import time_to_seconds
from AnonMusic import LOGGER

# --- CONFIGURATION ---
try:
    from config import API_ID, BOT_TOKEN, MONGO_DB_URI
except ImportError:
    LOGGER.error("Config file not found! Ensure API_ID, BOT_TOKEN and MONGO_DB_URI are set.")

API_URL = "https://shrutibots.site"
DOWNLOAD_DIR = Path("downloads").resolve()
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
COOKIES_FILE = "cookies.txt" if os.path.exists("cookies.txt") else None

# Download Semaphore: Ek saath sirf 3 downloads (CPU/RAM protect karne ke liye)
DOWNLOAD_SEMAPHORE = asyncio.Semaphore(3)

# --- SECURITY: SENSITIVE DATA REDACTION ---
class SensitiveDataFilter(logging.Filter):
    """Logs se sensitive info ko remove karne ke liye custom filter"""
    def filter(self, record):
        msg = str(record.msg)
        patterns = {
            r"\d{8,10}:[a-zA-Z0-9_-]{35,}": "[BOT_TOKEN_REDACTED]",
            r"mongodb\+srv://\S+": "[MONGO_URI_REDACTED]",
            r"session[a-zA-Z0-9]{50,}": "[SESSION_REDACTED]",
        }
        for pattern, replacement in patterns.items():
            msg = re.sub(pattern, replacement, msg)
        record.msg = msg
        return True

logging.getLogger().addFilter(SensitiveDataFilter())

# --- UTILS ---

def get_clean_id(link: str) -> Optional[str]:
    """YouTube ID validate aur sanitize karta hai"""
    pattern = r"(?:v=|\/)([0-9A-Za-z_-]{11}).*"
    match = re.search(pattern, link)
    if match:
        video_id = match.group(1)
        return video_id if len(video_id) == 11 else None
    return None

async def auto_cleanup(file_path: Path):
    """File ko 10 min baad delete kar dega space bachane ke liye"""
    await asyncio.sleep(600) 
    try:
        if file_path.exists():
            os.remove(file_path)
            LOGGER.info(f"Auto-cleaned: {file_path.name}")
    except Exception:
        pass

# --- CORE DOWNLOADER (Security Hardened) ---

async def api_downloader(link: str, media_type: str) -> Optional[str]:
    video_id = get_clean_id(link)
    if not video_id:
        return None

    ext = "mp3" if media_type == "audio" else "mp4"
    # Strict Path Validation
    file_path = (DOWNLOAD_DIR / f"{video_id}.{ext}").resolve()
    
    # Path Traversal Check: Ensure file is inside DOWNLOAD_DIR
    if not str(file_path).startswith(str(DOWNLOAD_DIR)):
        LOGGER.warning(f"Security Alert: Blocked path traversal attempt for ID {video_id}")
        return None

    if file_path.exists():
        return str(file_path)

    async with DOWNLOAD_SEMAPHORE:
        try:
            timeout = aiohttp.ClientTimeout(total=600) 
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36"}
            
            async with aiohttp.ClientSession(headers=headers, timeout=timeout) as session:
                # Step 1: Token Generation
                params = {"url": video_id, "type": media_type}
                async with session.get(f"{API_URL}/download", params=params) as resp:
                    if resp.status != 200: return None
                    data = await resp.json()
                    token = data.get("download_token")
                    if not token: return None

                # Step 2: Streaming Download
                stream_url = f"{API_URL}/stream/{video_id}?type={media_type}&token={token}"
                async with session.get(stream_url) as file_resp:
                    if file_resp.status == 200:
                        with open(file_path, "wb") as f:
                            async for chunk in file_resp.content.iter_chunked(65536):
                                f.write(chunk)
                        
                        if file_path.exists() and file_path.stat().st_size > 0:
                            asyncio.create_task(auto_cleanup(file_path))
                            return str(file_path)
        except Exception:
            LOGGER.error(f"API Download Error for {video_id}")
            if file_path.exists(): os.remove(file_path)
    return None

class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.listbase = "https://youtube.com/playlist?list="

    def _get_ytdl_opts(self):
        """yt-dlp security aur bypass settings"""
        opts = {
            "quiet": True,
            "no_warnings": True,
            "nocheckcertificate": True,
            "no_color": True,
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "geo_bypass": True,
            "extract_flat": True,
        }
        if COOKIES_FILE:
            opts["cookiefile"] = COOKIES_FILE
        return opts

    async def url(self, message: Message) -> Optional[str]:
        """Message se YouTube URL extract karne ke liye (Safe Method)"""
        for msg in [message, message.reply_to_message]:
            if not msg: continue
            text = msg.text or msg.caption
            if not text: continue
            
            if msg.entities:
                for entity in msg.entities:
                    if entity.type == MessageEntityType.URL:
                        url = text[entity.offset : entity.offset + entity.length]
                        if "youtube.com" in url or "youtu.be" in url:
                            return url
                    if entity.type == MessageEntityType.TEXT_LINK:
                        if "youtube.com" in entity.url or "youtu.be" in entity.url:
                            return entity.url
        return None

    async def details(self, link: str, videoid: bool = False):
        if videoid: link = self.base + link
        try:
            # Clean link for py_yt
            link = link.split("&")[0]
            results = VideosSearch(link, limit=1)
            search_res = await results.next()
            if not search_res["result"]: return None
            
            res = search_res["result"][0]
            return (
                res["title"],
                res["duration"],
                int(time_to_seconds(res["duration"])),
                res["thumbnails"][0]["url"].split("?")[0],
                res["id"]
            )
        except Exception:
            return None

    async def formats(self, link: str, videoid: bool = False):
        """yt-dlp formats fetcher with cookies support"""
        if videoid: link = self.base + link
        link = link.split("&")[0]
        
        ytdl_opts = self._get_ytdl_opts()

        def fetch_info():
            with yt_dlp.YoutubeDL(ytdl_opts) as ydl:
                return ydl.extract_info(link, download=False)

        try:
            info = await asyncio.to_thread(fetch_info)
            formats_available = []
            for f in info.get("formats", []):
                if f.get("filesize") or f.get("filesize_approx"):
                    formats_available.append({
                        "format_id": f.get("format_id"),
                        "ext": f.get("ext"),
                        "filesize": f.get("filesize") or f.get("filesize_approx"),
                        "format_note": f.get("format_note", ""),
                        "yturl": link,
                    })
            return formats_available, link
        except Exception as e:
            LOGGER.error(f"yt-dlp formats error: {str(e)}")
            return [], link

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        **kwargs
    ) -> Tuple[Optional[str], bool]:
        """Final secure download entry"""
        if videoid: link = self.base + link
        
        # Verify Link again
        if not get_clean_id(link):
            return None, False

        file_path = await (api_downloader(link, "video") if video else api_downloader(link, "audio"))
        return (file_path, True) if file_path else (None, False)

    async def playlist(self, link, limit, user_id, videoid: bool = False):
        if videoid: link = self.listbase + link
        try:
            plist = await Playlist.get(link)
            return [v["id"] for v in plist.get("videos", [])[:limit] if v.get("id")]
        except:
            return []
