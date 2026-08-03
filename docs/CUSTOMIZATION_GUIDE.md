# 🛠️ Customization & Reusability Guide

This guide explains how to configure and reuse the **Cinema Ticket Monitor** for **any movie**, **any Cinema City cinema**, **any auditorium format** (IMAX, 4DX, Standard, VIP), or **any custom showtime schedule**.

---

## 📋 Table of Contents
1. [Overview](#overview)
2. [Finding Cinema IDs & Film Endpoints](#1-finding-cinema-ids--film-endpoints)
3. [Configuration Schema & `local.settings.json`](#2-configuration-schema--localsettingsjson)
4. [Customizing Target Dates & Showtime Filters](#3-customizing-target-dates--showtime-filters)
5. [Understanding `RATIO_THRESHOLD`](#4-understanding-ratio_threshold)
6. [Deploying Custom Settings to Azure](#5-deploying-custom-settings-to-azure)

---

## Overview

All system rules are externalized into environment variables. You do **not** need to modify Python code to monitor a different movie or cinema—simply update `local.settings.json` (for local running) or Azure App Settings (for cloud deployment).

---

## 1. Finding Cinema IDs & Film Endpoints

Cinema City uses a standardized Quickbook API:
```http
https://www.cinemacity.cz/cz/data-api-service/v1/quickbook/10101/film-events/in-cinema/{CINEMA_ID}/at-date/{YYYY-MM-DD}?attr=&lang=cs_CZ
```

### Common Cinema IDs (Czech Republic):
| Cinema Location | Cinema ID |
| :--- | :---: |
| **Cinema City Flora (Prague - IMAX 70mm)** | `1052` |
| Cinema City Letňany (Prague) | `1056` |
| Cinema City Westfield Chodov (Prague) | `1057` |
| Cinema City Nový Smíchov (Prague) | `1053` |
| Cinema City Olympia (Brno) | `1055` |
| Cinema City Velký Špalíček (Brno) | `1054` |
| Cinema City Forum (Ústí nad Labem) | `1058` |
| Cinema City Pardubice | `1059` |
| Cinema City Plzeň Plaza | `1060` |

> 💡 **Tip:** To find the Cinema ID for any cinema:
> 1. Open [cinemacity.cz](https://www.cinemacity.cz) in your browser.
> 2. Open Developer Tools (`F12`) -> **Network** tab -> filter by `film-events`.
> 3. Select your cinema and date, then copy the 4-digit ID from the URL path.

---

## 2. Configuration Schema & `local.settings.json`

Create or edit `local.settings.json` in the root folder:

```json
{
  "IsEncrypted": false,
  "Values": {
    "AzureWebJobsStorage": "UseDevelopmentStorage=true",
    "FUNCTIONS_WORKER_RUNTIME": "python",
    "MONITOR_SCHEDULE": "0 */1 * * * *",
    "CINEMA_ID": "1052",
    "MOVIE_NAME": "The Odyssey",
    "AUDITORIUM_NAME": "IMAX",
    "TARGET_DATES": "[\"2026-08-08\", \"2026-08-09\"]",
    "ALLOWED_SHOWTIMES": "{\"2026-08-08\": [\"16:40\", \"20:30\"], \"2026-08-09\": [\"09:00\", \"12:50\", \"16:40\"]}",
    "MOVIE_PAGE_URL": "https://www.cinemacity.cz/films/odyssea/7268s2r#/buy-tickets-by-cinema?in-cinema={cinema_id}&at-date={date_str}",
    "RATIO_THRESHOLD": "0.016",
    "TELEGRAM_BOT_TOKEN": "YOUR_TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID": "YOUR_TELEGRAM_CHAT_ID"
  }
}
```

### Environment Variable Reference

| Setting | Type | Required | Default Value | Description |
| :--- | :---: | :---: | :--- | :--- |
| `MONITOR_SCHEDULE` | Cron | No | `0 */1 * * * *` | Azure Functions timer schedule (CRON syntax). Defaults to every 60s. |
| `CINEMA_ID` | String | No | `1052` | Cinema City location ID. |
| `MOVIE_NAME` | String | No | `The Odyssey` | Display name of the movie for notifications. |
| `AUDITORIUM_NAME` | String | No | `IMAX` | Filter for `auditoriumTinyName` (e.g. `IMAX`, `4DX`, `VIP`, `Sál 1`). Set to `""` to allow all auditoriums. |
| `TARGET_DATES` | JSON Array / String | No | `["2026-08-08", "2026-08-09"]` | List of target dates in `YYYY-MM-DD` format. Can be JSON array or comma-separated string (`"2026-08-08,2026-08-09"`). |
| `ALLOWED_SHOWTIMES` | JSON Object | No | *See below* | Showtime start filter map. If empty (`"{}"`), **all** showtimes on the target dates will be monitored. |
| `MOVIE_PAGE_URL` | String | No | *Cinema City Odyssey URL* | Web page template link. Supports `{cinema_id}` and `{date_str}` placeholders. |
| `RATIO_THRESHOLD` | Float | No | `0.016` | Minimum seat ratio threshold to trigger notification. |
| `TELEGRAM_BOT_TOKEN` | String | **Yes** | - | Telegram Bot token from `@BotFather`. |
| `TELEGRAM_CHAT_ID` | String | **Yes** | - | Your Telegram chat ID from `@userinfobot`. |

---

## 3. Customizing Target Dates & Showtime Filters

### Option A: Specific Showtime Filtering (Recommended for narrow availability)
If you only want alerts for specific showtime slots on specific days (e.g. evening shows only):

```json
"ALLOWED_SHOWTIMES": "{\"2026-08-08\": [\"16:40\", \"20:30\"], \"2026-08-09\": [\"09:00\", \"12:50\"]}"
```

### Option B: Monitor ALL Showtimes on Target Dates
If you want alerts whenever **any** showtime on the target dates opens up, leave `ALLOWED_SHOWTIMES` empty:

```json
"ALLOWED_SHOWTIMES": "{}"
```

---

## 4. Understanding & Recalculating `RATIO_THRESHOLD`

The Cinema City API reports seat availability as an `availabilityRatio`:

$$\text{availabilityRatio} = \frac{\text{Available Seats}}{\text{Total Auditorium Capacity}}$$

### ⚠️ Why `RATIO_THRESHOLD` must be adjusted for different rooms:

Cinema City API reports `"soldOut": false` as long as **wheelchair-accessible seats** remain reserved for disabled patrons. In high-demand movies (like *The Odyssey* IMAX 70mm), regular seats sell out completely while wheelchair seats remain vacant, producing a non-zero baseline ratio.

Because different cinema auditoriums have different seating capacities ($N$) and different numbers of reserved wheelchair spots ($W$), **you must recalculate `RATIO_THRESHOLD` when switching cinemas or room types**:

$$\text{Baseline Ratio} = \frac{\text{Wheelchair Seats } (W)}{\text{Total Auditorium Capacity } (N)}$$

#### Examples:
1. **Cinema City Flora IMAX (Room 1, $N \approx 384$ seats, $W \approx 4\text{--}6$ wheelchair seats):**
   - $\text{Baseline Ratio} \approx \frac{6}{384} \approx 0.0156$
   - **Set `RATIO_THRESHOLD = 0.016`** (triggers only when regular public seats open above $0.0156$).

2. **Smaller Auditorium (e.g. $N = 150$ seats, $W = 2$ wheelchair seats):**
   - $\text{Baseline Ratio} = \frac{2}{150} \approx 0.0133$
   - **Set `RATIO_THRESHOLD = 0.014`**.

3. **Standard Cinema / No Wheelchair Baseline (or monitoring any single seat release):**
   - **Set `RATIO_THRESHOLD = 0.001`**.

> 💡 **Quick Tip to find your room's baseline:**  
> Run a manual `curl` query on a completely sold-out showtime in your target cinema and look at the returned `"availabilityRatio"`. Set your `RATIO_THRESHOLD` slightly higher than that baseline value!

---


## 5. Deploying Custom Settings to Azure

When deploying to Azure Functions, update your App Settings via **Azure CLI**:

```bash
az functionapp config appsettings set \
    --name <YOUR_FUNCTION_APP_NAME> \
    --resource-group rg-imaxon-prague \
    --settings \
        "MOVIE_NAME=Avatar 3" \
        "CINEMA_ID=1052" \
        "AUDITORIUM_NAME=IMAX" \
        "TARGET_DATES=[\"2026-12-18\", \"2026-12-19\"]" \
        "ALLOWED_SHOWTIMES={}" \
        "RATIO_THRESHOLD=0.016" \
        "TELEGRAM_BOT_TOKEN=<YOUR_TOKEN>" \
        "TELEGRAM_CHAT_ID=<YOUR_CHAT_ID>"
```

Or edit settings directly in the [Azure Portal](https://portal.azure.com) under **Function App -> Settings -> Environment variables**.
