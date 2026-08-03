# Telegram Alerting Setup Guide

This guide provides step-by-step instructions for creating and configuring a **Telegram Bot** to receive instant push notifications from the **IMAX 70mm Ticket Monitor**.

Telegram notifications are **100% free**, instant, and have no daily message limits for personal notifications.

---

## 🤖 Step 1: Create Your Telegram Bot via `@BotFather`

1. Open your Telegram app on phone or desktop.
2. Search for `@BotFather` and click **Start**.
3. Send the command `/newbot`.
4. Follow the prompts:
   - **Name:** Choose a display name for your bot (e.g., `IMAX 70mm Monitor`).
   - **Username:** Choose a unique username ending in `bot` (e.g., `FloraImax70mmBot`).
5. `@BotFather` will reply with your **HTTP API Token** (Format: `1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ`). Save this token securely!

---

## 👤 Step 2: Retrieve Your Personal Telegram `CHAT_ID`

1. Search for `@userinfobot` on Telegram and click **Start**.
2. It will reply immediately with your personal numerical **Id** (e.g., `334236075`).
3. Alternatively, start a chat with your new bot (send it `/start`), then open your web browser to:
   ```http
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates
   ```
   Look for `"chat":{"id": 334236075}` in the JSON output.

---

## 🧪 Step 3: Test Notification Delivery

You can test sending a test alert to your phone right now using `curl` or `PowerShell`:

### Using `curl` (Linux / macOS):
```bash
curl -s -X POST "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/sendMessage" \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "<YOUR_CHAT_ID>",
    "text": "🚨 *IMAX 70mm Ticket Alert!* 🚨\nMovie: *The Odyssey* (Cinema City Flora Prague)\n\n📅 *Date:* 2026-08-08 @ *16:40*\n🎟️ [Direct Booking Link](https://www.cinemacity.cz/cz/booking-router/launch/220731?lang=cs)\n🌐 [Cinema City Web Page](https://www.cinemacity.cz/films/odyssea/7268s2r)\n\n⚡ *Act fast before seats sell out!*",
    "parse_mode": "Markdown",
    "disable_web_page_preview": true
  }' | jq .
```

### Using PowerShell (Windows):
```powershell
$payload = @{
    chat_id = "<YOUR_CHAT_ID>"
    text = "🚨 *IMAX 70mm Ticket Alert!* 🚨`nMovie: *The Odyssey* (Cinema City Flora Prague)`n`n📅 *Date:* 2026-08-08 @ *16:40*`n🎟️ [Direct Booking Link](https://www.cinemacity.cz/cz/booking-router/launch/220731?lang=cs)`n🌐 [Cinema City Web Page](https://www.cinemacity.cz/films/odyssea/7268s2r)`n`n⚡ *Act fast before seats sell out!"
    parse_mode = "Markdown"
    disable_web_page_preview = $true
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/sendMessage" -Method Post -ContentType "application/json" -Body $payload
```

---

## ⚙️ Step 4: Configure App Settings

Set the following environment variables in your Azure Function App Settings or `local.settings.json`:

| Variable Name | Required | Value |
| :--- | :---: | :--- |
| `TELEGRAM_BOT_TOKEN` | **Yes** | Your Telegram Bot Token from `@BotFather` |
| `TELEGRAM_CHAT_ID` | **Yes** | Your numerical Chat ID from `@userinfobot` |

For additional configuration settings (`MOVIE_NAME`, `CINEMA_ID`, `TARGET_DATES`, `ALLOWED_SHOWTIMES`, etc.), see [docs/CUSTOMIZATION_GUIDE.md](CUSTOMIZATION_GUIDE.md).

---

## 💡 Important Note on Cloudflare Link Previews

The notification payload sets `"disable_web_page_preview": true`. This is required to prevent Telegram's background bot servers from pre-fetching booking URLs, which can trigger Cloudflare security blocks (`403 Forbidden` / `Sorry, you have been blocked`).

