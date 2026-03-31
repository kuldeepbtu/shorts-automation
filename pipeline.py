"""
YouTube Shorts Automation Pipeline  (Windows Edition)
=======================================================
Sources : YouTube URL / Channel / Local Folder
Processing: Trim highlights, crop 9:16, captions, background music
Output   : Auto-scheduled uploads to YouTube
Report   : upload_manifest.json saved to Desktop automatically
"""

import os
import json
import time
import random
import shutil
import logging
import argparse
import urllib.request
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

# ─── Windows Paths ────────────────────────────────────────────────────────────
# Everything lives inside C:\ShortsBot\
BASE_DIR    = Path(r"C:\ShortsBot")
OUTPUT_DIR  = BASE_DIR / "output"
RAW_DIR     = OUTPUT_DIR / "raw"
SHORTS_DIR  = OUTPUT_DIR / "shorts"
MUSIC_DIR   = BASE_DIR / "assets" / "music"
LOG_FILE    = BASE_DIR / "automation.log"
MANIFEST    = BASE_DIR / "upload_manifest.json"
DESKTOP     = Path.home() / "Desktop" / "upload_manifest.json"

# Windows font path used by ffmpeg drawtext
WINDOWS_FONT = r"C\:/Windows/Fonts/arialbd.ttf"   # escaped for ffmpeg filter

