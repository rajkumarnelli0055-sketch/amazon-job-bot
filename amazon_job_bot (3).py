import requests
import time
import os
from datetime import datetime

# ============================================================
#   YOUR SETTINGS
# ============================================================
BOT_TOKEN = "8931086903:AAFCrTw9sCCzg6IP_fXHMB-fncsGyiCBp20"
CHAT_ID   = "7387110484"
# ============================================================

# Search settings
SEARCH_LOCATION = "Middlesbrough, UK"
SEARCH_RADIUS_MILES = 100
CHECK_INTERVAL_SECONDS = 30

# Amazon Jobs API — Fulfilment Centre jobs only
AMAZON_API_URL = (
    "https://www.amazon.jobs/en-gb/search.json"
    "?base_query=fulfilment+centre&loc_query=Middlesbrough%2C+UK"
    "&radius=100mi"
    "&job_type=Full-Time,Part-Time,Seasonal,Temporary"
    "&category[]=fulfillment-and-operations"
    "&offset=0&result_limit=50&sort=recent"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "en-GB,en;q=0.9",
    "Referer": "https://www.amazon.jobs/en-gb/",
}

# Track jobs we've already seen
seen_job_ids = set()


def send_telegram(message: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    try:
        resp = requests.post(url, data=payload, timeout=10)
        if not resp.ok:
            print(f"[Telegram error] {resp.status_code}: {resp.text}")
    except Exception as e:
        print(f"[Telegram send failed] {e}")


def fetch_jobs():
    try:
        resp = requests.get(AMAZON_API_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        return data.get("jobs", [])
    except Exception as e:
        print(f"[Fetch error] {e}")
        return []


def format_job_message(job: dict) -> str:
    title       = job.get("title", "Unknown Title")
    location    = job.get("location", "Unknown Location")
    job_id      = job.get("job_id", "")
    posted_date = job.get("posted_date", "")
    job_type    = job.get("job_type", "")
    url         = f"https://www.amazon.jobs/en-gb/jobs/{job_id}"

    distance_str = ""
    if job.get("distance_from_search"):
        try:
            dist = float(job["distance_from_search"])
            distance_str = f"\n📍 <b>Distance:</b> {dist:.1f} miles"
        except Exception:
            pass

    message = (
        f"🚨 <b>NEW AMAZON FULFILMENT JOB!</b>\n"
        f"{'─' * 30}\n"
        f"💼 <b>{title}</b>\n"
        f"📌 <b>Location:</b> {location}"
        f"{distance_str}\n"
        f"⏰ <b>Posted:</b> {posted_date}\n"
        f"📋 <b>Type:</b> {job_type}\n"
        f"🔗 <a href='{url}'>Apply Now</a>"
    )
    return message


def check_for_new_jobs():
    global seen_job_ids
    jobs = fetch_jobs()

    if not jobs:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] No jobs returned or fetch failed.")
        return

    new_jobs = [j for j in jobs if j.get("job_id") not in seen_job_ids]

    if new_jobs:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ {len(new_jobs)} new job(s) found!")
        for job in new_jobs:
            job_id = job.get("job_id")
            if job_id:
                seen_job_ids.add(job_id)
            message = format_job_message(job)
            send_telegram(message)
            time.sleep(1)
    else:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] No new jobs. ({len(jobs)} total checked)")


def startup_message():
    msg = (
        "✅ <b>Amazon Fulfilment Centre Job Alert Started!</b>\n"
        f"📍 Searching near: <b>{SEARCH_LOCATION}</b>\n"
        f"📏 Radius: <b>{SEARCH_RADIUS_MILES} miles</b>\n"
        f"🔄 Checking every <b>{CHECK_INTERVAL_SECONDS} seconds</b>\n\n"
        "I'll notify you the moment new fulfilment centre jobs appear! 🚀"
    )
    send_telegram(msg)


def main():
    print("=" * 50)
    print("  Amazon Fulfilment Centre Job Alert Bot")
    print(f"  Location: {SEARCH_LOCATION}")
    print(f"  Radius:   {SEARCH_RADIUS_MILES} miles")
    print(f"  Interval: every {CHECK_INTERVAL_SECONDS} seconds")
    print("=" * 50)

    startup_message()

    print("\n[Startup] Loading existing jobs (won't notify for these)...")
    existing = fetch_jobs()
    for job in existing:
        jid = job.get("job_id")
        if jid:
            seen_job_ids.add(jid)
    print(f"[Startup] {len(seen_job_ids)} existing jobs loaded. Now watching for NEW ones...\n")

    while True:
        try:
            check_for_new_jobs()
        except KeyboardInterrupt:
            print("\nBot stopped by user.")
            break
        except Exception as e:
            print(f"[Unexpected error] {e}")

        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
