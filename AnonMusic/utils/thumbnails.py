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

# Aesthetic Constants
FONT_PATH_BRUSH = "AnonMusic/assets/thumb/brush_font.ttf" # Mashup likhne ke liye brush font use karein
FONT_PATH_REGULAR = "AnonMusic/assets/thumb/font.ttf"
MAX_TITLE_WIDTH = 700

def trim_to_width(text: str, font: ImageFont.FreeTypeFont, max_w: int) -> str:
    ellipsis = "…"
    text = text[:45]
    if font.getlength(text) <= max_w:
        return text
    for i in range(len(text) - 1, 0, -1):
        if font.getlength(text[:i] + ellipsis) <= max_w:
            return text[:i] + ellipsis
    return ellipsis

async def get_thumb(videoid: str) -> str:
    cache_path = os.path.join(CACHE_DIR, f"{videoid}_aesthetic.png")
    if os.path.exists(cache_path):
        return cache_path

    try:
        results = VideosSearch(f"https://www.youtube.com/watch?v={videoid}", limit=1)
        results_data = await results.next()
        data = results_data["result"][0]
        title = re.sub(r"\W+", " ", data.get("title", "Unsupported Title")).title()
        thumbnail = data.get("thumbnails", [{}])[0].get("url", YOUTUBE_IMG_URL)
        duration = data.get("duration")
    except Exception as e:
        logging.error(f"Error fetching YouTube data: {e}")
        title, thumbnail, duration = "Unsupported Title", YOUTUBE_IMG_URL, None

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
        # 1. Base Image: Black & White & Blurred
        base = Image.open(thumb_path).resize((1280, 720)).convert("L").convert("RGBA")
        bg = base.filter(ImageFilter.GaussianBlur(10))
        bg = ImageEnhance.Brightness(bg).enhance(0.4)

        # 2. Main Character Image (Thumbnail as B&W focus)
        main_img = Image.open(thumb_path).resize((800, 800)).convert("L").convert("RGBA")
        main_img = ImageEnhance.Contrast(main_img).enhance(1.2)
        # Paste slightly off-center for aesthetic look
        bg.paste(main_img, (-100, -50), main_img)

        # 3. Create Golden Light Leak (Diagonal Gradient)
        overlay = Image.new("RGBA", (1280, 720), (0, 0, 0, 0))
        draw_overlay = ImageDraw.Draw(overlay)
        
        # Ek bada triangle jo top-right se light effect de
        # Color: Golden Yellow with transparency
        draw_overlay.polygon([(600, 0), (1280, 0), (1280, 720)], fill=(255, 180, 50, 100))
        overlay = overlay.filter(ImageFilter.GaussianBlur(120)) # Bahut zyada blur soft light ke liye
        bg = Image.alpha_composite(bg, overlay)

        # 4. Text and Branding
        draw = ImageDraw.Draw(bg)
        
        # Load Fonts
        try:
            mashup_font = ImageFont.truetype(FONT_PATH_BRUSH, 140)
            title_font = ImageFont.truetype(FONT_PATH_REGULAR, 35)
            small_font = ImageFont.truetype(FONT_PATH_REGULAR, 20)
        except:
            mashup_font = ImageFont.load_default()
            title_font = ImageFont.load_default()
            small_font = ImageFont.load_default()

        # "Mashup" Text (Stylized)
        draw.text((100, 480), "Mashup", fill="white", font=mashup_font)
        draw.text((450, 580), "songs", fill="white", font=title_font)

        # Song Title (Current Track)
        cleaned_title = trim_to_width(title, title_font, 800)
        draw.text((110, 440), cleaned_title, fill=(200, 200, 200), font=title_font)

        # Bottom Branding
        draw.text((110, 650), f"Playing on @{app.username}", fill="white", font=small_font)
        draw.text((1100, 680), "www.MusicBot.com", fill=(150, 150, 150), font=small_font)

        # Cleanup & Save
        os.remove(thumb_path)
        bg.save(cache_path, "PNG")
        return cache_path

    except Exception as e:
        logging.error(f"Image processing error: {e}")
        return YOUTUBE_IMG_URL
