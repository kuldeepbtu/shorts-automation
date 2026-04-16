"""
<<<<<<< HEAD
ShortsBot  pipeline.py  v10  — Accounts Folder Edition
========================================================
Run:  python pipeline.py   (no arguments needed)

CHANNEL SETUP — DROP-IN FOLDER SYSTEM:
  C:/ShortsBot/
  └── accounts/
      ├── MyMainChannel/
      │   └── client_secrets.json   drop this file here
      ├── MyFitnessChannel/
      │   └── client_secrets.json
      └── MyCookingChannel/
          └── client_secrets.json

  HOW IT WORKS:
  1. Create a folder inside accounts/ named after your channel
  2. Drop your client_secrets.json file inside that folder
  3. Run python pipeline.py
  4. Script scans all folders, authenticates each one, fetches real channel names
  5. You pick which channel to upload to — done

  OPTIONAL: add a settings.json file in the channel folder to set niche:
  {"niche": "fitness"}   ← without this, script asks you to pick

HIERARCHY:
  Start → channel folder scan → pick channel → pick mode → process → upload → cleanup

10-DAY MONETIZATION STRATEGY (built-in):
  Day 1-2: Viral copy 3 Shorts/day
  Day 3-4: 3 Shorts + 1 long video (watch hours)
  Day 5-6: Reply ALL comments within 2h (5x algorithm boost)
  Day 7-8: 3 Shorts + 1 long video
  Day 9-10: 3 Shorts/day + pin comment on every upload
  Target: 1000 subs + 4000 watch hours = YouTube Partner Program
"""

import json, time, random, shutil, logging, subprocess, textwrap, sys
import urllib.request, urllib.parse, os
=======
YouTube Shorts Automation Pipeline  —  Ultimate Edition  (Windows)
====================================================================
NEW FEATURES in this version:
  ✅ Progress bars + percentage for every task
  ✅ Auto-delete source video after Shorts uploaded, save URL/name to log
  ✅ AI-enhanced titles, descriptions, unique hashtags per video
  ✅ Viral Shorts scraper — download top 10 most viewed Shorts from any channel
     and learn their metadata to write better titles/descriptions/hashtags
  ✅ Lossless video quality — no compression on original footage
  ✅ Multi-account support — choose which YouTube channel to upload to
  ✅ Resume from last step if script was interrupted
  ✅ 20+ free music tracks auto-downloaded from multiple sources

AI Stack:
  Captions    → Groq Whisper Large v3 Turbo   (free)
  Titles/Tags → Google Gemini 2.5 Flash        (free)
  Music       → Jamendo + Bensound + ccMixter  (all free)
