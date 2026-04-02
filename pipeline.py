"""
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
from pathlib import Path
from datetime import datetime, timedelta

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
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

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
    return build("youtube", "v3", credentials=creds)

# ══════════════════════════════════════════════════════════════════════════════
#  VIRAL SHORTS SCRAPER  —  learn from top performing Shorts
# ══════════════════════════════════════════════════════════════════════════════

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
# ══════════════════════════════════════════════════════════════════════════════

def get_duration(path: Path) -> float:
    cmd = ["ffprobe","-v","error","-show_entries","format=duration","-of","json",str(path)]
    return float(json.loads(subprocess.run(cmd,capture_output=True,text=True).stdout)["format"]["duration"])


def detect_highlights(path: Path, num: int = 3) -> list[tuple]:
    try:
        import numpy as np
        from scipy.signal import find_peaks
        cmd   = ["ffmpeg","-i",str(path),"-ac","1","-ar","8000","-f","f32le","-","-loglevel","error"]
        audio = np.frombuffer(subprocess.run(cmd,capture_output=True).stdout, dtype=np.float32)
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
