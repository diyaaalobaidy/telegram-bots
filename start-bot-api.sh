#!/bin/bash
docker run -d --name telegram-bot-api --restart unless-stopped \
  -e TELEGRAM_API_ID=5364220 \
  -e TELEGRAM_API_HASH=efc4300b1badfedafd28272bef4dad9a \
  -p 8081:8081 \
  -v telegram-bot-api-data:/var/lib/telegram-bot-api \
  aiogram/telegram-bot-api:latest
