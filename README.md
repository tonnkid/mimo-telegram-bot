# 🤖 MiMo Telegram Bot

Ultimate DeFi AI Assistant powered by Xiaomi MiMo V2.5 Pro

## Features

### 💰 Market & Prices
- `/price <token>` — Real-time token price (CoinGecko)
- `/market` — Top 10 crypto market overview
- `/trending` — Trending coins 24h
- `/gas` — Ethereum gas prices
- `/fear` — Fear & Greed Index

### 🛡️ Security
- `/check <address>` — Scan address/contract for scam
- `/security` — DeFi security checklist
- Auto scam detection in chat

### 💡 AI Assistant
- `/ask <question>` — Ask anything about DeFi
- `/airdrops` — Latest airdrop info
- `/defitips` — DeFi tips & tricks
- `/portfolio` — Portfolio tips
- `/news` — Crypto news summary
- `/analyze <project>` — Deep project analysis

### 💬 Smart Chat
- Just send any message for AI conversation
- Auto scam keyword detection

## Setup

1. Clone this repo
2. Copy `.env.example` to `.env`
3. Fill in `TELEGRAM_TOKEN` and `MIMO_API_KEY`
4. `pip install -r requirements.txt`
5. `python bot.py`

## Deploy on Railway

1. Fork this repo
2. Go to Railway
3. New Project -> Deploy from GitHub
4. Add Environment Variables
5. Deploy!

## Tech Stack
- Python 3.11
- python-telegram-bot 21+
- Xiaomi MiMo V2.5 Pro API
- CoinGecko API (free)
