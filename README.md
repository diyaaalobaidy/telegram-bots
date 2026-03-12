# Telegram Video Downloader Bot

A Telegram bot that downloads videos and audio from YouTube (and other yt-dlp supported sites) at user-selected quality, and sends them directly to the chat.

## Features

- Paste any supported URL and get an inline quality picker
- Choose from all available video resolutions (1080p, 720p, 480p, …)
- Download audio-only as MP3
- Sends the file with a rich caption: title, channel, duration, view count, and selected quality
- Supports files up to **2 GB** via the local Telegram Bot API server
- Short hash-based filenames prevent filesystem path-too-long errors

## Requirements

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/) *(recommended)*
- **Or** for manual setup: Python 3.10+, ffmpeg, Node.js

## Quick Start (Docker — recommended)

### 1. Clone and configure

```bash
git clone <repo-url>
cd telegram-summarizer
cp .env.example .env
```

Edit `.env`:

```env
BOT_TOKEN=<your_bot_token_from_BotFather>
API_ID=<your_api_id_from_my.telegram.org>
API_HASH=<your_api_hash_from_my.telegram.org>
```

- **BOT_TOKEN** — create a bot via [@BotFather](https://t.me/BotFather)
- **API_ID / API_HASH** — obtain from [my.telegram.org](https://my.telegram.org) → API development tools

### 2. Build and run

```bash
docker compose up -d --build
```

That's it. Both the local Telegram Bot API server and the bot itself start together.

**Useful commands:**

```bash
docker compose logs -f bot            # Follow bot logs
docker compose logs -f telegram-bot-api
docker compose down                   # Stop everything
docker compose up -d                  # Start again (no rebuild)
docker compose up -d --build          # Rebuild after code changes
```

---

## Manual Setup (without Docker)

### 1. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Install system dependencies

```bash
sudo apt install ffmpeg nodejs
```

### 3. Configure `.env`

```bash
cp .env.example .env  # then fill in values
```

### 4. Start the local Telegram Bot API server

```bash
./start-bot-api.sh
```

### 5. Run the bot

```bash
.venv/bin/python main.py
```

## Usage

1. Start a chat with your bot on Telegram
2. Send any video URL (YouTube, etc.)
3. The bot fetches available formats and shows an inline keyboard
4. Tap a resolution button (e.g. **🎬 1080p**) or **🎵 Audio only (MP3)**
5. The bot downloads and sends the file with title, channel, duration, and view count in the caption

## Project Structure

```
telegram-summarizer/
├── main.py              # Bot logic
├── Dockerfile           # Bot container image
├── docker-compose.yml   # Orchestrates bot + local Bot API server
├── requirements.txt     # Python dependencies
├── start-bot-api.sh     # Manual script to start the local Bot API server
├── .env                 # Secret keys (not committed)
├── .env.example         # Template for .env
└── downloads/           # Temporary download directory (auto-created)
```

## Dependencies

| Package | Purpose |
|---|---|
| `python-telegram-bot` | Telegram Bot API client |
| `yt-dlp` | Video/audio downloading |
| `python-dotenv` | Load `.env` file |

## Notes

- The `downloads/` folder is a staging area; files are deleted after being sent. In Docker it is bind-mounted so it is accessible on the host at `./downloads`.
- The local Bot API server must be running before the bot starts — `docker compose` handles this ordering automatically via `depends_on`.
- The bot uses `asyncio.run_in_executor` to offload yt-dlp downloads to a thread, keeping the event loop responsive.
- `LOCAL_API_URL` defaults to `http://localhost:8081` for manual runs, and is overridden to `http://telegram-bot-api:8081` inside Docker Compose.