"""

import os, json, time, random, shutil, logging, argparse
import urllib.request, urllib.parse, subprocess, textwrap, sys, re
>>>>>>> 64497acc2905e2ab02e72faaffb871464a15f9a7
from pathlib import Path
from datetime import datetime, timedelta, timezone

<<<<<<< HEAD
# ── Config import ──────────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("\n❌  python-dotenv not installed. Run: pip install python-dotenv\n")
    pass

# ── Paths ──────────────────────────────────────────────────────────────────────
# BASE_DIR = folder where pipeline.py lives (works wherever you put it)
BASE_DIR     = Path(__file__).parent.resolve()
ACCOUNTS_DIR = BASE_DIR / "accounts"      # each subfolder = one channel
RAW_DIR      = BASE_DIR / "output" / "raw"
SHORTS_DIR   = BASE_DIR / "output" / "shorts"
VIDEOS_DIR   = BASE_DIR / "output" / "videos"
MUSIC_DIR    = BASE_DIR / "assets"  / "music"
THUMB_DIR    = BASE_DIR / "output" / "thumbnails"
LOG_FILE     = BASE_DIR / "automation.log"
MANIFEST     = BASE_DIR / "upload_manifest.json"
DESKTOP      = Path.home() / "Desktop" / "upload_manifest.json"
PROCESSED_DB = BASE_DIR / "processed_videos.json"
CHECKPOINT   = BASE_DIR / "checkpoint.json"
CHANNELS_DB  = BASE_DIR / "channels_cache.json"
WINDOWS_FONT = r"C\:/Windows/Fonts/arialbd.ttf"

# IMPORTANT: Include youtube.readonly so channels.list(mine=True) returns ALL channels
YT_SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly",
]

for d in [BASE_DIR, ACCOUNTS_DIR, RAW_DIR, SHORTS_DIR, VIDEOS_DIR, MUSIC_DIR, THUMB_DIR]:
    d.mkdir(parents=True, exist_ok=True)

=======
# ══════════════════════════════════════════════════════════════════════════════
#  WINDOWS PATHS
# ══════════════════════════════════════════════════════════════════════════════
BASE_DIR      = Path(r"C:\ShortsBot")
OUTPUT_DIR    = BASE_DIR / "output"
RAW_DIR       = OUTPUT_DIR / "raw"
SHORTS_DIR    = OUTPUT_DIR / "shorts"
MUSIC_DIR     = BASE_DIR / "assets" / "music"
LOG_FILE      = BASE_DIR / "automation.log"
MANIFEST      = BASE_DIR / "upload_manifest.json"
DESKTOP       = Path.home() / "Desktop" / "upload_manifest.json"
PROCESSED_DB  = BASE_DIR / "processed_videos.json"   # tracks deleted source vids
CHECKPOINT    = BASE_DIR / "checkpoint.json"           # resume from last step
ACCOUNTS_FILE = BASE_DIR / "accounts.json"            # multi-account credentials
VIRAL_DB      = BASE_DIR / "viral_learnings.json"     # learned from viral Shorts
WINDOWS_FONT  = r"C\:/Windows/Fonts/arialbd.ttf"

# ══════════════════════════════════════════════════════════════════════════════
#  LOGGING
# ══════════════════════════════════════════════════════════════════════════════
BASE_DIR.mkdir(parents=True, exist_ok=True)
>>>>>>> 64497acc2905e2ab02e72faaffb871464a15f9a7
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(str(LOG_FILE), encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════════
<<<<<<< HEAD
#  NICHE HASHTAGS
# ══════════════════════════════════════════════════════════════════════════════
NICHE_TAGS = {
    "fitness"   :["gym","workout","fitness","health","fitnessmotivation","bodybuilding",
                  "weightloss","exercise","fit","cardio","gymmotivation","homeworkout"],
    "cooking"   :["food","recipe","cooking","foodie","chef","homecooking","easyrecipe",
                  "delicious","tasty","kitchen","mealprep","healthyfood","instafood"],
    "finance"   :["money","investing","finance","wealth","personalfinance","stockmarket",
                  "crypto","business","entrepreneur","passiveincome","financialfreedom"],
    "gaming"    :["gaming","gamer","gameplay","games","videogames","ps5","xbox",
                  "streamer","gamingcommunity","esports","freefire","bgmi","pubg"],
    "motivation":["motivation","inspire","success","mindset","hustle","goals",
                  "positivity","selfimprovement","growth","believe","nevergiveup"],
    "tech"      :["technology","tech","gadgets","ai","artificialintelligence",
                  "coding","programming","startup","techreview","unboxing"],
    "education" :["education","learn","facts","science","history","didyouknow",
                  "amazingfacts","trivia","mindblowing","funfacts","awareness"],
    "bhajan"    :["bhajan","kirtan","devotional","bhakti","spiritual","mantra",
                  "hindu","god","prayer","aarti","krishna","shiva","hanuman"],
    "general"   :["facts","interesting","amazing","tips","lifehacks","howto",
                  "tutorial","diy","satisfying","trending","viral","india"],
}

def get_tags(niche: str, i: int, trending: list = None) -> list:
    pool = NICHE_TAGS.get(niche.lower(), NICHE_TAGS["general"])
    random.seed(i * 13 + len(pool))
    picks = random.sample(pool, min(8, len(pool)))
    random.seed()
    tr   = random.sample(trending, min(4, len(trending))) if trending else []
    base = ["shorts","viral","trending","youtubeshorts","fyp","foryoupage","subscribe"]
    return list(dict.fromkeys(base + picks + tr))[:20]

# ══════════════════════════════════════════════════════════════════════════════
#  COLOUR + UI HELPERS
# ══════════════════════════════════════════════════════════════════════════════

# ANSI colour codes (Windows 10+ supports these natively in PowerShell / Terminal)
# Falls back silently on older systems — the progress bar still works, just no colour
class C:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    # Progress bar fill colours (gradient green → yellow → red by %)
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    CYAN    = "\033[96m"
    MAGENTA = "\033[95m"
    RED     = "\033[91m"
    BLUE    = "\033[94m"
    WHITE   = "\033[97m"
    DIM     = "\033[2m"
    # Background for label
    BG_DARK = "\033[40m"

def _enable_ansi():
    """Enable ANSI escape codes on Windows."""
    if sys.platform == "win32":
        try:
            import ctypes
            kernel = ctypes.windll.kernel32
            # Enable VIRTUAL_TERMINAL_PROCESSING (0x0004) on stdout
            kernel.SetConsoleMode(kernel.GetStdHandle(-11), 7)
        except Exception:
            pass

_enable_ansi()


def _fmt_eta(seconds: float) -> str:
    """
    Format ETA as human-readable:
      < 60s   → '45s'
      < 3600s → '4m 12s'
      >= 3600s → '1h 23m'
    """
    s = int(seconds)
    if s < 60:
        return f"{s}s"
    elif s < 3600:
        m, sec = divmod(s, 60)
        return f"{m}m {sec}s" if sec else f"{m}m"
    else:
        h, rem = divmod(s, 3600)
        m      = rem // 60
        return f"{h}h {m}m" if m else f"{h}h"


# Per-bar start times: keyed by label so separate bars don't share state
_pb_starts: dict = {}

def progress_bar(cur: int, tot: int, lbl: str = "", w: int = 32, bar_id: str = ""):
    """
    Colourful animated progress bar with smart ETA.

    Colour changes by progress:
      0–33%  → Blue
      34–66% → Cyan
      67–89% → Yellow / Magenta
      90–99% → Green
      100%   → Bold Green ✓

    ETA format:
      < 60s     → '12s'
      < 60min   → '4m 12s'
      >= 1 hour → '1h 23m'
    """
    key = bar_id or lbl or "default"
    if cur == 0:
        _pb_starts[key] = time.time()

    t0  = _pb_starts.get(key, time.time())
    el  = time.time() - t0
    pct = int(cur / max(tot, 1) * 100)
    fl  = int(w * cur / max(tot, 1))

    # Colour based on progress
    if cur >= tot:
        fill_col = C.GREEN + C.BOLD
        ic       = "✓"
        eta_str  = f"{C.DIM}done {_fmt_eta(el)}{C.RESET}"
    else:
        if pct < 33:
            fill_col = C.BLUE
        elif pct < 67:
            fill_col = C.CYAN
        elif pct < 90:
            fill_col = C.YELLOW
        else:
            fill_col = C.MAGENTA
        sp  = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
        ic  = sp[int(time.time() * 8) % len(sp)]
        if cur > 0 and el > 0:
            eta_secs = el / cur * (tot - cur)
            eta_str  = f"{C.CYAN}ETA {_fmt_eta(eta_secs)}{C.RESET}"
        else:
            eta_str  = ""

    # Build coloured bar
    filled  = f"{fill_col}{'█' * fl}{C.RESET}"
    empty   = f"{C.DIM}{'░' * (w - fl)}{C.RESET}"
    bar_str = filled + empty

    # Percentage colour
    if pct >= 90:
        pct_col = C.GREEN
    elif pct >= 50:
        pct_col = C.YELLOW
    else:
        pct_col = C.WHITE

    pct_str  = f"{pct_col}{pct:3d}%{C.RESET}"
    lbl_str  = f"{C.WHITE}{lbl[:28]:<28}{C.RESET}"

    sys.stdout.write(f"\r  {ic} [{bar_str}] {pct_str}  {lbl_str}  {eta_str:<20}")
    sys.stdout.flush()
    if cur >= tot:
        sys.stdout.write("\n")
        sys.stdout.flush()
        _pb_starts.pop(key, None)


# Per-video / per-shorts dedicated progress bars
# Call these instead of progress_bar when processing individual clips

def pb_video(cur: int, tot: int, step_name: str, clip_num: int, clip_total: int):
    """
    Dedicated coloured progress bar for video/shorts processing.
    Shows:  [Clip 2/5]  ██████░░  67%  Encoding 9:16  ETA 23s
    """
    lbl    = f"[Clip {clip_num}/{clip_total}] {step_name}"
    bar_id = f"clip_{clip_num}"
    progress_bar(cur, tot, lbl[:32], bar_id=bar_id)


def pb_upload(cur: int, tot: int, item_num: int, item_total: int, pct_up: int):
    """Dedicated progress bar for uploads."""
    lbl    = f"[Upload {item_num}/{item_total}] {pct_up}% sent"
    bar_id = f"upload_{item_num}"
    progress_bar(cur, tot, lbl[:32], bar_id=bar_id)


def hdr(t):
    print(f"\n{C.CYAN}{'─'*64}{C.RESET}")
    print(f"  {C.BOLD}{C.WHITE}▶  {t}{C.RESET}")
    print(f"{C.CYAN}{'─'*64}{C.RESET}")

def ok(t):   print(f"  {C.GREEN}✅  {t}{C.RESET}")
def warn(t): print(f"  {C.YELLOW}⚠️   {t}{C.RESET}")

def box(title, rows, footer=""):
    w = 62
    print(f"\n╔{'═'*w}╗")
    if title: print(f"║  {title:<{w-2}} ║")
    print(f"╠{'═'*w}╣")
    for r in rows: print(f"║  {str(r):<{w-2}} ║")
    if footer:
        print(f"╠{'═'*w}╣")
        print(f"║  {footer:<{w-2}} ║")
    print(f"╚{'═'*w}╝")

def menu(title: str, options: list, prompt: str = "Enter number") -> int:
    w = 62
    print(f"\n╔{'═'*w}╗")
    print(f"║  {title:<{w-2}} ║")
    print(f"╠{'═'*w}╣")
    for i, opt in enumerate(options, 1):
        print(f"║  {i}.  {str(opt):<{w-5}} ║")
    print(f"╚{'═'*w}╝")
    while True:
        raw = input(f"\n  {prompt} (1-{len(options)}): ").strip()
        try:
            n = int(raw)
            if 1 <= n <= len(options): return n
        except ValueError: pass
        print(f"  ⚠  Enter a number 1–{len(options)}")

def yn(q: str, default: bool = True) -> bool:
    hint = "(Y/n)" if default else "(y/N)"
    ans  = input(f"\n  {q} {hint}: ").strip().lower()
    if ans == "": return default
    return ans not in ("n","no","0")

def get_input(prompt: str, required: bool = True) -> str:
    while True:
        val = input(f"\n  {prompt}: ").strip()
        if val or not required: return val
        print("  ⚠  Required.")

# ══════════════════════════════════════════════════════════════════════════════
#  HTTP
# ══════════════════════════════════════════════════════════════════════════════
def http_get(url: str, headers: dict = None) -> bytes:
    req = urllib.request.Request(url, headers=headers or {"User-Agent":"ShortsBot/9"})
    with urllib.request.urlopen(req, timeout=40) as r: return r.read()

def http_post_json(url: str, payload: dict, headers: dict) -> dict:
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                  headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=90) as r: return json.loads(r.read())

def gemini(prompt: str, max_retries: int = 5) -> str:
    """
    Call Gemini API with automatic retry + exponential backoff.
    Seamlessly falls back to Groq (Llama 3.3 70B) if all Google quotas are exhausted.
    """
    models   = ["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-flash-latest"]
    waits    = [5, 15, 30, 60, 90]
    last_err = None

    keys = []
    if os.getenv("GEMINI_API_KEY"): keys.append(os.getenv("GEMINI_API_KEY"))
    for i in range(2, 6):
        k = os.getenv(f"GEMINI_API_KEY_{i}")
        if k: keys.append(k)
        
    if not keys: keys = [""]

    # Configure attempt sequences
    configs = [("gemini", m, k) for m in models for k in keys]
    
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        configs.append(("groq", "llama-3.3-70b-versatile", groq_key))

    total_attempts = max_retries * len(configs)

    for attempt in range(total_attempts):
        provider, current_model, current_key = configs[attempt % len(configs)]
        
        try:
            if provider == "gemini":
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{current_model}:generateContent"
                resp = http_post_json(
                    url,
                    {"contents": [{"parts": [{"text": prompt}]}]},
                    {"Content-Type": "application/json", "x-goog-api-key": current_key}
                )
                return resp["candidates"][0]["content"]["parts"][0]["text"].strip()
                
            elif provider == "groq":
                url = "https://api.groq.com/openai/v1/chat/completions"
                resp = http_post_json(
                    url,
                    {"model": current_model, "messages": [{"role": "user", "content": prompt}]},
                    {"Content-Type": "application/json", "Authorization": f"Bearer {current_key}"}
                )
                return resp["choices"][0]["message"]["content"].strip()

        except Exception as e:
            last_err = e
            
            # Rapid jump to next config on ANY API error before ever blocking/waiting
            if len(configs) > 1 and (attempt + 1) % len(configs) != 0:
                next_prov, next_model, next_key = configs[(attempt + 1) % len(configs)]
                if next_prov == "gemini":
                    k_idx = keys.index(next_key) + 1 if next_key in keys else 1
                    print(f"\n  {C.YELLOW}API limit hit... switching to {next_model} (Key #{k_idx}){C.RESET}")
                else:
                    print(f"\n  {C.YELLOW}Gemini exhausted! Falling back to Groq ({next_model})...{C.RESET}")
                time.sleep(1)
                continue
                
            cycle = attempt // len(configs)
            wait = waits[min(cycle, len(waits) - 1)]
            print(f"\n  {C.YELLOW}All AI providers rate-limited — waiting {wait}s "
                  f"(retry {cycle+1}/{max_retries})...{C.RESET}")
            for rem in range(wait, 0, -1):
                sys.stdout.write(f"\r  {C.DIM}  resuming in {rem:3d}s ...{C.RESET}  ")
                sys.stdout.flush()
                time.sleep(1)
            sys.stdout.write("\r" + " "*40 + "\r"); sys.stdout.flush()
            continue

    raise last_err

# ══════════════════════════════════════════════════════════════════════════════
#  CHECKPOINT
# ══════════════════════════════════════════════════════════════════════════════
def save_cp(d: dict):
    """
    Save checkpoint with FULL session + channel so any crash can be resumed
    without re-asking any questions.
    """
    d["saved_at"] = str(datetime.now())
    CHECKPOINT.write_text(json.dumps(d, indent=2), encoding="utf-8")

def load_cp() -> dict | None:
    if CHECKPOINT.exists():
        try:
            return json.loads(CHECKPOINT.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None

def clear_cp():
    if CHECKPOINT.exists(): CHECKPOINT.unlink()

def ask_resume() -> dict | None:
    cp = load_cp()
    if not cp:
        return None
    step     = cp.get("step", "?")
    saved_at = cp.get("saved_at", "")[:16]
    account  = ""
    if cp.get("channel"):
        account = cp["channel"].get("real_name", "")
    elif cp.get("account"):
        account = cp["account"]
    source   = ""
    if cp.get("session"):
        source = cp["session"].get("source", "")[:55]
    elif cp.get("source"):
        source = cp["source"][:55]
    print(f"\n{C.YELLOW}⚠️  Incomplete run found:{C.RESET}")
    print(f"   Step    : {C.BOLD}{step}{C.RESET}")
    print(f"   Channel : {account}")
    print(f"   Source  : {source}")
    print(f"   Saved   : {saved_at}")
    if yn("Resume from last step?"):
        return cp
    clear_cp()   # user said NO — delete stale checkpoint
    return None

# ══════════════════════════════════════════════════════════════════════════════
#  INTERNET CHECK
# ══════════════════════════════════════════════════════════════════════════════
def _check_internet() -> bool:
    try:
        urllib.request.urlopen("https://www.google.com", timeout=5)
        return True
    except Exception:
        return False

def _require_internet():
    if not _check_internet():
        box("❌  NO INTERNET CONNECTION", [
            "Google OAuth + YouTube API need internet.",
            "",
            "Fix one of these:",
            "1. Check WiFi / ethernet is connected",
            "2. Disconnect VPN if using one",
            "3. Allow python.exe in Windows Firewall:",
            "   Windows Security → Firewall → Allow an app",
            "   → python.exe → tick Private + Public",
            "4. Open browser → check google.com loads",
        ], "After fixing, run: python pipeline.py")
        sys.exit(1)

# ══════════════════════════════════════════════════════════════════════════════
#  AUTH  (per-secrets-file, per-channel tokens)
# ══════════════════════════════════════════════════════════════════════════════

def _auth(secrets_file: str):
    """
    OAuth2 login using a specific client_secrets file.
    Token cached as token_<stem>.json
    Uses FULL scope including youtube.readonly so channels.list returns ALL channels.
    Deletes stale token and re-auths if refresh fails.
    """
=======
#  API KEYS
# ══════════════════════════════════════════════════════════════════════════════
GROQ_API_KEY   = "Your_api"
JAMENDO_ID     = "Your_api"
GEMINI_API_KEY = "Your_api"

# ══════════════════════════════════════════════════════════════════════════════
#  CONFIG
# ══════════════════════════════════════════════════════════════════════════════
CONFIG = {
    "shorts_duration"      : 58,
    "max_shorts_per_video" : 3,
    "upload_interval_hours": 4,
    "music_volume"         : 0.12,
    "caption_fontsize"     : 52,
    "youtube": {
        "category_id"   : "22",
        "privacy_status": "private",
        "base_tags"     : ["shorts", "viral", "trending", "youtubeshorts",
                           "fyp", "foryoupage", "explore", "subscribe",
                           "reels", "entertainment"],
    },
    "jamendo_moods": ["energetic","happy","inspiring","motivational","upbeat","calm","dramatic"],

    # 20 free music tracks from 3 sources
    "bensound_tracks": [
        {"name":"bs_energy.mp3",     "url":"https://www.bensound.com/bensound-music/bensound-energy.mp3"},
        {"name":"bs_ukulele.mp3",    "url":"https://www.bensound.com/bensound-music/bensound-ukulele.mp3"},
        {"name":"bs_littleidea.mp3", "url":"https://www.bensound.com/bensound-music/bensound-littleidea.mp3"},
        {"name":"bs_sunny.mp3",      "url":"https://www.bensound.com/bensound-music/bensound-sunny.mp3"},
        {"name":"bs_adventure.mp3",  "url":"https://www.bensound.com/bensound-music/bensound-adventure.mp3"},
        {"name":"bs_dubstep.mp3",    "url":"https://www.bensound.com/bensound-music/bensound-dubstep.mp3"},
        {"name":"bs_epic.mp3",       "url":"https://www.bensound.com/bensound-music/bensound-epic.mp3"},
        {"name":"bs_summer.mp3",     "url":"https://www.bensound.com/bensound-music/bensound-summer.mp3"},
    ],
    "pixabay_tracks": [
        {"name":"px_lofi.mp3",       "url":"https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3"},
        {"name":"px_upbeat.mp3",     "url":"https://cdn.pixabay.com/download/audio/2022/03/10/audio_270f49c5e9.mp3"},
        {"name":"px_motivate.mp3",   "url":"https://cdn.pixabay.com/download/audio/2021/11/25/audio_5b5bb9e0a6.mp3"},
        {"name":"px_cinematic.mp3",  "url":"https://cdn.pixabay.com/download/audio/2022/01/18/audio_d0fd6a0f9e.mp3"},
        {"name":"px_corporate.mp3",  "url":"https://cdn.pixabay.com/download/audio/2022/08/02/audio_884fe92c21.mp3"},
        {"name":"px_happy.mp3",      "url":"https://cdn.pixabay.com/download/audio/2021/08/09/audio_dc39bde5b9.mp3"},
    ],
}

# ══════════════════════════════════════════════════════════════════════════════
#  PROGRESS BAR
# ══════════════════════════════════════════════════════════════════════════════

_pb_start: float = 0.0

def progress_bar(current: int, total: int, label: str = "", width: int = 36):
    """
    Responsive live progress bar with percentage, elapsed + ETA.
    Overwrites same line using carriage return — no scroll spam.
    """
    global _pb_start
    if current == 0:
        _pb_start = time.time()
    pct    = int((current / max(total, 1)) * 100)
    filled = int(width * current / max(total, 1))
    bar    = "█" * filled + "░" * (width - filled)
    elapsed = time.time() - _pb_start
    if current > 0 and current < total:
        eta = int(elapsed / current * (total - current))
        time_str = f"ETA {eta}s"
    elif current >= total:
        time_str = f"done {elapsed:.1f}s"
    else:
        time_str = ""
    spin = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
    icon = spin[int(time.time()*8) % len(spin)] if current < total else "✓"
    sys.stdout.write(f"\r  {icon} [{bar}] {pct:3d}%  {label[:28]:<28}  {time_str:<12}")
    sys.stdout.flush()
    if current >= total:
        sys.stdout.write("\n")
        sys.stdout.flush()


def task_header(title: str):
    """Print a bold section header."""
    print(f"\n{'─'*60}")
    print(f"  ▶  {title}")
    print(f"{'─'*60}")


def task_done(title: str):
    print(f"  ✅  {title} — DONE")

# ══════════════════════════════════════════════════════════════════════════════
#  CHECKPOINT (resume from last step)
# ══════════════════════════════════════════════════════════════════════════════

def save_checkpoint(data: dict):
    CHECKPOINT.write_text(json.dumps(data, indent=2), encoding="utf-8")

def load_checkpoint() -> dict | None:
    if CHECKPOINT.exists():
        return json.loads(CHECKPOINT.read_text(encoding="utf-8"))
    return None

def clear_checkpoint():
    if CHECKPOINT.exists():
        CHECKPOINT.unlink()

def ask_resume() -> dict | None:
    """Ask user if they want to resume from a saved checkpoint."""
    cp = load_checkpoint()
    if not cp:
        return None
    print(f"\n⚠️  Found incomplete run from {cp.get('saved_at','unknown')}")
    print(f"   Step reached : {cp.get('step','unknown')}")
    print(f"   Source       : {cp.get('source','unknown')}")
    ans = input("\n  Resume from last step? (y/n): ").strip().lower()
    return cp if ans == "y" else None

# ══════════════════════════════════════════════════════════════════════════════
#  PROCESSED VIDEO DATABASE  (tracks deleted source videos)
# ══════════════════════════════════════════════════════════════════════════════

def load_processed_db() -> list:
    if PROCESSED_DB.exists():
        return json.loads(PROCESSED_DB.read_text(encoding="utf-8"))
    return []

def save_processed_db(entries: list):
    PROCESSED_DB.write_text(json.dumps(entries, indent=2), encoding="utf-8")

def record_and_delete_source(video_path: Path, source_url: str, shorts_uploaded: list):
    """
    1. Save video info to processed_videos.json
    2. Delete the source video file
    3. Delete all processed Short .mp4 files for this video
    """
    db = load_processed_db()
    db.append({
        "video_name"    : video_path.name,
        "source_url"    : source_url,
        "processed_at"  : str(datetime.now()),
        "shorts_created": [s.get("url","") for s in shorts_uploaded],
        "file_deleted"  : True,
    })
    save_processed_db(db)

    # Delete source video
    if video_path.exists():
        video_path.unlink()
        log.info(f"[Cleanup] Deleted source video: {video_path.name}")

    # Delete processed Short clips for this video
    stem = "".join(c for c in video_path.stem[:40] if c.isalnum() or c in " _-").strip()
    deleted_clips = 0
    for clip in SHORTS_DIR.glob(f"{stem}*_final.mp4"):
        clip.unlink(missing_ok=True)
        deleted_clips += 1

    task_done(f"Cleaned up: source video + {deleted_clips} Short clip(s) deleted")

# ══════════════════════════════════════════════════════════════════════════════
#  MULTI-ACCOUNT SELECTOR
# ══════════════════════════════════════════════════════════════════════════════

def select_youtube_account() -> str:
    """
    Ask user which YouTube account/channel to upload to.
    Each account has its own client_secrets_<name>.json and token_<name>.json
    stored in C:\\ShortsBot\\accounts\\
    """
    accounts_dir = BASE_DIR / "accounts"
    accounts_dir.mkdir(exist_ok=True)

    # Find all account secret files
    secrets = sorted(accounts_dir.glob("client_secrets_*.json"))

    print("\n╔══════════════════════════════════════════════════════════╗")
    print("║           SELECT YOUTUBE CHANNEL TO UPLOAD TO            ║")
    print("╠══════════════════════════════════════════════════════════╣")

    if not secrets:
        print("║  No accounts found. Using default client_secrets.json    ║")
        print("╚══════════════════════════════════════════════════════════╝\n")
        return "default"

    print(f"║  {'#':<4} {'Account Name':<48} ║")
    print(f"║  {'─'*52} ║")
    account_names = []
    for i, s in enumerate(secrets):
        name = s.stem.replace("client_secrets_", "")
        account_names.append(name)
        print(f"║  {i+1:<4} {name:<48} ║")
    print(f"║  {len(secrets)+1:<4} {'Default (client_secrets.json)':<48} ║")
    print("╚══════════════════════════════════════════════════════════╝")

    while True:
        try:
            choice = int(input(f"\n  Enter account number (1-{len(secrets)+1}): ").strip())
            if 1 <= choice <= len(secrets):
                return account_names[choice - 1]
            elif choice == len(secrets) + 1:
                return "default"
        except ValueError:
            pass
        print("  Invalid choice. Try again.")


def authenticate_youtube(account_name: str = "default"):
    """OAuth2 login for a specific account. Caches token per account."""
>>>>>>> 64497acc2905e2ab02e72faaffb871464a15f9a7
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request

<<<<<<< HEAD
    sp = BASE_DIR / secrets_file
    if not sp.exists():
        box(f"❌  {secrets_file} NOT FOUND", [
            f"Place {secrets_file} in C:\\ShortsBot\\",
            "",
            "Get it from: console.cloud.google.com",
            "APIs & Services → Credentials → OAuth 2.0 Client → Download JSON",
            f"Rename to: {secrets_file}",
        ])
        sys.exit(1)

    _require_internet()

    # One token file per secrets file (so different Gmails don't conflict)
    tp    = BASE_DIR / f"token_{sp.stem}.json"
    creds = None

    if tp.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(tp), YT_SCOPES)
        except Exception:
            tp.unlink(missing_ok=True)
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                from google.auth.transport.requests import Request as _Req
                creds.refresh(_Req())
                tp.write_text(creds.to_json())
                return creds
            except Exception as e:
                log.warning(f"[Auth] Token refresh failed ({e}) — deleting and re-logging in")
                tp.unlink(missing_ok=True)
                creds = None

        print(f"\n  🔐 Opening browser for Google sign-in...")
        print(f"     Secrets file: {secrets_file}")
        print(f"     ℹ  Click 'Continue' if you see 'App not verified'\n")
        flow  = InstalledAppFlow.from_client_secrets_file(str(sp), YT_SCOPES)
        creds = flow.run_local_server(port=0)
        tp.write_text(creds.to_json())
        print(f"  ✓  Login saved → {tp.name}\n")

    return creds


def _yt_client_from_creds(creds):
    from googleapiclient.discovery import build
=======
    SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
    accounts_dir = BASE_DIR / "accounts"
    accounts_dir.mkdir(exist_ok=True)

    if account_name == "default":
        secrets_path = BASE_DIR / "client_secrets.json"
        token_path   = BASE_DIR / "token.json"
    else:
        secrets_path = accounts_dir / f"client_secrets_{account_name}.json"
        token_path   = accounts_dir / f"token_{account_name}.json"

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow  = InstalledAppFlow.from_client_secrets_file(str(secrets_path), SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json())

    log.info(f"[Auth] Authenticated: {account_name}")
>>>>>>> 64497acc2905e2ab02e72faaffb871464a15f9a7
    return build("youtube", "v3", credentials=creds)

# ══════════════════════════════════════════════════════════════════════════════
#  VIRAL SHORTS SCRAPER  —  learn from top performing Shorts
# ══════════════════════════════════════════════════════════════════════════════

<<<<<<< HEAD
def _yt_client_for_channel(channel: dict):
    """
    Return authenticated YouTube API client for a specific channel.
    Uses the token.json stored INSIDE the channel's account folder.
    Falls back to old-style BASE_DIR token if no folder_name set.
    """
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request

    # New folder-based system: token stored inside accounts/FolderName/token.json
    if channel.get("token_path"):
        tp = Path(channel["token_path"])
    else:
        # Legacy fallback
        sf = channel.get("secrets_file","client_secrets.json")
        tp = BASE_DIR / f"token_{Path(sf).stem}.json"

    creds = None
    if tp.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(tp), YT_SCOPES)
        except Exception:
            tp.unlink(missing_ok=True)
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                tp.write_text(creds.to_json())
                return _yt_client_from_creds(creds)
            except Exception:
                tp.unlink(missing_ok=True)
                creds = None
        if not creds:
            # Re-auth using the account folder system
            if channel.get("folder_name"):
                acc = {
                    "name"        : channel["folder_name"],
                    "folder"      : Path(channel["folder"]),
                    "secrets_path": Path(channel["secrets_path"]),
                    "token_path"  : tp,
                    "niche"       : channel.get("niche","general"),
                }
                creds = _auth_account(acc)
            else:
                sf    = channel.get("secrets_file","client_secrets.json")
                creds = _auth(sf)
            tp.write_text(creds.to_json())

    return _yt_client_from_creds(creds)

# ══════════════════════════════════════════════════════════════════════════════
#  ACCOUNTS FOLDER SYSTEM
#  ─────────────────────────────────────────────────────────────────────────────
#  Structure:
#    C:\ShortsBot/
#    └── accounts/
#        ├── MyMainChannel/          ← folder name = display name in menu
#        │   ├── client_secrets.json  ← REQUIRED: drop OAuth file here
#        │   ├── settings.json        ← OPTIONAL: {"niche":"general"}
#        │   └── token.json           ← AUTO: created on first login
#        ├── FitnessChannel/
#        │   ├── client_secrets.json
#        │   ├── settings.json        ← {"niche":"fitness"}
#        │   └── token.json
#        └── CookingChannel/
#            ├── client_secrets.json
#            └── settings.json        ← {"niche":"cooking"}
#
#  WORKFLOW:
#  1. Create a folder in accounts/ — name it anything you like
#  2. Drop client_secrets.json inside that folder
#  3. Optionally add settings.json with {"niche":"fitness"} etc.
#  4. Run python pipeline.py
#  5. Script finds all folders, authenticates each, shows real YouTube names
#  6. Pick a channel — token.json is saved automatically in that folder
# ══════════════════════════════════════════════════════════════════════════════

def _scan_account_folders() -> list:
    """
    Scan C:/ShortsBot/accounts/ for channel folders.
    Each folder that contains a client_secrets.json is a valid channel.
    Returns list of account dicts.
    """
    ACCOUNTS_DIR.mkdir(parents=True, exist_ok=True)
    accounts = []

    for folder in sorted(ACCOUNTS_DIR.iterdir()):
        if not folder.is_dir():
            continue
        secrets = folder / "client_secrets.json"
        if not secrets.exists():
            continue

        # Read optional settings.json
        niche     = "general"
        settings  = folder / "settings.json"
        if settings.exists():
            try:
                s     = json.loads(settings.read_text(encoding="utf-8"))
                niche = s.get("niche", "general")
            except Exception:
                pass

        accounts.append({
            "folder"      : folder,
            "name"        : folder.name,          # folder name shown in menu
            "secrets_path": secrets,
            "token_path"  : folder / "token.json",
            "niche"       : niche,
        })

    return accounts


def _auth_account(account: dict):
    """
    Authenticate one account folder.
    Token saved as accounts/FolderName\token.json — never conflicts with others.
    """
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request

    sp = account["secrets_path"]
    tp = account["token_path"]
    _require_internet()

    creds = None
    if tp.exists():
        try:
            creds = Credentials.from_authorized_user_file(str(tp), YT_SCOPES)
        except Exception:
            tp.unlink(missing_ok=True)
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                tp.write_text(creds.to_json())
                return creds
            except Exception as e:
                log.warning(f"[Auth] {account['name']}: refresh failed ({e}) — re-login")
                tp.unlink(missing_ok=True)
                creds = None

        print(f"\n  🔐 Sign in for: {account['name']}")
        print(f"     File: {sp}")
        print(f"     Click 'Continue' if you see 'App not verified'\n")
        flow  = InstalledAppFlow.from_client_secrets_file(str(sp), YT_SCOPES)
        creds = flow.run_local_server(port=0)
        tp.write_text(creds.to_json())
        print(f"  ✓  Token saved → {tp}\n")

    return creds


def _fetch_channels_for_account(account: dict) -> list:
    """
    Fetch ALL YouTube channels linked to this account's Gmail.
    Saves real_name, channel_id, subs, videos into the account dict list.
    """
    creds = _auth_account(account)
    yt    = _yt_client_from_creds(creds)

    try:
        resp = yt.channels().list(
            part="snippet,id,statistics",
            mine=True,
            maxResults=50
        ).execute()
    except Exception as e:
        log.warning(f"[Channels] {account['name']}: API error: {e}")
        return []

    channels = []
    for item in resp.get("items", []):
        stats = item.get("statistics", {})
        ch = {
            "real_name"   : item["snippet"]["title"],  # REAL YouTube channel name
            "channel_id"  : item["id"],
            "subs"        : stats.get("subscriberCount", "0"),
            "videos"      : stats.get("videoCount", "0"),
            "folder"      : str(account["folder"]),
            "folder_name" : account["name"],
            "secrets_path": str(account["secrets_path"]),
            "token_path"  : str(account["token_path"]),
            "niche"       : account["niche"],
        }
        channels.append(ch)
        log.info(f"[Channels] Found: {ch['real_name']} ({ch['channel_id']}) in {account['name']}/")

    # If still empty, delete token and retry once
    if not channels and account["token_path"].exists():
        log.warning(f"[Channels] {account['name']}: no channels — deleting token and retrying")
        account["token_path"].unlink()
        creds = _auth_account(account)
        yt    = _yt_client_from_creds(creds)
        try:
            resp = yt.channels().list(part="snippet,id,statistics", mine=True, maxResults=50).execute()
            for item in resp.get("items", []):
                stats = item.get("statistics", {})
                channels.append({
                    "real_name"   : item["snippet"]["title"],
                    "channel_id"  : item["id"],
                    "subs"        : stats.get("subscriberCount","0"),
                    "videos"      : stats.get("videoCount","0"),
                    "folder"      : str(account["folder"]),
                    "folder_name" : account["name"],
                    "secrets_path": str(account["secrets_path"]),
                    "token_path"  : str(account["token_path"]),
                    "niche"       : account["niche"],
                })
        except Exception:
            pass

    return channels


def channel_menu() -> dict:
    """
    Channel management with 3 separate options:
      1. SELECT a channel (shows all, cached, instant)
      2. ADD new channel  (scans for new account folders only)
      3. REFRESH all      (re-fetches all from Google API)

    All channels shown at once — no repeated configuration needed.
    """
    _require_internet()
    accounts = _scan_account_folders()

    if not accounts:
        accounts_path = str(ACCOUNTS_DIR)
        print(f"\n{C.YELLOW}╔══════════════════════════════════════════════════════════════╗")
        print(f"║  📁  NO ACCOUNTS FOUND                                       ║")
        print(f"╠══════════════════════════════════════════════════════════════╣")
        print(f"║  Accounts folder:  {accounts_path:<42} ║")
        print(f"║                                                              ║")
        print(f"║  STEP 1 — Create a folder inside accounts/                  ║")
        print(f"║           e.g.  accounts/MyMainChannel/                     ║")
        print(f"║  STEP 2 — Drop client_secrets.json inside that folder       ║")
        print(f'║  STEP 3 — Optional settings.json:  {{"niche":"fitness"}}       ║')
        print(f"║  STEP 4 — Run:  python pipeline.py                          ║")
        print(f"╚══════════════════════════════════════════════════════════════╝{C.RESET}\n")
        sys.exit(0)

    # ── Load cache ───────────────────────────────────────────────────────────
    all_channels = []
    use_cache    = False
    cache_age_min = 0
    if CHANNELS_DB.exists():
        try:
            data = json.loads(CHANNELS_DB.read_text(encoding="utf-8"))
            age  = time.time() - data.get("ts", 0)
            if age < 3600:
                all_channels  = data.get("channels", [])
                use_cache     = True
                cache_age_min = int(age / 60)
        except Exception:
            pass

    # ── First time or no cache: fetch all ────────────────────────────────────
    if not use_cache:
        print(f"\n  {C.CYAN}🔍 Scanning {len(accounts)} account folder(s)...{C.RESET}")
        for acc in accounts:
            print(f"\n  {C.BLUE}📁 {acc['name']}/{C.RESET}  (niche: {acc['niche']})")
            found = _fetch_channels_for_account(acc)
            if found:
                existing_ids = {c["channel_id"] for c in all_channels}
                for ch in found:
                    if ch["channel_id"] not in existing_ids:
                        all_channels.append(ch)
                names = ", ".join(c["real_name"] for c in found)
                print(f"     {C.GREEN}✓ {len(found)} channel(s): {names}{C.RESET}")
            else:
                print(f"     {C.YELLOW}⚠  No channels found{C.RESET}")
        if all_channels:
            CHANNELS_DB.write_text(json.dumps(
                {"ts": time.time(), "channels": all_channels}, indent=2))
            ok(f"Saved {len(all_channels)} channel(s) to cache")

    if not all_channels:
        print(f"\n  {C.RED}❌  No YouTube channels found.{C.RESET}")
        print("  Make sure client_secrets.json is inside an accounts/ subfolder.\n")
        sys.exit(1)

    # ════════════════════════════════════════════════════════════════
    #  MAIN CHANNEL MANAGEMENT MENU
    # ════════════════════════════════════════════════════════════════
    while True:
        # ── Build channel list display ────────────────────────────────────
        w = 70
        print(f"\n{C.CYAN}╔{'═'*w}╗{C.RESET}")
        print(f"{C.CYAN}║{C.RESET}  {C.BOLD}{C.WHITE}{'YOUTUBE CHANNEL MANAGER':<{w-2}}{C.RESET}{C.CYAN}║{C.RESET}")
        if use_cache:
            cache_info = f"(cached {cache_age_min}min ago — using saved data)"
            print(f"{C.CYAN}║{C.RESET}  {C.DIM}{cache_info:<{w-2}}{C.RESET}{C.CYAN}║{C.RESET}")
        print(f"{C.CYAN}╠{'═'*w}╣{C.RESET}")

        # All channels listed with numbers
        for i, ch in enumerate(all_channels, 1):
            subs      = int(ch.get("subs",  "0") or "0")
            vids      = int(ch.get("videos","0") or "0")
            name      = ch["real_name"][:28]
            folder    = ch.get("folder_name","")[:14]
            niche     = ch.get("niche","general")[:10]
            subs_fmt  = f"{subs:,}"
            # Colour the channel name based on subscriber count
            if subs >= 1000:
                name_col = C.GREEN
            elif subs >= 100:
                name_col = C.YELLOW
            else:
                name_col = C.WHITE
            row = (f"  {C.BOLD}{i:<3}{C.RESET} "
                   f"{name_col}{name:<28}{C.RESET}  "
                   f"{C.DIM}{subs_fmt:>8} subs  "
                   f"{vids:>4} videos  "
                   f"[{folder}]  niche:{niche}{C.RESET}")
            print(f"{C.CYAN}║{C.RESET}{row}")

        print(f"{C.CYAN}╠{'═'*w}╣{C.RESET}")

        # Management options at the bottom
        mgmt_opts = [
            ("+", f"{C.GREEN}➕  Add new channel{C.RESET}         "
                  f"{C.DIM}(scan for new account folders only){C.RESET}"),
            ("R", f"{C.YELLOW}🔄  Refresh ALL channels{C.RESET}    "
                  f"{C.DIM}(re-fetch all from Google API){C.RESET}"),
            ("Q", f"{C.RED}✖   Quit{C.RESET}"),
        ]
        for key, label in mgmt_opts:
            print(f"{C.CYAN}║{C.RESET}  [{C.BOLD}{key}{C.RESET}]  {label}")
        print(f"{C.CYAN}╚{'═'*w}╝{C.RESET}")

        raw = input(
            f"\n  {C.BOLD}Pick channel (1-{len(all_channels)}), "
            f"[+] add, [R] refresh all, [Q] quit:{C.RESET} "
        ).strip().lower()

        # ── + Add new channels only ───────────────────────────────────────
        if raw == "+":
            print(f"\n  {C.CYAN}Scanning for NEW account folders...{C.RESET}")
            # Find folders not already in cache
            cached_folders = {ch.get("folder_name","") for ch in all_channels}
            new_accounts   = [a for a in accounts if a["name"] not in cached_folders]
            if not new_accounts:
                print(f"  {C.YELLOW}No new account folders found.{C.RESET}")
                print(f"  Add a new folder in: {ACCOUNTS_DIR}")
                print(f"  Then press [+] again.")
                input("  Press Enter to continue...")
                continue
            added = 0
            for acc in new_accounts:
                print(f"\n  {C.BLUE}📁 {acc['name']}/{C.RESET}")
                found = _fetch_channels_for_account(acc)
                if found:
                    existing_ids = {c["channel_id"] for c in all_channels}
                    for ch in found:
                        if ch["channel_id"] not in existing_ids:
                            all_channels.append(ch)
                            added += 1
                    names = ", ".join(c["real_name"] for c in found)
                    print(f"     {C.GREEN}✓ Added: {names}{C.RESET}")
            if added:
                CHANNELS_DB.write_text(json.dumps(
                    {"ts": time.time(), "channels": all_channels}, indent=2))
                ok(f"Added {added} new channel(s) — saved to cache")
            else:
                print(f"  {C.YELLOW}No new channels found in the new folders.{C.RESET}")
            use_cache = True
            cache_age_min = 0
            continue

        # ── R Refresh all ─────────────────────────────────────────────────
        if raw == "r":
            print(f"\n  {C.YELLOW}Refreshing ALL channels from Google API...{C.RESET}")
            # Delete cache and all tokens so fresh login
            if CHANNELS_DB.exists():
                CHANNELS_DB.unlink()
            for acc in accounts:
                if acc["token_path"].exists():
                    acc["token_path"].unlink()
                    print(f"  {C.DIM}Deleted token: {acc['name']}{C.RESET}")
            all_channels  = []
            use_cache     = False
            cache_age_min = 0
            # Re-fetch all
            print(f"  {C.CYAN}Fetching from Google API...{C.RESET}")
            for acc in accounts:
                print(f"\n  {C.BLUE}📁 {acc['name']}/{C.RESET}")
                found = _fetch_channels_for_account(acc)
                if found:
                    existing_ids = {c["channel_id"] for c in all_channels}
                    for ch in found:
                        if ch["channel_id"] not in existing_ids:
                            all_channels.append(ch)
                    names = ", ".join(c["real_name"] for c in found)
                    print(f"     {C.GREEN}✓ {names}{C.RESET}")
                else:
                    print(f"     {C.YELLOW}⚠  No channels found{C.RESET}")
            if all_channels:
                CHANNELS_DB.write_text(json.dumps(
                    {"ts": time.time(), "channels": all_channels}, indent=2))
                ok(f"Refreshed — {len(all_channels)} channel(s) saved")
            use_cache     = True
            cache_age_min = 0
            continue

        # ── Q Quit ────────────────────────────────────────────────────────
        if raw == "q":
            print("  Exiting.")
            sys.exit(0)

        # ── Number: select channel ────────────────────────────────────────
        try:
            n = int(raw)
            if 1 <= n <= len(all_channels):
                sel   = all_channels[n - 1]
                niche = sel.get("niche", "general")

                # ── Niche handling ────────────────────────────────────────
                if sel.get("folder_name"):
                    settings_file = Path(sel["folder"]) / "settings.json"

                    if settings_file.exists() and niche != "general":
                        # Niche already saved in settings.json — just confirm, no question
                        print(f"\n  {C.GREEN}✓  Niche locked: {C.BOLD}{niche}{C.RESET}  "
                              f"{C.DIM}(from accounts/{sel['folder_name']}/settings.json){C.RESET}")

                    else:
                        # New channel or niche=general: offer rich suggestion menu
                        niches      = list(NICHE_TAGS.keys())
                        # Show niche options with example keywords for each
                        niche_examples = {
                            "fitness"   : "gym, workout, transformation, weight loss, home exercise",
                            "cooking"   : "recipe, food, street food, 5-minute meal, viral dish",
                            "finance"   : "money, investing, savings, crypto, passive income",
                            "gaming"    : "gameplay, tips, highlights, BGMI, Free Fire, Xbox",
                            "motivation": "success, mindset, hustle, self-improvement, never give up",
                            "tech"      : "AI, gadgets, review, coding, startup, unboxing",
                            "education" : "facts, science, history, amazing, did you know",
                            "bhajan"    : "bhakti, kirtan, mantra, devotional, aarti, Krishna",
                            "general"   : "viral, trending, facts, tips, life hacks, DIY",
                        }
                        print(f"\n  {C.CYAN}╔══════════════════════════════════════════════════════════╗")
                        print(f"  ║  📌  SELECT NICHE FOR: {sel['real_name'][:36]:<36} ║")
                        print(f"  ╠══════════════════════════════════════════════════════════╣")
                        print(f"  ║  {C.DIM}Choose the niche that best matches this channel.{C.RESET}{C.CYAN}        ║")
                        print(f"  ║  {C.DIM}This sets hashtags, music, AI titles & content ideas.{C.RESET}{C.CYAN}   ║")
                        print(f"  ╠══════════════════════════════════════════════════════════╣{C.RESET}")
                        for idx_n, niche_opt in enumerate(niches, 1):
                            kws = niche_examples.get(niche_opt, "")
                            print(f"  {C.CYAN}║{C.RESET} {C.BOLD}{idx_n:<2}{C.RESET}  "
                                  f"{C.WHITE}{niche_opt:<12}{C.RESET}  "
                                  f"{C.DIM}{kws[:40]:<40}{C.RESET}  {C.CYAN}║{C.RESET}")
                        print(f"  {C.CYAN}╚══════════════════════════════════════════════════════════╝{C.RESET}")

                        while True:
                            raw_n = input(f"\n  Enter niche number (1-{len(niches)}), "
                                          f"or press Enter to keep 'general': ").strip()
                            if not raw_n:
                                break
                            try:
                                ni = int(raw_n)
                                if 1 <= ni <= len(niches):
                                    niche = niches[ni - 1]
                                    settings_file.write_text(
                                        json.dumps({"niche": niche}, indent=2))
                                    sel["niche"] = niche
                                    CHANNELS_DB.write_text(json.dumps(
                                        {"ts": time.time(), "channels": all_channels},
                                        indent=2))
                                    ok(f"Niche '{niche}' saved to "
                                       f"accounts/{sel['folder_name']}/settings.json")
                                    print(f"  {C.DIM}Next run will skip this question."
                                          f" Edit settings.json to change.{C.RESET}")
                                    break
                            except ValueError:
                                pass
                            print(f"  ⚠  Enter a number 1–{len(niches)} or press Enter")

                subs = int(sel.get("subs","0") or "0")
                print(f"\n  {C.GREEN}✓  Selected: {C.BOLD}{sel['real_name']}{C.RESET}")
                print(f"     {C.DIM}Subscribers: {subs:,}  |  "
                      f"Videos: {sel.get('videos','?')}  |  "
                      f"Niche: {niche}  |  "
                      f"Folder: accounts/{sel.get('folder_name','')}{C.RESET}")
                sel["niche"] = niche
                return sel
        except ValueError:
            pass

        print(f"  {C.RED}Invalid — enter a number 1–{len(all_channels)}, "
              f"[+], [R], or [Q]{C.RESET}")


# ══════════════════════════════════════════════════════════════════════════════
#  AI-POWERED 10-DAY MONETIZATION STRATEGY
#
#  Generated fresh by Gemini for each channel based on:
#    - Real subscriber count (how close to 1000 YPP target)
#    - Niche (bhajan vs gaming vs fitness etc.)
#    - Video count (new vs established channel)
#  The strategy is ALSO injected into every metadata generation call
#  so Gemini's title/description writing is guided by the current strategy.
# ══════════════════════════════════════════════════════════════════════════════

def generate_monetization_strategy(channel: dict) -> dict:
    """
    Ask Gemini to generate a personalised, adaptive 10-day monetization
    strategy for this specific channel. Returns a dict with:
      - display_lines : list of strings to show in the terminal box
      - ai_guidance   : compact string injected into every Gemini metadata prompt
      - raw           : full JSON from Gemini
    Result cached in trend_cache.json under key 'strategy_<channel_id>'.
    """
    ch_id    = channel.get("channel_id", "unknown")
    ch_name  = channel.get("real_name", "?")
    niche    = channel.get("niche", "general")
    subs     = int(channel.get("subs",  "0") or 0)
    videos   = int(channel.get("videos","0") or 0)
    need_subs = max(0, 1000 - subs)

    # Cache key — regenerate at most once per 24h per channel
    cache_file = BASE_DIR / "trend_cache.json"
    cache_key  = f"strategy_{ch_id}"
    if cache_file.exists():
        try:
            cache = json.loads(cache_file.read_text(encoding="utf-8"))
            entry = cache.get(cache_key, {})
            if time.time() - entry.get("ts", 0) < 86400:
                ok(f"Strategy cache valid for {ch_name}")
                return entry["data"]
        except Exception:
            pass

    print(f"\n  {C.CYAN}🤖 Gemini is generating your personalised strategy...{C.RESET}")

    prompt = textwrap.dedent(f"""
        You are an expert YouTube growth strategist.

        CHANNEL DATA:
          Name      : {ch_name}
          Niche     : {niche}
          Subs now  : {subs}  (need {need_subs} more to reach YouTube Partner Program)
          Videos    : {videos} uploaded so far
          Goal      : Reach 1,000 subscribers + 4,000 watch hours as fast as possible

        TASK:
        Design a personalised, adaptive 10-day content & monetization strategy
        specifically for this channel's niche and current growth stage.
        The strategy must:
        - Be SPECIFIC to the '{niche}' niche (not generic)
        - Account for the current subscriber count ({subs} subs)
        - Change methods if subs > 500 vs subs < 100 (different tactics for each stage)
        - Include content format advice (Shorts vs long video split per day)
        - Include engagement tactics for the algorithm
        - Include title/hook style recommendations for this niche

        Return ONLY valid JSON (no markdown, no explanation):
        {{
          "strategy_name": "One-line catchy name for this strategy",
          "stage": "starter|growing|near_ypp",
          "daily_plan": [
            {{
              "days"   : "Day 1-2",
              "action" : "What to do",
              "why"    : "Why this works for {niche} at {subs} subs",
              "content_format": "e.g. 3 Shorts + 0 long",
              "hook_style": "e.g. curiosity gap or emotional trigger"
            }}
          ],
          "title_approach" : "How to write titles for {niche} at this stage",
          "hook_approach"  : "Best 3-second hook style for {niche} Shorts",
          "engagement_tip" : "Single most important engagement action this week",
          "ai_guidance"    : "2-3 sentence instruction for the AI writing titles & descriptions — what tone, what angle, what emotion to target for {niche} channel with {subs} subs"
        }}
    """).strip()

    try:
        raw_text = gemini(prompt).replace("```json","").replace("```","").strip()
        data     = json.loads(raw_text)
    except Exception as e:
        log.warning(f"[Strategy] Gemini error: {e} — using fallback")
        data = {
            "strategy_name" : f"{niche.title()} Fast-Track to YPP",
            "stage"         : "starter" if subs < 100 else "growing" if subs < 500 else "near_ypp",
            "daily_plan"    : [
                {"days":"Day 1-2","action":"Upload 3 Shorts/day in viral copy mode",
                 "why":"Jump-start algorithm","content_format":"3 Shorts","hook_style":"curiosity gap"},
                {"days":"Day 3-4","action":"3 Shorts + 1 long video (8-15min)",
                 "why":"Build watch hours","content_format":"3 Shorts + 1 long","hook_style":"story"},
                {"days":"Day 5-6","action":"Trending topic Shorts + reply ALL comments in 2h",
                 "why":"Comments = 5x algorithm weight","content_format":"3 Shorts","hook_style":"question"},
                {"days":"Day 7-8","action":"3 Shorts + 1 long video",
                 "why":"Sustain watch hours","content_format":"3 Shorts + 1 long","hook_style":"emotional"},
                {"days":"Day 9-10","action":"3 Shorts/day, 12h gap, pin comment on each",
                 "why":"Push final sub count","content_format":"3 Shorts","hook_style":"FOMO"},
            ],
            "title_approach" : f"Curiosity-gap titles for {niche}, 2 emojis max, end with #shorts",
            "hook_approach"  : "First 2 seconds: bold claim or shocking visual",
            "engagement_tip" : "Reply to every comment within 2 hours of posting",
            "ai_guidance"    : (f"Write titles for a {niche} channel with {subs} subscribers. "
                                f"Use emotional hooks, curiosity gaps, and niche-specific language. "
                                f"Prioritise virality and subscriber growth over brand polish."),
        }

    # Build display lines for the terminal box
    plan    = data.get("daily_plan", [])
    display = [
        f"Strategy  : {data.get('strategy_name','')[:56]}",
        f"Channel   : {ch_name[:50]}",
        f"Stage     : {data.get('stage','?').upper()}  |  Subs: {subs:,}  (need {need_subs:,} more)",
        f"AI Tip    : {data.get('engagement_tip','')[:56]}",
        "",
        f"TITLE APPROACH: {data.get('title_approach','')[:56]}",
        f"HOOK STYLE    : {data.get('hook_approach','')[:56]}",
        "",
    ]
    for p in plan:
        display.append(f"{p.get('days','?'):<8}  {p.get('content_format',''):<18}  "
                       f"{p.get('action','')[:28]}")
        display.append(f"         WHY: {p.get('why','')[:54]}")
        display.append("")

    result = {
        "display_lines": display,
        "ai_guidance"  : data.get("ai_guidance", ""),
        "title_approach": data.get("title_approach", ""),
        "hook_approach" : data.get("hook_approach", ""),
        "raw"           : data,
    }

    # Cache the result
    try:
        cache = json.loads(cache_file.read_text(encoding="utf-8")) if cache_file.exists() else {}
    except Exception:
        cache = {}
    cache[cache_key] = {"ts": time.time(), "data": result}
    # Don't overwrite niche trend data — merge
    if "niche" in cache and "data" in cache:
        trend_entry = {"niche": cache.pop("niche"), "ts": cache.pop("ts", 0),
                       "data": cache.pop("data", {})}
        cache["trend"] = trend_entry
    cache_file.write_text(json.dumps(cache, indent=2), encoding="utf-8")
    ok(f"Strategy generated by Gemini AI — cached 24h")
    return result


def show_monetization_strategy(channel: dict, strategy: dict):
    """Display the AI-generated strategy in the terminal."""
    box(f"🎯  AI MONETIZATION STRATEGY — {channel.get('real_name','')[:40]}",
        strategy["display_lines"],
        "Powered by Gemini AI — adapts to your channel's stage")
    input("  Press Enter to continue with automation...")

# ══════════════════════════════════════════════════════════════════════════════
#  TREND RESEARCH  (Gemini + YouTube Data API)
# ══════════════════════════════════════════════════════════════════════════════

def research_niche(niche: str) -> dict:
    hdr(f"Phase 1 — Trend Research: '{niche}'")

    cache_file = BASE_DIR / "trend_cache.json"
    if cache_file.exists():
        try:
            c = json.loads(cache_file.read_text(encoding="utf-8"))
            if c.get("niche") == niche and time.time() - c.get("ts",0) < 21600:
                ok(f"Trend cache valid ({int((time.time()-c['ts'])/60)}min old)")
                return c["data"]
        except Exception:
            pass

    viral_titles  = []
    trending_tags = []

    yt_key = os.getenv("YT_DATA_API_KEY", "")
    if yt_key:
        try:
            params = urllib.parse.urlencode({
                "part":"snippet","q":f"viral {niche} shorts","type":"video",
                "videoDuration":"short","order":"viewCount","maxResults":"10",
                "key": yt_key,
                "publishedAfter":(datetime.now(timezone.utc).replace(tzinfo=None)-timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            })
            data = json.loads(http_get(f"https://www.googleapis.com/youtube/v3/search?{params}"))
            for item in data.get("items",[]):
                viral_titles.append(item["snippet"].get("title",""))
            ok(f"YouTube API: {len(viral_titles)} viral videos found")
        except Exception as e:
            log.info(f"[Research] YouTube API: {e}")

    progress_bar(0, 2, "Gemini analysing niche...")
    prompt = textwrap.dedent(f"""
        YouTube Shorts expert for '{niche}' niche.
        {'Viral titles found: ' + chr(10).join(viral_titles[:6]) if viral_titles else ''}
        Return ONLY valid JSON (no markdown):
        {{
          "hot_topics"    : ["5 specific topics trending RIGHT NOW in {niche}"],
          "title_formulas": ["3 proven viral title formulas with examples"],
          "hook_patterns" : ["3 first-3-second hooks that stop scrolling"],
          "trending_tags" : ["10 hashtags trending in {niche} right now"],
          "content_ideas" : ["5 specific video ideas for {niche} channel"]
        }}
    """).strip()
    progress_bar(1, 2, "Gemini thinking...")
    try:
        raw  = gemini(prompt).replace("```json","").replace("```","").strip()
        data = json.loads(raw)
        trending_tags = list(dict.fromkeys(data.get("trending_tags",[])))[:15]
    except Exception as e:
        log.warning(f"[Research] Gemini: {e}")
        data = {"hot_topics":[f"Top {niche} tips"],"title_formulas":[],
                "hook_patterns":[],"trending_tags":NICHE_TAGS.get(niche,[]),
                "content_ideas":[]}
    progress_bar(2, 2, "Research complete")

    result = {
        "niche": niche, "viral_titles": viral_titles[:8],
        "trending_tags": trending_tags,
        "hot_topics": data.get("hot_topics",[]),
        "title_formulas": data.get("title_formulas",[]),
        "hook_patterns": data.get("hook_patterns",[]),
        "content_ideas": data.get("content_ideas",[]),
        "strategy_guidance": "",   # filled in by main() after generate_monetization_strategy()
    }
    cache_file.write_text(json.dumps({"niche":niche,"ts":time.time(),"data":result},indent=2))
    ok(f"Research done — {len(result['hot_topics'])} topics, {len(trending_tags)} tags")
    if result["hot_topics"]:
        print(f"  Hot topics: {' | '.join(result['hot_topics'][:3])}")
    return result

# ══════════════════════════════════════════════════════════════════════════════
#  AI METADATA
# ══════════════════════════════════════════════════════════════════════════════

def generate_metadata(video_title: str, transcript: str, idx: int,
                      niche: str, research: dict, mode: str = "shorts",
                      lang: str = "english",
                      original_title: str = "", original_desc: str = "",
                      title_style: str = "fresh") -> dict:
    """
    Generate AI metadata with language + title style control.

    lang        : "english" or "hindi"
    original_title : fetched from the source video (yt-dlp)
    original_desc  : fetched from the source video (yt-dlp)
    title_style : "enhance" = keep original meaning, improve format
                  "fresh"   = new title/desc with same topic but different angle
    """
    vt   = "\n".join(f"  • {t}" for t in research.get("viral_titles",[])[:5])
    tp   = "\n".join(f"  • {t}" for t in research.get("hot_topics",[])[:4])
    tags = get_tags(niche, idx, research.get("trending_tags",[]))

    if mode == "shorts":
        title_rule = "Max 60 chars, curiosity gap, 1-2 emojis, MUST end with #shorts"
        desc_rule  = "Hook + value + CTA + #shorts in hashtags at end"
    else:
        title_rule = "Max 100 chars, compelling, NO #shorts anywhere, for Videos section"
        desc_rule  = "Hook + value + CTA + hashtags at end — NO #shorts tag"

    # Language instruction
    if lang == "hindi":
        lang_inst = ("Write EVERYTHING (title, description, hook, comment) in HINDI (Devanagari script). "
                     "Use natural Hindi that YouTube viewers in India understand. "
                     "Keep #shorts and hashtags in English.")
    else:
        lang_inst = "Write in clear, engaging English."

    # Title/description approach
    if title_style == "enhance" and original_title:
        style_inst = textwrap.dedent(f"""
            ORIGINAL VIDEO TITLE: {original_title}
            ORIGINAL DESCRIPTION: {original_desc[:400] if original_desc else "(none)"}

            TASK: ENHANCE the original title and description.
            - Keep the EXACT SAME meaning and topic
            - Improve the format: add curiosity gap, better emojis, stronger hook
            - Do NOT change what the video is about
            - Title should feel like an upgrade of the original, not a replacement
        """).strip()
    else:
        style_inst = textwrap.dedent(f"""
            ORIGINAL VIDEO TITLE: {original_title or video_title}

            TASK: Write a FRESH title and description.
            - Same topic/niche as the original
            - Completely different angle and wording
            - Use curiosity gap, trending formats, viral patterns
            - Feel different from the original while covering the same subject
        """).strip()

    prompt = textwrap.dedent(f"""
        You are a top YouTube growth expert for the '{niche}' niche.
        {lang_inst}

        ALGORITHM RULES:
        • First 3 seconds hook = #1 retention signal
        • Comments = 5x weight vs likes — end description with a question
        • Curiosity-gap titles = 2x higher CTR
        • {title_rule}

        {style_inst}

        VIRAL TITLES in this niche: {vt or "(use niche knowledge)"}
        HOT TOPICS: {tp or "(use niche knowledge)"}
        TRANSCRIPT SNIPPET: {transcript[:300] or "(none)"}
        CLIP NUMBER: {idx + 1}
        GROWTH STRATEGY GUIDANCE: {research.get('strategy_guidance','') or '(standard growth mode)'}
        TITLE APPROACH: {research.get('title_approach','') or '(curiosity gap titles)'}
        HOOK APPROACH: {research.get('hook_approach','') or '(bold claim in first 2 seconds)'}

        Return ONLY valid JSON — no markdown, no explanation:
        {{
          "title"          : "{title_rule}",
          "description"    : "{desc_rule}",
          "tags"           : {json.dumps(tags)},
          "hook_overlay"   : "3-6 word {'Hindi' if lang=='hindi' else 'English'} hook for first 3 seconds on screen",
          "mood"           : "energetic|happy|inspiring|motivational|upbeat|calm|dramatic",
          "title_alt"      : "Alternate title — different angle, same topic",
          "comment_prompt" : "Pinnable question in {'Hindi' if lang=='hindi' else 'English'} to drive comments"
        }}
    """).strip()

    try:
        raw  = gemini(prompt).replace("```json","").replace("```","").strip()
        data = json.loads(raw)
        data["tags"] = tags
        return data

    except Exception as e:
        log.warning(f"[AI] Metadata error: {e}")

        # ── Smart fallback — niche-specific, NOT raw filename ─────────────────
        suffix = " #shorts" if mode == "shorts" else ""
        hot    = research.get("hot_topics", [])
        topic  = hot[idx % len(hot)] if hot else niche.title()

        # If we have original title, use enhanced version of it
        if original_title and len(original_title) > 5:
            base = original_title[:50].strip()
            if lang == "hindi":
                fallback_title = f"{base} 🙏{suffix}" if "भजन" in base or "कीर्तन" in base else f"{base} 🔥{suffix}"
            else:
                fallback_title = f"{base} 🔥{suffix}"
        else:
            # Niche templates
            if lang == "hindi":
                niche_titles = {
                    "bhajan"    : [f"इस भजन ने मन को छू लिया 🙏{suffix}", f"जीवन बदल देगा यह भजन ✨{suffix}"],
                    "fitness"   : [f"इस एक्सरसाइज से जीवन बदल गया 💪{suffix}", f"30 दिन में फर्क देखें 🔥{suffix}"],
                    "cooking"   : [f"यह रेसिपी वायरल हो गई 🍳{suffix}", f"5 मिनट में बनाएं {topic[:20]} 😍{suffix}"],
                    "motivation": [f"यह सुनकर जिंदगी बदल जाएगी 💯{suffix}", f"हार मत मानो — देखो यह 🔥{suffix}"],
                    "education" : [f"यह सच जानकर हैरान हो जाएंगे 🤯{suffix}", f"अद्भुत तथ्य — {topic[:25]} 💡{suffix}"],
                }
            else:
                niche_titles = {
                    "bhajan"    : [f"This bhajan will touch your soul 🙏{suffix}", f"Divine music that brings peace ✨{suffix}"],
                    "fitness"   : [f"This workout changed everything 💪{suffix}", f"30-day transformation results 🔥{suffix}"],
                    "cooking"   : [f"This recipe is going viral 🍳{suffix}", f"5-minute {topic[:25]} recipe 😍{suffix}"],
                    "motivation": [f"Watch this when you want to quit 💯{suffix}", f"This will change your mindset 🔥{suffix}"],
                    "gaming"    : [f"No one expected this play 🎮{suffix}", f"This trick broke the game 😱{suffix}"],
                    "tech"      : [f"This tech will blow your mind 🤯{suffix}", f"Hidden feature nobody knows 💡{suffix}"],
                    "finance"   : [f"This money tip changed my life 🚀{suffix}", f"How to grow money fast 💰{suffix}"],
                    "education" : [f"You won't believe this fact 🤯{suffix}", f"{topic[:35]} — amazing! 💡{suffix}"],
                }
            options       = niche_titles.get(niche.lower(), [f"{topic[:40]} 🔥{suffix}", f"Must watch 👀{suffix}"])
            fallback_title = options[idx % len(options)]

        return {
            "title"         : fallback_title[:100],
            "description"   : f"Watch till end 🔥\n\n{topic}\n\nLike & Subscribe 🔔\n\nComment below 👇",
            "tags"          : tags,
            "hook_overlay"  : (topic[:30] if topic else niche.title()),
            "mood"          : "energetic",
            "title_alt"     : fallback_title[:100],
            "comment_prompt": ("आपको यह कैसा लगा? कमेंट करें 👇" if lang=="hindi"
                               else "What did you think? Comment below 👇"),
        }

# ══════════════════════════════════════════════════════════════════════════════
#  VIDEO HELPERS
=======
def scrape_viral_shorts(channel_url: str, max_shorts: int = 10) -> list[dict]:
    """
    Download the top 10 most-viewed Shorts from a channel using yt-dlp.
    Extract their title, description, tags and store in viral_learnings.json.
    Returns list of metadata dicts.
    """
    task_header(f"Scraping top {max_shorts} viral Shorts from channel")
    viral_dir = BASE_DIR / "viral_scrape"
    viral_dir.mkdir(exist_ok=True)

    # Get video info only (no download) sorted by views
    info_cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--playlist-end", str(max_shorts * 3),   # grab more, filter to Shorts
        "--match-filter", "duration < 65",        # Shorts are under 65s
        "--print", "%(id)s|||%(title)s|||%(view_count)s|||%(description)s",
        "--no-warnings",
        channel_url
    ]

    task_header("Fetching viral Shorts metadata")
    try:
        result = subprocess.run(info_cmd, capture_output=True, text=True, timeout=120)
        lines  = [l for l in result.stdout.strip().split("\n") if "|||" in l]
    except Exception as e:
        log.warning(f"[Viral] Could not scrape channel: {e}")
        return []

    # Parse and sort by views
    entries = []
    for line in lines:
        parts = line.split("|||")
        if len(parts) >= 3:
            try:
                entries.append({
                    "id"         : parts[0].strip(),
                    "title"      : parts[1].strip(),
                    "views"      : int(parts[2].strip() or 0),
                    "description": parts[3].strip() if len(parts) > 3 else "",
                })
            except Exception:
                pass

    entries.sort(key=lambda x: x["views"], reverse=True)
    top = entries[:max_shorts]

    if not top:
        log.warning("[Viral] No Shorts found on this channel")
        return []

    # Now download the actual video files
    print(f"\n  Found {len(top)} viral Shorts. Downloading...")
    downloaded = []
    for i, entry in enumerate(top):
        progress_bar(i, len(top), f"Downloading Short {i+1}/{len(top)}")
        url = f"https://www.youtube.com/shorts/{entry['id']}"
        out = viral_dir / f"viral_{i+1}_{entry['id']}.mp4"
        if not out.exists():
            try:
                subprocess.run([
                    "yt-dlp",
                    "--format", "bestvideo[height<=1080]+bestaudio/best",
                    "--merge-output-format", "mp4",
                    "--output", str(out),
                    "--no-warnings", url
                ], check=True, capture_output=True, timeout=120)
            except Exception as e:
                log.warning(f"[Viral] Could not download {url}: {e}")
                continue
        entry["local_path"] = str(out)
        downloaded.append(entry)
    progress_bar(len(top), len(top), "Download complete")

    # Save learnings
    existing = []
    if VIRAL_DB.exists():
        existing = json.loads(VIRAL_DB.read_text(encoding="utf-8"))
    existing.extend(downloaded)
    VIRAL_DB.write_text(json.dumps(existing, indent=2), encoding="utf-8")

    task_done(f"Scraped {len(downloaded)} viral Shorts — learnings saved")
    return downloaded


def load_viral_learnings() -> list[dict]:
    if VIRAL_DB.exists():
        return json.loads(VIRAL_DB.read_text(encoding="utf-8"))
    return []

# ══════════════════════════════════════════════════════════════════════════════
#  HTTP HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def http_get(url: str, headers: dict = None) -> bytes:
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "ShortsBot/5.0"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read()

def http_post_json(url: str, payload: dict, headers: dict) -> dict:
    data = json.dumps(payload).encode()
    req  = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.loads(r.read())

# ══════════════════════════════════════════════════════════════════════════════
#  MODULE 1 — MUSIC  (Jamendo → Bensound → Pixabay)
# ══════════════════════════════════════════════════════════════════════════════

def ensure_starter_music():
    """Pre-download 20 free tracks from Bensound and Pixabay on first run."""
    MUSIC_DIR.mkdir(parents=True, exist_ok=True)
    all_tracks = CONFIG["bensound_tracks"] + CONFIG["pixabay_tracks"]
    total = len(all_tracks)
    task_header(f"Music library — downloading {total} free tracks")
    for i, t in enumerate(all_tracks):
        progress_bar(i, total, t["name"])
        dest = MUSIC_DIR / t["name"]
        if dest.exists():
            continue
        try:
            dest.write_bytes(http_get(t["url"]))
        except Exception as e:
            log.warning(f"[Music] Could not download {t['name']}: {e}")
    progress_bar(total, total, "Music library ready")
    task_done(f"Music library ready — {len(list(MUSIC_DIR.glob('*.mp3')))} tracks available")


def fetch_jamendo_track(mood: str = "energetic") -> Path | None:
    dest = MUSIC_DIR / f"jamendo_{mood}.mp3"
    if dest.exists():
        return dest
    MUSIC_DIR.mkdir(parents=True, exist_ok=True)
    params = urllib.parse.urlencode({
        "client_id": JAMENDO_ID, "format": "json", "limit": "10",
        "tags": mood, "audioformat": "mp32", "order": "popularity_total",
    })
    try:
        data    = json.loads(http_get(f"https://api.jamendo.com/v3.0/tracks/?{params}"))
        results = data.get("results", [])
        if not results:
            return _any_cached_music()
        track     = random.choice(results[:5])
        audio_url = track.get("audio") or track.get("audiodownload")
        if not audio_url:
            return _any_cached_music()
        log.info(f"[Music] Jamendo: {track['name']} by {track['artist_name']}")
        dest.write_bytes(http_get(audio_url))
        return dest
    except Exception as e:
        log.warning(f"[Music] Jamendo error: {e}")
        return _any_cached_music()


def _any_cached_music() -> Path | None:
    files = list(MUSIC_DIR.glob("*.mp3")) + list(MUSIC_DIR.glob("*.m4a"))
    return random.choice(files) if files else None

# ══════════════════════════════════════════════════════════════════════════════
#  MODULE 2 — CAPTIONS  (Groq Whisper)
# ══════════════════════════════════════════════════════════════════════════════

def extract_audio_chunk(video_path: Path, start: int, duration: int) -> Path:
    out = video_path.parent / f"_chunk_{start}.mp3"
    subprocess.run([
        "ffmpeg", "-y", "-ss", str(start), "-i", str(video_path),
        "-t", str(duration), "-ac", "1", "-ar", "16000",
        "-c:a", "libmp3lame", "-b:a", "64k", str(out)
    ], check=True, capture_output=True)
    return out


def transcribe_groq(audio_path: Path) -> list[dict]:
    import mimetypes
    boundary    = "----ShortsBot"
    audio_bytes = audio_path.read_bytes()
    mime        = mimetypes.guess_type(str(audio_path))[0] or "audio/mpeg"
    body  = f'--{boundary}\r\nContent-Disposition: form-data; name="model"\r\n\r\nwhisper-large-v3-turbo\r\n'
    body += f'--{boundary}\r\nContent-Disposition: form-data; name="response_format"\r\n\r\nverbose_json\r\n'
    body += f'--{boundary}\r\nContent-Disposition: form-data; name="timestamp_granularities[]"\r\n\r\nword\r\n'
    body += f'--{boundary}\r\nContent-Disposition: form-data; name="language"\r\n\r\nen\r\n'
    body += (f'--{boundary}\r\nContent-Disposition: form-data; name="file"; '
             f'filename="{audio_path.name}"\r\nContent-Type: {mime}\r\n\r\n')
    body_bytes = body.encode() + audio_bytes + f'\r\n--{boundary}--\r\n'.encode()
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type" : f"multipart/form-data; boundary={boundary}",
        "User-Agent"   : "ShortsBot/5.0",
    }
    try:
        req = urllib.request.Request(
            "https://api.groq.com/openai/v1/audio/transcriptions",
            data=body_bytes, headers=headers, method="POST"
        )
        with urllib.request.urlopen(req, timeout=60) as r:
            result = json.loads(r.read())
        return result.get("words", [])
    except Exception as e:
        log.warning(f"[Captions] Groq error: {e}")
        return []


def build_srt(words: list[dict], max_chars: int = 22) -> str:
    """
    Group words into short subtitle lines — max 22 chars each (3-4 words).
    Short lines look cleaner on vertical 9:16 Shorts format.
    """
    if not words:
        return ""
    def t(s: float) -> str:
        h=int(s//3600); m=int((s%3600)//60); sec=s%60
        return f"{h:02d}:{m:02d}:{sec:06.3f}".replace(".",",")
    lines, cur, t0 = [], [], None
    for w in words:
        if t0 is None: t0 = w["start"]
        cur.append(w["word"])
        # Break at max_chars OR at natural punctuation
        joined = " ".join(cur)
        if len(joined) >= max_chars or joined.rstrip().endswith((",",".","!","?")):
            lines.append((t0, w["end"], joined.strip()))
            cur, t0 = [], None
    if cur and t0 is not None:
        lines.append((t0, words[-1]["end"], " ".join(cur).strip()))
    return "".join(f"{i}\n{t(s)} --> {t(e)}\n{txt}\n\n"
                   for i,(s,e,txt) in enumerate(lines,1))


def burn_srt(src: Path, dst: Path, srt_path: Path):
    """
    Burn SRT captions with:
    - FontSize 18 (fits 9:16 without dominating frame)
    - Semi-transparent dark box behind text for readability
    - Bold white text, black outline
    - Centred near bottom with comfortable margin
    """
    srt_esc = str(srt_path).replace("\\","/").replace(":","\\:")
    subprocess.run([
        "ffmpeg", "-y", "-i", str(src),
        "-vf", (
            f"subtitles='{srt_esc}':"
            f"force_style='"
            f"FontName=Arial,"
            f"FontSize=18,"            # ← clean small size for 1080×1920
            f"Bold=1,"
            f"PrimaryColour=&H00FFFFFF,"   # white text
            f"OutlineColour=&H00000000,"   # black outline
            f"BackColour=&H80000000,"      # semi-transparent black box
            f"BorderStyle=4,"              # 4 = opaque box style
            f"Outline=1,"
            f"Shadow=0,"
            f"Alignment=2,"               # bottom-centre
            f"MarginV=120'"               # lift from very bottom
        ),
        "-c:a", "copy", str(dst)
    ], check=True, capture_output=True)


def burn_placeholder(src: Path, dst: Path, text: str):
    """Fallback static caption — same small size with box background."""
    safe = text.replace("'","").replace(":","").replace("\\","")[:40]
    # drawtext with box background, size 18, bottom-centre
    subprocess.run([
        "ffmpeg", "-y", "-i", str(src),
        "-vf", (
            f"drawtext=text='{safe}':"
            f"fontfile='{WINDOWS_FONT}':"
            f"fontsize=18:"
            f"fontcolor=white:"
            f"borderw=2:bordercolor=black:"
            f"box=1:boxcolor=black@0.55:boxborderw=10:"
            f"x=(w-text_w)/2:y=h-text_h-120"
        ),
        "-codec:a", "copy", str(dst)
    ], check=True, capture_output=True)

# ══════════════════════════════════════════════════════════════════════════════
#  MODULE 3 — AI METADATA  (Gemini 2.5 Flash)
#  Learns from viral Shorts if available
# ══════════════════════════════════════════════════════════════════════════════

# Niche-specific hashtag pools — unique combinations per video
NICHE_HASHTAGS = {
    "fitness"    : ["gym","workout","fitness","health","fitnessmotivation","bodybuilding",
                    "weightloss","exercise","fit","getfit","musclebuilding","cardio",
                    "personaltrainer","healthylifestyle","fitlife"],
    "cooking"    : ["food","recipe","cooking","foodie","chef","homecooking","easyrecipe",
                    "delicious","tasty","kitchen","foodlover","mealprep","healthyfood",
                    "cookingvideo","instafood"],
    "finance"    : ["money","investing","finance","wealth","personalfinance","stockmarket",
                    "crypto","business","entrepreneur","richlife","financetips","trading",
                    "passiveincome","financialfreedom","invest"],
    "gaming"     : ["gaming","gamer","gameplay","games","videogames","ps5","xbox","twitch",
                    "streamer","gamingcommunity","pcgaming","mobilegaming","esports",
                    "gamingnews","gaminglife"],
    "motivation" : ["motivation","inspire","success","mindset","hustle","grind","goals",
                    "positivity","selfimprovement","mindfulness","growth","believe",
                    "winning","nevergiveup","dailymotivation"],
    "general"    : ["facts","didyouknow","interesting","amazing","knowledge","learn",
                    "education","tips","lifehacks","howto","tutorial","diy","hack",
                    "satisfying","mindblowing"],
}

def get_niche_tags(niche: str, clip_index: int, count: int = 8) -> list[str]:
    """Pick a different random subset of niche tags for each clip."""
    pool = NICHE_HASHTAGS.get(niche.lower(), NICHE_HASHTAGS["general"])
    random.seed(clip_index * 7 + len(pool))   # deterministic but varied
    chosen = random.sample(pool, min(count, len(pool)))
    random.seed()
    return chosen


def generate_metadata(video_title: str, transcript: str,
                      clip_index: int, niche: str = "general") -> dict:
    """
    Ask Gemini to write viral metadata, also feeding it viral learnings
    so it can imitate what works on the platform.
    """
    # Pull viral learnings context
    learnings = load_viral_learnings()
    viral_ctx = ""
    if learnings:
        samples = random.sample(learnings, min(3, len(learnings)))
        viral_ctx = "TOP VIRAL SHORTS on this niche (learn from their style):\n"
        for s in samples:
            viral_ctx += f"  Title: {s.get('title','')}\n"
            viral_ctx += f"  Views: {s.get('views',0):,}\n\n"

    niche_tags = get_niche_tags(niche, clip_index)

    prompt = textwrap.dedent(f"""
        You are a top YouTube Shorts viral copywriter for the '{niche}' niche.

        {viral_ctx}
        Source video  : {video_title}
        Clip number   : {clip_index + 1}
        Transcript    : {transcript[:600] if transcript else "(no transcript)"}
        Suggested tags: {', '.join(niche_tags)}

        Write MAXIMUM engagement metadata. Study the viral examples above.
        Return ONLY valid JSON — no markdown fences, no extra text:

        {{
          "title"           : "irresistible hook title max 80 chars, emoji, ends #shorts — make it curiosity-driven or shocking",
          "description"     : "Write 4 paragraphs: 1) Strong hook that continues the title 2) Key value/insight from the video 3) Why viewer should watch more 4) Strong CTA to subscribe + like. End with 15 hashtags mixing popular and niche tags on a new line.",
          "tags"            : ["tag1","tag2",...],
          "caption_overlay" : "5-7 word punchy on-screen text that hooks viewer in first second",
          "mood"            : "one of: energetic happy inspiring motivational upbeat calm dramatic",
          "title_variants"  : ["alternative title 1", "alternative title 2"]
        }}
    """).strip()

    # Use stable model name + key as header (not query param) to avoid 404
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
    try:
        log.info(f"[AI] Gemini writing metadata for clip {clip_index+1}...")
        resp = http_post_json(url, {"contents": [{"parts": [{"text": prompt}]}]},
                              {"Content-Type": "application/json",
                               "x-goog-api-key": GEMINI_API_KEY})
        raw  = resp["candidates"][0]["content"]["parts"][0]["text"].strip()
        raw  = raw.replace("```json","").replace("```","").strip()
        data = json.loads(raw)

        # Merge base tags + niche tags + AI tags (deduplicated)
        base   = CONFIG["youtube"]["base_tags"]
        ai_tags = data.get("tags", [])
        merged = list(dict.fromkeys(base + niche_tags + ai_tags))[:20]
        data["tags"] = merged

        log.info(f"[AI] Title: {data.get('title','')[:65]}")
        return data
    except Exception as e:
        log.warning(f"[AI] Gemini error: {e} — using template")
        return _template_metadata(video_title, clip_index, niche)


def _template_metadata(title: str, idx: int, niche: str) -> dict:
    tags = CONFIG["youtube"]["base_tags"] + get_niche_tags(niche, idx)
    return {
        "title"           : f"{title[:52]} 🔥 Part {idx+1} #shorts",
        "description"     : f"Watch this amazing clip!\n\nLike & subscribe 🔔\n\n#shorts #viral #trending",
        "tags"            : tags,
        "caption_overlay" : title[:30],
        "mood"            : "energetic",
        "title_variants"  : [],
    }

# ══════════════════════════════════════════════════════════════════════════════
#  VIDEO PROCESSING  (lossless quality)
>>>>>>> 64497acc2905e2ab02e72faaffb871464a15f9a7
# ══════════════════════════════════════════════════════════════════════════════

def get_duration(path: Path) -> float:
    cmd = ["ffprobe","-v","error","-show_entries","format=duration","-of","json",str(path)]
    return float(json.loads(subprocess.run(cmd,capture_output=True,text=True).stdout)["format"]["duration"])

<<<<<<< HEAD
def calculate_plan(path: Path, transcript: str = "", is_viral: bool = False) -> dict:
    secs = get_duration(path)
    if secs < 120:
        if is_viral and secs > 12:
            import random
            if random.random() < 0.5:
                n, d, r = 1, min(int(secs), 58), f"Full viral ({min(int(secs), 58)}s)"
            else:
                max_clip = min(58, int(secs) - 2)
                d = random.randint(10, max_clip)
                n, r = 1, f"Random viral clip ({d}s)"
        else:
            n, d, r = 1, min(int(secs), 58), f"{secs/60:.1f}min → 1 Short"
    elif secs < 360:  n,d,r = 2, 45,  f"{secs/60:.1f}min → 2×45s Shorts"
    elif secs < 600:  n,d,r = 3, 50,  f"{secs/60:.1f}min → 3×50s Shorts"
    elif secs < 1200: n,d,r = 4, 55,  f"{secs/60:.1f}min → 4×55s Shorts"
    else:             n,d,r = 5, 58,  f"{secs/60:.0f}min → 5×58s Shorts"
    if transcript:
        t = transcript.lower()
        if any(w in t for w in ["tutorial","how to","step","guide","learn"]):
            d = min(d+5,58); r += " (+5s tutorial)"
        elif any(w in t for w in ["funny","laugh","joke","prank"]):
            d = max(d-5,20); r += " (-5s comedy)"
    est = "95%+" if d<=30 else "90%+" if d<=45 else "80%+"
    return {"num":n,"dur":d,"reason":r,"completion":est}

def detect_highlights(path: Path, n: int, dur: int) -> list:
=======

def detect_highlights(path: Path, num: int = 3) -> list[tuple]:
>>>>>>> 64497acc2905e2ab02e72faaffb871464a15f9a7
    try:
        import numpy as np
        from scipy.signal import find_peaks
        cmd   = ["ffmpeg","-i",str(path),"-ac","1","-ar","8000","-f","f32le","-","-loglevel","error"]
        audio = np.frombuffer(subprocess.run(cmd,capture_output=True).stdout, dtype=np.float32)
<<<<<<< HEAD
        w = 8000
        e = np.array([np.sqrt(np.mean(audio[i:i+w]**2)) for i in range(0,len(audio)-w,w)])
        peaks,_ = find_peaks(e, height=np.percentile(e,70), distance=30)
        clips = [(max(0,p-dur//2), max(0,p-dur//2)+dur) for p in peaks[:n]]
        if clips: return clips
    except ImportError: pass
    total = get_duration(path); step = total/(n+1)
    return [(int(step*i), int(step*i)+dur) for i in range(1,n+1)]

def crop_vertical(src: Path, dst: Path, start: int, end: int):
    """9:16 crop → Shorts feed."""
    dur = end - start
    try:
        fps_d = json.loads(subprocess.run(["ffprobe","-v","error","-select_streams","v:0",
            "-show_entries","stream=r_frame_rate","-of","json",str(src)],
            capture_output=True,text=True).stdout)
        nn,dd = fps_d["streams"][0]["r_frame_rate"].split("/")
        tf = max(1, int(dur*float(nn)/float(dd)))
    except: tf = dur*30
    cmd = ["ffmpeg","-y","-ss",str(start),"-i",str(src),"-t",str(dur),
           "-vf","scale=iw*max(1080/iw\\,1920/ih):ih*max(1080/iw\\,1920/ih),crop=1080:1920",
           "-c:v","libx264","-crf",str(os.getenv("VIDEO_CRF",18)),"-preset","slow",
           "-profile:v","high","-level","4.1","-pix_fmt","yuv420p",
           "-c:a","aac","-b:a","192k","-progress","pipe:1","-nostats",str(dst)]
    proc = subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True)
    for line in proc.stdout:
        if line.startswith("frame="):
            try: progress_bar(min(int(line.split("=")[1]),tf),tf,"Encoding 9:16 Short")
            except: pass
    proc.wait()
    progress_bar(tf,tf,"Encoding 9:16 Short")

def encode_original_aspect(src: Path, dst: Path, start: int = 0, end: int = 0):
    """Encode keeping original aspect ratio → Videos section (NOT Shorts)."""
    cmd = ["ffmpeg","-y"]
    if start > 0: cmd += ["-ss",str(start)]
    cmd += ["-i",str(src)]
    if end > start: cmd += ["-t",str(end-start)]
    cmd += ["-c:v","libx264","-crf",str(os.getenv("VIDEO_CRF",18)),
            "-preset","slow","-c:a","aac","-b:a","192k",str(dst)]
    subprocess.run(cmd,check=True,capture_output=True)

def random_video_clips(src: Path, title_base: str) -> list:
    """
    Cut 2-5 random clips of 1-3 minutes from a big video.
    Keeps ORIGINAL aspect ratio → goes to Videos section.
    """
    VIDEOS_DIR.mkdir(parents=True,exist_ok=True)
    total   = get_duration(src)
    if total < 120:
        out = VIDEOS_DIR / f"{title_base}_clip_1.mp4"
        encode_original_aspect(src, out)
        return [out]
    n_clips  = 2 if total<300 else 3 if total<600 else 4 if total<1200 else 5
    min_len, max_len = 60, min(180, int(total)-60)
    clips = []; used = []
    for i in range(n_clips):
        clip_dur = random.randint(min_len, max_len)
        for _ in range(20):
            start = random.randint(0, max(0, int(total)-clip_dur))
            if not any(abs(start-u)<clip_dur for u in used):
                used.append(start); break
        out = VIDEOS_DIR / f"{title_base}_clip_{i+1}_{clip_dur}s.mp4"
        progress_bar(i,n_clips,f"Clip {i+1}/{n_clips} ({clip_dur}s)")
        encode_original_aspect(src,out,start,start+clip_dur)
        clips.append(out)
    progress_bar(n_clips,n_clips,"Video clips done")
    ok(f"Created {len(clips)} video clips from {int(total)}s source")
    return clips

def mix_music(src: Path, dst: Path, track: Path | None):
    vol = float(os.getenv("MUSIC_VOLUME", 0.10))
    if not track: shutil.copy(src,dst); return
    dur = get_duration(src)
    subprocess.run([
        "ffmpeg","-y","-i",str(src),"-stream_loop","-1","-i",str(track),
        "-filter_complex",f"[1:a]volume={vol},atrim=0:{dur}[m];[0:a][m]amix=inputs=2:duration=first[a]",
        "-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","192k",str(dst)
    ],check=True,capture_output=True)

# ── Captions ────────────────────────────────────────────────────────────────

def extract_audio(path: Path, start: int, dur: int) -> Path:
    out = path.parent / f"_chunk_{start}.mp3"
    subprocess.run(["ffmpeg","-y","-ss",str(start),"-i",str(path),
                    "-t",str(dur),"-ac","1","-ar","16000",
                    "-c:a","libmp3lame","-b:a","64k",str(out)],
                   check=True,capture_output=True)
    return out

def transcribe(audio: Path, caption_lang: str = "en") -> list:
    import mimetypes
    bd="-SB"; ab=audio.read_bytes(); mime=mimetypes.guess_type(str(audio))[0] or "audio/mpeg"
    body  = f'--{bd}\r\nContent-Disposition: form-data; name="model"\r\n\r\nwhisper-large-v3-turbo\r\n'
    body += f'--{bd}\r\nContent-Disposition: form-data; name="response_format"\r\n\r\nverbose_json\r\n'
    body += f'--{bd}\r\nContent-Disposition: form-data; name="timestamp_granularities[]"\r\n\r\nword\r\n'
    body += f'--{bd}\r\nContent-Disposition: form-data; name="language"\r\n\r\n{caption_lang}\r\n'
    body += (f'--{bd}\r\nContent-Disposition: form-data; name="file"; '
             f'filename="{audio.name}"\r\nContent-Type: {mime}\r\n\r\n')
    body_b = body.encode()+ab+f'\r\n--{bd}--\r\n'.encode()
    try:
        req = urllib.request.Request("https://api.groq.com/openai/v1/audio/transcriptions",
            data=body_b,
            headers={"Authorization":f"Bearer {os.getenv('GROQ_API_KEY', '')}",
                     "Content-Type":f"multipart/form-data; boundary={bd}"},
            method="POST")
        with urllib.request.urlopen(req,timeout=60) as r:
            return json.loads(r.read()).get("words",[])
    except Exception as e:
        log.warning(f"[Captions] {e}"); return []

def build_srt(words: list) -> str:
    if not words: return ""
    def t(s):
        h=int(s//3600); m=int((s%3600)//60); sec=s%60
        return f"{h:02d}:{m:02d}:{sec:06.3f}".replace(".",",")
    lines,cur,t0=[],[],None
    for w in words:
        if t0 is None: t0=w["start"]
        cur.append(w["word"]); j=" ".join(cur)
        if len(j)>=22 or j.rstrip().endswith((",",".","!","?")):
            lines.append((t0,w["end"],j.strip())); cur,t0=[],None
    if cur and t0: lines.append((t0,words[-1]["end"]," ".join(cur).strip()))
    return "".join(f"{i}\n{t(s)} --> {t(e)}\n{x}\n\n" for i,(s,e,x) in enumerate(lines,1))

def burn_captions(src: Path, dst: Path, srt: Path):
    esc = str(srt).replace("\\","/").replace(":","\\:")
    subprocess.run(["ffmpeg","-y","-i",str(src),
        "-vf",(f"subtitles='{esc}':force_style='FontName=Arial,FontSize=18,Bold=1,"
               f"PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,"
               f"BackColour=&H80000000,BorderStyle=4,Outline=1,"
               f"Shadow=0,Alignment=2,MarginV=120'"),
        "-c:a","copy",str(dst)],check=True,capture_output=True)

# ── Thumbnail ────────────────────────────────────────────────────────────────

def generate_thumbnail(video_path: Path, title: str, niche: str) -> Path | None:
    THUMB_DIR.mkdir(parents=True,exist_ok=True)
    tp = THUMB_DIR / f"{video_path.stem}_thumb.jpg"
    if os.getenv("PIKZELS_API_KEY", ""):
        try:
            resp = http_post_json("https://api.pikzels.com/v1/thumbnail",
                {"prompt":f"YouTube thumbnail: {title}. Niche: {niche}. Bold, viral.",
                 "format":"9:16","model":"pkz-2"},
                {"X-Api-Key":os.getenv("PIKZELS_API_KEY", ""),"Content-Type":"application/json"})
            url = resp.get("output","")
            if url: tp.write_bytes(http_get(url)); return tp
        except Exception as e: log.warning(f"[Thumb] Pikzels: {e}")
    try:
        dur=get_duration(video_path); seek=int(dur*0.12)
        subprocess.run(["ffmpeg","-y","-ss",str(seek),"-i",str(video_path),
                        "-vframes","1","-q:v","2",str(tp)],check=True,capture_output=True)
        return tp
    except Exception as e: log.warning(f"[Thumb] ffmpeg: {e}"); return None

# ── Music ────────────────────────────────────────────────────────────────────

def ensure_music():
    MUSIC_DIR.mkdir(parents=True,exist_ok=True)
    if len(list(MUSIC_DIR.glob("*.mp3"))) >= 5:
        ok(f"Music library: {len(list(MUSIC_DIR.glob('*.mp3')))} tracks"); return
    hdr("Downloading starter music")
    starters=[
        ("energetic_01.mp3","https://www.bensound.com/bensound-music/bensound-energy.mp3"),
        ("happy_01.mp3","https://www.bensound.com/bensound-music/bensound-ukulele.mp3"),
        ("calm_01.mp3","https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3"),
        ("motivate_01.mp3","https://www.bensound.com/bensound-music/bensound-adventure.mp3"),
        ("inspire_01.mp3","https://www.bensound.com/bensound-music/bensound-littleidea.mp3"),
    ]
    for i,(name,url) in enumerate(starters):
        progress_bar(i,len(starters),name)
        dest=MUSIC_DIR/name
        if not dest.exists():
            try: dest.write_bytes(http_get(url))
            except: pass
    progress_bar(len(starters),len(starters),"Done")

def fetch_music(mood: str = "energetic", niche: str = "general") -> Path | None:
    """
    Get mood-matched, niche-specific track.
    Priority:
    1. Jamendo API (live, mood-tagged) — if key set
    2. Niche subfolder: assets/music/<niche>/ — best match
    3. Mood subfolder: assets/music/moods/mood_<mood>*.mp3
    4. General folder: assets/music/general/
    5. Any .mp3 anywhere in assets/music/
    """
    # 1. Jamendo live fetch
    jid = os.getenv("JAMENDO_CLIENT_ID", "")
    if jid:
        dest = MUSIC_DIR / f"jamendo_{niche}_{mood}.mp3"
        if not dest.exists():
            try:
                tags   = f"{mood},{niche}" if niche != "general" else mood
                params = urllib.parse.urlencode({
                    "client_id": jid, "format": "json", "limit": "5",
                    "tags": tags, "audioformat": "mp32"
                })
                data   = json.loads(http_get(
                    f"https://api.jamendo.com/v3.0/tracks/?{params}"))
                results = data.get("results", [])
                if results:
                    url = random.choice(results[:3]).get("audio", "")
                    if url:
                        dest.write_bytes(http_get(url))
                        return dest
            except Exception:
                pass
        elif dest.exists():
            return dest

    # 2. Niche-specific folder
    niche_dir = MUSIC_DIR / niche.lower()
    if niche_dir.exists():
        niche_files = list(niche_dir.glob("*.mp3"))
        if niche_files:
            return random.choice(niche_files)

    # 3. Mood subfolder
    mood_dir   = MUSIC_DIR / "moods"
    mood_files = list(mood_dir.glob(f"mood_{mood}*.mp3")) if mood_dir.exists() else []
    if mood_files:
        return random.choice(mood_files)

    # 4. General folder
    general_dir   = MUSIC_DIR / "general"
    general_files = list(general_dir.glob("*.mp3")) if general_dir.exists() else []
    if general_files:
        return random.choice(general_files)

    # 5. Flat fallback (old structure)
    flat = list(MUSIC_DIR.glob("*.mp3"))
    if flat:
        return random.choice(flat)

    # 6. Recursive search
    all_mp3 = list(MUSIC_DIR.rglob("*.mp3"))
    return random.choice(all_mp3) if all_mp3 else None

# ══════════════════════════════════════════════════════════════════════════════
#  PROCESS SHORTS  (9:16 vertical ≤58s → Shorts feed)
# ══════════════════════════════════════════════════════════════════════════════

def process_shorts(video_path: Path, title_base: str, niche: str,
                   research: dict, add_captions: bool,
                   lang: str = "english", caption_lang: str = "en",
                   title_style: str = "fresh",
                   original_title: str = "", original_desc: str = "",
                   is_viral: bool = False) -> list:
    SHORTS_DIR.mkdir(parents=True,exist_ok=True)
    qt=""
    try:
        ch=extract_audio(video_path,0,min(30,int(get_duration(video_path))))
        qt=" ".join(w["word"] for w in transcribe(ch)); ch.unlink(missing_ok=True)
    except: pass
    plan=calculate_plan(video_path,qt,is_viral=is_viral)
    print(f"\n  📊 Shorts Plan: {plan['reason']}  |  Est. completion: {plan['completion']}")
    clips=detect_highlights(video_path,plan["num"],plan["dur"])
    shorts=[]
    for i,(s,e) in enumerate(clips):
        dur=e-s; base=SHORTS_DIR/f"{title_base}_short_{i+1}"
        print(f"\n  ── Short {i+1}/{len(clips)}  ({s}s→{e}s  {dur}s) ──")
        f_crop=Path(str(base)+"_crop.mp4"); f_cap=Path(str(base)+"_cap.mp4")
        f_fin =Path(str(base)+"_final.mp4")
        progress_bar(0,4,"Cropping 9:16 for Shorts feed")
        crop_vertical(video_path,f_crop,s,e)
        transcript=""
        if add_captions:
            progress_bar(1,4,"Whisper transcribing...")
            ch=extract_audio(video_path,s,dur); words=transcribe(ch, caption_lang)
            transcript=" ".join(w["word"] for w in words); ch.unlink(missing_ok=True)
            if words:
                srt_f=Path(str(base)+".srt"); srt_f.write_text(build_srt(words),encoding="utf-8")
                burn_captions(f_crop,f_cap,srt_f); srt_f.unlink(missing_ok=True)
            else: shutil.copy(f_crop,f_cap)
        else:
            progress_bar(1,4,"Captions: OFF"); shutil.copy(f_crop,f_cap)
        progress_bar(2,4,"Gemini writing metadata...")
        # Small delay between Gemini calls to stay within free tier (15 req/min)
        if i > 0: time.sleep(4)
        meta=generate_metadata(title_base,transcript,i,niche,research,"shorts",
                               lang=lang,original_title=original_title,
                               original_desc=original_desc,title_style=title_style)
        thumb=generate_thumbnail(f_cap,meta["title"],niche)
        progress_bar(3,4,"Mixing music...")
        track=fetch_music(meta.get("mood","energetic"), niche)
        mix_music(f_cap,f_fin,track)
        for tmp in [f_crop,f_cap]: tmp.unlink(missing_ok=True)
        desc=meta["description"]
        if track and "bensound" in track.name.lower(): desc+="\n\nMusic: www.bensound.com"
        progress_bar(4,4,f"Short {i+1} ready ✓")
        print(f"\n  ✦ Title : {meta['title'][:65]}")
        print(f"  ✦ Hook  : {meta.get('hook_overlay','')[:40]}")
        print(f"  → Will appear in: SHORTS FEED (9:16 + ≤60s)")
        shorts.append({"path":str(f_fin),"thumb_path":str(thumb) if thumb else "",
                       "title":meta["title"][:100],"description":desc[:5000],
                       "tags":meta.get("tags",[]),"mood":meta.get("mood","energetic"),
                       "music_track":track.name if track else "none",
                       "title_alt":meta.get("title_alt",""),
                       "comment_prompt":meta.get("comment_prompt",""),
                       "mode":"shorts"})
    return shorts

# ══════════════════════════════════════════════════════════════════════════════
#  PROCESS VIDEO CLIPS  (original aspect ratio → Videos section)
# ══════════════════════════════════════════════════════════════════════════════

def process_video_clips(video_path: Path, title_base: str, niche: str,
                        research: dict, add_captions: bool,
                        edit_mode: str = "random",
                        trim_start: int = 0, trim_end: int = 0,
                        lang: str = "english", caption_lang: str = "en",
                        title_style: str = "fresh",
                        original_title: str = "", original_desc: str = "") -> list:
    VIDEOS_DIR.mkdir(parents=True,exist_ok=True)

    if edit_mode == "random":
        hdr(f"Video Clips — Random cuts (original aspect ratio → Videos section)")
        source_clips = random_video_clips(video_path, title_base)
    elif edit_mode == "custom":
        hdr(f"Video Clip — Custom trim {trim_start}s–{trim_end}s")
        out = VIDEOS_DIR / f"{title_base}_custom.mp4"
        encode_original_aspect(video_path, out, trim_start, trim_end)
        source_clips = [out]
    else:
        hdr(f"Full Video — As-is (original aspect ratio → Videos section)")
        out = VIDEOS_DIR / f"{title_base}_encoded.mp4"
        encode_original_aspect(video_path, out)
        source_clips = [out]

    results = []
    for i, clip in enumerate(source_clips):
        transcript=""
        if add_captions:
            try:
                dur=min(60,int(get_duration(clip)))
                ch=extract_audio(clip,0,dur)
                transcript=" ".join(w["word"] for w in transcribe(ch, caption_lang))
                ch.unlink(missing_ok=True)
            except: pass
        meta  = generate_metadata(title_base,transcript,i,niche,research,"video",
                                  lang=lang,original_title=original_title,
                                  original_desc=original_desc,title_style=title_style)
        thumb = generate_thumbnail(clip,meta["title"],niche)
        track = fetch_music(meta.get("mood","energetic"))
        f_fin = VIDEOS_DIR/f"{title_base}_video_{i+1}_final.mp4"
        mix_music(clip,f_fin,track)
        if clip!=video_path and clip.exists(): clip.unlink(missing_ok=True)
        print(f"  ✦ Title : {meta['title'][:65]}")
        print(f"  → Will appear in: VIDEOS SECTION (original aspect ratio, NO #shorts)")
        results.append({"path":str(f_fin),"thumb_path":str(thumb) if thumb else "",
                        "title":meta["title"][:100],"description":meta["description"][:5000],
                        "tags":meta.get("tags",[]),"mood":meta.get("mood","energetic"),
                        "music_track":track.name if track else "none",
                        "title_alt":meta.get("title_alt",""),
                        "comment_prompt":meta.get("comment_prompt",""),
                        "mode":"video"})
    return results

# ══════════════════════════════════════════════════════════════════════════════
#  SMART SCHEDULING  — algorithm-aware with randomness
#
#  YOUTUBE ALGORITHM FACTS (2025):
#  • Peak hours for Indian audience: 6PM–10PM weekdays, 10AM–9PM weekends
#  • Shorts: algorithm tests with seed audience first 6-12h → needs isolation
#  • Videos: best discovery when posted 30-60 min before peak (people browse)
#  • Friday evening + Saturday = highest RPM + engagement for most niches
#  • Avoid exact-hour posting (12:00, 18:00) — too many creators post then
#  • Random ±15 min window avoids the algorithm "rush" at :00
#  • 3 Shorts/day max — more than that and algorithm splits the test audience
#  • Long videos need 48h gap minimum to accumulate watch hours before next upload
# ══════════════════════════════════════════════════════════════════════════════

# Upload frequency rules per content type (per day limits)
UPLOAD_RULES = {
    "shorts": {
        "max_per_day"    : 3,    # Never more than 3 Shorts/day
        "min_gap_hours"  : 8,    # Absolute minimum between Shorts
        "ideal_gap_hours": 11,   # ~11h ideal (full seed + CTR test cycle)
        "gap_variance_h" : 3,    # +-3h random variance so gaps never look robotic
    },
    "video": {
        "max_per_day"    : 1,    # 1 long video per day max
        "min_gap_hours"  : 24,   # Min 24h between long videos
        "ideal_gap_hours": 44,   # Slightly under 48h so next can drift earlier
        "gap_variance_h" : 8,    # +-8h variance for videos
    },
}

# Base peak windows (IST) per day  -  (start_h, end_h, weight)
# Based on IST audience research for Indian YouTube creators.
_BASE_PEAK_WINDOWS = {
    "Monday"   : [(6,8,0.5),(12,14,0.6),(17,19,0.8),(20,22,1.0)],
    "Tuesday"  : [(6,8,0.5),(12,14,0.6),(17,19,0.8),(20,22,1.0)],
    "Wednesday": [(6,8,0.5),(12,14,0.7),(17,19,0.9),(20,22,1.0)],
    "Thursday" : [(6,8,0.5),(12,14,0.7),(17,19,0.9),(21,23,1.0)],
    "Friday"   : [(6,8,0.6),(12,14,0.8),(16,18,0.9),(20,23,1.0)],
    "Saturday" : [(8,11,0.9),(13,16,1.0),(17,20,1.0),(20,23,0.9)],
    "Sunday"   : [(8,11,0.9),(13,16,1.0),(17,20,1.0),(20,22,0.8)],
}

# Per-niche time-of-day bias multipliers on the base weights
# morning=6-11, noon=11-16, evening=16-19, night=19-24
_NICHE_TIME_BIAS = {
    "bhajan"    : {"morning":1.8,"noon":1.3,"evening":1.0,"night":0.7},
    "motivation": {"morning":1.6,"noon":1.1,"evening":1.3,"night":1.0},
    "fitness"   : {"morning":1.7,"noon":1.0,"evening":1.5,"night":0.8},
    "cooking"   : {"morning":1.1,"noon":1.5,"evening":1.7,"night":1.2},
    "gaming"    : {"morning":0.6,"noon":0.9,"evening":1.1,"night":1.8},
    "finance"   : {"morning":1.4,"noon":1.2,"evening":1.3,"night":0.9},
    "tech"      : {"morning":1.0,"noon":1.1,"evening":1.4,"night":1.5},
    "education" : {"morning":1.3,"noon":1.4,"evening":1.3,"night":1.0},
    "general"   : {"morning":1.0,"noon":1.0,"evening":1.0,"night":1.0},
}


def _win_label(start_h: int) -> str:
    if start_h < 11:  return "morning"
    if start_h < 16:  return "noon"
    if start_h < 19:  return "evening"
    return "night"


def _pick_peak_window_niche(day_name: str, niche: str,
                            rng: random.Random) -> tuple:
    """Pick best window for day+niche using bias-weighted selection."""
    windows = _BASE_PEAK_WINDOWS.get(day_name, [(18,21,1.0)])
    bias    = _NICHE_TIME_BIAS.get(niche, _NICHE_TIME_BIAS["general"])
    weighted = [(s, e, w * bias.get(_win_label(s), 1.0), _win_label(s))
                for s, e, w in windows]
    total  = sum(x[2] for x in weighted)
    r      = rng.random() * total
    cum    = 0.0
    for s, e, w, lbl in weighted:
        cum += w
        if r <= cum:
            return s, e, lbl
    s, e, _, lbl = weighted[-1]
    return s, e, lbl


def _rand_min_in_window(start_h: int, end_h: int,
                        rng: random.Random) -> tuple:
    """Random (h, m) inside window, blacklisting :00+-6 and :30+-6."""
    total = (end_h - start_h) * 60
    for _ in range(30):
        off = rng.randint(8, max(9, total - 8))
        h   = (start_h + off // 60) % 24
        m   = off % 60
        if abs(m) <= 6 or abs(m - 60) <= 6: continue
        if abs(m - 30) <= 6:                  continue
        return h, m
    return (start_h + 1) % 24, 17


def make_schedule(items: list, niche: str = "general") -> list:
    """
    Deep-research-based upload scheduler that maximises reach and retention.

    What makes this different from a fixed-time scheduler:
    - Every run produces a DIFFERENT schedule (crypto-entropy seed per item)
    - Peak windows are NICHE-SPECIFIC:
        bhajan    -> morning prayer times weighted 1.8x
        gaming    -> late-night weighted 1.8x
        fitness   -> morning/evening gym times weighted 1.7x
        cooking   -> meal-prep times (noon+evening) weighted 1.7x
    - Gaps vary +-variance so uploads never form a robot-detectable pattern
    - Shorts post INSIDE the peak (audience already scrolling)
    - Videos post 15-50 min PRE-PEAK (indexed before audience arrives)
    - Daily limits: 3 Shorts + 1 long max per day
    - Exact :00 and :30 are blacklisted (creator rush = traffic jam)
    """
    IST  = timedelta(hours=5, minutes=30)
    now  = datetime.now(timezone.utc).replace(tzinfo=None) + IST
    days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

    import os as _os
    base_entropy  = int.from_bytes(_os.urandom(4), "big")

    out           = []
    last_short    = now
    last_video    = now
    uploads_today = {}

    for i, item in enumerate(items):
        mode  = item.get("mode", "shorts")
        rules = UPLOAD_RULES.get(mode, UPLOAD_RULES["shorts"])
        rng   = random.Random(base_entropy + i * 9973)  # unique rng per slot

        min_gap   = rules["min_gap_hours"]
        ideal_gap = rules["ideal_gap_hours"]
        variance  = rules["gap_variance_h"]
        # Variable gap: never robotic, never below minimum
        actual_gap = max(min_gap, ideal_gap + rng.uniform(-variance * 0.4, variance))

        search_from = (last_short if mode == "shorts" else last_video) + \
                      timedelta(hours=actual_gap)

        best_time    = None
        chosen_label = "evening"
        window_desc  = ""

        for day_offset in range(14):
            check_date = (search_from + timedelta(days=day_offset)).date()
            date_key   = str(check_date)
            day_name   = days[check_date.weekday()]
            day_counts = uploads_today.get(date_key, {"shorts":0, "videos":0})

            if mode == "shorts" and day_counts["shorts"] >= rules["max_per_day"]:
                continue
            if mode == "video"  and day_counts["videos"] >= rules["max_per_day"]:
                continue

            start_h, end_h, win_label = _pick_peak_window_niche(day_name, niche, rng)
            chosen_label = win_label

            if mode == "video":
                pre_min = rng.randint(15, 50)
                pre_tot = start_h * 60 - pre_min
                cand_h  = pre_tot // 60
                cand_m  = pre_tot % 60
                if abs(cand_m - 0) <= 6 or abs(cand_m - 30) <= 6:
                    cand_m += rng.randint(7, 11)
                cand_m = min(cand_m, 59)
                window_desc = (f"pre-peak {cand_h:02d}:{cand_m:02d} "
                               f"({pre_min}min before {start_h:02d}:00 {win_label})")
            else:
                cand_h, cand_m = _rand_min_in_window(start_h, end_h, rng)
                window_desc = (f"inside {win_label} window "
                               f"{start_h:02d}:00-{end_h:02d}:00")

            candidate = datetime(
                check_date.year, check_date.month, check_date.day, cand_h, cand_m
            )

            if candidate <= search_from and day_offset == 0:
                # Try other windows today
                for ws, we, _ in _BASE_PEAK_WINDOWS.get(day_name, []):
                    ch, cm = _rand_min_in_window(ws, we, rng)
                    c2 = datetime(check_date.year, check_date.month,
                                  check_date.day, ch, cm)
                    if c2 > search_from:
                        candidate   = c2
                        window_desc = f"backup window {ws:02d}:00-{we:02d}:00"
                        break
                else:
                    continue

            if candidate > search_from:
                best_time = candidate
                break

        if not best_time:
            extra     = timedelta(minutes=rng.randint(11, 47))
            best_time = search_from + timedelta(hours=ideal_gap) + extra
            window_desc = "fallback slot"

        date_key = str(best_time.date())
        dc = uploads_today.get(date_key, {"shorts":0, "videos":0})
        if mode == "shorts": dc["shorts"] += 1
        else:                dc["videos"] += 1
        uploads_today[date_key] = dc

        if mode == "shorts": last_short = best_time
        else:                last_video = best_time

        day_name    = days[best_time.weekday()]
        is_peak_day = day_name in ("Friday", "Saturday", "Sunday")
        bias_val    = _NICHE_TIME_BIAS.get(niche, {}).get(chosen_label, 1.0)
        bias_note   = (f" [{niche}x{bias_val:.1f} {chosen_label} boost]"
                       if bias_val > 1.2 else "")
        reasoning   = (
            f"{'PEAK DAY ' if is_peak_day else ''}"
            f"{day_name} | {window_desc}{bias_note} | gap {actual_gap:.1f}h"
        )

        out.append({
            "n"         : i + 1,
            "mode"      : mode,
            "ist"       : best_time.strftime("%a %d %b %Y %I:%M %p IST"),
            "utc"       : best_time - IST,
            "day"       : day_name,
            "window"    : chosen_label,
            "gap_hours" : round(actual_gap, 1),
            "reasoning" : reasoning,
        })

    return out
    IST  = timedelta(hours=5, minutes=30)
    now  = datetime.utcnow() + IST
    days = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]

    # Use date-based seed so schedule varies day to day but is consistent within a day
    day_seed = int(now.strftime("%Y%m%d"))
    rng      = random.Random(day_seed + len(items))

    out         = []
    last_short  = now
    last_video  = now
    uploads_today = {}  # date → {"shorts":0, "videos":0}

    for i, item in enumerate(items):
        mode     = item.get("mode", "shorts")
        rules    = UPLOAD_RULES.get(mode, UPLOAD_RULES["shorts"])
        min_gap  = rules["min_gap_hours"]
        ideal_gap= rules["ideal_gap_hours"]

        # Start from minimum gap after last upload of same type
        if mode == "shorts":
            # Add slight randomness to gap: ideal ± 1-2 hours
            actual_gap = ideal_gap + rng.randint(-1, 2)
            search_from = last_short + timedelta(hours=max(min_gap, actual_gap))
        else:
            actual_gap  = ideal_gap + rng.randint(0, 12)  # videos can wait longer
            search_from = last_video + timedelta(hours=max(min_gap, actual_gap))

        best_time = None

        # Search up to 14 days ahead for a valid peak slot
        for day_offset in range(14):
            check_date  = (search_from + timedelta(days=day_offset)).date()
            date_key    = str(check_date)
            day_name    = days[check_date.weekday()]
            day_counts  = uploads_today.get(date_key, {"shorts": 0, "videos": 0})

            # Check daily limits
            if mode == "shorts" and day_counts["shorts"] >= rules["max_per_day"]:
                continue
            if mode == "video"  and day_counts["videos"] >= rules["max_per_day"]:
                continue

            # Pick a peak window for this day
            start_h, end_h = _pick_peak_window(day_name, rng)

            # For videos: post 30-45 min BEFORE the peak window starts (discovery)
            if mode == "video":
                pre_minutes = rng.randint(25, 45)
                start_h_adj = start_h
                start_m_adj = -pre_minutes
                if start_m_adj < 0:
                    start_h_adj -= 1
                    start_m_adj += 60
                candidate_h, candidate_m = start_h_adj, start_m_adj
            else:
                # Shorts: post INSIDE the peak window with randomness
                candidate_h, candidate_m = _smart_time_in_window(start_h, end_h)

            candidate = datetime(check_date.year, check_date.month, check_date.day,
                                  candidate_h, candidate_m)

            # Must be after search_from
            if candidate <= search_from and day_offset == 0:
                # Try next window on same day
                windows = PEAK_WINDOWS_IST.get(day_name, [])
                for s, e, _ in windows:
                    ch, cm = _smart_time_in_window(s, e)
                    c2 = datetime(check_date.year, check_date.month, check_date.day, ch, cm)
                    if c2 > search_from:
                        candidate = c2
                        break
                else:
                    continue

            if candidate > search_from:
                best_time = candidate
                break

        if not best_time:
            # Hard fallback: just add ideal gap
            best_time = search_from + timedelta(hours=ideal_gap)

        # Record this upload
        date_key = str(best_time.date())
        dc = uploads_today.get(date_key, {"shorts": 0, "videos": 0})
        if mode == "shorts": dc["shorts"] += 1
        else:                dc["videos"] += 1
        uploads_today[date_key] = dc

        # Update last upload tracker
        if mode == "shorts": last_short = best_time
        else:                last_video = best_time

        # Build reasoning string for display
        day_name   = days[best_time.weekday()]
        is_weekend = day_name in ("Friday","Saturday","Sunday")
        reasoning  = (
            f"{'🔥 High-reach ' if is_weekend else ''}"
            f"{day_name} peak window"
            f"{' (pre-peak for discovery)' if mode == 'video' else ' (inside peak)'}"
        )

        out.append({
            "n"        : i + 1,
            "mode"     : mode,
            "ist"      : best_time.strftime("%a %d %b %Y %I:%M %p IST"),
            "utc"      : best_time - IST,
            "day"      : day_name,
            "reasoning": reasoning,
        })

    return out

# ══════════════════════════════════════════════════════════════════════════════
#  UPLOAD
#  KEY RULES:
#  SHORTS  = mode=="shorts" → 9:16 + ≤60s → title has #shorts → Shorts feed
#  VIDEOS  = mode=="video"  → original aspect → no #shorts → Videos section
# ══════════════════════════════════════════════════════════════════════════════

def upload_one(yt, item: dict, sched: dict, num: int, total: int,
               privacy: str = "public") -> str:
    from googleapiclient.http import MediaFileUpload

    is_short = item.get("mode") == "shorts"

    # Privacy
    if privacy == "public":
        status = {"privacyStatus":"public","selfDeclaredMadeForKids":False}
    elif privacy == "scheduled":
        pub = sched["utc"].strftime("%Y-%m-%dT%H:%M:%S.000Z")
        status = {"privacyStatus":"private","publishAt":pub,"selfDeclaredMadeForKids":False}
    else:
        status = {"privacyStatus":"private","selfDeclaredMadeForKids":False}

    title = item["title"]
    desc  = item["description"]
    tags  = list(item.get("tags",[]))

    if is_short:
        # Ensure #shorts is in title for Shorts discovery
        if "#shorts" not in title.lower() and len(title) <= 93:
            title = title.rstrip() + " #shorts"
        if "shorts" not in [t.lower() for t in tags]:
            tags.insert(0,"shorts")
    else:
        # STRIP ALL #shorts from videos → must go to Videos section
        title = title.replace(" #shorts","").replace("#shorts","").strip()
        desc  = desc.replace("#shorts ","").replace(" #shorts","").replace("#shorts","").strip()
        tags  = [t for t in tags if t.lower() not in ("shorts","youtubeshorts")]

    body = {
        "snippet":{"title":title[:100],"description":desc[:5000],
                   "tags":tags[:30],"categoryId":os.getenv("YOUTUBE_CATEGORY","22")},
        "status": status,
    }
    log.info(f"[Upload] {'SHORT' if is_short else 'VIDEO'}: {title[:60]}")

    media = MediaFileUpload(item["path"],mimetype="video/mp4",resumable=True,chunksize=1024*1024)
    req   = yt.videos().insert(part="snippet,status",body=body,media_body=media)
    resp  = None
    while resp is None:
        st,resp = req.next_chunk()
        if st:
            up = int(st.progress()*100)
            ov = int(((num-1+st.progress())/total)*100)
            progress_bar(ov,100,f"Uploading {num}/{total} → {up}%")

    vid = resp["id"]
    url = f"https://youtube.com/shorts/{vid}" if is_short else f"https://www.youtube.com/watch?v={vid}"
    log.info(f"[Upload] ✓ {url}")

    # Thumbnail - Shorts don't support custom API thumbnails and will return 403
    tp = item.get("thumb_path","")
    if tp and Path(tp).exists() and not is_short:
        try:
            yt.thumbnails().set(videoId=vid,
                media_body=MediaFileUpload(tp,mimetype="image/jpeg")).execute()
        except Exception as e: log.warning(f"[Thumb] {e}")
    return vid


def upload_all(items: list, channel: dict, privacy: str = "public") -> list:
    hdr(f"Uploading {len(items)} item(s) → {channel.get('real_name',channel.get('label','?'))}")

    # Smart algorithm-aware schedule — pass full item list so each gets correct mode-based timing
    sched = make_schedule(items)

    shorts_count = sum(1 for x in items if x.get("mode")=="shorts")
    videos_count = sum(1 for x in items if x.get("mode")=="video")
    print(f"\n  📋 Upload summary:")
    if shorts_count: print(f"     {shorts_count} Short(s) → Shorts feed  (random peak window, ±random minutes)")
    if videos_count: print(f"     {videos_count} Video(s) → Videos section  (pre-peak slot for discovery)")

    print(f"\n  📅 Smart Schedule (algorithm-aware, randomised):")
    for s in sched:
        mode_label = "Short" if s.get("mode") == "shorts" else "Video"
        print(f"     {s['n']}. [{mode_label:<5}]  {s['ist']}  ← {s.get('reasoning','peak window')}")
    print()

    yt = _yt_client_for_channel(channel)
    results = []
    for i, item in enumerate(items):
        kind = "Short" if item.get("mode")=="shorts" else "Video"
        print(f"\n  {kind} {i+1}/{len(items)}: {item['title'][:55]}")
        try:
            vid = upload_one(yt,item,sched[i],i+1,len(items),privacy=privacy)
            url = (f"https://youtube.com/shorts/{vid}" if item.get("mode")=="shorts"
                   else f"https://www.youtube.com/watch?v={vid}")
            results.append({"n":i+1,"type":kind,"title":item["title"],"id":vid,
                             "url":url,"scheduled":sched[i]["ist"],
                             "comment_prompt":item.get("comment_prompt","")})
            time.sleep(2)
        except Exception as e:
            log.error(f"  ✗ Upload failed: {e}")
    ok(f"{len(results)}/{len(items)} uploaded")
    return results

# ══════════════════════════════════════════════════════════════════════════════
#  SOURCE DOWNLOADERS
# ══════════════════════════════════════════════════════════════════════════════

def download_url(url: str) -> list:
    for d in [RAW_DIR,SHORTS_DIR]:
        if d.exists(): shutil.rmtree(d)
        d.mkdir(parents=True,exist_ok=True)
    hdr(f"Downloading: {url[:60]}")
    subprocess.run(["yt-dlp","--format","bestvideo[height<=1080]+bestaudio/best",
                    "--merge-output-format","mp4","--output",str(RAW_DIR/"%(title)s.%(ext)s"),
                    "--no-playlist",url],check=True)
    v=list(RAW_DIR.glob("*.mp4")); ok(f"Downloaded {len(v)} video(s)"); return v

def download_viral(channel_url: str, n: int = 5) -> list:
    """
    Download top videos from a channel.
    SMART: remembers which videos were already downloaded from each channel.
    Next run → skips already-uploaded videos → downloads the NEXT new ones.
    History saved in: BASE_DIR/viral_history.json
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    # ── Load viral history ────────────────────────────────────────────────────
    history_file = BASE_DIR / "viral_history.json"
    history      = {}
    if history_file.exists():
        try:
            history = json.loads(history_file.read_text(encoding="utf-8"))
        except Exception:
            history = {}

    already_done = set(history.get(channel_url, []))

    hdr(f"Viral Copy — channel: {channel_url[:50]}")
    if already_done:
        print(f"  ℹ  {len(already_done)} video(s) already uploaded from this channel — skipping them")

    # ── Fetch video IDs + metadata from channel (no download yet) ────────────
    print("  Fetching video list from channel...")
    meta_cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--playlist-end", str(n * 5),   # fetch 5x more so we have extras after filtering
        "--print", "%(id)s|||%(title)s|||%(duration)s|||%(view_count)s",
        "--no-warnings",
        channel_url
    ]
    try:
        result = subprocess.run(meta_cmd, capture_output=True, text=True, timeout=60)
        raw_lines = [l for l in result.stdout.strip().split("\n") if "|||" in l]
    except Exception as e:
        log.warning(f"[Viral] Metadata fetch failed: {e} — falling back to direct download")
        raw_lines = []

    # Parse and filter
    candidates = []
    for line in raw_lines:
        parts = line.split("|||")
        if len(parts) < 2: continue
        vid_id    = parts[0].strip()
        vid_title = parts[1].strip()
        try:
            duration = int(float(parts[2].strip() or 0)) if len(parts) > 2 and parts[2].strip() != "NA" else 0
        except ValueError:
            duration = 0
            
        try:
            views = int(float(parts[3].strip() or 0)) if len(parts) > 3 and parts[3].strip() != "NA" else 0
        except ValueError:
            views = 0
        if vid_id and vid_id not in already_done:
            candidates.append({
                "id"      : vid_id,
                "title"   : vid_title,
                "duration": duration,
                "views"   : views,
            })

    # Sort by views descending (most viral first), pick top n
    candidates.sort(key=lambda x: x["views"], reverse=True)
    to_download = candidates[:n]

    if not to_download:
        if already_done:
            print(f"\n  ⚠  All top videos from this channel have already been uploaded!")
            print(f"     Total uploaded so far: {len(already_done)}")
            ans = input("  Download the next batch anyway (ignoring history)? (y/n): ").strip().lower()
            if ans == "y":
                already_done = set()
                to_download  = candidates[:n] if candidates else []
                if not to_download:
                    # Re-fetch without filtering
                    to_download = [{"id": None, "title": "", "duration": 0, "views": 0}]
                    to_download = []  # trigger fallback below
        if not to_download:
            print("  Falling back to direct channel download...")

    # ── Download selected videos ───────────────────────────────────────────────
    for f in RAW_DIR.glob("*.mp4"): f.unlink()

    downloaded_ids = []
    if to_download:
        print(f"\n  Downloading {len(to_download)} new video(s) (not previously uploaded):")
        for i, v in enumerate(to_download):
            print(f"     {i+1}. {v['title'][:60]}  ({v['views']:,} views)")

        video_ids = [v["id"] for v in to_download]
        urls      = [f"https://www.youtube.com/watch?v={vid}" for vid in video_ids]

        for i, (vid_url, v) in enumerate(zip(urls, to_download)):
            progress_bar(i, len(to_download), f"Downloading {i+1}/{len(to_download)}")
            try:
                subprocess.run([
                    "yt-dlp",
                    "--format", "bestvideo[height<=1080]+bestaudio/best",
                    "--merge-output-format", "mp4",
                    "--output", str(RAW_DIR / "%(view_count)s_%(id)s_%(title)s.%(ext)s"),
                    "--no-playlist", "--no-warnings",
                    vid_url
                ], check=True, capture_output=True)
                downloaded_ids.append(v["id"])
            except Exception as e:
                log.warning(f"[Viral] Failed to download {v['id']}: {e}")

        progress_bar(len(to_download), len(to_download), "Downloads done")

    else:
        # Fallback: direct channel download with playlist-end limit
        print("  Downloading directly from channel (no history filtering)...")
        cmd = [
            "yt-dlp",
            "--format", "bestvideo[height<=1080]+bestaudio/best",
            "--merge-output-format", "mp4",
            "--output", str(RAW_DIR / "%(view_count)s_%(title)s.%(ext)s"),
            "--playlist-end", str(n),
            "--match-filter", "duration < 65",
            "--no-warnings",
            channel_url
        ]
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError:
            cmd.remove("--match-filter"); cmd.remove("duration < 65")
            subprocess.run(cmd, check=True)

    # ── Save updated history ──────────────────────────────────────────────────
    updated_done = list(already_done | set(downloaded_ids))
    history[channel_url] = updated_done
    history_file.write_text(json.dumps(history, indent=2), encoding="utf-8")

    videos = sorted(RAW_DIR.glob("*.mp4"), reverse=True)[:n]
    ok(f"Downloaded {len(videos)} video(s)  |  History: {len(updated_done)} total from this channel")
    if downloaded_ids:
        print(f"  Next run will skip these {len(downloaded_ids)} video(s) and download the next batch.")
    # Return original titles alongside videos — both sorted by view_count desc so order matches
    _viral_titles = [v["title"] for v in to_download[:len(videos)]]
    return videos, _viral_titles

