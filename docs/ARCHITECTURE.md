# Architecture & System Design

This document details the internal design, data flow, and filtering logic for the **Cinema Ticket Monitor**.

---

## 🏗️ Architecture Overview

The system is built on **Azure Functions (Python 3.11, v2 Programming Model)** and deployed to an **Azure Linux Consumption (Y1) Plan** for 100% free tier coverage (up to 1,000,000 monthly executions).

```
 ┌──────────────────────────────────┐
 │  Azure Function Timer Trigger    │
 │ (Schedule via MONITOR_SCHEDULE)  │
 └─────────────────┬────────────────┘
                   │
                   ▼
 ┌──────────────────────────────────┐
 │  Cinema City Quickbook API       │
 │ (JSON Endpoint via CINEMA_ID)    │
 └─────────────────┬────────────────┘
                   │
                   ▼
 ┌──────────────────────────────────┐
 │  Showtime & Auditorium Filtering │
 │ (AUDITORIUM_NAME, ALLOWED_TIMES) │
 └─────────────────┬────────────────┘
                   │
                   ▼
 ┌──────────────────────────────────┐
 │ Availability Ratio > Threshold? │
 └───────┬──────────────────┬───────┘
         │ Yes              │ No
         ▼                  ▼
┌──────────────────┐  ┌───────────┐
│ Send Push Alert  │  │ Log & End │
│  (Telegram API)  │  └───────────┘
└──────────────────┘
```

---

## ⚙️ Dynamic Configuration Architecture

All runtime parameters are fetched dynamically from `os.environ` on each function invocation:

1. **`CINEMA_ID`**: Controls target cinema endpoint (`/film-events/in-cinema/{CINEMA_ID}`).
2. **`TARGET_DATES`**: Parsed via `get_target_dates()` helper (supports JSON lists or CSV strings).
3. **`ALLOWED_SHOWTIMES`**: Parsed via `get_allowed_showtimes()` helper (JSON dictionary). If empty, allows all showtimes on the target dates.
4. **`AUDITORIUM_NAME`**: Filters events matching auditorium format (e.g. `IMAX`, `4DX`, `VIP`).
5. **`RATIO_THRESHOLD`**: Float threshold determining when ticket availability triggers an alert.

---

## 🎯 Showtime Filter Specifications (Default Profile)

By default, the system monitors ticket availability for Christopher Nolan's *The Odyssey* at **Cinema City Flora in Prague (Cinema ID: 1052)**.

### Target Dates & Schedule Rules
| Date | Monitored Showtimes | Excluded Showtimes | Reason |
| :--- | :--- | :--- | :--- |
| **August 8, 2026** (`2026-08-08`) | `16:40`, `20:30` | `09:00`, `12:50` | User unavailable during morning/midday showtimes |
| **August 9, 2026** (`2026-08-09`) | `09:00`, `12:50`, `16:40` | `20:30` | User unavailable during evening showtime |

---

## 📊 Availability Ratio Threshold Logic & The "Wheelchair Trap"

### Problem Statement & API Behavior
This system was designed for users traveling to Prague specifically for **IMAX 70mm** screenings of *The Odyssey* at Cinema City Flora. Because film enthusiasts travel from all across Europe for 70mm screenings, tickets sell out almost instantly upon release.

When querying Cinema City's Quickbook API endpoint, a naive boolean check on `"soldOut"` fails:
- Cinema City reserves wheelchair-accessible seats for disabled patrons.
- Even when **100% of regular seats are sold out**, the API continues to report `"soldOut": false` because wheelchair spots remain unbooked.
- Simple monitors checking `soldOut: false` generate constant false-positive alerts.

### Solution: `availabilityRatio` Filtering
To solve this, the monitor tracks the numerical `availabilityRatio` property:

$$\text{availabilityRatio} = \frac{\text{Seats Available}}{\text{Total Auditorium Capacity}}$$

- **Baseline Ratio (`~0.0104 - 0.0156`):** Indicates only baseline reserved spots (wheelchair accessible spaces) remain available. Regular public seats are **100% sold out**.
- **Trigger Threshold (`> 0.016`):** Indicates regular seat tiers have officially opened for public booking or seats have been released/canceled.


---

## 🔒 Security & Cloudflare Anti-Bot Handling

1. **User-Agent Impersonation:** Requests sent to Cinema City's endpoint carry a standard browser `User-Agent` header (`Mozilla/5.0...`).
2. **Disabled Link Previews (`disable_web_page_preview: True`):** Prevents Telegram's server from pre-fetching booking launch URLs (`/booking-router/launch/`), avoiding Cloudflare bot detection blocks.

