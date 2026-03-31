# YouTube Shorts Automation

Automatically converts YouTube videos / local videos into Shorts and uploads them on a schedule.

## What it does
1. **Downloads** videos from a YouTube URL, channel, or local folder
2. **Detects highlights** using audio energy analysis
3. **Crops** clips to 9:16 vertical (1080×1920)
4. **Adds captions** burned into the video
5. **Mixes background music** from your royalty-free library
6. **Uploads to YouTube** and schedules them at evenly spaced intervals

---

## Setup (One-time)

### 1. Install system dependencies
```bash
# macOS
brew install ffmpeg yt-dlp

# Ubuntu/Debian
sudo apt install ffmpeg
pip install yt-dlp
```

### 2. Install Python packages
```bash
pip install -r requirements.txt
```

### 3. Get YouTube API credentials
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a project → Enable **YouTube Data API v3**
3. Create **OAuth 2.0 credentials** (Desktop App)
4. Download as `client_secrets.json` → place in this folder

### 4. Add royalty-free music (optional)
Put `.mp3` files in `assets/music/`. 
Free sources: [pixabay.com/music](https://pixabay.com/music), [freemusicarchive.org](https://freemusicarchive.org)

---

## Usage

### From a YouTube video URL
```bash
python pipeline.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

### From a YouTube channel
```bash
python pipeline.py "https://www.youtube.com/@ChannelName" --type channel
```

### From a local folder
```bash
python pipeline.py "/path/to/your/videos" --type local
```

---

## Configuration

Edit the `CONFIG` dict in `pipeline.py`:

| Key | Default | Description |
|-----|---------|-------------|
| `shorts_duration` | 58s | Length of each Short |
| `max_shorts_per_video` | 3 | How many Shorts to make per video |
| `upload_interval_hours` | 4 | Hours between each scheduled upload |
| `youtube.privacy_status` | `private` | Set to `public` when you're confident |

---

## First Run (OAuth)
On the first run, a browser window opens for Google sign-in.
After approving, credentials are saved in `token.json` — you won't need to log in again.

---

## Folder Structure
```
shorts_automation/
├── pipeline.py           ← Main script
├── requirements.txt
├── client_secrets.json   ← Your Google OAuth file (you add this)
├── token.json            ← Auto-created after first auth
├── upload_manifest.json  ← Auto-created after uploads
├── assets/
│   └── music/            ← Put royalty-free .mp3 files here
└── output/
    ├── raw/              ← Downloaded source videos
    └── shorts/           ← Final processed Shorts
```

---

## Pro Tips
- Start with `privacy_status: "private"` to review before going public
- Add AI captions by uncommenting `openai-whisper` in requirements.txt
- Run on a schedule using cron: `0 9 * * * python /path/to/pipeline.py "..."`