def collect_local(folder: str) -> list:
    exts={".mp4",".mov",".mkv",".avi",".webm"}
    v=[p for p in Path(folder).iterdir() if p.suffix.lower() in exts]
    ok(f"Found {len(v)} local video(s)"); return v

# ══════════════════════════════════════════════════════════════════════════════
#  ORIGINAL VIDEO METADATA FETCHER
#  Reads original title + description from the source URL BEFORE processing.
#  This lets Gemini enhance the existing meaning instead of guessing from scratch.
# ══════════════════════════════════════════════════════════════════════════════

def fetch_original_meta(url: str) -> dict:
    """
    Fetch original video title + description from any YouTube URL.
    Uses yt-dlp --dump-json (metadata only, no video download).
    Returns {"title": str, "description": str}.
    """
    try:
        result = subprocess.run(
            ["yt-dlp", "--dump-json", "--no-playlist", "--no-warnings", url],
            capture_output=True, text=True, timeout=45, encoding="utf-8"
        )
        if result.returncode == 0 and result.stdout.strip():
            # yt-dlp may return one JSON object per line for playlists — take first
            first_line = result.stdout.strip().splitlines()[0]
            data       = json.loads(first_line)
            orig_title = data.get("title", "")
            orig_desc  = (data.get("description") or "")[:800]
            return {"title": orig_title, "description": orig_desc}
    except Exception as e:
        log.warning(f"[Meta] fetch_original_meta({url[:50]}): {e}")
    return {"title": "", "description": ""}

