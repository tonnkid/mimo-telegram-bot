#!/usr/bin/env python3
"""
MiMo Telegram Bot
Powered by Xiaomi MiMo V2.5 Pro AI

Features:
- /start - Welcome message
- /help - Show help
- /ask <question> - Ask MiMo AI
- /scan <project> - Scan airdrop project
- Direct chat - Auto-reply with MiMo AI
"""

import os
import logging
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread

import httpx
from dotenv import load_dotenv

load_dotenv()

# Config
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
MIMO_API_KEY = os.getenv("MIMO_API_KEY", "")
MIMO_API_URL = os.getenv("MIMO_API_URL", "https://api.xiaomimimo.com/v1")
PORT = int(os.getenv("PORT", "8080"))

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("mimo-bot")

# ============== Health Check Server (for Railway) ==============

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"MiMo Bot is running!")
    
    def log_message(self, format, *args):
        pass  # Suppress logs

def start_health_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    logger.info(f"Health check server on port {PORT}")
    server.serve_forever()

# ============== MiMo AI Client ==============

async def ask_mimo(question: str, system_prompt: str = "") -> str:
    """Ask MiMo AI a question."""
    if not MIMO_API_KEY:
        return "❌ MiMo API key not configured!"
    
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": question})
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{MIMO_API_URL}/chat/completions",
                json={
                    "model": "mimo-v2.5-pro",
                    "messages": messages,
                    "max_tokens": 2000,
                    "temperature": 0.7,
                },
                headers={"Authorization": f"Bearer {MIMO_API_KEY}"}
            )
            data = resp.json()
            if "choices" in data:
                return data["choices"][0]["message"]["content"]
            return f"Error: {data.get('error', {}).get('message', 'Unknown error')}"
    except Exception as e:
        return f"❌ Error: {str(e)}"

# ============== Telegram Bot ==============

async def send_message(chat_id: int, text: str):
    """Send message to Telegram."""
    async with httpx.AsyncClient() as client:
        await client.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
        )

async def handle_update(update: dict):
    """Handle incoming Telegram update."""
    message = update.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")
    username = message.get("from", {}).get("first_name", "User")
    
    if not chat_id or not text:
        return
    
    logger.info(f"[{username}] {text}")
    
    # Command handlers
    if text == "/start":
        await send_message(chat_id, 
            f"🤖 *MiMo Guard Bot*

"
            f"Halo {username}! Aku bot AI powered by *Xiaomi MiMo V2.5 Pro*.

"
            f"📋 *Commands:*
"
            f"/ask <pertanyaan> - Tanya ke MiMo AI
"
            f"/scan <project> - Scan airdrop project
"
            f"/help - Bantuan

"
            f"Atau langsung chat aja! 💬"
        )
    
    elif text == "/help":
        await send_message(chat_id,
            "📚 *Bantuan MiMo Bot*

"
            "1️⃣ *Tanya AI:*
`/ask Apa itu DeFi?`

"
            "2️⃣ *Scan Project:*
`/scan LayerZero`

"
            "3️⃣ *Chat Biasa:*
Kirim pesan langsung, bot akan balas pakai AI

"
            "🤖 Powered by Xiaomi MiMo V2.5 Pro"
        )
    
    elif text.startswith("/ask "):
        question = text[5:]
        await send_message(chat_id, "🤔 Thinking...")
        response = await ask_mimo(question)
        await send_message(chat_id, f"🤖 *MiMo:*

{response}")
    
    elif text.startswith("/scan "):
        project = text[6:]
        await send_message(chat_id, f"🔍 Scanning *{project}*...")
        system = "You are a crypto airdrop analyst. Analyze the project and give: legitimacy score (0-100), potential airdrop chance, risks, and recommendation. Be concise."
        response = await ask_mimo(f"Analyze this crypto project for airdrop potential: {project}", system)
        await send_message(chat_id, f"📊 *Scan Result: {project}*

{response}")
    
    elif text.startswith("/"):
        await send_message(chat_id, "❌ Command tidak dikenal. Ketik /help untuk bantuan.")
    
    else:
        # Auto-reply for regular messages
        await send_message(chat_id, "🤔 Thinking...")
        system = "You are MiMo Guard Bot, a helpful AI assistant powered by Xiaomi MiMo. Be concise and helpful. Reply in the same language the user uses."
        response = await ask_mimo(text, system)
        await send_message(chat_id, f"🤖 {response}")

async def poll_updates():
    """Long-poll for Telegram updates."""
    offset = 0
    async with httpx.AsyncClient() as client:
        while True:
            try:
                resp = await client.get(
                    f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates",
                    params={"offset": offset, "timeout": 30}
                )
                data = resp.json()
                
                if data.get("ok"):
                    for update in data.get("result", []):
                        offset = update["update_id"] + 1
                        await handle_update(update)
            except Exception as e:
                logger.error(f"Poll error: {e}")
                await asyncio.sleep(5)

async def main():
    """Main entry point."""
    if not TELEGRAM_TOKEN:
        print("❌ TELEGRAM_TOKEN not set!")
        return
    
    # Start health check server in background
    Thread(target=start_health_server, daemon=True).start()
    
    # Set bot commands
    async with httpx.AsyncClient() as client:
        await client.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setMyCommands",
            json={"commands": [
                {"command": "start", "description": "Start the bot"},
                {"command": "ask", "description": "Ask MiMo AI a question"},
                {"command": "scan", "description": "Scan airdrop project"},
                {"command": "help", "description": "Show help"},
            ]}
        )
    
    logger.info("🤖 MiMo Bot started!")
    await poll_updates()

if __name__ == "__main__":
    asyncio.run(main())
