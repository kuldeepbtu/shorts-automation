"""
auto_scheduler.py
==================
ShortsBot — AWS Daily Automation Daemon

Runs forever on your Ubuntu EC2. Triggers the full AI pipeline on schedule:
  • 4 long videos/week (Mon/Wed/Fri/Sun) at low-traffic hours (2:30 AM UTC)
  • 1 Short every day  (from auto-clip OR standalone)
  • 3 standalone Shorts/week (Tue/Thu/Sat at 3:00 AM UTC)

Usage:
  python auto_scheduler.py              # normal daemon mode
  python auto_scheduler.py --test-once  # run ONE full pipeline right now (for testing)
  python auto_scheduler.py --shorts-now # run a short right now (for testing)

No extra pip packages needed — uses only stdlib time.sleep() scheduling.
"""

import os
import sys
import json
import time
import logging
import argparse
import traceback
import shutil
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ── Ensure we can import from ShortsBot root ──────────────────────────────────
BASE_DIR = Path(__file__).parent.resolve()
sys.path.insert(0, str(BASE_DIR))

try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_FILE = BASE_DIR / "scheduler.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("ShortsBot.Scheduler")

# ── History ───────────────────────────────────────────────────────────────────
HISTORY_FILE = BASE_DIR / "run_history.json"
CONFIG_FILE  = BASE_DIR / "project_config.json"


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            log.error(f"[Config] Cannot read project_config.json: {e}")
    return {}


def _load_history() -> list:
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


def _save_history(history: list):
    HISTORY_FILE.write_text(json.dumps(history, indent=2, default=str), encoding="utf-8")


def _record_run(run_type: str, status: str, detail: str = "", video_title: str = ""):
    history = _load_history()
    history.append({
        "date"        : datetime.now(timezone.utc).isoformat(),
        "type"        : run_type,
        "status"      : status,
        "video_title" : video_title,
        "detail"      : detail[:300],
    })
    # Keep last 500 runs
    _save_history(history[-500:])


