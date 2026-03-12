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

- Python 3.10+
- [ffmpeg](https://ffmpeg.org/) (for audio extraction and video merging)
- [Docker](https://docs.docker.com/get-docker/) (for the local Telegram Bot API server)
- Node.js (for yt-dlp YouTube extraction — already used automatically if `node` is on `$PATH`)

## Setup

### 1. Clone and create a virtual environment

```bash
git clone <repo-url>
cd telegram-summarizer
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Install ffmpeg (if not already installed)

```bash
sudo apt install ffmpeg
```

### 3. Configure environment variables

Copy the example and fill in your values:

```bash
cp .env.example .env   # or edit .env directly
```

`.env` file:

```env
BOT_TOKEN=<your_bot_token_from_BotFather>
API_ID=<your_api_id_from_my.telegram.org>
API_HASH=<your_api_hash_from_my.telegram.org>
```

- **BOT_TOKEN** — create a bot via [@BotFather](https://t.me/BotFather)
- **API_ID / API_HASH** — obtain from [my.telegram.org](https://my.telegram.org) → API development tools

### 4. Start the local Telegram Bot API server

The local server removes the default 50 MB upload limit, allowing files up to 2 GB.

```bash
./start-bot-api.sh
```

This starts a Docker container (`telegram-bot-api`) on port `8081` with `--restart unless-stopped`, so it survives reboots.

Check it is running:

```bash
docker logs telegram-bot-api
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
├── requirements.txt     # Python dependencies
├── start-bot-api.sh     # Script to start the local Telegram Bot API server
├── .env                 # Secret keys (not committed)
└── downloads/           # Temporary download directory (auto-created)
```

## Dependencies

| Package | Purpose |
|---|---|
| `python-telegram-bot` | Telegram Bot API client |
| `yt-dlp` | Video/audio downloading |
| `python-dotenv` | Load `.env` file |

## Notes

- The `downloads/` folder is used as a staging area; files are deleted after being sent.
- The local Bot API server must be running before starting the bot, otherwise large file sends will fail.
- The bot uses `asyncio.run_in_executor` to offload yt-dlp downloads to a thread, keeping the event loop responsive.