# ══════════════════════════════════════════════════════════════════════════════
#  CLEANUP
# ══════════════════════════════════════════════════════════════════════════════

def ask_cleanup(source_videos: list, output_items: list):
    choice = menu(
        "CLEANUP — What would you like to delete?",
        ["🗑️  Delete source videos only  (keep processed clips)",
         "🗑️  Delete processed clips only (keep source videos)",
         "🗑️  Delete BOTH               (free all space)",
         "💾  Keep everything"]
    )
    deleted_src=0; deleted_clips=0
    if choice in (1,3):
        for vp in source_videos:
            p=Path(vp) if isinstance(vp,str) else vp
            if p.exists(): p.unlink(); deleted_src+=1
        ok(f"Deleted {deleted_src} source video(s)")
    if choice in (2,3):
        for item in output_items:
            p=Path(item.get("path",""))
            if p.exists(): p.unlink(); deleted_clips+=1
            tp=Path(item.get("thumb_path",""))
            if tp.exists(): tp.unlink()
        ok(f"Deleted {deleted_clips} output clip(s)")
    if choice==4: ok("All files kept")
    db=json.loads(PROCESSED_DB.read_text()) if PROCESSED_DB.exists() else []
    db.append({"at":str(datetime.now()),"src_del":choice in(1,3),"clip_del":choice in(2,3)})
    PROCESSED_DB.write_text(json.dumps(db,indent=2))

