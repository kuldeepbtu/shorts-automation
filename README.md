# ShortsBot — Complete Setup Guide
## YouTube Shorts AI Automation (Windows)

---

## What This Bot Does

1. Downloads videos from a YouTube URL, channel, or local folder
2. Detects the best highlight moments using audio energy analysis
3. Crops each clip to 9:16 vertical (1080×1920) — lossless CRF-18 quality
4. Transcribes speech → word-by-word animated captions (Groq Whisper AI)
5. Writes a viral title, description, and 20 hashtags (Google Gemini AI)
6. Mixes mood-matched background music (Jamendo + Bensound + Pixabay)
7. Uploads to YouTube as Private, auto-scheduled every 4 hours
8. Deletes source video + Short clips after upload, saves report to Desktop

---

## Files in This Package

```
C:\ShortsBot\
├── pipeline.py                  ← Main automation script
├── requirements.txt             ← Python packages to install
├── setup.py                     ← Run this first — sets up everything
├── client_secrets_PLACEHOLDER.txt ← Replace with your real client_secrets.json
├── README.md                    ← This file
└── accounts\
    └── README.txt               ← How to add multiple YouTube channels
```

---

## Step-by-Step Setup

### Step 1 — Install Python

1. Go to https://python.org/downloads
2. Download Python 3.11 or newer
3. Run installer — **tick "Add Python to PATH"** at the bottom
4. Verify: open Command Prompt → type `python --version`

---

### Step 2 — Install ffmpeg

1. Go to https://github.com/BtbN/FFmpeg-Builds/releases
2. Download `ffmpeg-master-latest-win64-gpl.zip`
3. Extract → rename folder to `ffmpeg` → move to `C:\ffmpeg`
4. Add to PATH:
   - Press Windows key → search "Environment Variables" → open it
   - System Variables → click `Path` → Edit → New → type `C:\ffmpeg\bin` → OK
5. Verify: open NEW Command Prompt → type `ffmpeg -version`

---

### Step 3 — Copy files to C:\ShortsBot\

Create the folder `C:\ShortsBot\` and place inside it:
- `pipeline.py`
- `requirements.txt`
- `setup.py`

---

### Step 4 — Get YouTube API credentials

1. Go to https://console.cloud.google.com (sign in with your YouTube channel's Google account)
2. New Project → name it `ShortsBot` → Create
3. APIs & Services → Library → search "YouTube Data API v3" → Enable
4. APIs & Services → OAuth consent screen → External → fill in app name + email → Save
5. APIs & Services → Credentials → +Create Credentials → OAuth client ID → Desktop app → Create
6. Download the JSON → rename it to `client_secrets.json` → place in `C:\ShortsBot\`

---

### Step 5 — Run setup.py

Open Command Prompt:
```
cd C:\ShortsBot
python setup.py
```

This will:
- Create all folders automatically
- Install all Python packages
- Verify all 3 API keys work
- Tell you if anything is missing

---

### Step 6 — Run the bot

```
cd C:\ShortsBot
python pipeline.py "https://www.youtube.com/@ChannelName" --type channel --niche "fitness"
```

**First time only:** A browser window opens for Google sign-in. Approve it.
After that it runs fully automatically every time.

---

## All Run Commands

### Single video URL:
```
python pipeline.py "https://www.youtube.com/watch?v=VIDEO_ID" --niche "cooking"
```

### Full channel (latest 5 videos):
```
python pipeline.py "https://www.youtube.com/@ChannelName" --type channel --niche "fitness"
```

### Local folder of videos:
```
python pipeline.py "C:\Users\YourName\Videos\MyNiche" --type local --niche "motivation"
```

### Scrape viral Shorts first (improves AI titles):
```
python pipeline.py "https://www.youtube.com/@YourSource" --scrape-viral --viral-channel "https://www.youtube.com/@BigChannel" --niche "gaming"
```

---

## Available Niches

Use any of these with `--niche`:

| Niche | Hashtag pool |
|-------|-------------|
| fitness | gym, workout, health, bodybuilding... |
| cooking | food, recipe, chef, homecooking... |
| finance | money, investing, stockmarket, crypto... |
| gaming | gaming, gamer, ps5, xbox, esports... |
| motivation | success, mindset, hustle, goals... |
| general | facts, tips, tutorial, lifehacks... |

---

## Multi-Account (Multiple YouTube Channels)

See `accounts\README.txt` for full instructions.

Short version: put `client_secrets_channelname.json` files in `C:\ShortsBot\accounts\`
and the bot asks which channel to upload to when you run it.

---

## Resume After Crash

If the script stops mid-run, just run the same command again.
It asks: `Resume from last step? (y/n)` — type `y` to continue.

---

## File Locations After a Run

| File | Location |
|------|----------|
| Upload report | Desktop → `upload_manifest.json` |
| Upload report (copy) | `C:\ShortsBot\upload_manifest.json` |
| Deleted video log | `C:\ShortsBot\processed_videos.json` |
| Full run log | `C:\ShortsBot\automation.log` |
| Music library | `C:\ShortsBot\assets\music\` |
| Viral learnings | `C:\ShortsBot\viral_learnings.json` |

---

## API Keys (Pre-Configured)

All keys are already set in `pipeline.py`. No changes needed.

| Service | Purpose | Free Limit |
|---------|---------|------------|
| Groq | Whisper captions | 2,000 req/day |
| Google Gemini | Titles + descriptions | 1,000 req/day |
| Jamendo | Mood-matched music | 50,000 calls/day |
| Bensound | Fallback music | Unlimited |
| Pixabay | Fallback music | Unlimited |

---

## Change Upload Privacy

By default Shorts upload as **Private** so you can review them first.

To change to public, open `pipeline.py` in Notepad and find:
```python
"privacy_status": "private",
```
Change to:
```python
"privacy_status": "public",
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ffmpeg not found` | Add `C:\ffmpeg\bin` to PATH (Step 2) |
| `yt-dlp not found` | Run `pip install yt-dlp` |
| Gemini 404 error | Already fixed in this version |
| Google sign-in fails | Delete `token.json` and run again |
| No music downloaded | Check internet connection |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` again |