def _tg_send(text: str):
    """Quick Telegram message (no import needed — raw HTTP)."""
    import urllib.request
    token   = os.getenv("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        return
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({
        "chat_id"   : chat_id,
        "text"      : text,
        "parse_mode": "HTML",
    }).encode()
    try:
        req = urllib.request.Request(url, data=payload,
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=15)
    except Exception as e:
        log.debug(f"[Telegram] {e}")


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _today_weekday(cfg: dict) -> str:
    """Return lowercase weekday name in UTC."""
    return _now_utc().strftime("%A").lower()


def _seconds_until(target_hour_utc: int, target_min_utc: int) -> float:
    """Seconds until the next occurrence of HH:MM UTC (today or tomorrow)."""
    now     = _now_utc()
    target  = now.replace(hour=target_hour_utc, minute=target_min_utc,
                          second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return (target - now).total_seconds()


# ══════════════════════════════════════════════════════════════════════════════
#  AUTO-DETECT CHANNEL
# ══════════════════════════════════════════════════════════════════════════════

def _resolve_channel(cfg: dict) -> dict | None:
    """
    Find the channel to use:
    - If config says 'auto' → pick first valid folder in accounts/
    - Otherwise match by folder name
    """
    accounts_dir = BASE_DIR / "accounts"
    target_folder = cfg.get("channel", {}).get("folder", "auto")

    for folder in sorted(accounts_dir.iterdir()):
        if not folder.is_dir():
            continue
        has_secrets = (folder / "client_secrets.json").exists()
        has_token   = (folder / "token.json").exists()
        if not (has_secrets or has_token):
            continue
        if target_folder == "auto" or folder.name == target_folder:
            ch = {
                "folder"      : folder,
                "name"        : folder.name,
                "real_name"   : folder.name,
                "folder_name" : folder.name,
                "secrets_path": folder / "client_secrets.json",
                "token_path"  : str(folder / "token.json"),
            }
            log.info(f"[Scheduler] Using channel: {folder.name}")
            return ch

    log.error("[Scheduler] No valid channel found in accounts/ — check token.json exists")
    return None


def _resolve_niche(cfg: dict, channel: dict):
    """Load niche from saved channel config or project_config.json."""
    from ai_workflow.generator import load_saved_niche
    from ai_workflow.niche_config import NICHES

    niche_key = cfg.get("niche", {}).get("key", "auto")
    channel_folder = channel["folder"]

    if niche_key == "auto":
        saved_key, saved_cfg = load_saved_niche(channel_folder)
        if saved_cfg:
            log.info(f"[Scheduler] Niche from channel config: {saved_key}")
            return saved_key, saved_cfg
        niche_key = "motivation"  # safe default

    if niche_key in NICHES:
        return niche_key, NICHES[niche_key]

    log.warning(f"[Scheduler] Unknown niche '{niche_key}' → using 'motivation'")
    return "motivation", NICHES["motivation"]


# ══════════════════════════════════════════════════════════════════════════════
#  CORE PIPELINE RUNNER
# ══════════════════════════════════════════════════════════════════════════════

def run_pipeline(run_type: str = "long_video", cfg: dict = None) -> bool:
    """
    Execute the full headless pipeline.
    run_type: 'long_video' | 'short'
    Returns True on success.
    """
    cfg = cfg or _load_config()
    log.info(f"[Scheduler] ▶ Starting pipeline: {run_type}")
    _tg_send(f"🤖 <b>ShortsBot starting</b>\n📦 Type: {run_type}\n🕐 {_now_utc().strftime('%Y-%m-%d %H:%M UTC')}")

    try:
        channel = _resolve_channel(cfg)
        if not channel:
            raise RuntimeError("No valid channel found")

        niche_key, niche_cfg = _resolve_niche(cfg, channel)

        is_shorts   = (run_type == "short")
        auto_clip   = cfg.get("video", {}).get("auto_clip_to_shorts", True) and not is_shorts
        auto_upload = cfg.get("upload", {}).get("auto_upload", True)
        visibility  = cfg.get("upload", {}).get("visibility", "public")
        target_min  = cfg.get("video", {}).get("target_duration_minutes", 10)

        from ai_workflow.headless_runner import run_headless
        result = run_headless(
            channel      = channel,
            niche_key    = niche_key,
            niche_cfg    = niche_cfg,
            is_shorts    = is_shorts,
            auto_clip    = auto_clip,
            auto_upload  = auto_upload,
            visibility   = visibility,
            target_duration_min = target_min,
        )

        if result.get("success"):
            title = result.get("title", "Unknown")
            log.info(f"[Scheduler] ✅ Pipeline complete: '{title}'")
            _tg_send(
                f"✅ <b>Upload complete!</b>\n"
                f"📌 <b>{title}</b>\n"
                f"🎬 Type: {run_type}\n"
                f"🔗 {result.get('url', '')}\n"
                f"📅 {_now_utc().strftime('%Y-%m-%d %H:%M UTC')}"
            )
            _record_run(run_type, "success", video_title=title)
            return True
        else:
            err = result.get("error", "Unknown error")
            raise RuntimeError(err)

    except Exception as e:
        tb = traceback.format_exc()
        log.error(f"[Scheduler] ❌ Pipeline failed: {e}\n{tb}")
        _tg_send(
            f"❌ <b>ShortsBot ERROR</b>\n"
            f"Type: {run_type}\n"
            f"Error: <code>{str(e)[:200]}</code>"
        )
        _record_run(run_type, "failed", detail=str(e))
        return False


# ══════════════════════════════════════════════════════════════════════════════
#  SCHEDULE LOGIC
# ══════════════════════════════════════════════════════════════════════════════

def _should_run_long_video_today(cfg: dict) -> bool:
    today = _today_weekday(cfg)
    days  = [d.lower() for d in cfg.get("schedule", {}).get("long_video_days",
             ["monday", "wednesday", "friday", "sunday"])]
    return today in days


def _should_run_standalone_short_today(cfg: dict) -> bool:
    today = _today_weekday(cfg)
    days  = [d.lower() for d in cfg.get("schedule", {}).get("shorts_standalone_days",
             ["tuesday", "thursday", "saturday"])]
    return today in days


def _already_ran_today(run_type: str) -> bool:
    """Check run_history.json to avoid double-running on same day."""
    today = _now_utc().date().isoformat()
    history = _load_history()
    for entry in reversed(history[-20:]):
        entry_date = entry.get("date", "")[:10]
        if entry_date == today and entry.get("type") == run_type and entry.get("status") == "success":
            return True
    return False


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN DAEMON LOOP
# ══════════════════════════════════════════════════════════════════════════════

def daemon_loop():
    """
    Main event loop. Wakes up every minute to check if it's time to run.
    Extremely simple — no APScheduler, no cron, no extra deps.
    """
    log.info("══════════════════════════════════════════════════════")
    log.info("  ShortsBot Scheduler — AWS Daily Automation Daemon")
    log.info("══════════════════════════════════════════════════════")
    _tg_send(
        "🚀 <b>ShortsBot Scheduler started on AWS</b>\n"
        "📅 Daily automation is now active.\n"
        "⏰ Long videos: Mon/Wed/Fri/Sun @ 2:30 UTC\n"
        "📱 Shorts: every day @ 3:00 UTC"
    )

    cfg = _load_config()

    while True:
        cfg = _load_config()   # reload config each tick (allows live edits)
        now_utc = _now_utc()
        h, m    = now_utc.hour, now_utc.minute

        sched   = cfg.get("schedule", {})
        lv_h    = sched.get("long_video_hour_utc", 2)
        lv_m    = sched.get("long_video_minute_utc", 30)
        sh_h    = sched.get("shorts_hour_utc", 3)
        sh_m    = sched.get("shorts_minute_utc", 0)

        # ── Long video trigger ────────────────────────────────────────────────
        if h == lv_h and m == lv_m:
            if _should_run_long_video_today(cfg) and not _already_ran_today("long_video"):
                log.info("[Scheduler] 🎬 Long video trigger fired!")
                retry_cfg = cfg.get("retry", {})
                max_retries = retry_cfg.get("max_retries_on_failure", 3)
                retry_delay = retry_cfg.get("retry_delay_minutes", 15) * 60

                for attempt in range(1, max_retries + 1):
                    log.info(f"[Scheduler] Attempt {attempt}/{max_retries}")
                    ok = run_pipeline("long_video", cfg)
                    if ok:
                        break
                    if attempt < max_retries:
                        log.info(f"[Scheduler] Retry in {retry_delay//60} min…")
                        time.sleep(retry_delay)
                time.sleep(90)  # avoid double-trigger within same minute

        # ── Shorts trigger ────────────────────────────────────────────────────
        if h == sh_h and m == sh_m:
            if sched.get("shorts_daily", True) and not _already_ran_today("short"):
                run_type = "short" if _should_run_standalone_short_today(cfg) else "short_clip"
                log.info(f"[Scheduler] 📱 Shorts trigger fired → {run_type}")
                run_pipeline("short", cfg)
                time.sleep(90)

        # ── Heartbeat log every hour (so you can verify it's alive) ───────────
        if m == 0:
            next_lv = _seconds_until(lv_h, lv_m)
            next_sh = _seconds_until(sh_h, sh_m)
            log.info(
                f"[Scheduler] ⏳ alive | "
                f"Next long video in {int(next_lv//3600)}h{int((next_lv%3600)//60)}m | "
                f"Next short in {int(next_sh//3600)}h{int((next_sh%3600)//60)}m"
            )

        time.sleep(55)   # sleep ~55s, check every minute


# ══════════════════════════════════════════════════════════════════════════════
#  ENTRYPOINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ShortsBot AWS Daily Scheduler")
    parser.add_argument("--test-once",   action="store_true",
                        help="Run ONE full long-video pipeline right now (for testing)")
    parser.add_argument("--shorts-now",  action="store_true",
                        help="Run ONE Short pipeline right now (for testing)")
    parser.add_argument("--status",      action="store_true",
                        help="Show last 10 run history entries and exit")
    args = parser.parse_args()

    if args.status:
        history = _load_history()
        print("\n── ShortsBot Run History (last 10) ──────────────────")
        for entry in history[-10:]:
            icon = "✅" if entry["status"] == "success" else "❌"
            print(f"  {icon} {entry['date'][:16]}  [{entry['type']}]  {entry.get('video_title','')[:50]}")
        print()
        sys.exit(0)

    elif args.test_once:
        log.info("[Scheduler] TEST MODE — running one full pipeline now…")
        success = run_pipeline("long_video")
        sys.exit(0 if success else 1)

    elif args.shorts_now:
        log.info("[Scheduler] TEST MODE — running one Short now…")
        success = run_pipeline("short")
        sys.exit(0 if success else 1)

    else:
        try:
            daemon_loop()
        except KeyboardInterrupt:
            log.info("[Scheduler] Stopped by user (Ctrl+C)")
