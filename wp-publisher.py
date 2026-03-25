import feedparser
import subprocess
from deep_translator import GoogleTranslator

# --- CONFIGURATION ---

# WordPress Setup
WP_PATH = "/var/www/html"  # Absolute path to the WordPress installation
WP_CLI  = "wp"            # Path to wp-cli binary, e.g. /usr/local/bin/wp

# Target Feeds (Examples)
FEEDS = [
    "https://feeds.feedburner.com/TheHackersNews",
    "https://techcrunch.com/feed/",
    "https://www.theverge.com/rss/index.xml"
]

def translate_to_arabic(text):
    if not text: return ""
    return GoogleTranslator(source='auto', target='ar').translate(text)

def post_to_wordpress(title, content, source_url, media_url=None):
    img_tag = f'<img src="{media_url}" style="width:100%; height:auto;" /><br>' if media_url else ""
    attribution = f'<p><em>المصدر: <a href="{source_url}">{source_url}</a></em></p>'
    full_content = f"{img_tag}{content}<br>{attribution}"

    cmd = [
        WP_CLI, "post", "create",
        f"--post_title={title}",
        f"--post_content={full_content}",
        "--post_status=draft",   # Change to 'publish' to go live immediately
        "--post_category=1",     # Replace with your tech category ID
        f"--path={WP_PATH}",
        "--allow-root",
        "--porcelain",           # Outputs only the new post ID
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.strip()  # Returns the new post ID
    else:
        print(f"WP-CLI error: {result.stderr.strip()}")
        return None

def process_feeds():
    for url in FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:3]: # Processing top 3 newest for demo
            print(f"Processing: {entry.title}")
            
            # Extract Media (Looking for common RSS media tags)
            media_url = None
            if 'media_content' in entry:
                media_url = entry.media_content[0]['url']
            elif 'links' in entry:
                for link in entry.links:
                    if 'image' in link.get('type', ''):
                        media_url = link.get('href')

            # Translate
            ar_title = translate_to_arabic(entry.title)
            ar_content = translate_to_arabic(entry.summary if 'summary' in entry else "")
            
            # Publish via WP-CLI
            post_id = post_to_wordpress(ar_title, ar_content, entry.link, media_url)
            if post_id:
                print(f"Created post ID: {post_id}")
            else:
                print(f"Failed to create post for: {entry.title}")

if __name__ == "__main__":
    process_feeds()