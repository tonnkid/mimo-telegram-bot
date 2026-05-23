#!/usr/bin/env python3
"""
MiMo Telegram Bot
Bot Telegram dengan AI MiMo V2.5 Pro
"""
import os
import httpx
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ============ CONFIG ============
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "YOUR_BOT_TOKEN_HERE")
MIMO_API_KEY = os.getenv("MIMO_API_KEY", "YOUR_MIMO_API_KEY_HERE")
MIMO_API_URL = "https://api.xiaomimimo.com/v1/chat/completions"
MODEL = "mimo-v2.5-pro"

# ============ MiMo Client ============
async def chat_with_mimo(user_message: str, system_prompt: str = None) -> str:
    """Kirim pesan ke MiMo API dan dapatkan respons."""
    messages = []
    
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    
    messages.append({"role": "user", "content": user_message})
    
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                MIMO_API_URL,
                json={
                    "model": MODEL,
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 2000,
                },
                headers={
                    "Authorization": f"Bearer {MIMO_API_KEY}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            else:
                return f"Error: API returned {response.status_code}"
                
    except Exception as e:
        return f"Error: {str(e)}"

# ============ System Prompt ============
SYSTEM_PROMPT = """Kamu adalah MiMo Guard AI Assistant, bot Telegram yang membantu dengan:
- 🛡️ Analisis keamanan DeFi dan crypto
- 🔍 Informasi tentang airdrop dan mining
- 💡 Saran investasi (bukan financial advice)
- 📚 Pengetahuan umum tentang blockchain

Selalu ramah, informatif, dan gunakan emoji. 
Jawab dalam bahasa Indonesia.
"""

# ============ Handlers ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /start"""
    user = update.effective_user
    await update.message.reply_text(
        f"🤖 Halo {user.first_name}! Aku MiMo Guard AI.\n\n"
        f"Powered by Xiaomi MiMo V2.5 Pro\n\n"
        f"Ketik pesan apa saja, nanti aku bantu!"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /help"""
    help_text = """
🤖 MiMo Guard AI - Commands

/start - Mulai bot
/help - Bantuan
/info - Info bot

Atau langsung ketik pertanyaan!
"""
    await update.message.reply_text(help_text)

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk /info"""
    await update.message.reply_text(
        "ℹ️ Bot Info\n\n"
        "🤖 Model: Xiaomi MiMo V2.5 Pro\n"
        "🔗 API: api.xiaomimimo.com\n"
        "💡 Fitur: Chat AI, Analisis Crypto"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler untuk semua pesan teks"""
    user_message = update.message.text
    
    # Show typing indicator
    await update.message.chat.send_action("typing")
    
    # Get response from MiMo
    response = await chat_with_mimo(user_message, SYSTEM_PROMPT)
    
    # Send response
    await update.message.reply_text(response)

def main():
    """Main function"""
    print("🤖 Starting MiMo Telegram Bot...")
    
    # Build application
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("info", info))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Run bot
    print("✅ Bot running!")
    app.run_polling()

if __name__ == "__main__":
    main()
