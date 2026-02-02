"""
alert_webhooks.py

sends alerts to Discord/Telegram when high-value intel is extracted.
FREE - uses webhook URLs (no paid APIs).

alerts:
- new scam session started
- high-value intel extracted (bank accounts, UPIs)
- repeat scammer detected
- session summary when completed
"""

import requests
from typing import Optional, Dict, List
from datetime import datetime
import json


# webhook URLs (set these in .env or directly here)
DISCORD_WEBHOOK_URL = ""  # paste your discord webhook URL
TELEGRAM_BOT_TOKEN = ""   # your telegram bot token
TELEGRAM_CHAT_ID = ""     # your telegram chat/group ID


def send_discord_alert(
    title: str,
    description: str,
    color: int = 0xFF5733,  # orange-red
    fields: List[Dict] = None,
    webhook_url: str = None
) -> bool:
    """
    send alert to Discord via webhook.
    
    FREE - just create a webhook in Discord channel settings.
    """
    url = webhook_url or DISCORD_WEBHOOK_URL
    
    if not url:
        print("[ALERT] Discord webhook not configured")
        return False
    
    try:
        embed = {
            "title": title,
            "description": description,
            "color": color,
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {"text": "Honeypot Alert System"}
        }
        
        if fields:
            embed["fields"] = fields
        
        payload = {
            "embeds": [embed]
        }
        
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=5
        )
        
        return response.status_code in [200, 204]
        
    except Exception as e:
        print(f"[ALERT] Discord error: {e}")
        return False


def send_telegram_alert(
    message: str,
    bot_token: str = None,
    chat_id: str = None,
    parse_mode: str = "HTML"
) -> bool:
    """
    send alert to Telegram via bot API.
    
    FREE - create a bot via @BotFather on Telegram.
    """
    token = bot_token or TELEGRAM_BOT_TOKEN
    chat = chat_id or TELEGRAM_CHAT_ID
    
    if not token or not chat:
        print("[ALERT] Telegram not configured")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        
        payload = {
            "chat_id": chat,
            "text": message,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True
        }
        
        response = requests.post(url, json=payload, timeout=5)
        return response.status_code == 200
        
    except Exception as e:
        print(f"[ALERT] Telegram error: {e}")
        return False


def alert_new_session(session_id: str, initial_message: str, scam_type: str = None):
    """alert when new scam session starts"""
    
    title = "🎣 New Scam Session Detected!"
    description = f"Session `{session_id}` started"
    
    fields = [
        {"name": "First Message", "value": initial_message[:200], "inline": False},
    ]
    if scam_type:
        fields.append({"name": "Scam Type", "value": scam_type, "inline": True})
    
    # Discord
    send_discord_alert(title, description, color=0xFFA500, fields=fields)
    
    # Telegram
    telegram_msg = f"""
🎣 <b>New Scam Session</b>

<b>Session:</b> <code>{session_id}</code>
<b>Type:</b> {scam_type or 'Unknown'}
<b>Message:</b> {initial_message[:200]}
"""
    send_telegram_alert(telegram_msg)


def alert_intel_extracted(session_id: str, intel: Dict):
    """alert when high-value intel is extracted"""
    
    # only alert if we got good intel
    phones = intel.get("phoneNumbers", [])
    upis = intel.get("upiIds", [])
    accounts = intel.get("bankAccounts", [])
    
    if not (phones or upis or accounts):
        return
    
    title = "🔍 Intel Extracted!"
    description = f"Session `{session_id}` yielded valuable intel"
    
    fields = []
    if phones:
        fields.append({"name": "📱 Phone Numbers", "value": ", ".join(phones[:5]), "inline": False})
    if upis:
        fields.append({"name": "💳 UPI IDs", "value": ", ".join(upis[:5]), "inline": False})
    if accounts:
        fields.append({"name": "🏦 Bank Accounts", "value": ", ".join(accounts[:3]), "inline": False})
    
    send_discord_alert(title, description, color=0x00FF00, fields=fields)
    
    # Telegram
    telegram_msg = f"""
🔍 <b>Intel Extracted</b>

<b>Session:</b> <code>{session_id}</code>
"""
    if phones:
        telegram_msg += f"📱 <b>Phones:</b> {', '.join(phones[:5])}\n"
    if upis:
        telegram_msg += f"💳 <b>UPIs:</b> {', '.join(upis[:5])}\n"
    if accounts:
        telegram_msg += f"🏦 <b>Accounts:</b> {', '.join(accounts[:3])}\n"
    
    send_telegram_alert(telegram_msg)