# ══════════════════════════════════════════════════════════════════════════════
#  REPORT
# ══════════════════════════════════════════════════════════════════════════════

def save_report(results: list, channel: dict, session: dict):
    r = {"run_at":str(datetime.now()),"channel":channel.get("real_name",""),
         "content":session.get("ct_label",""),"captions":session.get("add_captions",False),
         "total":len(results),"items":results}
    for d in [MANIFEST,DESKTOP]:
        d.parent.mkdir(parents=True,exist_ok=True)
        d.write_text(json.dumps(r,indent=2),encoding="utf-8")

    ch = channel.get("real_name",channel.get("label",""))
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║           ✅  ALL TASKS COMPLETED SUCCESSFULLY  ✅            ║
╠══════════════════════════════════════════════════════════════╣
║  Channel: {ch[:52]:<52} ║
║  Total  : {len(results):<5}  Captions: {'ON' if session.get('add_captions') else 'OFF':<5}  Gap: {os.getenv('UPLOAD_GAP_HOURS',12)}h          ║
╠══════════════════════════════════════════════════════════════╣""")
    for r2 in results:
        u=f"  {r2['n']}.  {r2['url']}"
        s=f"     Posts: {r2['scheduled']}"
        c=f"     📌 Pin: {r2.get('comment_prompt','')[:42]}"
        print(f"║ {u[:62]:<62} ║")
        print(f"║ {s[:62]:<62} ║")
        if r2.get("comment_prompt"): print(f"║ {c[:62]:<62} ║")
        print(f"║ {'─'*62} ║")
    print(f"""╠══════════════════════════════════════════════════════════════╣