# ─── Setup Logging ────────────────────────────────────────────────────────────
BASE_DIR.mkdir(parents=True, exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(str(LOG_FILE), encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# ─── Config ───────────────────────────────────────────────────────────────────
CONFIG = {
    "shorts_duration"       : 58,    # seconds — keeps it under 60s
    "max_shorts_per_video"  : 3,
    "upload_interval_hours" : 4,
    "music_volume"          : 0.15,  # 15% — subtle background
    "caption_fontsize"      : 48,
    "youtube": {
        "category_id"    : "22",     # People & Blogs
        "privacy_status" : "private",# change to "public" when ready
        "tags"           : ["shorts", "viral", "trending"],
    },
    # Royalty-free tracks from Pixabay CDN (direct MP3 links, no login needed)
    "music_tracks": [
        {
            "name": "lofi_chill.mp3",
            "url" : "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3"
        },
        {
            "name": "upbeat_energy.mp3",
            "url" : "https://cdn.pixabay.com/download/audio/2022/03/10/audio_270f49c5e9.mp3"
        },
        {
            "name": "motivational_beat.mp3",
            "url" : "https://cdn.pixabay.com/download/audio/2021/11/25/audio_5b5bb9e0a6.mp3"
        },
    ]
}

# ─── Step 0: Auto-download royalty-free music ─────────────────────────────────

def ensure_music():
    """Download royalty-free background tracks if not already present."""
    MUSIC_DIR.mkdir(parents=True, exist_ok=True)
    for track in CONFIG["music_tracks"]:
        dest = MUSIC_DIR / track["name"]
        if dest.exists():
            log.info(f"Music already exists: {track['name']}")
            continue
        log.info(f"Downloading music: {track['name']} ...")
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            req = urllib.request.Request(track["url"], headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp, open(dest, "wb") as f:
                shutil.copyfileobj(resp, f)
            log.info(f"Saved: {dest}")
        except Exception as e:
            log.warning(f"Could not download {track['name']}: {e}")

# ─── Step 1: Download / Collect Videos ───────────────────────────────────────

def download_youtube_video(url: str) -> list[Path]:
    """Download a single YouTube video using yt-dlp."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [
        "yt-dlp",
        "--format", "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        "--merge-output-format", "mp4",
        "--output", str(RAW_DIR / "%(title)s.%(ext)s"),
        "--no-playlist",
        url
    ]
    log.info(f"Downloading video: {url}")
    subprocess.run(cmd, check=True)
    return list(RAW_DIR.glob("*.mp4"))


def download_channel(channel_url: str, max_videos: int = 5) -> list[Path]:
    """Download the latest N videos from a YouTube channel."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    cmd = [
        "yt-dlp",
        "--format", "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
        "--merge-output-format", "mp4",
        "--output", str(RAW_DIR / "%(title)s.%(ext)s"),
        "--playlist-end", str(max_videos),
        channel_url
    ]
    log.info(f"Downloading latest {max_videos} videos from: {channel_url}")
    subprocess.run(cmd, check=True)
    return list(RAW_DIR.glob("*.mp4"))


def collect_local_videos(folder: str) -> list[Path]:
    """Collect all video files from a local folder."""
    exts = {".mp4", ".mov", ".mkv", ".avi", ".webm"}
    videos = [p for p in Path(folder).iterdir() if p.suffix.lower() in exts]
    log.info(f"Found {len(videos)} video(s) in {folder}")
    return videos

# ─── Step 2: Detect Highlights ───────────────────────────────────────────────

def get_video_duration(video_path: Path) -> float:
    """Return video duration in seconds via ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json", str(video_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return float(json.loads(result.stdout)["format"]["duration"])


def detect_highlights(video_path: Path, num_clips: int = 3) -> list[tuple]:
    """
    Find the most energetic (loudest) moments in the video.
    Falls back to evenly-spaced clips if numpy/scipy are not installed.
    """
    try:
        import numpy as np
        from scipy.signal import find_peaks

        cmd = [
            "ffmpeg", "-i", str(video_path),
            "-ac", "1", "-ar", "8000",
            "-f", "f32le", "-", "-loglevel", "error"
        ]
        result = subprocess.run(cmd, capture_output=True)
        audio  = np.frombuffer(result.stdout, dtype=np.float32)
        window = 8000
        energy = np.array([
            np.sqrt(np.mean(audio[i:i+window]**2))
            for i in range(0, len(audio) - window, window)
        ])
        peaks, _ = find_peaks(energy, height=np.percentile(energy, 70), distance=30)

        clips    = []
        duration = CONFIG["shorts_duration"]
        for peak in peaks[:num_clips]:
            start = max(0, peak - duration // 2)
            clips.append((start, start + duration))

        if clips:
            return clips

    except ImportError:
        log.warning("numpy/scipy not found — using evenly-spaced clips")

    # Fallback
    total    = get_video_duration(video_path)
    duration = CONFIG["shorts_duration"]
    step     = total / (num_clips + 1)
    return [(int(step * i), int(step * i) + duration) for i in range(1, num_clips + 1)]

# ─── Step 3: Process Clips ────────────────────────────────────────────────────

def crop_to_vertical(src: Path, dst: Path, start: int, end: int):
    """Trim + crop to 9:16 (1080×1920)."""
    cmd = [
        "ffmpeg", "-y",
        "-ss", str(start), "-i", str(src),
        "-t", str(end - start),
        "-vf", "scale=iw*max(1080/iw\\,1920/ih):ih*max(1080/iw\\,1920/ih),crop=1080:1920",
        "-c:v", "libx264", "-crf", "23", "-preset", "fast",
        "-c:a", "aac", "-b:a", "128k",
        str(dst)
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    log.info(f"Cropped  → {dst.name}")


def add_captions(src: Path, dst: Path, text: str):
    """Burn caption text onto the video (Windows Arial Bold font)."""
    # Escape special characters for ffmpeg filter
    safe_text = text.replace("'", "").replace(":", " ").replace("\\", "")
    drawtext  = (
        f"drawtext=text='{safe_text}':"
        f"fontfile='{WINDOWS_FONT}':"
        f"fontsize={CONFIG['caption_fontsize']}:"
        f"fontcolor=white:"
        f"borderw=2:bordercolor=black:"
        f"x=(w-text_w)/2:y=h-text_h-80"
    )
    cmd = [
        "ffmpeg", "-y", "-i", str(src),
        "-vf", drawtext,
        "-codec:a", "copy",
        str(dst)
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    log.info(f"Captions → {dst.name}")


def mix_background_music(src: Path, dst: Path):
    """Mix a random royalty-free track at low volume under the original audio."""
    music_files = list(MUSIC_DIR.glob("*.mp3")) + list(MUSIC_DIR.glob("*.m4a"))
    if not music_files:
        log.warning("No music files found — skipping music mix")
        shutil.copy(src, dst)
        return

    track    = random.choice(music_files)
    duration = get_video_duration(src)
    vol      = CONFIG["music_volume"]

    cmd = [
        "ffmpeg", "-y",
        "-i", str(src),
        "-stream_loop", "-1", "-i", str(track),
        "-filter_complex",
        f"[1:a]volume={vol},atrim=0:{duration}[music];[0:a][music]amix=inputs=2:duration=first[aout]",
        "-map", "0:v", "-map", "[aout]",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        str(dst)
    ]
    subprocess.run(cmd, check=True, capture_output=True)
    log.info(f"Music    → {dst.name}  (track: {track.name})")


def process_video(video_path: Path, title_base: str) -> list[dict]:
    """Run the full editing pipeline on one source video → list of Short dicts."""
    SHORTS_DIR.mkdir(parents=True, exist_ok=True)
    shorts = []
    clips  = detect_highlights(video_path, CONFIG["max_shorts_per_video"])

    for i, (start, end) in enumerate(clips):
        log.info(f"  Clip {i+1}/{len(clips)}  ({start}s – {end}s)")
        base = SHORTS_DIR / f"{title_base}_short_{i+1}"

        step1 = Path(str(base) + "_crop.mp4")
        step2 = Path(str(base) + "_cap.mp4")
        final = Path(str(base) + "_final.mp4")

        crop_to_vertical(video_path, step1, start, end)
        add_captions(step1, step2, f"{title_base} Part {i+1}")
        mix_background_music(step2, final)

        for tmp in [step1, step2]:
            if tmp.exists():
                tmp.unlink()

        shorts.append({
            "path"       : str(final),
            "title"      : f"{title_base} #{i+1} #shorts",
            "description": f"Auto-generated Short\n\n#shorts #viral #trending",
            "tags"       : CONFIG["youtube"]["tags"] + [title_base.replace(" ", "")],
        })

    return shorts

# ─── Step 4: YouTube Upload & Scheduling ─────────────────────────────────────

def authenticate_youtube():
    """OAuth2 login — opens browser on first run, uses cached token.json after."""
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    SCOPES     = ["https://www.googleapis.com/auth/youtube.upload"]
    token_path = BASE_DIR / "token.json"
    secrets    = BASE_DIR / "client_secrets.json"
    creds      = None

    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
                import json as _json
                with open(str(secrets), "r", encoding="utf-8-sig") as f:
                    _client_config = _json.load(f)
                flow = InstalledAppFlow.from_client_config(_client_config, SCOPES)
                creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json())

    return build("youtube", "v3", credentials=creds)


def upload_short(youtube, short: dict, publish_at: datetime) -> str:
    """Upload one Short, scheduled to go public at publish_at (UTC)."""
    from googleapiclient.http import MediaFileUpload

    publish_str = publish_at.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    body = {
        "snippet": {
            "title"      : short["title"][:100],
            "description": short["description"][:5000],
            "tags"       : short["tags"],
            "categoryId" : CONFIG["youtube"]["category_id"],
        },
        "status": {
            "privacyStatus"          : "private",
            "publishAt"              : publish_str,
            "selfDeclaredMadeForKids": False,
        }
    }
    media    = MediaFileUpload(short["path"], mimetype="video/mp4", resumable=True)
    request  = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            log.info(f"  Upload: {int(status.progress()*100)}%")

    vid = response["id"]
    log.info(f"  Uploaded → https://youtube.com/shorts/{vid}  (scheduled: {publish_str})")
    return vid


def schedule_and_upload(shorts: list[dict]):
    """Upload all Shorts spaced CONFIG['upload_interval_hours'] apart."""
    youtube  = authenticate_youtube()
    now      = datetime.utcnow()
    interval = timedelta(hours=CONFIG["upload_interval_hours"])
    results  = []

    for i, short in enumerate(shorts):
        publish_at = now + interval * (i + 1)
        log.info(f"Uploading Short {i+1}: '{short['title']}'")
        try:
            vid = upload_short(youtube, short, publish_at)
            results.append({
                "title"    : short["title"],
                "id"       : vid,
                "url"      : f"https://youtube.com/shorts/{vid}",
                "scheduled": str(publish_at)
            })
            time.sleep(2)
        except Exception as e:
            log.error(f"Upload failed: {e}")

    # ── Save report to project folder AND Desktop ──
    report_data = {
        "run_at" : str(datetime.now()),
        "total"  : len(results),
        "shorts" : results
    }
    for dest in [MANIFEST, DESKTOP]:
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)
        log.info(f"Report saved → {dest}")

    log.info(f"\n{'='*50}")
    log.info(f"DONE! {len(results)} Short(s) scheduled.")
    log.info(f"Report on your Desktop: {DESKTOP}")
    log.info(f"{'='*50}\n")
    return results

# ─── Main Orchestrator ────────────────────────────────────────────────────────

def run(source: str, source_type: str = "auto"):
    log.info("="*50)
    log.info("YouTube Shorts Automation — Starting")
    log.info("="*50)

    # Auto-download background music
    ensure_music()

    # ── Detect source type ──
    if source_type == "auto":
        if source.startswith("http") and ("@" in source or "/c/" in source or "/channel/" in source):
            source_type = "channel"
        elif source.startswith("http"):
            source_type = "url"
        else:
            source_type = "local"

    log.info(f"Source type : {source_type}")
    log.info(f"Source      : {source}")

    # ── Collect source videos ──
    if source_type == "url":
        videos = download_youtube_video(source)
    elif source_type == "channel":
        videos = download_channel(source, max_videos=5)
    else:
        videos = collect_local_videos(source)

    log.info(f"Videos found: {len(videos)}")

    # ── Process ──
    all_shorts = []
    for video in videos:
        title = video.stem[:40]
        title = "".join(c for c in title if c.isalnum() or c in " _-").strip()
        log.info(f"\nProcessing: {title}")
        all_shorts.extend(process_video(video, title))

    log.info(f"\nTotal Shorts created: {len(all_shorts)}")

    # ── Upload ──
    schedule_and_upload(all_shorts)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YouTube Shorts Automation (Windows)")
    parser.add_argument("source", help="YouTube URL, channel URL, or local folder path")
    parser.add_argument("--type", choices=["url", "channel", "local", "auto"], default="auto",
                        help="Force source type (default: auto-detect)")
    args = parser.parse_args()
    run(args.source, args.type)