def alert_repeat_scammer(session_id: str, fingerprint: Dict):
    """alert when repeat scammer is detected"""
    
    title = "⚠️ Repeat Scammer Detected!"
    description = f"Known scammer in session `{session_id}`"
    
    fields = [
        {"name": "Fingerprint ID", "value": fingerprint.get("fingerprint_id", "?"), "inline": True},
        {"name": "Previous Sessions", "value": str(fingerprint.get("session_count", 0)), "inline": True},
        {"name": "First Seen", "value": fingerprint.get("first_seen", "?")[:10], "inline": True},
    ]
    
    send_discord_alert(title, description, color=0xFF0000, fields=fields)
    
    # Telegram
    telegram_msg = f"""
⚠️ <b>REPEAT SCAMMER</b>

<b>Session:</b> <code>{session_id}</code>
<b>Fingerprint:</b> <code>{fingerprint.get("fingerprint_id", "?")}</code>
<b>Previous Sessions:</b> {fingerprint.get("session_count", 0)}
<b>Scam Types:</b> {', '.join(fingerprint.get("patterns", {}).get("scam_types", []))}
"""
    send_telegram_alert(telegram_msg)


def alert_session_complete(session_id: str, metrics: Dict, intel: Dict):
    """alert with session summary when completed"""
    
    engagement = metrics.get("engagement", {})
    messages = metrics.get("messages", {})
    
    title = "✅ Session Complete"
    description = f"Session `{session_id}` ended"
    
    fields = [
        {"name": "⏱️ Duration", "value": engagement.get("duration", "?"), "inline": True},
        {"name": "💬 Messages", "value": str(messages.get("total", 0)), "inline": True},
        {"name": "🔍 Intel Items", "value": str(len(intel.get("phoneNumbers", [])) + len(intel.get("upiIds", []))), "inline": True},
    ]
    
    send_discord_alert(title, description, color=0x00BFFF, fields=fields)
    
    # Telegram
    telegram_msg = f"""
✅ <b>Session Complete</b>

<b>Session:</b> <code>{session_id}</code>
⏱️ <b>Duration:</b> {engagement.get("duration", "?")}
💬 <b>Messages:</b> {messages.get("total", 0)}
🔍 <b>Intel:</b> {len(intel.get("phoneNumbers", []))} phones, {len(intel.get("upiIds", []))} UPIs
"""
    send_telegram_alert(telegram_msg)


def test_alerts():
    """test alert functions"""
    print("Testing alert system...")
    
    # test data
    test_session = "test-session-123"
    test_intel = {
        "phoneNumbers": ["+919876543210"],
        "upiIds": ["scammer@ybl"],
    }
    
    print("\nTesting Discord...")
    result = send_discord_alert(
        "🧪 Test Alert",
        "This is a test from the honeypot system",
        fields=[{"name": "Status", "value": "Testing", "inline": True}]
    )
    print(f"Discord: {'Success' if result else 'Failed (webhook not configured?)'}")
    
    print("\nTesting Telegram...")
    result = send_telegram_alert("🧪 <b>Test Alert</b>\n\nThis is a test from the honeypot system")
    print(f"Telegram: {'Success' if result else 'Failed (bot not configured?)'}")


if __name__ == "__main__":
    test_alerts()
