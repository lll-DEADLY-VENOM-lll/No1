import os
import re
import aiofiles
import aiohttp
import logging
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps
from youtubesearchpython.__future__ import VideosSearch
from config import YOUTUBE_IMG_URL
from AnonMusic import app

# Logging Setup
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

CACHE_DIR = "cache"
os.makedirs(CACHE_DIR, exist_ok=True)

async def get_thumb(videoid: str) -> str:
    cache_path = os.path.join(CACHE_DIR, f"{videoid}_full_color.png")
    if os.path.exists(cache_path):
        return cache_path

    try:
        results = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
        results_data = await results.next()
        data = results_data["result"][0]
        title = re.sub(r"\W+", " ", data.get("title", "Unsupported Title")).title()
        thumbnail = data.get("thumbnails", [{}])[0].get("url", YOUTUBE_IMG_URL)
        views = data.get("viewCount", {}).get("short", "Unknown Views")
    except Exception as e:
        logging.error(f"Error fetching YouTube data: {e}")
        title, thumbnail, views = "Unsupported Title", YOUTUBE_IMG_URL, "Unknown Views"

    thumb_path = os.path.join(CACHE_DIR, f"temp_{videoid}.jpg")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(thumbnail) as resp:
                if resp.status == 200:
                    async with aiofiles.open(thumb_path, "wb") as f:
                        await f.write(await resp.read())
                else:
                    return YOUTUBE_IMG_URL
    except Exception as e:
        return YOUTUBE_IMG_URL

    try:
        # 1. Base Image - Background (Full Screen 1280x720)
        # Hum thumbnail ko hi background banayenge aur usey blur karenge
        img = Image.open(thumb_path).convert("RGBA")
        bg = img.resize((1280, 720), Image.LANCZOS)
        bg = bg.filter(ImageFilter.GaussianBlur(25)) # Piche ka background blur
        bg = ImageEnhance.Brightness(bg).enhance(0.5) # Thoda dark taaki text dikhe

        # 2. Main Thumbnail (Center mein colorful dikhega)
        main_w, main_h = 750, 420
        main_thumb = img.resize((main_w, main_h), Image.LANCZOS)
        
        # Rounded corners for main thumb
        mask = Image.new("L", (main_w, main_h), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.rounded_rectangle((0, 0, main_w, main_h), radius=30, fill=255)
        
        # Paste main thumb in the center
        bg.paste(main_thumb, ((1280 - main_w) // 2, 80), mask)

        # 3. Text and Details
        draw = ImageDraw.Draw(bg)
        try:
            # Font paths check karein aapke system mein sahi hain ya nahi
            title_font = ImageFont.truetype("AnonMusic/assets/thumb/font.ttf", 45)
            small_font = ImageFont.truetype("AnonMusic/assets/thumb/font.ttf", 25)
        except:
            title_font = ImageFont.load_default()
            small_font = ImageFont.load_default()

        # Song Title (Centered)
        clean_title = title[:40] + "..." if len(title) > 40 else title
        title_w = draw.textlength(clean_title, font=title_font)
        draw.text(((1280 - title_w) // 2, 530), clean_title, fill="white", font=title_font)

        # Bottom Metadata
        info_text = f"Views: {views}  |  Playing on @{app.username}"
        info_w = draw.textlength(info_text, font=small_font)
        draw.text(((1280 - info_w) // 2, 600), info_text, fill=(230, 230, 230), font=small_font)

        # Progress Bar
        draw.rounded_rectangle((340, 650, 940, 658), radius=4, fill=(80, 80, 80)) # Background bar
        draw.rounded_rectangle((340, 650, 640, 658), radius=4, fill="#FF0000") # Red Progress

        # Cleanup & Save
        os.remove(thumb_path)
        bg.save(cache_path, quality=95)
        return cache_path

    except Exception as e:
        logging.error(f"Image error: {e}")
        return YOUTUBE_IMG_URL