║  📄 Report: Desktop/upload_manifest.json                     ║
║  📄 Report: C:/ShortsBot/upload_manifest.json                ║
║  💡 YouTube Studio → pin top comment on each upload NOW      ║
╚══════════════════════════════════════════════════════════════╝
""")

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN MENU
# ══════════════════════════════════════════════════════════════════════════════

def main_mode_menu(channel: dict) -> dict:
    niche  = channel.get("niche","general")
    ch_name= channel.get("real_name", channel.get("label","?"))
    session= {"channel":channel,"niche":niche}

    # ── Source mode ──────────────────────────────────────────────────────────
    src_choice = menu(
        f"SOURCE MODE  (Channel: {ch_name[:40]})",
        ["📥  Download from URL  — paste any YouTube/video URL",
         "📂  Local upload       — videos already on this PC",
         "🔥  Viral Copy         — download top videos from a channel"]
    )
    if src_choice == 1:
        session["source"]      = get_input("Paste video URL")
        session["source_type"] = "url"
        session["mode_label"]  = "URL"
    elif src_choice == 2:
        session["source"]      = get_input("Full folder path (e.g. C:\\Users\\You\\Videos)")
        session["source_type"] = "local"
        session["mode_label"]  = "Local"
    else:
        session["source"]      = get_input("Channel URL to copy from (e.g. https://youtube.com/@Channel)")
        session["viral_count"] = int(get_input("How many top videos? (default 5)", required=False) or "5")
        session["source_type"] = "viral"
        session["mode_label"]  = "Viral Copy"

    # ── Content type ─────────────────────────────────────────────────────────
    print("\n  ℹ  YouTube routing rules:")
    print("     SHORTS feed   → 9:16 vertical + under 60s + #shorts in title")
    print("     VIDEOS section → original aspect ratio + no #shorts\n")
    ct = menu(
        "WHAT CONTENT TO CREATE?",
        ["✂️   Shorts only        — 9:16 clips ≤58s → Shorts feed",
         "🎬  Video clips        — 1-3min clips, original ratio → Videos section",
         "📽️   Full video         — whole video, original ratio → Videos section",
         "🎯  Shorts + Video clips (BOTH)",
         "🎯  Shorts + Full video  (BOTH)"]
    )
    session["make_shorts"]     = ct in (1,4,5)
    session["make_vid_clips"]  = ct in (2,4)
    session["make_full_video"] = ct in (3,5)
    session["ct_label"]        = ["Shorts","Video Clips","Full Video",
                                   "Shorts+Clips","Shorts+Full"][ct-1]

    # ── Full video edit mode ─────────────────────────────────────────────────
    session["video_edit"]  = "random"
    session["trim_start"]  = 0
    session["trim_end"]    = 0
    if session["make_full_video"]:
        rc = menu("FULL VIDEO EDIT MODE?",
                  ["📼  Upload as-is","🎞️   Custom trim (enter start/end seconds)"])
        session["video_edit"] = ["asis","custom"][rc-1]
        if session["video_edit"] == "custom":
            session["trim_start"] = int(get_input("Start time (seconds)") or "0")
            session["trim_end"]   = int(get_input("End time (seconds)") or "0")

    # ── Privacy / monetization ───────────────────────────────────────────────
    print("\n  ⚡ MONETIZATION TIP:")
    print("  PUBLIC = videos visible immediately + watch hours count NOW")
    print("  SCHEDULED = videos visible at set time (watch hours count when published)")
    print("  PRIVATE = not visible, watch hours do NOT count\n")
    pv = menu("UPLOAD VISIBILITY?",
              ["🟢  Public   — visible immediately, watch hours count NOW (RECOMMENDED)",
               "📅  Scheduled — publish at IST peak times automatically",
               "🔒  Private  — review before publishing"])
    session["privacy"] = ["public","scheduled","private"][pv-1]

    # ── Captions ─────────────────────────────────────────────────────────────
    session["add_captions"] = yn("Add AI captions (Groq Whisper speech-to-text)?", default=False)
    print(f"  Captions: {'✓ ON' if session['add_captions'] else '✗ OFF'}")

    # ── Language for titles & descriptions ───────────────────────────────────
    hdr("Language & Title Settings")
    lang_choice = menu(
        "TITLE & DESCRIPTION LANGUAGE?",
        ["\U0001f1ec\U0001f1e7  English  — titles & descriptions written in English",
         "\U0001f1ee\U0001f1f3  Hindi (\u0939\u093f\u0902\u0926\u0940)  — titles & descriptions in Hindi Devanagari script"]
    )
    session["lang"] = "hindi" if lang_choice == 2 else "english"
    print(f"  {C.GREEN}\u2714  Language: {'Hindi \U0001f1ee\U0001f1f3' if session['lang'] == 'hindi' else 'English \U0001f1ec\U0001f1e7'}{C.RESET}")

    # ── Caption / Subtitle language ───────────────────────────────────────────
    if session.get("add_captions"):
        cap_choice = menu(
            "SUBTITLE / CAPTION LANGUAGE?",
            ["\U0001f1ec\U0001f1e7  English subtitles  (Whisper auto-detects & transcribes in English)",
             "\U0001f1ee\U0001f1f3  Hindi subtitles    (Whisper auto-detects & transcribes in Hindi)"]
        )
        session["caption_lang"] = "hi" if cap_choice == 2 else "en"
        print(f"  {C.GREEN}\u2714  Caption Language: "
              f"{'Hindi \U0001f1ee\U0001f1f3' if session['caption_lang'] == 'hi' else 'English \U0001f1ec\U0001f1e7'}{C.RESET}")
    else:
        session["caption_lang"] = "en"

    # ── Title / Description style ─────────────────────────────────────────────
    print(f"\n  {C.DIM}The bot will read the original video's title & description,")
    print(f"  then generate yours based on the style you choose below.{C.RESET}")
    style_choice = menu(
        "TITLE & DESCRIPTION STYLE?",
        ["\u2728  Enhance Original  — keep exact same meaning & topic, improve "
         "format, hooks, emojis, CTR (RECOMMENDED)",
         "\U0001f504  Write Fresh       — same niche & topic, completely new angle & wording"]
    )
    session["title_style"] = "enhance" if style_choice == 1 else "fresh"
    if style_choice == 1:
        print(f"  {C.GREEN}\u2714  Enhanced mode: original meaning preserved, "
              f"stronger hook & format{C.RESET}")
    else:
        print(f"  {C.CYAN}\u2714  Fresh mode: same niche, brand-new title & "
              f"description angle{C.RESET}")

    # ── Niche ────────────────────────────────────────────────────────────────
    if yn(f"  Change niche from '{niche}'?", default=False):
        niches = list(NICHE_TAGS.keys())
        ni = menu("SELECT NICHE", niches)
        session["niche"] = niches[ni-1]

    return session

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print("""
╔══════════════════════════════════════════════════════════════╗
║   🚀  ShortsBot  v10  — 10-Day Monetization Edition          ║
╠══════════════════════════════════════════════════════════════╣
║  Real channel names from YouTube API                         ║
║  Shorts → Shorts feed  |  Videos → Videos section           ║
║  Hindi / English support  |  Enhance or Fresh titles        ║
╚══════════════════════════════════════════════════════════════╝
""")

    # ─────────────────────────────────────────────────────────────────────────
    #  RESUME vs FRESH START
    #
    #  If a checkpoint exists AND has a full saved session+channel, we skip
    #  ALL menus and jump straight to the right step.
    #  If checkpoint is old-format (missing session/channel), fall back to
    #  fresh start with a warning.
    # ─────────────────────────────────────────────────────────────────────────
    cp       = ask_resume()
    resuming = bool(cp and cp.get("session") and cp.get("channel"))

    if resuming:
        # ── RESUME PATH: restore everything from checkpoint ───────────────
        session = cp["session"]
        channel = cp["channel"]
        niche   = session.get("niche", channel.get("niche", "general"))
        step    = cp.get("step", "downloading")
        box("RESUMING FROM CHECKPOINT", [
            f"Step    : {step.upper()}",
            f"Channel : {channel.get('real_name', '?')}",
            f"Niche   : {niche}",
            f"Source  : {session.get('source', '?')[:55]}",
            f"Saved   : {cp.get('saved_at', '')[:16]}",
        ], "Skipping menus — restoring saved settings")
        ensure_music()
        research = research_niche(niche)
        # On resume: regenerate strategy from cache (won't call Gemini if <24h old)
        strategy = generate_monetization_strategy(channel)
        research["strategy_guidance"] = strategy.get("ai_guidance", "")
        research["title_approach"]    = strategy.get("title_approach", "")
        research["hook_approach"]     = strategy.get("hook_approach", "")

    else:
        # ── FRESH START: full interactive menu ────────────────────────────
        if cp:
            warn("Checkpoint has no saved session — starting fresh")
            clear_cp()
        step = "downloading"   # always start from the top on a fresh run

        # STEP 1: Channel
        channel = channel_menu()
        niche   = channel.get("niche", "general")

        # Generate AI-powered strategy (Gemini, adapts to this channel's stage)
        strategy = generate_monetization_strategy(channel)
        if yn("Show AI monetization strategy?", default=True):
            show_monetization_strategy(channel, strategy)

        # STEP 2: All options
        session = main_mode_menu(channel)
        niche   = session.get("niche", niche)

        ensure_music()
        research = research_niche(niche)
        # Inject AI strategy guidance into research so Gemini uses it for metadata
        research["strategy_guidance"] = strategy.get("ai_guidance", "")
        research["title_approach"]    = strategy.get("title_approach", "")
        research["hook_approach"]     = strategy.get("hook_approach", "")

        # Save checkpoint with FULL session + channel so a crash can be resumed
        save_cp({"step": "downloading", "session": session, "channel": channel,
                 "niche": niche})

    # ─────────────────────────────────────────────────────────────────────────
    #  STEP 3: DOWNLOAD
    #  • downloading → run the download now
    #  • processing  → download already done; use files in output/raw/
    #  • uploading   → processing done too; use files in output/raw/
    # ─────────────────────────────────────────────────────────────────────────
    st                = session.get("source_type", "url")
    viral_titles_list = []
    session_original_title = ""
    session_original_desc  = ""

    if step in ("processing", "uploading"):
        # Skip download — raw files already on disk from the interrupted run
        videos = sorted(RAW_DIR.glob("*.mp4"))
        ok(f"Skipping download (step={step}) — "
           f"using {len(videos)} file(s) already in output/raw/")
        # Restore original meta from checkpoint if available
        session_original_title = session.get("_orig_title", "")
        session_original_desc  = session.get("_orig_desc",  "")

    else:
        # step == "downloading" — do the actual download
        if st == "viral":
            videos, viral_titles_list = download_viral(
                session["source"], session.get("viral_count", 5))
        elif st == "url":
            videos = download_url(session["source"])
        else:
            videos = collect_local(session["source"])

        # Fetch original video metadata for AI title guidance
        if st == "url" and session.get("source", "").startswith("http"):
            hdr("Reading Original Video Info")
            print(f"  {C.DIM}Fetching original title & description to guide AI..."
                  f"{C.RESET}")
            orig = fetch_original_meta(session["source"])
            session_original_title = orig["title"]
            session_original_desc  = orig["description"]
            if session_original_title:
                ok(f"Original title: {session_original_title[:65]}")
                if session_original_desc:
                    print(f"  {C.DIM}Description: "
                          f"{session_original_desc[:80]}...{C.RESET}")
            else:
                warn("Could not fetch original metadata — AI will generate fresh")
        elif st == "viral" and viral_titles_list:
            print(f"  {C.DIM}Viral mode: per-video original titles captured "
                  f"({len(viral_titles_list)} video(s)){C.RESET}")
        else:
            print(f"  {C.DIM}Local mode — AI generates from niche context{C.RESET}")

        # Persist orig meta into session so a crash here can restore it on resume
        session["_orig_title"] = session_original_title
        session["_orig_desc"]  = session_original_desc

        # Update checkpoint: step=processing + full session with orig meta saved
        save_cp({"step": "processing", "session": session, "channel": channel,
                 "niche": niche})

    if not videos:
        print("\n❌  No videos found.\n"); sys.exit(1)

    # ─────────────────────────────────────────────────────────────────────────
    #  STEP 4: PROCESS
    #  • uploading → processing already done; restore all_items from checkpoint
    #  • otherwise  → process now
    # ─────────────────────────────────────────────────────────────────────────
    if step == "uploading" and cp and cp.get("all_items"):
        # Skip processing — restore the already-processed item list
        all_items = cp["all_items"]
        ok(f"Skipping processing — restored {len(all_items)} item(s) from checkpoint")

    else:
        all_items    = []
        add_captions = session.get("add_captions", False)
        lang         = session.get("lang", "english")
        caption_lang = session.get("caption_lang", "en")
        title_style  = session.get("title_style", "fresh")
        make_shorts  = session.get("make_shorts", True)
        make_vc      = session.get("make_vid_clips", False)
        make_fv      = session.get("make_full_video", False)
        video_edit   = session.get("video_edit", "asis")
        trim_start   = int(session.get("trim_start", 0) or 0)
        trim_end     = int(session.get("trim_end",   0) or 0)

        for vi, video in enumerate(videos):
            title = "".join(
                c for c in video.stem[:40]
                if c.isalnum() or c in " _-"
            ).strip()

            # Pick per-video original metadata
            if viral_titles_list and vi < len(viral_titles_list):
                orig_title = viral_titles_list[vi]
                orig_desc  = ""
            else:
                orig_title = session_original_title
                orig_desc  = session_original_desc

            if make_shorts:
                shorts = process_shorts(
                    video, title, niche, research, add_captions,
                    lang=lang, caption_lang=caption_lang,
                    title_style=title_style,
                    original_title=orig_title, original_desc=orig_desc,
                    is_viral=(st=="viral"))
                all_items.extend(shorts)
                print(f"\n  ✅ {len(shorts)} Short(s) queued → Shorts feed")

            if make_vc:
                clips = process_video_clips(
                    video, title, niche, research, add_captions,
                    "random", lang=lang, caption_lang=caption_lang,
                    title_style=title_style,
                    original_title=orig_title, original_desc=orig_desc)
                all_items.extend(clips)
                print(f"\n  ✅ {len(clips)} video clip(s) queued → Videos section")

            if make_fv:
                full = process_video_clips(
                    video, title, niche, research, add_captions,
                    video_edit, trim_start, trim_end,
                    lang=lang, caption_lang=caption_lang,
                    title_style=title_style,
                    original_title=orig_title, original_desc=orig_desc)
                all_items.extend(full)
                print(f"\n  ✅ {len(full)} full video(s) queued → Videos section")

        # Save checkpoint with all_items so an upload crash can be resumed
        save_cp({"step": "uploading", "session": session, "channel": channel,
                 "niche": niche, "all_items": all_items})

    # ─────────────────────────────────────────────────────────────────────────
    #  STEP 5: UPLOAD
    # ─────────────────────────────────────────────────────────────────────────
    uploaded = upload_all(all_items, channel, session.get("privacy", "public"))

    # ─────────────────────────────────────────────────────────────────────────
    #  STEP 6: REPORT + CLEANUP
    # ─────────────────────────────────────────────────────────────────────────
    save_report(uploaded, channel, session)
    ask_cleanup(videos, all_items)
    clear_cp()
    print("\n  🎉  Done! Check YouTube Studio → your content is live.\n")


if __name__ == "__main__":
    main()
=======
        w     = 8000
        energy = np.array([np.sqrt(np.mean(audio[i:i+w]**2)) for i in range(0,len(audio)-w,w)])
        peaks, _ = find_peaks(energy, height=np.percentile(energy,70), distance=30)
        dur   = CONFIG["shorts_duration"]
        clips = [(max(0,p-dur//2), max(0,p-dur//2)+dur) for p in peaks[:num]]
        if clips: return clips
    except ImportError:
        log.warning("[Highlights] numpy/scipy missing — even-spaced clips")
    total = get_duration(path)
    dur   = CONFIG["shorts_duration"]
    step  = total / (num + 1)
    return [(int(step*i), int(step*i)+dur) for i in range(1, num+1)]


def crop_vertical_lossless(src: Path, dst: Path, start: int, end: int):
    """
    Crop to 9:16 with visually lossless CRF-18.
    Streams ffmpeg progress to show a live sub-bar while encoding.
    """
    duration = end - start
    # Use ffmpeg -progress pipe to read frame count live
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start), "-i", str(src), "-t", str(duration),
        "-vf", "scale=iw*max(1080/iw\\,1920/ih):ih*max(1080/iw\\,1920/ih),crop=1080:1920",
        "-c:v", "libx264", "-crf", "18", "-preset", "slow",
        "-profile:v", "high", "-level", "4.1", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-progress", "pipe:1", "-nostats",
        str(dst)
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                            text=True)
    frame = 0
    # estimate total frames from duration
    try:
        fps_probe = subprocess.run(
            ["ffprobe","-v","error","-select_streams","v:0",
             "-show_entries","stream=r_frame_rate","-of","json",str(src)],
            capture_output=True, text=True)
        fps_data = json.loads(fps_probe.stdout)
        fps_str  = fps_data["streams"][0]["r_frame_rate"]  # e.g. "30/1"
        num, den = fps_str.split("/")
        fps = float(num) / float(den)
        total_frames = max(1, int(duration * fps))
    except Exception:
        total_frames = duration * 30  # fallback estimate

    for line in proc.stdout:
        line = line.strip()
        if line.startswith("frame="):
            try:
                frame = int(line.split("=")[1])
                progress_bar(min(frame, total_frames), total_frames,
                             "Encoding 9:16 lossless")
            except ValueError:
                pass
    proc.wait()
    progress_bar(total_frames, total_frames, "Encoding 9:16 lossless")


def mix_music(src: Path, dst: Path, track: Path | None):
    if not track:
        shutil.copy(src, dst)
        return
    dur = get_duration(src)
    vol = CONFIG["music_volume"]
    cmd = [
        "ffmpeg", "-y", "-i", str(src),
        "-stream_loop", "-1", "-i", str(track),
        "-filter_complex",
        f"[1:a]volume={vol},atrim=0:{dur}[m];[0:a][m]amix=inputs=2:duration=first[a]",
        "-map","0:v","-map","[a]",
        "-c:v","copy","-c:a","aac","-b:a","192k", str(dst)
    ]
    subprocess.run(cmd, check=True, capture_output=True)


def process_video(video_path: Path, title_base: str,
                  niche: str = "general") -> list[dict]:
    SHORTS_DIR.mkdir(parents=True, exist_ok=True)
    shorts = []
    clips  = detect_highlights(video_path, CONFIG["max_shorts_per_video"])
    total_steps = len(clips) * 4   # crop, caption, music, upload-prep

    task_header(f"Processing: {title_base}  ({len(clips)} clips)")

    for i, (start, end) in enumerate(clips):
        base_step = i * 4
        print(f"\n  Clip {i+1}/{len(clips)}  —  {start}s → {end}s")
        dur  = end - start
        base = SHORTS_DIR / f"{title_base}_short_{i+1}"
        f_crop  = Path(str(base)+"_crop.mp4")
        f_cap   = Path(str(base)+"_cap.mp4")
        f_final = Path(str(base)+"_final.mp4")

        # Step A — Crop (lossless)
        progress_bar(base_step+1, total_steps, "Cropping to 9:16 (lossless)")
        crop_vertical_lossless(video_path, f_crop, start, end)

        # Step B — Transcribe + captions
        progress_bar(base_step+2, total_steps, "Groq Whisper transcribing...")
        audio_chunk = extract_audio_chunk(video_path, start, dur)
        words       = transcribe_groq(audio_chunk)
        transcript  = " ".join(w["word"] for w in words)
        audio_chunk.unlink(missing_ok=True)

        # Step C — AI metadata
        progress_bar(base_step+3, total_steps, "Gemini writing title & tags...")
        meta = generate_metadata(title_base, transcript, i, niche)

        if words:
            srt = Path(str(base)+".srt")
            srt.write_text(build_srt(words), encoding="utf-8")
            burn_srt(f_crop, f_cap, srt)
            srt.unlink(missing_ok=True)
        else:
            burn_placeholder(f_crop, f_cap, meta.get("caption_overlay", title_base))

        # Step D — Music mix
        progress_bar(base_step+4, total_steps, "Mixing mood-matched music...")
        mood  = meta.get("mood", "energetic")
        track = fetch_jamendo_track(mood)
        if not track:
            track = _any_cached_music()
        mix_music(f_cap, f_final, track)

        for tmp in [f_crop, f_cap]:
            tmp.unlink(missing_ok=True)

        desc = meta["description"]
        if track and "bs_" in track.name:
            desc += "\n\nMusic: www.bensound.com"

        shorts.append({
            "path"         : str(f_final),
            "title"        : meta["title"][:100],
            "description"  : desc[:5000],
            "tags"         : meta.get("tags", CONFIG["youtube"]["base_tags"]),
            "transcript"   : transcript[:300],
            "mood"         : mood,
            "music_track"  : track.name if track else "none",
            "title_variants": meta.get("title_variants", []),
        })

        progress_bar(total_steps, total_steps, f"Clip {i+1} complete ✓")
        print(f"\n  Title: {meta['title'][:65]}")

    task_done(f"All {len(shorts)} clips processed for: {title_base}")
    return shorts

# ══════════════════════════════════════════════════════════════════════════════
#  UPLOAD + PROGRESS BAR
# ══════════════════════════════════════════════════════════════════════════════

def upload_short(youtube, short: dict, publish_at: datetime,
                 short_num: int, total: int) -> str:
    from googleapiclient.http import MediaFileUpload
    pub_str = publish_at.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    body = {
        "snippet": {
            "title"      : short["title"],
            "description": short["description"],
            "tags"       : short["tags"],
            "categoryId" : CONFIG["youtube"]["category_id"],
        },
        "status": {
            "privacyStatus"          : "private",
            "publishAt"              : pub_str,
            "selfDeclaredMadeForKids": False,
        },
    }
    media   = MediaFileUpload(short["path"], mimetype="video/mp4", resumable=True,
                              chunksize=1024*1024)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            upload_pct = int(status.progress() * 100)
            overall    = int(((short_num - 1 + status.progress()) / total) * 100)
            progress_bar(overall, 100,
                         f"Short {short_num}/{total} uploading... {upload_pct}%")
    progress_bar(int(short_num/total*100), 100, f"Short {short_num}/{total} uploaded ✓")
    return response["id"]


def schedule_and_upload(shorts: list[dict], account_name: str = "default") -> list[dict]:
    task_header(f"Uploading {len(shorts)} Shorts to YouTube ({account_name})")
    youtube  = authenticate_youtube(account_name)
    interval = timedelta(hours=CONFIG["upload_interval_hours"])
    now      = datetime.utcnow()
    results  = []

    for i, short in enumerate(shorts):
        publish_at = now + interval * (i + 1)
        print(f"\n  Short {i+1}/{len(shorts)}: {short['title'][:55]}")
        try:
            vid = upload_short(youtube, short, publish_at, i+1, len(shorts))
            results.append({
                "short_number" : i + 1,
                "title"        : short["title"],
                "id"           : vid,
                "url"          : f"https://youtube.com/shorts/{vid}",
                "scheduled_at" : str(publish_at),
                "mood"         : short.get("mood",""),
                "music_track"  : short.get("music_track",""),
                "title_variants": short.get("title_variants",[]),
            })
            time.sleep(2)
        except Exception as e:
            log.error(f"  ✗ Upload failed: {e}")

    task_done(f"{len(results)}/{len(shorts)} Shorts uploaded successfully")
    return results

# ══════════════════════════════════════════════════════════════════════════════
#  REPORT + COMPLETION BANNER
# ══════════════════════════════════════════════════════════════════════════════

def save_report_and_notify(results: list[dict], total_shorts: int):
    report = {
        "run_at"      : str(datetime.now()),
        "total_shorts": total_shorts,
        "uploaded"    : len(results),
        "shorts"      : results,
    }
    for dest in [MANIFEST, DESKTOP]:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║           ✅  ALL TASKS COMPLETED SUCCESSFULLY  ✅            ║
╠══════════════════════════════════════════════════════════════╣
║  Shorts created   : {total_shorts:<5}                                    ║
║  Shorts uploaded  : {len(results):<5}                                    ║
║  Schedule gap     : Every {CONFIG['upload_interval_hours']} hours                          ║
╠══════════════════════════════════════════════════════════════╣""")

    for r in results:
        url_line  = f"  Short {r['short_number']}  →  {r['url']}"
        sched_line = f"  Scheduled : {r['scheduled_at'][:19]}"
        print(f"║ {url_line:<62}║")
        print(f"║ {sched_line:<62}║")
        if r.get("title_variants"):
            for alt in r["title_variants"][:1]:
                print(f"║   Alt title: {alt[:57]:<57}║")
        print(f"║ {'─'*62}║")

    print(f"""╠══════════════════════════════════════════════════════════════╣
║  📄 Report → Desktop/upload_manifest.json                    ║
║  📄 Report → C:\\ShortsBot\\upload_manifest.json              ║
║  🗃️  Deleted source videos logged → processed_videos.json    ║
║  📋 Full log → C:\\ShortsBot\\automation.log                  ║
╚══════════════════════════════════════════════════════════════╝
""")

