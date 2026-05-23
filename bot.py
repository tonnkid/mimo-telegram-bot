#!/usr/bin/env python3
"""
MiMo Telegram Bot - Ultimate DeFi AI Assistant
Powered by Xiaomi MiMo V2.5 Pro
"""

import logging
import os
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    filters, ContextTypes
)
import httpx
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
MIMO_API_KEY = os.getenv("MIMO_API_KEY", "")
MIMO_API_URL = os.getenv("MIMO_API_URL", "https://api.xiaomimimo.com/v1")
MIMO_MODEL = os.getenv("MIMO_MODEL", "mimo-v2.5-pro")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

if not TELEGRAM_TOKEN:
    logger.error("TELEGRAM_TOKEN not set!")
    exit(1)

# ============================================================
#  MiMo API Client
# ============================================================

async def call_mimo(messages: list, max_tokens: int = 2000) -> str:
    """Call MiMo API with error handling."""
    if not MIMO_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{MIMO_API_URL}/chat/completions",
                json={
                    "model": MIMO_MODEL,
                    "messages": messages,
                    "max_tokens": max_tokens,
                    "temperature": 0.7,
                },
                headers={"Authorization": f"Bearer {MIMO_API_KEY}"}
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
            else:
                logger.warning(f"MiMo API returned {resp.status_code}")
    except Exception as e:
        logger.error(f"MiMo API error: {e}")
    return None


# ============================================================
#  Price Data (CoinGecko Free API)
# ============================================================

COINGECKO_IDS = {
    "btc": "bitcoin", "eth": "ethereum", "bnb": "binancecoin",
    "sol": "solana", "xrp": "ripple", "ada": "cardano",
    "doge": "dogecoin", "avax": "avalanche-2", "dot": "polkadot",
    "matic": "matic-network", "link": "chainlink", "uni": "uniswap",
    "aave": "aave", "arb": "arbitrum", "op": "optimism",
    "atom": "cosmos", "near": "near", "ftm": "fantom",
    "usdt": "tether", "usdc": "usd-coin", "dai": "dai",
}

async def get_price(token: str) -> dict:
    """Get token price from CoinGecko."""
    token_id = COINGECKO_IDS.get(token.lower(), token.lower())
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"https://api.coingecko.com/api/v3/simple/price",
                params={
                    "ids": token_id,
                    "vs_currencies": "usd",
                    "include_24hr_change": "true",
                    "include_market_cap": "true",
                    "include_24hr_vol": "true",
                }
            )
            if resp.status_code == 200:
                data = resp.json().get(token_id, {})
                return {
                    "price": data.get("usd", 0),
                    "change_24h": data.get("usd_24h_change", 0),
                    "market_cap": data.get("usd_market_cap", 0),
                    "volume_24h": data.get("usd_24h_vol", 0),
                }
    except Exception as e:
        logger.error(f"Price fetch error: {e}")
    return None


async def get_market_overview() -> list:
    """Get top 10 coins market data."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                "https://api.coingecko.com/api/v3/coins/markets",
                params={
                    "vs_currency": "usd",
                    "order": "market_cap_desc",
                    "per_page": 10,
                    "page": 1,
                    "sparkline": "false",
                    "price_change_percentage": "24h",
                }
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        logger.error(f"Market overview error: {e}")
    return []


async def get_gas_prices() -> dict:
    """Get Ethereum gas prices."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get("https://api.etherscan.io/api?module=gastracker&action=gasoracle")
            if resp.status_code == 200:
                data = resp.json().get("result", {})
                return {
                    "low": data.get("SafeGasPrice", "?"),
                    "medium": data.get("ProposeGasPrice", "?"),
                    "high": data.get("FastGasPrice", "?"),
                }
    except Exception as e:
        logger.error(f"Gas price error: {e}")
    return None


async def get_trending() -> list:
    """Get trending coins."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get("https://api.coingecko.com/api/v3/search/trending")
            if resp.status_code == 200:
                return resp.json().get("coins", [])[:7]
    except Exception as e:
        logger.error(f"Trending error: {e}")
    return []


async def get_fear_greed() -> dict:
    """Get Fear & Greed Index."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get("https://api.alternative.me/fng/?limit=1")
            if resp.status_code == 200:
                data = resp.json().get("data", [{}])[0]
                return {
                    "value": data.get("value", "?"),
                    "label": data.get("value_classification", "?"),
                }
    except Exception as e:
        logger.error(f"Fear & Greed error: {e}")
    return None


# ============================================================
#  Scam Detection Patterns
# ============================================================

