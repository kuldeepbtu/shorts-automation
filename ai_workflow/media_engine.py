import urllib.request
import urllib.parse
import os
import subprocess
import time
import logging
from pathlib import Path

log = logging.getLogger("ShortsBot.AIWorkflow.Media")

# We select a free but premium-sounding Edge TTS voice.
VOICE_MODEL = "en-US-ChristopherNeural"  # or "en-US-AndrewNeural", "en-GB-RyanNeural"

# Simple retry helper
def download_with_retry(url: str, dest: Path, retries: int = 3):
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as response, open(dest, 'wb') as out_file:
                out_file.write(response.read())
            return
        except Exception as e:
            log.warning(f"Download failed ({i+1}/{retries}): {e}")
            time.sleep(2)
    raise RuntimeError(f"Failed to download from {url} after {retries} retries.")

def get_audio_duration(file_path: Path) -> float:
    """Uses ffprobe to extract exact duration of media file."""
    cmd = [
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration", "-of",
        "default=noprint_wrappers=1:nokey=1", str(file_path)
    ]
    try:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        return float(res.stdout.strip())
    except Exception as e:
        log.error(f"Failed to get duration for {file_path}: {e}")
        return 5.0 # safe fallback

def generate_voice(text: str, output_path: Path) -> float:
    """Generates MP3 using Edge TTS and returns duration."""
    # edge-tts is a CLI interface to the library when installed globally
    log.info(f"Generating voice to {output_path}...")
    cmd = [
        "python", "-m", "edge_tts",
        "--voice", VOICE_MODEL,
        "--text", text,
        "--write-media", str(output_path),
        # Increase speech rate slightly for better retention if shorts
        "--rate", "+5%" 
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return get_audio_duration(output_path)

def generate_image(prompt: str, is_shorts: bool, output_path: Path):
    """Downloads an AI generated image from pollinations.ai"""
    log.info(f"Generating image for prompt from Pollinations.ai...")
    safe_prompt = urllib.parse.quote(prompt)
    seed = int(time.time())
    
    if is_shorts:
        w, h = 1080, 1920
    else:
        w, h = 1920, 1080

    url = f"https://image.pollinations.ai/prompt/{safe_prompt}?width={w}&height={h}&nologo=true&seed={seed}"
    download_with_retry(url, output_path)

def build_scene_video(image_path: Path, audio_path: Path, duration: float, output_path: Path, is_shorts: bool):
    """
    Combines static image + voice audio + Ken Burns zoom effect using ffmpeg.
    This creates professional dynamic movement for the 'faceless' vibe.
    """
    log.info(f"Building scene video: {output_path.name} ({duration}s)")
    
    # Randomly pick zoom-in or zoom-out to make it feel natural
    # "zoom in"  -> zoom=min(zoom+0.0015,1.5)
    # "zoom out" -> zoom=max(1.5-0.0015*on,1.0)
    zoom_dir = "in" if hash(str(output_path)) % 2 == 0 else "out"

    # For 30fps, 0.0015 per frame creates a gentle scale.
    zoom_expr = "zoom+0.0015" if zoom_dir == "in" else "max(1.5-0.0015*on,1.0)"

    if is_shorts:
        scale_param = "scale=1080:-2"
        crop_param = "crop=1080:1920"
    else:
        scale_param = "scale=1920:-2"
        crop_param = "crop=1920:1080"

    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-loop", "1", "-i", str(image_path),
        "-i", str(audio_path),
        "-c:v", "libx264", "-c:a", "aac", "-b:a", "192k",
        "-t", str(duration + 0.2), # slight padding
        "-pix_fmt", "yuv420p",
        "-vf", f"{scale_param},zoompan=z='{zoom_expr}':d={int((duration+0.5)*30)}:s={1080 if is_shorts else 1920}x{1920 if is_shorts else 1080}:fps=30,{crop_param},format=yuv420p",
        "-r", "30",
        str(output_path)
    ]
    subprocess.run(cmd, check=True)

def concat_scenes(scene_videos: list, output_path: Path):
    """Concatenates all individual scene videos into the final video."""
    log.info(f"Concatenating {len(scene_videos)} scenes into final video...")
    
    workspace = scene_videos[0].parent
    list_file = workspace / "concat_list.txt"
    
    with open(list_file, "w") as f:
        for vid in scene_videos:
            # properly format path for ffmpeg concat demuxer
            safe_vid = vid.as_posix().replace("'", "'\\''")
            f.write(f"file '{safe_vid}'\n")

    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0",
        "-i", str(list_file),
        "-c", "copy",
        str(output_path)
    ]
    subprocess.run(cmd, check=True)

def add_background_music(video_path: Path, music_dir: Path, final_output_path: Path):
    """Mixes a random background track from assets/music quietly behind the voiceover."""
    log.info("Adding background music...")
    music_files = list(Path(music_dir).glob("*.mp3")) + list(Path(music_dir).glob("*.wav"))
    if not music_files:
        log.warning("No music files found. Skipping BGM.")
        import shutil
        shutil.copy2(video_path, final_output_path)
        return
        
    bgm = music_files[hash(str(video_path)) % len(music_files)]
    log.info(f"Selected BGM: {bgm.name}")

    # Mix BGM. Video audio (voice) normal volume, BGM very low (0.1)
    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(video_path),
        "-stream_loop", "-1", "-i", str(bgm), # Loop music indefinitely
        "-filter_complex", "[0:a]volume=1.2[a1];[1:a]volume=0.08[a2];[a1][a2]amix=inputs=2:duration=first:dropout_transition=2",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        str(final_output_path)
    ]
    subprocess.run(cmd, check=True)