# ══════════════════════════════════════════════════════════════════════════════
#  SOURCE DOWNLOADERS
# ══════════════════════════════════════════════════════════════════════════════

def download_video_url(url: str) -> list[Path]:
    """
    Download exactly ONE video from a URL.
    Clears RAW_DIR and SHORTS_DIR first so no old clips bleed into this run.
    """
    # Clean previous run's files so only THIS video's Shorts get uploaded
    for d in [RAW_DIR, SHORTS_DIR]:
        if d.exists():
            shutil.rmtree(d)
        d.mkdir(parents=True, exist_ok=True)

    task_header(f"Downloading video: {url[:60]}")
    subprocess.run([
        "yt-dlp",
        "--format", "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        "--merge-output-format", "mp4",
        "--output", str(RAW_DIR / "%(title)s.%(ext)s"),
        "--no-playlist", url
    ], check=True)
    vids = list(RAW_DIR.glob("*.mp4"))
    task_done(f"Downloaded {len(vids)} video(s)  |  Old clips cleared ✓")
    return vids


def download_channel(url: str, max_videos: int = 5) -> list[Path]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    task_header(f"Downloading latest {max_videos} videos from channel")
    subprocess.run([
        "yt-dlp",
        "--format", "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        "--merge-output-format", "mp4",
        "--output", str(RAW_DIR / "%(title)s.%(ext)s"),
        "--playlist-end", str(max_videos), url
    ], check=True)
    vids = list(RAW_DIR.glob("*.mp4"))
    task_done(f"Downloaded {len(vids)} video(s)")
    return vids