SCAM_KEYWORDS = [
    "send eth to claim", "send btc to", "private key", "seed phrase",
    "guaranteed profit", "100x guaranteed", "send 1 get 10 back",
    "airdrop claim fee", "connect wallet here", "urgent action required",
]

def quick_scam_check(text: str) -> dict:
    """Quick scam keyword check."""
    text_lower = text.lower()
    found = [kw for kw in SCAM_KEYWORDS if kw in text_lower]
    if found:
        return {
            "safe": False,
            "risk": "HIGH" if len(found) >= 2 else "MEDIUM",
            "flags": found,
        }
    return {"safe": True, "risk": "LOW", "flags": []}


# ============================================================
#  Bot Commands
# ============================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📊 Market", callback_data="market"),
         InlineKeyboardButton("💰 Prices", callback_data="prices")],
        [InlineKeyboardButton("🔥 Trending", callback_data="trending"),
         InlineKeyboardButton("⛽ Gas", callback_data="gas")],
        [InlineKeyboardButton("🛡️ Scan Scam", callback_data="scan"),
         InlineKeyboardButton("🪂 Airdrops", callback_data="airdrops")],
        [InlineKeyboardButton("❓ Help", callback_data="help")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = (
        "🛡️ *MiMo Guard Bot*\n\n"
        "Ultimate DeFi AI Assistant\n"
        "Powered by Xiaomi MiMo V2.5 Pro\n\n"
        "📌 *Commands:*\n"
        "/ask <pertanyaan> — Tanya AI\n"
        "/price <token> — Harga token\n"
        "/market — Market overview\n"
        "/trending — Trending coins\n"
        "/gas — Gas prices ETH\n"
        "/fear — Fear & Greed Index\n"
        "/check <address> — Cek address scam\n"
        "/analyze <project> — Analisis project\n"
        "/token <name> — Info token\n"
        "/airdrops — Info airdrop terbaru\n"
        "/defitips — Tips DeFi\n"
        "/security — Security checklist\n"
        "/portfolio — Tips portfolio\n"
        "/news — Berita crypto terbaru\n\n"
        "💬 Atau langsung chat aja!"
    )
    await update.message.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📚 *Bantuan MiMo Guard Bot*\n\n"
        "*🔍 Market & Prices:*\n"
        "/price ETH — Harga token\n"
        "/market — Top 10 market\n"
        "/trending — Trending coins\n"
        "/gas — Gas prices Ethereum\n"
        "/fear — Fear & Greed Index\n\n"
        "*🛡️ Security:*\n"
        "/check <address> — Cek scam\n"
        "/analyze <project> — Analisis\n"
        "/security — Security checklist\n\n"
        "*💡 AI Assistant:*\n"
        "/ask <pertanyaan> — Tanya AI\n"
        "/defitips — Tips DeFi\n"
        "/airdrops — Info airdrop\n"
        "/portfolio — Tips portfolio\n"
        "/news — Berita crypto\n\n"
        "💬 Langsung chat juga bisa!"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# --- PRICE COMMAND ---
async def price_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token = " ".join(context.args).upper() if context.args else None
    if not token:
        await update.message.reply_text("❓ Contoh: /price ETH\n\nToken tersedia: BTC, ETH, SOL, BNB, XRP, ADA, DOGE, AVAX, DOT, MATIC, LINK, UNI, AAVE, ARB, OP")
        return

    await update.message.reply_text(f"📊 Fetching price *{token}*...", parse_mode="Markdown")
    data = await get_price(token.lower())

    if data:
        change_emoji = "🟢" if data["change_24h"] >= 0 else "🔴"
        change_sign = "+" if data["change_24h"] >= 0 else ""
        mcap = f"${data['market_cap']/1e9:.2f}B" if data['market_cap'] > 1e9 else f"${data['market_cap']/1e6:.2f}M"
        vol = f"${data['volume_24h']/1e9:.2f}B" if data['volume_24h'] > 1e9 else f"${data['volume_24h']/1e6:.2f}M"

        text = (
            f"💰 *{token}/USD*\n\n"
            f"💵 Price: `${data['price']:,.4f}`\n"
            f"{change_emoji} 24h: `{change_sign}{data['change_24h']:.2f}%`\n"
            f"📊 Market Cap: `{mcap}`\n"
            f"📈 Volume 24h: `{vol}`\n\n"
            f"🕐 {datetime.utcnow().strftime('%H:%M UTC')}"
        )
        await update.message.reply_text(text, parse_mode="Markdown")
    else:
        await update.message.reply_text("❌ Token tidak ditemukan. Coba: BTC, ETH, SOL, BNB")


# --- MARKET COMMAND ---
async def market_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 Loading market data...")
    coins = await get_market_overview()

    if coins:
        text = "📊 *Crypto Market Overview*\n\n"
        for i, coin in enumerate(coins[:10], 1):
            change = coin.get("price_change_percentage_24h", 0) or 0
            emoji = "🟢" if change >= 0 else "🔴"
            price = coin["current_price"]
            price_str = f"${price:,.2f}" if price > 1 else f"${price:,.6f}"
            mcap = coin["market_cap"] / 1e9
            text += (
                f"{i}. {emoji} *{coin['symbol'].upper()}* — {price_str}\n"
                f"   24h: {change:+.2f}% | MCap: ${mcap:.1f}B\n\n"
            )
        text += f"🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"
        await update.message.reply_text(text, parse_mode="Markdown")
    else:
        await update.message.reply_text("⚠️ Gagal fetch data market.")


# --- TRENDING COMMAND ---
async def trending_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔥 Loading trending...")
    coins = await get_trending()

    if coins:
        text = "🔥 *Trending Coins (24h)*\n\n"
        for i, item in enumerate(coins, 1):
            coin = item.get("item", {})
            name = coin.get("name", "?")
            symbol = coin.get("symbol", "?")
            rank = coin.get("market_cap_rank", "?")
            text += f"{i}. *{name}* ({symbol.upper()}) — Rank #{rank}\n"
        text += "\n📊 Data from CoinGecko"
        await update.message.reply_text(text, parse_mode="Markdown")
    else:
        await update.message.reply_text("⚠️ Gagal fetch trending data.")


# --- GAS COMMAND ---
async def gas_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⛽ Checking gas prices...")
    gas = await get_gas_prices()

    if gas:
        text = (
            "⛽ *Ethereum Gas Prices*\n\n"
            f"🐢 Low: `{gas['low']} Gwei`\n"
            f"🚶 Medium: `{gas['medium']} Gwei`\n"
            f"🚀 High: `{gas['high']} Gwei`\n\n"
            "💡 *Tips:*\n"
            "• Transaksi biasa: Low/Medium\n"
            "• NFT mint: High\n"
            "• DeFi swap: Medium/High\n"
        )
        await update.message.reply_text(text, parse_mode="Markdown")
    else:
        await update.message.reply_text("⚠️ Gagal fetch gas data. Coba lagi nanti.")


# --- FEAR & GREED COMMAND ---
async def fear_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = await get_fear_greed()
    if data:
        value = int(data["value"])
        if value <= 25:
            emoji = "😱"
        elif value <= 45:
            emoji = "😰"
        elif value <= 55:
            emoji = "😐"
        elif value <= 75:
            emoji = "😎"
        else:
            emoji = "🤑"

        text = (
            f"{emoji} *Fear & Greed Index*\n\n"
            f"📊 Value: *{data['value']}/100*\n"
            f"📝 Status: *{data['label']}*\n\n"
        )
        if value <= 25:
            text += "💡 *Extreme Fear* — Bisa jadi waktu beli! 🟢"
        elif value <= 45:
            text += "💡 *Fear* — Market sedang takut, perhatikan opportunity"
        elif value <= 55:
            text += "💡 *Neutral* — Market seimbang"
        elif value <= 75:
            text += "💡 *Greed* — Market mulai serakah, hati-hati!"
        else:
            text += "💡 *Extreme Greed* — Bisa jadi waktu jual! 🔴"

        await update.message.reply_text(text, parse_mode="Markdown")
    else:
        await update.message.reply_text("⚠️ Gagal fetch Fear & Greed data.")


# --- CHECK ADDRESS COMMAND ---
async def check_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    address = " ".join(context.args) if context.args else None
    if not address:
        await update.message.reply_text(
            "❓ Contoh: /check 0x123...abc\n\n"
            "Atau cek teks/URL untuk scam patterns."
        )
        return

    await update.message.reply_text(f"🔍 Scanning `{address[:20]}...`", parse_mode="Markdown")

    messages = [
        {"role": "system", "content": (
            "Kamu adalah DeFi security analyst. Analisis address/contract/URL. "
            "Kasih output format:\n"
            "🛡️ Risk Score: X/100\n"
            "📊 Status: SAFE/WARNING/DANGER\n"
            "🔍 Findings: (list temuan)\n"
            "💡 Recommendation: (saran)"
        )},
        {"role": "user", "content": f"Cek: {address}"}
    ]
    response = await call_mimo(messages)
    if response:
        await update.message.reply_text(response)
    else:
        await update.message.reply_text("⚠️ AI sedang offline. Coba lagi nanti.")


# --- ANALYZE PROJECT COMMAND ---
async def analyze_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    project = " ".join(context.args) if context.args else None
    if not project:
        await update.message.reply_text("❓ Contoh: /analyze EigenLayer")
        return

    await update.message.reply_text(f"📊 Analyzing *{project}*...", parse_mode="Markdown")

    messages = [
        {"role": "system", "content": (
            "Kamu adalah crypto project analyst. Analisis project dengan format:\n"
            "📋 Overview\n"
            "👥 Team & Backers\n"
            "💰 Funding & Tokenomics\n"
            "🪂 Airdrop Potential (jika ada)\n"
            "⚠️ Risk Factors\n"
            "💡 Verdict & Recommendation"
        )},
        {"role": "user", "content": f"Analisis: {project}"}
    ]
    response = await call_mimo(messages)
    if response:
        await update.message.reply_text(response)
    else:
        await update.message.reply_text("⚠️ AI sedang offline. Coba lagi nanti.")


# --- TOKEN INFO COMMAND ---
async def token_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = " ".join(context.args) if context.args else None
    if not name:
        await update.message.reply_text("❓ Contoh: /token ETH")
        return

    messages = [
        {"role": "system", "content": "Kamu adalah crypto token analyst. Kasih info: use case, tokenomics, harga saat ini (estimasi), prospek, risiko."},
        {"role": "user", "content": f"Info token: {name}"}
    ]
    response = await call_mimo(messages)
    if response:
        await update.message.reply_text(response)
    else:
        await update.message.reply_text("⚠️ AI sedang offline. Coba lagi nanti.")


# --- ASK COMMAND ---
async def ask_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = " ".join(context.args) if context.args else None
    if not query:
        await update.message.reply_text("❓ Contoh: /ask Apa itu liquidity pool?")
        return

    await update.message.reply_text("🤔 Mikir dulu...")
    messages = [
        {"role": "system", "content": "Kamu adalah asisten DeFi yang helpful. Jawab bahasa Indonesia santai, pakai emoji, max 500 kata."},
        {"role": "user", "content": query}
    ]
    response = await call_mimo(messages)
    if response:
        await update.message.reply_text(response)
    else:
        await update.message.reply_text("⚠️ AI sedang offline. Coba lagi nanti.")


# --- AIRDROPS COMMAND ---
async def airdrops_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🪂 Loading airdrop info...")
    messages = [
        {"role": "system", "content": (
            "Kamu adalah airdrop specialist. Kasih info airdrop terbaru yang legit. "
            "Format: Nama project, status (upcoming/active/ended), cara ikut, estimasi reward, tingkat kesulitan. "
            "Sebut 5-7 airdrop yang sedang aktif/upcoming. Kasih warning soal scam."
        )},
        {"role": "user", "content": "Info airdrop crypto terbaru 2025/2026"}
    ]
    response = await call_mimo(messages)
    if response:
        await update.message.reply_text(response)
    else:
        await update.message.reply_text("⚠️ AI sedang offline. Coba lagi nanti.")


# --- DEFI TIPS COMMAND ---
async def defitips_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    messages = [
        {"role": "system", "content": "Kamu adalah DeFi educator. Kasih tips DeFi yang praktis dan actionable. Pakai emoji. Max 300 kata."},
        {"role": "user", "content": "Kasih tips DeFi yang penting untuk pemula sampai intermediate"}
    ]
    response = await call_mimo(messages)
    if response:
        await update.message.reply_text(response)
    else:
        await update.message.reply_text("⚠️ AI sedang offline. Coba lagi nanti.")


# --- SECURITY COMMAND ---
async def security_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🛡️ *DeFi Security Checklist*\n\n"
        "✅ *Sebelum Connect Wallet:*\n"
        "• Cek URL — pastikan bukan phishing\n"
        "• Cek contract address di explorer\n"
        "• Baca review di Twitter/Discord\n"
        "• Cek audit — udah diaudit belum?\n\n"
        "✅ *Sebelum Approve:*\n"
        "• Jangan approve unlimited\n"
        "• Cek fungsi yang di-approve\n"
        "• Pakai Revoke.cash untuk manage approvals\n\n"
        "✅ *General Tips:*\n"
        "• Hardware wallet untuk holdings besar\n"
        "• Jangan share seed phrase/private key\n"
        "• Verify contract di Etherscan\n"
        "• Pakai wallet terpisah buat testing\n"
        "• Cek slippage sebelum swap\n\n"
        "🚨 *Red Flags:*\n"
        "• \"Send ETH to claim airdrop\"\n"
        "• \"Guaranteed 100x profit\"\n"
        "• Minta seed phrase/private key\n"
        "• Website baru tanpa audit\n"
        "• Token gak bisa dijual (honeypot)\n\n"
        "💡 /check <address> buat scan address!"
    )
    await update.message.reply_text(text, parse_mode="Markdown")


