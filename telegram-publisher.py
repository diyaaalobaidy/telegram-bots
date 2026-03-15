import re
import time
import feedparser
import asyncio
import json
import os
from telegram import Bot
from deep_translator import GoogleTranslator
import dotenv

dotenv.load_dotenv()

# --- CONFIGURATION ---
TOKEN = os.getenv('BOT_TOKEN')
CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')
DATABASE_FILE = 'last_seen.json'
TRANSLATE = False
PERIODIC_CHECK = False

# Dictionary of feeds: { "Name": "URL" }
FEEDS = {
    "BBC": "http://feeds.bbci.co.uk/news/world/rss.xml",
    "NYT": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "AlJazeera": "https://www.aljazeera.com/xml/rss/all.xml",
    "The Guardian": "https://www.theguardian.com/world/rss",
    "Al Arabiya": "https://english.alarabiya.net/feed/rss2/en/News.xml",
    "Middle East Eye": "https://www.middleeasteye.net/rss",
    "The New Arab": "https://www.newarab.com/rss",
    "Mehr News": "https://en.mehrnews.com/rss/tp/579",
}

ARABIC_FEEDS ={
    "BBC": "https://www.bbc.com/arabic/index.xml",
    "AlJazeera": "https://www.aljazeera.net/aljazeerarss/all.xml",
    "Al Arabiya": "https://www.alarabiya.net/feed/rss2/ar/arab-and-world.xml",
    "The New Arab": "https://www.alaraby.co.uk/rss",
    "CNN Arabic": "https://arabic.cnn.com/api/v1/rss/rss.xml",
    "France 24 Arabic": "https://www.france24.com/ar/%D8%A7%D9%84%D8%B4%D8%B1%D9%82-%D8%A7%D9%84%D8%A3%D9%88%D8%B3%D8%B7/rss",
    "Sky News Arabia": "https://www.skynewsarabia.com/rss",
    "RT Arabic": "https://arabic.rt.com/rss/",
    "Euro News Arabic": "https://arabic.euronews.com/rss",
    "AlSharq AlAwsat": "https://aawsat.com/feed",
}

names_ar ={
    "BBC": "بي بي سي",
    "NYT": "نيويورك تايمز",
    "AlJazeera": "الجزيرة",
    "The Guardian": "الغارديان",
    "Al Arabiya": "العربية",
    "Middle East Eye": "عين الشرق الأوسط",
    "The New Arab": "العربي الجديد",
    "Mehr News": "مهر نيوز",
    "CNN Arabic": "سي إن إن بالعربية",
    "France 24 Arabic": "فرانس 24 بالعربية",
    "Sky News Arabia": "سكاي نيوز بالعربية",
    "RT Arabic": "آر تي بالعربية",
    "Euro News Arabic": "يورونيوز بالعربية",
    "AlSharq AlAwsat": "الشرق الأوسط",
}

CHECK_INTERVAL = 60 # 1 minute
# ---------------------

bot = Bot(token=TOKEN)
translator = GoogleTranslator(source='auto', target='ar')

def load_last_seen():
    """Loads the last seen post IDs from the JSON file."""
    if os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_last_seen(data):
    """Saves the last seen post IDs to the JSON file."""
    with open(DATABASE_FILE, 'w') as f:
        json.dump(data, f, indent=4)

async def process_feeds():
    last_seen = load_last_seen()
    to_be_sent = []
    for name, url in ARABIC_FEEDS.items():
        print(f"Checking {name}...")
        feed = feedparser.parse(url)
        
        if not feed.entries:
            continue

        # The first entry in the RSS is usually the newest
        latest_entry = feed.entries[0]
        latest_id = latest_entry.link
        
        # Compare with what we have stored
        if last_seen.get(name) != latest_id:
            try:
                for entry in feed.entries[:2]:
                    if entry.link == last_seen.get(name):
                        break
                    # Translate
                    title = re.sub(r'<.*?>', '', entry.title) # strip html tags from title
                    if TRANSLATE:
                        title = translator.translate(title)
                    # strip html tags from description and limit to 5000 characters for translation
                    try:
                        description = re.sub(r'<.*?>', '', entry.description)[:5000]
                    except Exception as e:
                        print(e)
                        try:
                            description:str = re.sub(r'<.*?>', '', entry.content)[:5000]
                        except Exception as e:
                            print(e)
                            description = ""
                    if TRANSLATE:
                        description = translator.translate(description)
                    # get image if exists
                    image_url = None
                    if 'media_content' in entry:
                        image_url = entry.media_content[0]['url']
                    

                    message = ((
                        f"\u200f<b>{title}</b>\n\n"
                        f"{description}\n\n"
                        f"<a href='{entry.link}'>المصدر: {names_ar[name]}</a>\n"
                        f"#{name.replace(' ', '_')} #{names_ar[name].replace(' ', '_')}\n"
                    ), image_url)
                    try:
                        published_time = entry.published_parsed
                    except Exception as e:
                        published_time = time.gmtime() # use current time if published time is not available

                    # append to to_be_sent list with time of the post for ordering
                    to_be_sent.append((message, published_time, name, entry.link))
                last_seen[name] = latest_id
                save_last_seen(last_seen)
                print(f"New post added for {name}")
                
            except Exception as e:
                print(f"Error processing {name}: {e}")
    # order messages by feed published time
    to_be_sent.sort(key=lambda x: x[1])
    for message, _, _, _ in to_be_sent:
        try:
            await bot.send_message(chat_id=CHANNEL_ID, text=message[0], parse_mode='HTML', write_timeout=10, disable_web_page_preview=False, read_timeout=10, connect_timeout=10, pool_timeout=10)
            await asyncio.sleep(2)  # To avoid hitting rate limits
        except Exception as e:
            print(f"Error sending message: {e}")
    print("Finished checking all feeds.")

async def main():
    print("Bot started...")
    while True:
        await process_feeds()
        await asyncio.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    if PERIODIC_CHECK:
        asyncio.run(main())
    else:
        asyncio.run(process_feeds())