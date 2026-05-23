# 🤖 MiMo Telegram Bot

Bot Telegram dengan AI **Xiaomi MiMo V2.5 Pro**

## Fitur

- 💬 Chat AI dengan MiMo V2.5 Pro
- 🛡️ Analisis keamanan crypto
- 📚 Pengetahuan blockchain
- 🇮🇩 Bahasa Indonesia

## Setup

### 1. Buat Bot Telegram
1. Buka [@BotFather](https://t.me/BotFather)
2. Kirim `/newbot`
3. Ikuti instruksi, simpan token

### 2. Dapatkan MiMo API Key
1. Buka [platform.xiaomimimo.com](https://platform.xiaomimimo.com)
2. Buat akun, generate API key

### 3. Install & Jalankan

```bash
# Clone repo
git clone https://github.com/tonnkid/mimo-telegram-bot.git
cd mimo-telegram-bot

# Install dependencies
pip install -r requirements.txt

# Copy .env
cp .env.example .env
# Edit .env, isi token & API key

# Jalankan
python bot.py
```

### 4. Test di Telegram
Cari bot kamu, kirim `/start`, lalu chat!

## Commands

- `/start` - Mulai bot
- `/help` - Bantuan
- `/info` - Info bot

## Tech Stack

- Python 3.11+
- python-telegram-bot
- Xiaomi MiMo V2.5 Pro API

## License

MIT