# --- PORTFOLIO TIPS COMMAND ---
async def portfolio_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    messages = [
        {"role": "system", "content": "Kamu adalah portfolio advisor. Kasih tips diversifikasi portfolio crypto. Pakai emoji, max 300 kata."},
        {"role": "user", "content": "Kasih tips portfolio crypto yang balanced untuk pemula sampai intermediate"}
    ]
    response = await call_mimo(messages)
    if response:
        await update.message.reply_text(response)
    else:
        await update.message.reply_text("⚠️ AI sedang offline. Coba lagi nanti.")


# --- NEWS COMMAND ---
async def news_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📰 Loading crypto news...")
    messages = [
        {"role": "system", "content": "Kamu adalah crypto news analyst. Kasih ringkasan berita crypto terbaru. Max 5 berita, singkat dan padat."},
        {"role": "user", "content": "Apa berita crypto terbaru hari ini?"}
    ]
    response = await call_mimo(messages)
    if response:
        await update.message.reply_text(response)
    else:
        await update.message.reply_text("⚠️ AI sedang offline. Coba lagi nanti.")


# --- CALLBACK QUERY HANDLER ---
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "market":
        await market_cmd(update, context)
    elif query.data == "prices":
        await query.edit_message_text("💰 Ketik: /price ETH\n\nToken: BTC, ETH, SOL, BNB, XRP, ADA, DOGE, AVAX, DOT, MATIC, LINK, UNI, AAVE, ARB, OP")
    elif query.data == "trending":
        await trending_cmd(update, context)
    elif query.data == "gas":
        await gas_cmd(update, context)
    elif query.data == "scan":
        await query.edit_message_text("🛡️ Ketik: /check <address>\n\nContoh: /check 0x123...abc")
    elif query.data == "airdrops":
        await airdrops_cmd(update, context)
    elif query.data == "help":
        await help_cmd(update, context)


