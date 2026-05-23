#!/usr/bin/env python3
"""
MiMo Telegram Bot — DeFi AI Assistant
Powered by Xiaomi MiMo V2.5 Pro
"""

import logging
import os
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes
)
import httpx
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MIMO_API_KEY = os.getenv("MIMO_API_KEY")
MIMO_API_URL = os.getenv("MIMO_API_URL", "https://api.xiaomimimo.com/v1")
MIMO_MODEL = os.getenv("MIMO_MODEL", "mimo-v2.5-pro")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def call_mimo(messages: list) -> str:
    """Call MiMo API with fallback."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{MIMO_API_URL}/chat/completions",
                json={"model": MIMO_MODEL, "messages": messages, "max_tokens": 2000, "temperature": 0.7},
                headers={"Authorization": f"Bearer {MIMO_API_KEY}"}
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"MiMo API error: {e}")
    
    # Fallback response
    return None


# --- Commands ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🛡️ *MiMo Guard Bot*

"
        "DeFi AI Assistant powered by Xiaomi MiMo\!

"
        "📌 *Commands:*
"
        "/start \- Mulai bot
"
        "/help \- Bantuan
"
        "/ask <pertanyaan> \- Tanya AI
"
        "/check <address> \- Cek address scam
"
        "/analyze <project> \- Analisis project
"
        "/token <name> \- Info token

"
        "💬 Atau langsung kirim pesan aja\!"
    )
    await update.message.reply_text(text, parse_mode="MarkdownV2")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📚 *Bantuan MiMo Guard Bot*

"
        "*Fitur utama:*
"
        "🔍 \- Scan address scam/honeypot
"
        "📊 \- Analisis project crypto
"
        "💡 \- Tanya jawab seputar DeFi
"
        "🛡️ \- Tips keamanan crypto

"
        "*Contoh:*
"
        "/check 0x123\.\.\.abc
"
        "/analyze EigenLayer
"
        "/ask Apa itu liquidity pool?

"
        "💬 Atau langsung chat aja, aku bantu\!"
    )
    await update.message.reply_text(text, parse_mode="MarkdownV2")


async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args) if context.args else None
    if not query:
        await update.message.reply_text("❓ Contoh: /ask Apa itu DeFi?")
        return
    
    await update.message.reply_text("🤔 Mikir dulu...")
    
    messages = [
        {"role": "system", "content": "Kamu adalah asisten DeFi yang helpful. Jawab dengan bahasa Indonesia yang santai tapi informatif. Gunakan emoji. Max 500 kata."},
        {"role": "user", "content": query}
    ]
    
    response = await call_mimo(messages)
    if response:
        await update.message.reply_text(response)
    else:
        await update.message.reply_text(
            "⚠️ Maaf, AI sedang offline. Coba lagi nanti ya!"
        )


async def check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    address = " ".join(context.args) if context.args else None
    if not address:
        await update.message.reply_text("❓ Contoh: /check 0x123...abc")
        return
    
    await update.message.reply_text(f"🔍 Scanning `{address}`...", parse_mode="Markdown")
    
    messages = [
        {"role": "system", "content": "Kamu adalah DeFi security analyst. Analisis address/contract berikut. Kasih: risk score (0-100), status (safe/warning/danger), dan penjelasan singkat. Format pakai emoji."},
        {"role": "user", "content": f"Cek address ini: {address}"}
    ]
    
    response = await call_mimo(messages)
    if response:
        await update.message.reply_text(response)
    else:
        await update.message.reply_text(
            f"🔍 *Scan Result:* `{address}`\n\n"
            "⚠️ API sedang offline\. Coba lagi nanti\.",
            parse_mode="MarkdownV2"
        )


async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE):
    project = " ".join(context.args) if context.args else None
    if not project:
        await update.message.reply_text("❓ Contoh: /analyze EigenLayer")
        return
    
    await update.message.reply_text(f"📊 Analyzing *{project}*...", parse_mode="Markdown")
    
    messages = [
        {"role": "system", "content": "Kamu adalah crypto project analyst. Analisis project berikut. Kasih: overview, team, funding, tokenomics, airdrop potential, risk factors. Format rapi pakai emoji."},
        {"role": "user", "content": f"Analisis project: {project}"}
    ]
    
    response = await call_mimo(messages)
    if response:
        await update.message.reply_text(response)
    else:
        await update.message.reply_text(
            f"📊 *Analisis:* {project}\n\n"
            "⚠️ API sedang offline\. Coba lagi nanti\.",
            parse_mode="MarkdownV2"
        )


async def token_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = " ".join(context.args) if context.args else None
    if not name:
        await update.message.reply_text("❓ Contoh: /token ETH")
        return
    
    messages = [
        {"role": "system", "content": "Kamu adalah crypto token analyst. Kasih info tentang token berikut: harga, market cap, use case, dan prediksi singkat. Format pakai emoji."},
        {"role": "user", "content": f"Info token: {name}"}
    ]
    
    response = await call_mimo(messages)
    if response:
        await update.message.reply_text(response)
    else:
        await update.message.reply_text(
            f"🪙 *Info Token:* {name}\n\n"
            "⚠️ API sedang offline\. Coba lagi nanti\.",
            parse_mode="MarkdownV2"
        )


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    user_name = update.effective_user.first_name
    
    messages = [
        {"role": "system", "content": f"Kamu MiMo Guard Bot, asisten DeFi AI yang helpful untuk {user_name}. Jawab dengan bahasa Indonesia santai, pakai emoji, max 300 kata. Bisa bahas crypto, DeFi, airdrop, security."},
        {"role": "user", "content": user_msg}
    ]
    
    response = await call_mimo(messages)
    if response:
        await update.message.reply_text(response)
    else:
        await update.message.reply_text(
            "🤔 AI lagi istirahat, coba lagi nanti ya! Atau pakai command /help"
        )


def main():
    logger.info("🤖 MiMo Guard Bot starting...")
    
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("ask", ask))
    app.add_handler(CommandHandler("check", check))
    app.add_handler(CommandHandler("analyze", analyze))
    app.add_handler(CommandHandler("token", token_info))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    
    logger.info("✅ Bot is running!")
    app.run_polling()


if __name__ == "__main__":
    main()
