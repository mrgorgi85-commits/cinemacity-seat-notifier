import os
import json
import logging
import urllib.request
import urllib.parse
import urllib.error
import azure.functions as func

app = func.FunctionApp()

# Default fallback values for configuration
DEFAULT_CINEMA_ID = "1052"
DEFAULT_MOVIE_NAME = "The Odyssey"
DEFAULT_AUDITORIUM_NAME = "IMAX"
DEFAULT_RATIO_THRESHOLD = 0.016
DEFAULT_MONITOR_SCHEDULE = "0 */1 * * * *"
DEFAULT_MOVIE_PAGE_URL = "https://www.cinemacity.cz/films/odyssea/7268s2r#/buy-tickets-by-cinema?in-cinema={cinema_id}&at-date={date_str}"
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def get_target_dates() -> list[str]:
    """Parses target dates from TARGET_DATES environment variable (JSON list or comma-separated string)."""
    raw = os.environ.get("TARGET_DATES", "").strip()
    if not raw:
        return ["2026-08-08", "2026-08-09"]
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [str(d).strip() for d in parsed]
    except Exception:
        pass
    return [d.strip() for d in raw.split(",") if d.strip()]


def get_allowed_showtimes() -> dict[str, list[str]]:
    """
    Parses allowed showtimes per date from ALLOWED_SHOWTIMES environment variable (JSON object).
    Example: {"2026-08-08": ["16:40", "20:30"]}
    If empty or omitted, returns default filter or empty dict (meaning all showtimes allowed).
    """
    raw = os.environ.get("ALLOWED_SHOWTIMES", "").strip()
    if not raw:
        return {
            "2026-08-08": ["16:40", "20:30"],
            "2026-08-09": ["09:00", "12:50", "16:40"]
        }
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return {k: [str(t).strip() for t in v] for k, v in parsed.items()}
    except Exception as e:
        logging.warning(f"Could not parse ALLOWED_SHOWTIMES JSON: {e}. Allowing all showtimes.")
    return {}


def send_telegram_message(bot_token: str, chat_id: str, message: str) -> bool:
    """Sends notification via Telegram Bot API with link preview disabled to prevent Cloudflare blocks."""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = json.dumps({
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True  # Prevents Telegram bot server from pre-fetching URLs and triggering Cloudflare security blocks
        }).encode('utf-8')

        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                logging.info("Telegram notification sent successfully.")
                return True
            else:
                logging.error(f"Telegram API returned HTTP status {resp.status}")
                return False
    except Exception as e:
        logging.error(f"Failed to send Telegram notification: {e}")
        return False


def dispatch_alerts(alert_text: str):
    """Dispatches alert notification to configured Telegram Bot."""
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if bot_token and chat_id:
        send_telegram_message(bot_token, chat_id, alert_text)
    else:
        logging.warning("Telegram notification skipped: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID environment variables are missing.")


@app.timer_trigger(schedule="%MONITOR_SCHEDULE%", arg_name="myTimer", run_on_startup=False)
def imax_ticket_monitor(myTimer: func.TimerRequest) -> None:
    """Azure Function timer trigger running on configured schedule to monitor ticket availability."""
    cinema_id = os.environ.get("CINEMA_ID", DEFAULT_CINEMA_ID)
    movie_name = os.environ.get("MOVIE_NAME", DEFAULT_MOVIE_NAME)
    auditorium_filter = os.environ.get("AUDITORIUM_NAME", DEFAULT_AUDITORIUM_NAME)
    movie_page_url_template = os.environ.get("MOVIE_PAGE_URL", DEFAULT_MOVIE_PAGE_URL)
    user_agent = os.environ.get("USER_AGENT", DEFAULT_USER_AGENT)

    try:
        threshold_env = os.environ.get("RATIO_THRESHOLD")
        threshold = float(threshold_env) if threshold_env else DEFAULT_RATIO_THRESHOLD
    except ValueError:
        threshold = DEFAULT_RATIO_THRESHOLD

    target_dates = get_target_dates()
    allowed_showtimes_map = get_allowed_showtimes()

    logging.info(f"Starting ticket monitor check for '{movie_name}' at Cinema ID: {cinema_id} (Auditorium: '{auditorium_filter}')...")

    available_events = []

    for date_str in target_dates:
        url = f"https://www.cinemacity.cz/cz/data-api-service/v1/quickbook/10101/film-events/in-cinema/{cinema_id}/at-date/{date_str}?attr=&lang=cs_CZ"
        logging.info(f"Polling Cinema City API for date: {date_str}...")

        try:
            req = urllib.request.Request(url, headers={"User-Agent": user_agent, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status != 200:
                    logging.warning(f"Cinema City API returned non-200 status {resp.status} for date {date_str}")
                    continue

                raw_data = resp.read().decode('utf-8')
                data = json.loads(raw_data)

            events = data.get("body", {}).get("events", [])
            logging.info(f"Retrieved {len(events)} total events for {date_str}.")

            allowed_times = allowed_showtimes_map.get(date_str, [])

            for ev in events:
                auditorium = ev.get("auditoriumTinyName", "")
                if auditorium_filter and auditorium != auditorium_filter:
                    continue

                event_dt = ev.get("eventDateTime", "")  # Format e.g., "2026-08-08T16:40:00"
                time_part = event_dt.split("T")[-1][:5] if "T" in event_dt else ""

                # If allowed_times filter is defined for this date, enforce it
                if allowed_times and not any(time_part.startswith(t) for t in allowed_times):
                    logging.debug(f"Skipping showtime {event_dt} on {date_str} (not in allowed list {allowed_times})")
                    continue

                availability_ratio = ev.get("availabilityRatio", 0.0)
                logging.info(f"Matching Showtime ({auditorium}): {event_dt} | Availability Ratio: {availability_ratio:.4f} (Threshold: {threshold:.4f})")

                if availability_ratio > threshold:
                    launch_link = ev.get("bookingRouterLaunchLink") or ev.get("bookingLink") or f"https://tickets.cinemacity.cz/api/order/{ev.get('id')}"
                    movie_page_link = movie_page_url_template.format(cinema_id=cinema_id, date_str=date_str)
                    available_events.append({
                        "date": date_str,
                        "time": time_part,
                        "datetime": event_dt,
                        "launch_link": launch_link,
                        "movie_page_link": movie_page_link,
                        "auditorium": auditorium
                    })

        except urllib.error.URLError as e:
            logging.error(f"HTTP network error while polling date {date_str}: {e}")
        except Exception as e:
            logging.error(f"Unexpected error while processing date {date_str}: {e}")

    if available_events:
        logging.info(f"🚨 TICKET ALERT TRIGGERED! Found {len(available_events)} available showtime(s) exceeding threshold {threshold}.")

        msg_lines = [
            f"🚨 *{auditorium_filter or 'Cinema'} Ticket Alert!* 🚨",
            f"Movie: *{movie_name}*",
            ""
        ]

        for ev in available_events:
            msg_lines.append(f"📅 *Date:* {ev['date']} @ *{ev['time']}* ({ev['auditorium']})")
            msg_lines.append(f"🎟️ [Direct Booking Link]({ev['launch_link']})")
            msg_lines.append(f"🌐 [Cinema City Web Page]({ev['movie_page_link']})")
            msg_lines.append("")

        msg_lines.append("⚡ *Act fast before seats sell out!*")
        alert_message = "\n".join(msg_lines)

        dispatch_alerts(alert_message)
    else:
        logging.info(f"Check complete. No available tickets above threshold {threshold}.")