# --- FREE CHAT ---
async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text

    # Quick scam check
    scam = quick_scam_check(user_msg)
    if not scam["safe"]:
        flags = ", ".join(scam["flags"])
        await update.message.reply_text(
            f"🚨 *SCAM ALERT!*\n\n"
            f"Risk: *{scam['risk']}*\n"
            f"Flags: `{flags}`\n\n"
            f"⚠️ Jangan klik link atau kirim apapun!",
            parse_mode="Markdown"
        )
        return

    messages = [
        {"role": "system", "content": (
            "Kamu MiMo Guard Bot, asisten DeFi AI. Jawab bahasa Indonesia santai, "
            "pakai emoji, max 300 kata. Bisa bahas crypto, DeFi, airdrop, security, "
            "trading, NFT, blockchain. Kalau ditanya scam/hack, kasih warning yang jelas."
        )},
        {"role": "user", "content": user_msg}
    ]
    response = await call_mimo(messages)
    if response:
        await update.message.reply_text(response)
    else:
        await update.message.reply_text("🤔 AI lagi istirahat. Pakai /help buat liat command yang tersedia!")


# --- ERROR HANDLER ---
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Error: {context.error}")
    if update and update.message:
        await update.message.reply_text("⚠️ Terjadi error, coba lagi ya!")


# ============================================================
#  Main
# ============================================================

def main():
    logger.info("MiMo Guard Bot starting...")
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("ask", ask_cmd))
    app.add_handler(CommandHandler("price", price_cmd))
    app.add_handler(CommandHandler("market", market_cmd))
    app.add_handler(CommandHandler("trending", trending_cmd))
    app.add_handler(CommandHandler("gas", gas_cmd))
    app.add_handler(CommandHandler("fear", fear_cmd))
    app.add_handler(CommandHandler("check", check_cmd))
    app.add_handler(CommandHandler("analyze", analyze_cmd))
    app.add_handler(CommandHandler("token", token_cmd))
    app.add_handler(CommandHandler("airdrops", airdrops_cmd))
    app.add_handler(CommandHandler("defitips", defitips_cmd))
    app.add_handler(CommandHandler("security", security_cmd))
    app.add_handler(CommandHandler("portfolio", portfolio_cmd))
    app.add_handler(CommandHandler("news", news_cmd))

    # Callbacks
    app.add_handler(CallbackQueryHandler(button_callback))

    # Chat
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))

    # Error
    app.add_error_handler(error_handler)

    logger.info("Bot is running with all features!")
    app.run_polling()


if __name__ == "__main__":
    main()
