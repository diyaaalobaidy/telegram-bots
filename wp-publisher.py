import feedparser
import subprocess
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from deep_translator import GoogleTranslator
import dotenv
dotenv.load_dotenv()

# --- CONFIGURATION ---

# WordPress Setup
WP_PATH = os.environ["WP_PATH"]  # Absolute path to the WordPress installation
WP_CLI  = "wp"                   # Path to wp-cli binary, e.g. /usr/local/bin/wp

# Target Feeds (Examples)
FEEDS = [
    "https://feeds.feedburner.com/TheHackersNews",
    "https://techcrunch.com/feed/",
]

def fetch_full_article(url):
    """
    Returns (text, images) where:
      text   – plain text of the article body for translation
      images – list of absolute image URLs found in the article
    """
    try:
        response = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        # Try common article containers, fall back to <body>
        article = (
            soup.find("article")
            or soup.find(attrs={"class": lambda c: c and "article-body" in c})
            or soup.find(attrs={"class": lambda c: c and "post-content" in c})
            or soup.find(attrs={"class": lambda c: c and "entry-content" in c})
            or soup.find(attrs={"class": lambda c: c and "articlebody" in c})
        )
        if not article:
            return "", []
        # Collect all images with absolute URLs (skip tiny icons/trackers)
        images = []
        for img in article.find_all("img", src=True):
            src = urljoin(url, img["src"])
            width = int(img.get("width") or 0)
            if width and width < 100:
                continue  # skip small decorative images
            images.append(src)
        text = article.get_text(separator="\n", strip=True)
        return text, images
    except Exception as e:
        print(f"Failed to fetch article {url}: {e}")
        return "", []


def _split_into_chunks(text, max_size=4500):
    """Split text into chunks no larger than max_size, breaking on newline or full stop."""
    chunks = []
    while len(text) > max_size:
        # Search backwards from max_size for a newline or full stop
        split_at = max(
            text.rfind("\n", 0, max_size),
            text.rfind(".", 0, max_size),
        )
        if split_at == -1:
            split_at = max_size  # No safe break found; hard-cut as last resort
        else:
            split_at += 1  # Include the delimiter in the current chunk
        chunks.append(text[:split_at].strip())
        text = text[split_at:].strip()
    if text:
        chunks.append(text)
    return chunks

def translate_to_arabic(text):
    if not text:
        return ""
    translator = GoogleTranslator(source='auto', target='ar')
    chunks = _split_into_chunks(text)
    return " ".join(translator.translate(chunk) for chunk in chunks)

def is_already_published(source_url):
    """Return True if a post with this source URL already exists in WordPress."""
    cmd = [
        WP_CLI, "post", "list",
        "--meta_key=_source_url",
        f"--meta_value={source_url}",
        "--post_status=any",
        "--format=count",
        f"--path={WP_PATH}",
        "--allow-root",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0 and result.stdout.strip() != "0"

def post_to_wordpress(title, content, source_url, images=None):
    images_html = "".join(
        f'<img src="{src}" style="max-width:100%; height:auto; display:block; margin:1em 0;" />'
        for src in (images or [])
    )
    attribution = f'<p><em>المصدر: <a href="{source_url}">{source_url}</a></em></p>'
    full_content = f"{images_html}{content}<br>{attribution}"

    cmd = [
        WP_CLI, "post", "create",
        f"--post_title={title}",
        f"--post_content={full_content}",
        "--post_status=publish",   # Change to 'publish' to go live immediately
        "--post_category=1",     # Replace with your tech category ID
        f"--path={WP_PATH}",
        "--allow-root",
        "--porcelain",           # Outputs only the new post ID
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        post_id = result.stdout.strip()
        # Store the source URL as meta to enable deduplication on future runs
        meta_cmd = [
            WP_CLI, "post", "meta", "add",
            post_id, "_source_url", source_url,
            f"--path={WP_PATH}",
            "--allow-root",
        ]
        subprocess.run(meta_cmd, capture_output=True)
        return post_id  # Returns the new post ID
    else:
        print(f"WP-CLI error: {result.stderr.strip()}")
        return None

def process_feeds():
    for url in FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:3]: # Processing top 3 newest for demo
            print(f"Processing: {entry.title}")

            # Skip if already published
            if is_already_published(entry.link):
                print(f"Already published, skipping: {entry.title}")
                continue

            # Fetch full article and inline images
            full_text, images = fetch_full_article(entry.link)

            # Fall back to RSS-level media if no images found in article body
            if not images:
                if 'media_content' in entry:
                    images = [entry.media_content[0]['url']]
                else:
                    for link in entry.get('links', []):
                        if 'image' in link.get('type', ''):
                            images = [link.get('href')]
                            break

            # Translate
            ar_title = translate_to_arabic(entry.title)
            ar_content = translate_to_arabic(full_text or (entry.summary if 'summary' in entry else ""))

            # Publish via WP-CLI
            post_id = post_to_wordpress(ar_title, ar_content, entry.link, images)
            if post_id:
                print(f"Created post ID: {post_id}")
            else:
                print(f"Failed to create post for: {entry.title}")

if __name__ == "__main__":
    process_feeds()