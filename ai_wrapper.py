"""
MiMoGuard — Multi-Provider AI Wrapper
Auto-fallback: MiMo → OpenRouter → DeepSeek → Groq

Usage:
    from ai_wrapper import call_ai
    
    response = await call_ai("Analyze this DeFi protocol...")
"""

import os
import httpx
import asyncio
from typing import Optional

# Provider configs — using env vars that match user's .env
PROVIDERS = {
    "mimo": {
        "url": os.getenv("XIAOMI_BASE_URL", "https://api.xiaomimimo.com/v1/chat/completions"),
        "keys": [os.getenv("XIAOMI_API_KEY", "")],
        "model": "mimo-v2.5-pro",
        "timeout": 60,
    },
    "openrouter": {
        "url": "https://openrouter.ai/api/v1/chat/completions",
        "keys": [os.getenv("OPENROUTER_API_KEY", "")],
        "model": "deepseek/deepseek-chat-v3-0324:free",
        "timeout": 30,
    },
    "deepseek": {
        "url": "https://api.deepseek.com/v1/chat/completions",
        "keys": [os.getenv("DEEPSEEK_API_KEY", "")],
        "model": "deepseek-chat",
        "timeout": 30,
    },
    "groq": {
        "url": "https://api.groq.com/openai/v1/chat/completions",
        "keys": [os.getenv("GROQ_API_KEY", "")],
        "model": "llama-3.1-70b-versatile",
        "timeout": 15,
    },
}

# Fallback order
FALLBACK_ORDER = ["mimo", "openrouter", "deepseek", "groq"]

# Round-robin counter for MiMo keys
_mimo_key_index = 0

# System prompt for DeFi agent
DEFI_SYSTEM = """You are MiMoGuard AI — a DeFi security and intelligence assistant.

Your capabilities:
- Analyze DeFi protocols for rugpull/scam risks
- Check smart contract addresses for security issues
- Provide airdrop analysis and legitimacy checks
- Explain DeFi concepts in simple terms
- Track market trends and token analysis

Rules:
- Be direct and concise
- Use bullet points over paragraphs
- Always warn about risks in DeFi
- Never give financial advice — provide analysis only
- Respond in the user's language (Indonesian or English)
- If unsure, say so — never hallucinate contract addresses or token data"""


async def _call_provider(
    provider_name: str,
    message: str,
    system: str = DEFI_SYSTEM,
    history: list = None,
) -> Optional[str]:
    """Call a single provider. Returns None on failure."""
    config = PROVIDERS.get(provider_name)
    if not config:
        return None

    global _mimo_key_index
    keys = [k for k in config["keys"] if k]
    if not keys:
        return None

    # Round-robin for MiMo
    if provider_name == "mimo" and len(keys) > 1:
        key = keys[_mimo_key_index % len(keys)]
        _mimo_key_index += 1
    else:
        key = keys[0]

    # Build messages
    messages = [{"role": "system", "content": system}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": message})

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
    }

    # OpenRouter needs extra headers
    if provider_name == "openrouter":
        headers["X-Title"] = "MiMoGuard"
        headers["HTTP-Referer"] = "https://mimoguard.com"

    payload = {
        "model": config["model"],
        "messages": messages,
        "max_tokens": 1000,
        "temperature": 0.7,
    }

    try:
        async with httpx.AsyncClient(timeout=config["timeout"]) as client:
            resp = await client.post(
                config["url"],
                json=payload,
                headers=headers,
            )
            if resp.status_code == 401:
                return None
            if resp.status_code == 429:
                return None
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except Exception:
        return None


async def call_ai(
    message: str,
    system: str = DEFI_SYSTEM,
    history: list = None,
    provider: str = None,
    max_retries: int = 1,
) -> str:
    """
    Call AI with auto-fallback.
    """
    providers_to_try = [provider] if provider else FALLBACK_ORDER
    
    for prov in providers_to_try:
        for attempt in range(max_retries):
            result = await _call_provider(prov, message, system, history)
            if result:
                return result
            if attempt < max_retries - 1:
                await asyncio.sleep(1)
    
    return (
        "⚠️ AI sedang offline. Semua provider tidak tersedia.\n\n"
        "Coba lagi dalam beberapa menit, atau gunakan command:\n"
        "• `/check <address>` — scan manual\n"
        "• `/price <token>` — cek harga\n"
        "• `/market` — market overview"
    )


async def check_providers() -> dict:
    """Check which providers are available."""
    status = {}
    for name, config in PROVIDERS.items():
        keys = [k for k in config["keys"] if k]
        if not keys:
            status[name] = {"status": "❌ No API key", "model": config["model"]}
            continue
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    config["url"],
                    json={
                        "model": config["model"],
                        "messages": [{"role": "user", "content": "hi"}],
                        "max_tokens": 5,
                    },
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {keys[0]}",
                    },
                )
                if resp.status_code == 200:
                    status[name] = {"status": "✅ Online", "model": config["model"]}
                elif resp.status_code == 401:
                    status[name] = {"status": "🔑 Key invalid", "model": config["model"]}
                else:
                    status[name] = {"status": f"⚠️ {resp.status_code}", "model": config["model"]}
        except Exception as e:
            status[name] = {"status": f"❌ {str(e)[:40]}", "model": config["model"]}
    return status


# Sync wrapper for non-async contexts
def call_ai_sync(message: str, **kwargs) -> str:
    """Sync wrapper — use in Telegram bot handlers."""
    return asyncio.run(call_ai(message, **kwargs))


if __name__ == "__main__":
    async def main():
        print("🔍 Checking providers...")
        status = await check_providers()
        for name, info in status.items():
            print(f"  {name}: {info['status']} ({info['model']})")
        
        print("\n💬 Testing AI...")
        response = await call_ai("What is Uniswap in one sentence?")
        print(f"  Response: {response[:100]}...")
    
    asyncio.run(main())
