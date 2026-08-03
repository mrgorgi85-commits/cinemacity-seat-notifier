# 🎬 Cinema Ticket Monitor ("The Odyssey" IMAX 70mm & Custom Movies)

[![Azure Functions](https://img.shields.io/badge/Azure%20Functions-Python%203.11-0089D6?logo=microsoftazure)](https://azure.microsoft.com/en-us/services/functions/)
[![Runtime](https://img.shields.io/badge/Runtime-Serverless%20%28Consumption%20Y1%29-brightgreen)](https://azure.microsoft.com/en-us/pricing/details/functions/)
[![Telegram Alerting](https://img.shields.io/badge/Telegram-Bot%20API-26A5E4?logo=telegram)](https://core.telegram.org/bots/api)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A lightweight, serverless monitoring system built on **Azure Functions (Python 3.11)** to track ticket availability for cinema releases. Pre-configured to monitor Christopher Nolan's ***The Odyssey*** in **IMAX 70mm** at **Cinema City Flora in Prague (Cinema ID: 1052)**, but **100% customizable for any movie, any cinema, any format (IMAX, 4DX, VIP), and any schedule**.

The system polls Cinema City's backend API on a configurable schedule (default: every 60 seconds). When `availabilityRatio` rises above the baseline threshold (`> 0.016`), it sends an instant mobile push notification via **Telegram** with direct booking links.

---

## ✨ Features


- ⚡ **100% Free Tier Hosting:** Built on Azure Functions Consumption (Y1) plan (up to 1M free monthly executions).
- ⚙️ **Fully Parameterized:** All cinema IDs, movie titles, target dates, showtime rules, and thresholds are configured via `local.settings.json` or Azure App Settings—no code changes required.
- 🕒 **Schedule & Showtime Filtering:** Filter by exact showtimes per date or monitor all showtimes automatically.
- 📱 **Instant Telegram Alerts:** Delivers push notifications directly to your phone via Telegram Bot API with one-click direct ticket booking links.
- 🛡️ **Anti-Bot Protection:** Formats URLs and disables web previews to bypass Cloudflare security blocks.
- 🚀 **Automated Azure CLI Deployment:** One-command infrastructure setup via Bash (`deploy.sh`) or PowerShell (`deploy.ps1`).

---

## 📁 Repository Structure

```
cinemacity-seat-notifier/
├── function_app.py               # Main Azure Function (Timer Trigger & Alert Dispatcher)
├── host.json                     # Azure Functions host configuration (v2)
├── requirements.txt              # Python runtime dependencies
├── local.settings.json           # Environment configuration (git-ignored)
├── local.settings.json.template  # Template for environment variables
├── .gitignore                    # Prevents secrets & build artifacts from being committed
├── scripts/
│   ├── deploy.sh                 # Automated Azure CLI deployment script (Bash)
│   └── deploy.ps1                # Automated Azure CLI deployment script (PowerShell)
└── docs/
    ├── CUSTOMIZATION_GUIDE.md    # Guide to customize for OTHER movies, cinemas, or schedules
    ├── ALERTING_GUIDE.md         # Telegram Bot setup instructions
    └── ARCHITECTURE.md           # System design & API specification
```

---

## 🎯 Pre-Configured Default Target (*The Odyssey* IMAX 70mm)

- **Cinema:** Cinema City Flora, Prague (`CINEMA_ID: 1052`)
- **Format:** IMAX 70mm (`AUDITORIUM_NAME: IMAX`)
- **Target Dates & Monitored Showtimes:**
  - **August 8, 2026 (`2026-08-08`)**: Monitored showtimes: `16:40`, `20:30`
  - **August 9, 2026 (`2026-08-09`)**: Monitored showtimes: `09:00`, `12:50`, `16:40`
- **Threshold Condition:** `availabilityRatio > 0.016`

Want to monitor a different movie or cinema? See [docs/CUSTOMIZATION_GUIDE.md](docs/CUSTOMIZATION_GUIDE.md).

---

## 🚀 Quickstart Guide

### 1. Telegram Bot Setup
1. Create a bot using `@BotFather` on Telegram to get your **Bot Token**.
2. Get your personal **Chat ID** using `@userinfobot`.
3. Follow the detailed setup guide in [docs/ALERTING_GUIDE.md](docs/ALERTING_GUIDE.md).

### 2. Local Setup & Testing
```bash
# Clone repository
git clone https://github.com/<your-username>/odyssea-imax-monitor.git
cd odyssea-imax-monitor

# Setup virtual environment & dependencies
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure environment variables
cp local.settings.json.template local.settings.json
# Edit local.settings.json and set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID
```

### 3. Deploy to Azure (100% Free)

Ensure you have [Azure CLI](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli) installed and logged in:

```bash
az login
```

Provision the Azure infrastructure:
```bash
# Using Bash:
./scripts/deploy.sh

# Or using PowerShell:
./scripts/deploy.ps1
```

Publish your function code to Azure:
```bash
zip -r app.zip function_app.py host.json requirements.txt
az functionapp deployment source config-zip -g rg-imaxon-prague -n <YOUR_FUNCTION_APP_NAME> --src ./app.zip
```

---

## ⚙️ Configuration Parameters

Environment variables configured in `local.settings.json` or Azure Function App Settings:

| Variable Name | Required | Default | Description |
| :--- | :---: | :---: | :--- |
| `MONITOR_SCHEDULE` | No | `0 */1 * * * *` | Azure Functions timer trigger schedule (CRON format). |
| `CINEMA_ID` | No | `1052` | Cinema City location ID (e.g. `1052` = Flora Prague). |
| `MOVIE_NAME` | No | `The Odyssey` | Display title of the movie for notifications. |
| `AUDITORIUM_NAME` | No | `IMAX` | Auditorium filter (`IMAX`, `4DX`, `VIP`, etc.). Set empty for all. |
| `TARGET_DATES` | No | `["2026-08-08", "2026-08-09"]` | Target dates (`YYYY-MM-DD`) as JSON list or CSV string. |
| `ALLOWED_SHOWTIMES` | No | *See default map* | JSON map of allowed showtime start times per date (`"{}"` for all). |
| `MOVIE_PAGE_URL` | No | *Cinema City web link* | Template URL for web page link in alert payload. |
| `RATIO_THRESHOLD` | No | `0.016` | Minimum seat ratio threshold (`> 0.016`). |
| `TELEGRAM_BOT_TOKEN` | **Yes** | - | Telegram Bot HTTP API token from `@BotFather`. |
| `TELEGRAM_CHAT_ID` | **Yes** | - | Target numerical Chat ID from `@userinfobot`. |

For step-by-step instructions on customizing these for other movies or cinemas, refer to [docs/CUSTOMIZATION_GUIDE.md](docs/CUSTOMIZATION_GUIDE.md).

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