def collect_local(folder: str) -> list[Path]:
    exts   = {".mp4", ".mov", ".mkv", ".avi", ".webm"}
    videos = [p for p in Path(folder).iterdir() if p.suffix.lower() in exts]
    task_done(f"Found {len(videos)} local video(s)")
    return videos

# ══════════════════════════════════════════════════════════════════════════════
#  MAIN ORCHESTRATOR
# ══════════════════════════════════════════════════════════════════════════════

def run(source: str, source_type: str = "auto", niche: str = "general",
        scrape_viral: bool = False, viral_channel: str = ""):

    print("""
╔══════════════════════════════════════════════════════════════╗
║      🚀  YouTube Shorts AI Automation  —  Ultimate v5        ║
╠══════════════════════════════════════════════════════════════╣
║  Captions   : Groq Whisper Large v3 Turbo  (free)            ║
║  Titles     : Google Gemini 2.5 Flash      (free)            ║
║  Music      : Jamendo + Bensound + Pixabay (free, 20 tracks) ║
║  Quality    : Lossless CRF-18 encoding                       ║
╚══════════════════════════════════════════════════════════════╝
""")

    # ── Check for resume ────────────────────────────────────────────────────
    cp = ask_resume()
    if cp:
        print(f"\n  Resuming from step: {cp.get('step')}")
        source      = cp.get("source", source)
        source_type = cp.get("source_type", source_type)
        niche       = cp.get("niche", niche)

    # ── Select YouTube account ───────────────────────────────────────────────
    account = select_youtube_account()

    # ── Optional: scrape viral Shorts to learn from ─────────────────────────
    if scrape_viral and viral_channel:
        scrape_viral_shorts(viral_channel, max_shorts=10)
    elif scrape_viral:
        vc = input("\n  Enter channel URL to scrape viral Shorts from: ").strip()
        if vc:
            scrape_viral_shorts(vc, max_shorts=10)

    # ── Pre-download music ───────────────────────────────────────────────────
    ensure_starter_music()

    # ── Auto-detect source type ──────────────────────────────────────────────
    if source_type == "auto":
        if source.startswith("http") and ("@" in source or "/c/" in source or "/channel/" in source):
            source_type = "channel"
        elif source.startswith("http"):
            source_type = "url"
        else:
            source_type = "local"

    # ── Save checkpoint ──────────────────────────────────────────────────────
    save_checkpoint({
        "step"       : "downloading",
        "source"     : source,
        "source_type": source_type,
        "niche"      : niche,
        "account"    : account,
        "saved_at"   : str(datetime.now()),
    })

    # ── Collect videos ───────────────────────────────────────────────────────
    if cp and cp.get("step") not in ("downloading",):
        videos = list(RAW_DIR.glob("*.mp4"))
        log.info(f"[Resume] Using {len(videos)} already-downloaded video(s)")
    elif source_type == "url":
        videos = download_video_url(source)
    elif source_type == "channel":
        videos = download_channel(source)
    else:
        videos = collect_local(source)

    if not videos:
        log.error("No videos found. Check your source URL or folder path.")
        sys.exit(1)

    save_checkpoint({"step":"processing","source":source,
                     "source_type":source_type,"niche":niche,
                     "account":account,"saved_at":str(datetime.now())})

    # ── Process each video ───────────────────────────────────────────────────
    all_results = []
    for vi, video in enumerate(videos):
        title  = "".join(c for c in video.stem[:40] if c.isalnum() or c in " _-").strip()
        shorts = process_video(video, title, niche)

        save_checkpoint({"step":"uploading","source":source,
                         "source_type":source_type,"niche":niche,
                         "account":account,"saved_at":str(datetime.now()),
                         "video_index":vi})

        # Upload this video's Shorts immediately
        uploaded = schedule_and_upload(shorts, account)
        all_results.extend(uploaded)

        # Delete source video + log it
        record_and_delete_source(video, source, uploaded)

    # ── Final report ─────────────────────────────────────────────────────────
    save_report_and_notify(all_results, sum(1 for _ in all_results))
    clear_checkpoint()   # run completed — remove checkpoint


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="YouTube Shorts AI Automation — Ultimate v5")
    ap.add_argument("source",          help="YouTube URL, channel URL, or local folder path")
    ap.add_argument("--type",          choices=["url","channel","local","auto"], default="auto")
    ap.add_argument("--niche",         default="general",
                    help='e.g. "fitness" "cooking" "finance" "gaming" "motivation"')
    ap.add_argument("--scrape-viral",  action="store_true",
                    help="Scrape top viral Shorts from a channel to improve AI writing")
    ap.add_argument("--viral-channel", default="",
                    help="Channel URL to scrape viral Shorts from (used with --scrape-viral)")
    args = ap.parse_args()
    run(args.source, args.type, args.niche, args.scrape_viral, args.viral_channel)
>>>>>>> 64497acc2905e2ab02e72faaffb871464a15f9a7
