"""
ai_workflow/media_engine.py
============================
Multi-tier media generation engine for the ShortsBot AI Workflow.

ALL three generation tasks use the SAME Google AI Studio GEMINI_API_KEY_*:
  • Nano Banana 2  → image gen  → model: gemini-3.1-flash-image-preview
  • Veo 3.1        → video gen  → model: veo-3.1-lite-generate-preview
  • Veo 3.1 Full   → video gen  → model: veo-3.1-generate-preview

Key rotation:
  - GEMINI_API_KEY, GEMINI_API_KEY_2 … GEMINI_API_KEY_8 all used
  - Rate-limited keys are blacklisted per-session (thread-safe)
  - Scenes distributed in parallel across all available keys
  - Final fallback: Pollinations image + KenBurns zoom (no key required)

Fixes applied (v2):
  - Correct Veo model IDs from AI Studio (veo-3.1-*)
  - Nano Banana 2 image gen via google-genai SDK (gemini-3.1-flash-image-preview)
  - Thread-safe rate-limit key blacklist with exponential backoff
  - _mix_voice_into_video: fixed in-place Windows file replacement bug
  - generate_all_scenes_parallel: guaranteed results dict fill (no KeyError)
  - _build_kenburns: safe fallback if audio doesn't exist
  - concat_scenes: Windows-safe path formatting
  - generate_image: Nano Banana 2 primary → Pollinations fallback
"""

import os
import json
import base64
import time
import shutil
import subprocess
import urllib.request
import urllib.parse
import logging
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

log = logging.getLogger("ShortsBot.AIWorkflow.Media")

# ══════════════════════════════════════════════════════════════════════════════
#  THREAD-SAFE  RATE-LIMIT  KEY  POOL
# ══════════════════════════════════════════════════════════════════════════════

_key_pool_lock   = threading.Lock()
_rate_limited    : set = set()   # keys blacklisted this session (429 / quota)
_invalid_keys    : set = set()   # keys blacklisted permanently (400/401/403)


def _all_gemini_keys() -> list:
    """Read GEMINI_API_KEY + GEMINI_API_KEY_2..8 from env in order."""
    keys = []
    bare = os.getenv("GEMINI_API_KEY", "").strip()
    if bare:
        keys.append(bare)
    for i in range(2, 9):
        k = os.getenv(f"GEMINI_API_KEY_{i}", "").strip()
        if k and k not in keys:
            keys.append(k)
    return [k for k in keys if k]


def _available_keys() -> list:
    """Return keys that are not rate-limited or invalid."""
    all_keys = _all_gemini_keys()
    with _key_pool_lock:
        return [k for k in all_keys if k not in _rate_limited and k not in _invalid_keys]


def _mark_rate_limited(key: str):
    """Blacklist a key for this session (429 / quota exhausted)."""
    with _key_pool_lock:
        _rate_limited.add(key)
    log.warning(f"[KeyPool] Key …{key[-8:]} rate-limited → blacklisted for session")


def _mark_invalid(key: str):
    """Permanently blacklist a key (400/401/403)."""
    with _key_pool_lock:
        _invalid_keys.add(key)
    log.warning(f"[KeyPool] Key …{key[-8:]} invalid → permanently blacklisted")


def _pick_key(exclude: str = "") -> str:
    """Pick the first available key, skipping excluded one."""
    for k in _available_keys():
        if k != exclude:
            return k
    return ""   # all exhausted


def _http_status(exc: Exception) -> int:
    code = getattr(exc, "code", None)
    if code:
        return int(code)
    try:
        return int(str(exc).split("HTTP Error ")[1].split(":")[0])
    except Exception:
        return 500


# ══════════════════════════════════════════════════════════════════════════════
#  GOOGLE  GENAI  SDK  HELPER
#  Uses the new google-genai library. Falls back gracefully if not installed.
# ══════════════════════════════════════════════════════════════════════════════

def _genai_client(api_key: str):
    """Create a google.genai Client for the given key. Returns None if SDK missing."""
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except ImportError:
        return None


# ══════════════════════════════════════════════════════════════════════════════
#  UTILITY
# ══════════════════════════════════════════════════════════════════════════════

def _download(url: str, dest: Path, retries: int = 3):
    """Download a URL to a file, retrying on failure."""
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "Mozilla/5.0 ShortsBot/10"}
            )
            with urllib.request.urlopen(req, timeout=90) as r, open(dest, "wb") as f:
                f.write(r.read())
            return
        except Exception as e:
            log.warning(f"[Download] Attempt {attempt+1}/{retries} failed: {e}")
            time.sleep(2 ** attempt)   # 1s, 2s, 4s
    raise RuntimeError(f"Failed to download after {retries} retries: {url[:80]}")


def get_audio_duration(path: Path) -> float:
    """Use ffprobe to get exact media duration."""
    try:
        res = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, timeout=15
        )
        val = res.stdout.strip()
        return float(val) if val else 5.0
    except Exception as e:
        log.warning(f"[Media] ffprobe failed ({path.name}): {e}")
        return 5.0


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 3 — VOICE  GENERATION
#  Priority: ElevenLabs (if key set) → Edge TTS (always works)
# ══════════════════════════════════════════════════════════════════════════════

def generate_voice(text: str, output_path: Path, niche_cfg=None) -> float:
    """
    Generate speech audio. Returns duration in seconds.
    Priority: ElevenLabs free tier → Edge TTS fallback.
    """
    el_key = os.getenv("ELEVENLABS_API_KEY", "").strip()
    if el_key:
        is_kids = niche_cfg.is_kids if niche_cfg else False
        if is_kids:
            voice_id = os.getenv("ELEVENLABS_VOICE_ID_KIDS", "AZnzlk1XvdvUeBnXmlld")
        else:
            vid_default = niche_cfg.elevenlabs_voice_id if niche_cfg else "21m00Tcm4TlvDq8ikWAM"
            voice_id = os.getenv("ELEVENLABS_VOICE_ID_ADULT", vid_default or "21m00Tcm4TlvDq8ikWAM")

        if _voice_elevenlabs(text, voice_id, el_key, output_path):
            dur = get_audio_duration(output_path)
            log.info(f"[Voice] ElevenLabs ✅ {dur:.1f}s")
            return dur
        log.warning("[Voice] ElevenLabs failed → Edge TTS fallback")

    voice_model = niche_cfg.voice_model if niche_cfg else "en-US-ChristopherNeural"
    return _voice_edge_tts(text, voice_model, output_path)


def _voice_elevenlabs(text: str, voice_id: str, api_key: str, output_path: Path) -> bool:
    """ElevenLabs free-tier TTS (10,000 chars/month)."""
    try:
        payload = json.dumps({
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        }).encode()
        req = urllib.request.Request(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            data=payload,
            headers={
                "xi-api-key": api_key,
                "Content-Type": "application/json",
                "Accept": "audio/mpeg",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            output_path.write_bytes(resp.read())
        return output_path.stat().st_size > 1024   # verify non-empty
    except Exception as e:
        log.warning(f"[Voice] ElevenLabs error: {e}")
        return False


def _voice_edge_tts(text: str, voice_model: str, output_path: Path) -> float:
    """Microsoft Edge TTS — free and high quality."""
    log.info(f"[Voice] Edge TTS voice={voice_model}")
    # Slow down slightly for kids voices
    rate = "-5%" if any(v in voice_model for v in ("Ana", "Swara", "Jenny")) else "+5%"
    try:
        subprocess.run(
            ["python", "-m", "edge_tts",
             "--voice", voice_model,
             "--text", text,
             "--write-media", str(output_path),
             "--rate", rate],
            check=True, capture_output=True, timeout=90
        )
        return get_audio_duration(output_path)
    except Exception as e:
        log.error(f"[Voice] Edge TTS failed: {e}")
        # Create a 5-second silent audio as last resort
        _create_silent_audio(output_path, 5.0)
        return 5.0


def _create_silent_audio(output_path: Path, duration: float):
    """Emergency: create a silent audio file so the pipeline doesn't crash."""
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=mono",
             "-t", str(duration), "-q:a", "9", "-acodec", "libmp3lame", str(output_path)],
            check=True, capture_output=True, timeout=15
        )
    except Exception:
        pass   # if even this fails, the KenBurns fallback handles it


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 4 — IMAGE  GENERATION
#  Priority: Nano Banana 2 (gemini-3.1-flash-image-preview) → Pollinations.ai
# ══════════════════════════════════════════════════════════════════════════════

def generate_image(prompt: str, is_shorts: bool, output_path: Path,
                   style_hint: str = "") -> Path:
    """
    Generate a scene image.
    Primary  : Nano Banana 2 via Gemini API (gemini-3.1-flash-image-preview)
    Fallback : Pollinations.ai (free, no key)
    """
    w, h = (1080, 1920) if is_shorts else (1920, 1080)
    full_prompt = f"{prompt}, {style_hint}" if style_hint and style_hint not in prompt else prompt
    full_prompt = full_prompt[:500]

    # Try Nano Banana 2 first (higher quality AI images)
    key = _pick_key()
    if key:
        success = _image_nanobanana(full_prompt, w, h, output_path, key)
        if success:
            log.info(f"[Image] Nano Banana 2 ✅ {output_path.stat().st_size//1024}KB")
            return output_path
        log.info("[Image] Nano Banana 2 failed → Pollinations fallback")

    # Pollinations fallback (always free)
    _image_pollinations(full_prompt, w, h, output_path)
    return output_path


def _image_nanobanana(prompt: str, w: int, h: int, output_path: Path, api_key: str) -> bool:
    """
    Generate image using Nano Banana 2 = gemini-3.1-flash-image-preview.
    Uses google-genai SDK → REST fallback.
    """
    # ── Try google-genai SDK ──────────────────────────────────────────────────
    client = _genai_client(api_key)
    if client:
        try:
            from google.genai import types
            aspect = f"{w}:{h}"
            response = client.models.generate_content(
                model="gemini-3.1-flash-image-preview",
                contents=f"{prompt} | aspect ratio {aspect}, ultra high quality",
                config=types.GenerateContentConfig(
                    response_modalities=["image", "text"]
                ),
            )
            for part in response.candidates[0].content.parts:
                if hasattr(part, "inline_data") and part.inline_data:
                    output_path.write_bytes(
                        base64.b64decode(part.inline_data.data)
                        if isinstance(part.inline_data.data, str)
                        else part.inline_data.data
                    )
                    return output_path.stat().st_size > 1024
        except Exception as e:
            status = _http_status(e)
            if status == 429:
                _mark_rate_limited(api_key)
            elif status in (400, 401, 403):
                _mark_invalid(api_key)
            log.debug(f"[NanoBanana2] SDK error ({status}): {e}")

    # ── REST fallback ─────────────────────────────────────────────────────────
    try:
        endpoint = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-3.1-flash-image-preview:generateContent?key={api_key}"
        )
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseModalities": ["image"]},
        }
        req = urllib.request.Request(
            endpoint,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        data = json.loads(urllib.request.urlopen(req, timeout=60).read())
        for part in data["candidates"][0]["content"]["parts"]:
            if "inlineData" in part:
                output_path.write_bytes(base64.b64decode(part["inlineData"]["data"]))
                return output_path.stat().st_size > 1024
    except Exception as e:
        status = _http_status(e)
        if status == 429:
            _mark_rate_limited(api_key)
        log.debug(f"[NanoBanana2] REST error ({status}): {e}")

    return False


def _image_pollinations(prompt: str, w: int, h: int, output_path: Path):
    """Free Pollinations.ai image generation — always available as fallback."""
    safe   = urllib.parse.quote(prompt[:400])
    seed   = int(time.time() * 1000) % 999983
    url    = (
        f"https://image.pollinations.ai/prompt/{safe}"
        f"?width={w}&height={h}&nologo=true&seed={seed}&model=flux&enhance=true"
    )
    log.info(f"[Image] Pollinations {w}x{h}…")
    try:
        _download(url, output_path)
    except Exception as e:
        log.error(f"[Image] Pollinations failed: {e}")
        _create_blank_image(output_path, w, h)


def _create_blank_image(output_path: Path, w: int, h: int):
    """Last-resort: create a solid colour image so the pipeline continues."""
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi",
             "-i", f"color=c=black:s={w}x{h}:r=1",
             "-vframes", "1", str(output_path)],
            check=True, capture_output=True, timeout=10
        )
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 5 — VIDEO  GENERATION  (Veo 3.1 → KenBurns fallback)
#
#  Models (same API key, just different model ID):
#    veo-3.1-lite-generate-preview  → cost-effective, good quality
#    veo-3.1-generate-preview       → full quality, 1080p/4K, native audio
# ══════════════════════════════════════════════════════════════════════════════

_VEO_MODELS = [
    "veo-3.1-lite-generate-preview",   # try lite first (cheaper quota)
    "veo-3.1-generate-preview",        # full quality if lite fails
    "veo-2.0-generate-001",            # older fallback
]


def generate_scene_video(
    image_path: Path,
    scene: dict,
    audio_path: Path,
    duration: float,
    output_path: Path,
    is_shorts: bool,
    api_key: str = "",
) -> bool:
    """
    Generate one scene video.
    Tries Veo 3.1 → KenBurns zoom (ffmpeg) as final fallback.
    Returns True if Veo succeeded, False if KenBurns used.
    """
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)

    if api_key and api_key not in _rate_limited and api_key not in _invalid_keys:
        veo_ok = _generate_veo(image_path, scene, duration, output_path, is_shorts, api_key)
        if veo_ok:
            # Mix TTS voice over Veo ambient audio
            _mix_voice_into_video(output_path, audio_path)
            return True

    # KenBurns fallback — always works
    _build_kenburns(image_path, audio_path, duration, output_path, is_shorts)
    return False


def generate_all_scenes_parallel(
    scenes: list,
    image_paths: list,
    audio_paths: list,
    durations: list,
    workspace: Path,
    is_shorts: bool,
) -> list:
    """
    Generate all scene videos in parallel, distributing across Gemini keys.
    Each key handles different scenes simultaneously for maximum speed.
    Guaranteed: every scene index has a result (KenBurns used if Veo fails).
    """
    all_keys = _available_keys()
    n_keys   = max(len(all_keys), 1)
    n_scenes = len(scenes)

    # Pre-create output paths
    vid_paths = [workspace / f"scene_{i}" / "scene.mp4" for i in range(n_scenes)]
    for p in vid_paths:
        p.parent.mkdir(parents=True, exist_ok=True)

    # results dict — pre-fill with paths so KeyError is impossible
    results: dict = {i: vid_paths[i] for i in range(n_scenes)}
    lock = threading.Lock()

    def process_scene(idx: int):
        img = image_paths[idx]
        aud = audio_paths[idx]
        dur = durations[idx]
        out = vid_paths[idx]
        key = all_keys[idx % n_keys] if all_keys else ""

        suffix = f"…{key[-8:]}" if key else "none"
        log.info(f"[Scene {idx+1}/{n_scenes}] gen | key={suffix}")
        try:
            generate_scene_video(img, scenes[idx], aud, dur, out, is_shorts, api_key=key)
        except Exception as e:
            log.error(f"[Scene {idx+1}] Unhandled error: {e} → KenBurns fallback")
            try:
                _build_kenburns(img, aud, dur, out, is_shorts)
            except Exception as e2:
                log.error(f"[Scene {idx+1}] KenBurns also failed: {e2}")
        with lock:
            results[idx] = out

    max_workers = min(n_keys, 4, n_scenes)
    with ThreadPoolExecutor(max_workers=max(max_workers, 1)) as pool:
        futures = {pool.submit(process_scene, i): i for i in range(n_scenes)}
        for fut in as_completed(futures):
            i = futures[fut]
            try:
                fut.result()
                print(f"  ✅ Scene {i+1}/{n_scenes} done")
            except Exception as e:
                log.error(f"[Scene {i+1}] Future exception: {e}")
                # Already handled inside process_scene; result already set

    return [results[i] for i in range(n_scenes)]


# ── Veo 3.1 Generation ────────────────────────────────────────────────────────

def _generate_veo(
    image_path: Path,
    scene: dict,
    duration: float,
    output_path: Path,
    is_shorts: bool,
    api_key: str,
) -> bool:
    """
    Generate HD video using Veo 3.1 via Google AI Studio.
    Model IDs: veo-3.1-lite-generate-preview / veo-3.1-generate-preview
    All use the same GEMINI_API_KEY.
    Generates native audio so ambient sound matches the visuals.
    """
    aspect       = "9:16" if is_shorts else "16:9"
    veo_duration = min(max(int(duration), 5), 8)   # Veo supports 5–8s
    is_kids      = scene.get("is_kids", False)

    prompt_text = (
        f"{scene.get('image_prompt', 'cinematic scene')[:400]} | "
        f"HD 1080p, {aspect} aspect ratio, smooth cinematic camera motion, "
        f"{'colorful child-friendly animation, safe for kids' if is_kids else 'professional cinematography, film grain'}"
    )

    try:
        img_bytes = image_path.read_bytes()
    except Exception as e:
        log.warning(f"[Veo] Cannot read image: {e}")
        return False

    # ── Try google-genai SDK first ────────────────────────────────────────────
    client = _genai_client(api_key)
    if client:
        result = _veo_sdk(client, img_bytes, prompt_text, aspect,
                          veo_duration, output_path)
        if result:
            return True

    # ── REST API fallback ─────────────────────────────────────────────────────
    img_b64 = base64.b64encode(img_bytes).decode()
    return _veo_rest(img_b64, prompt_text, aspect, veo_duration, output_path, api_key)


def _veo_sdk(client, img_bytes: bytes, prompt: str, aspect: str,
             duration: int, output_path: Path) -> bool:
    """Attempt Veo video generation via google-genai SDK."""
    try:
        from google.genai import types

        for model in _VEO_MODELS:
            try:
                operation = client.models.generate_videos(
                    model=model,
                    prompt=prompt,
                    config=types.GenerateVideoConfig(
                        aspect_ratio=aspect,
                        duration_seconds=duration,
                        number_of_videos=1,
                        enhance_prompt=True,
                        generate_audio=True,   # Veo adds matching ambient audio
                    ),
                    image=types.Image(image_bytes=img_bytes),
                )
                # Poll until complete
                deadline = time.time() + 300   # 5 min timeout
                while not operation.done and time.time() < deadline:
                    time.sleep(10)
                    operation = client.operations.get(operation=operation)

                if operation.done and operation.result:
                    videos = operation.result.generated_videos
                    if videos:
                        vid = videos[0].video
                        if hasattr(vid, "video_bytes") and vid.video_bytes:
                            output_path.write_bytes(vid.video_bytes)
                            log.info(f"[Veo SDK] ✅ {model} | {len(vid.video_bytes)//1024}KB")
                            return True
                        if hasattr(vid, "uri") and vid.uri:
                            _download(vid.uri, output_path)
                            log.info(f"[Veo SDK] ✅ {model} (URI)")
                            return True
            except Exception as e:
                status = _http_status(e)
                if status in (400, 404):
                    log.debug(f"[Veo SDK] {model} not available ({status})")
                    continue
                raise   # re-raise for outer handler

    except Exception as e:
        status = _http_status(e)
        if status == 429:
            log.warning("[Veo SDK] Rate limited")
        else:
            log.debug(f"[Veo SDK] Failed: {e}")
    return False


def _veo_rest(img_b64: str, prompt: str, aspect: str, duration: int,
              output_path: Path, api_key: str) -> bool:
    """Attempt Veo video generation via direct REST API (no SDK required)."""
    for model in _VEO_MODELS:
        try:
            endpoint = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                f"{model}:predictLongRunning?key={api_key}"
            )
            payload = {
                "instances": [{
                    "prompt": prompt,
                    "image":  {"bytesBase64Encoded": img_b64},
                }],
                "parameters": {
                    "aspectRatio"    : aspect,
                    "durationSeconds": duration,
                    "numberOfVideos" : 1,
                    "enhancePrompt"  : True,
                    "generateAudio"  : True,
                    "outputOptions"  : {"mimeType": "video/mp4"},
                },
            }
            req = urllib.request.Request(
                endpoint,
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            resp  = json.loads(urllib.request.urlopen(req, timeout=30).read())
            op    = resp.get("name", "")
            if not op:
                continue

            log.info(f"[Veo REST] Operation started: …{op[-20:]} ({model})")
            video_bytes = _veo_poll_rest(op, api_key)
            if video_bytes:
                output_path.write_bytes(video_bytes)
                log.info(f"[Veo REST] ✅ {model} | {len(video_bytes)//1024}KB")
                return True

        except Exception as e:
            status = _http_status(e)
            if status == 429:
                _mark_rate_limited(api_key)
                return False
            if status in (400, 401, 403, 404):
                log.debug(f"[Veo REST] {model} — HTTP {status}, trying next")
                continue
            log.warning(f"[Veo REST] {model} error ({status}): {e}")

    return False


def _veo_poll_rest(op_name: str, api_key: str, timeout: int = 300) -> bytes:
    """Poll a long-running Veo REST operation until done. Returns video bytes or b''."""
    poll_url = f"https://generativelanguage.googleapis.com/v1beta/{op_name}?key={api_key}"
    deadline = time.time() + timeout
    interval = 8

    while time.time() < deadline:
        time.sleep(interval)
        interval = min(interval * 1.4, 25)   # exponential back-off up to 25s

        try:
            req  = urllib.request.Request(poll_url)
            data = json.loads(urllib.request.urlopen(req, timeout=20).read())
        except Exception as e:
            log.debug(f"[Veo Poll] Error: {e}")
            continue

        if not data.get("done"):
            continue
        if "error" in data:
            log.warning(f"[Veo Poll] Server error: {data['error']}")
            return b""

        # Extract video — handle multiple response shapes from different models
        try:
            resp    = data.get("response", {})
            samples = (
                resp.get("generateVideoResponse", {}).get("generatedSamples")
                or resp.get("videos", [])
                or []
            )
            if not samples:
                log.warning("[Veo Poll] No samples in response")
                return b""

            vid_info  = samples[0].get("video", samples[0])
            b64_data  = vid_info.get("bytesBase64Encoded", "")
            video_uri = vid_info.get("uri", "")

            if b64_data:
                return base64.b64decode(b64_data)
            if video_uri:
                req2 = urllib.request.Request(video_uri)
                return urllib.request.urlopen(req2, timeout=90).read()
        except Exception as e:
            log.warning(f"[Veo Poll] Parse error: {e}")
            return b""

    log.warning("[Veo Poll] Timed out after 5 minutes")
    return b""


# ── KenBurns Fallback ─────────────────────────────────────────────────────────

def _build_kenburns(
    image_path: Path,
    audio_path: Path,
    duration: float,
    output_path: Path,
    is_shorts: bool,
):
    """
    Static image + Ken Burns zoom effect + voice audio.
    Always works — no API key, no internet, pure ffmpeg.
    """
    log.info(f"[KenBurns] Building {output_path.name} ({duration:.1f}s)")

    if is_shorts:
        w, h, scale = 1080, 1920, "scale=1080:-2"
        crop = "crop=1080:1920"
    else:
        w, h, scale = 1920, 1080, "scale=1920:-2"
        crop = "crop=1920:1080"

    zoom_expr = "zoom+0.0013" if hash(str(output_path)) % 2 == 0 else "max(1.5-0.0013*on,1.0)"
    d_frames  = int((duration + 0.5) * 30)
    dur_padded = duration + 0.3

    has_audio = audio_path.exists() and audio_path.stat().st_size > 100

    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-loop", "1", "-i", str(image_path),
    ]
    if has_audio:
        cmd += ["-i", str(audio_path)]
    cmd += [
        "-c:v", "libx264",
        "-t", str(dur_padded),
        "-pix_fmt", "yuv420p",
        "-vf", f"{scale},zoompan=z='{zoom_expr}':d={d_frames}:s={w}x{h}:fps=30,{crop},format=yuv420p",
        "-r", "30",
    ]
    if has_audio:
        cmd += ["-c:a", "aac", "-b:a", "192k"]
    else:
        cmd += ["-an"]
    cmd.append(str(output_path))

    subprocess.run(cmd, check=True, capture_output=True)


# ── Voice / Veo Audio Mixer ───────────────────────────────────────────────────

def _mix_voice_into_video(video_path: Path, audio_path: Path):
    """
    Replace or mix TTS voice into a Veo-generated video.
    Veo ambient audio kept at 15%, TTS voice at 100%.
    FIXED: Uses a separate temp file to avoid Windows file-lock issues.
    """
    if not audio_path.exists() or audio_path.stat().st_size < 100:
        return

    # Use a distinct temp filename to avoid in-place lock on Windows
    tmp = video_path.parent / f"_mix_tmp_{video_path.name}"
    try:
        # Check if video has an audio track
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a",
             "-show_entries", "stream=codec_type",
             "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)],
            capture_output=True, text=True, timeout=10
        )
        has_veo_audio = "audio" in probe.stdout

        if has_veo_audio:
            filter_cx = (
                "[0:a]volume=0.15[amb];"
                "[1:a]volume=1.0[tts];"
                "[amb][tts]amix=inputs=2:duration=first:dropout_transition=2"
            )
            cmd = [
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-i", str(video_path),
                "-i", str(audio_path),
                "-filter_complex", filter_cx,
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                str(tmp),
            ]
        else:
            # No audio in video — just attach the voice track
            cmd = [
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-i", str(video_path),
                "-i", str(audio_path),
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                "-shortest",
                str(tmp),
            ]

        subprocess.run(cmd, check=True, capture_output=True, timeout=120)

        # Windows: rename, not replace (avoids file-lock errors)
        if video_path.exists():
            video_path.unlink()
        tmp.rename(video_path)

    except Exception as e:
        log.warning(f"[Mix] Audio mix failed: {e}")
        if tmp.exists():
            try:
                tmp.unlink()
            except Exception:
                pass


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 7 — CONCAT  +  BACKGROUND  MUSIC
# ══════════════════════════════════════════════════════════════════════════════

def concat_scenes(scene_videos: list, output_path: Path):
    """Concatenate scene videos into the final assembled video."""
    log.info(f"[Concat] Joining {len(scene_videos)} scenes")

    # Filter out missing files defensively
    valid = [p for p in scene_videos if p.exists() and p.stat().st_size > 0]
    if not valid:
        raise RuntimeError("No valid scene videos to concatenate")

    workspace = output_path.parent
    list_file = workspace / "concat_list.txt"

    with open(list_file, "w", encoding="utf-8") as f:
        for vid in valid:
            # Use forward slashes for ffmpeg on Windows; escape single quotes
            safe = str(vid).replace("\\", "/").replace("'", "\\'")
            f.write(f"file '{safe}'\n")

    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "concat", "-safe", "0",
        "-i", str(list_file),
        "-c", "copy",
        str(output_path),
    ]
    subprocess.run(cmd, check=True)


def add_background_music(video_path: Path, music_dir: Path, final_path: Path):
    """Mix a random background track quietly behind the voiceover."""
    log.info("[BGM] Adding background music")
    files = list(music_dir.glob("*.mp3")) + list(music_dir.glob("*.wav"))
    if not files:
        log.warning("[BGM] No music files — skipping")
        shutil.copy2(video_path, final_path)
        return

    bgm = files[hash(str(video_path)) % len(files)]
    log.info(f"[BGM] Track: {bgm.name}")

    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(video_path),
        "-stream_loop", "-1", "-i", str(bgm),
        "-filter_complex",
        "[0:a]volume=1.2[v];[1:a]volume=0.08[b];[v][b]amix=inputs=2:duration=first:dropout_transition=2",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
        str(final_path),
    ]
    try:
        subprocess.run(cmd, check=True)
    except Exception as e:
        log.error(f"[BGM] Mix failed: {e} — copying without music")
        shutil.copy2(video_path, final_path)


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 8 — SUBTITLE  BURN-IN  (ffmpeg drawtext — free)
# ══════════════════════════════════════════════════════════════════════════════

def _ffmpeg_escape_path(path: str) -> str:
    """Escape a file path for use inside an ffmpeg filter option value."""
    # On Windows: convert backslashes to forward slashes, escape colons and spaces
    return path.replace("\\", "/").replace(":", "\\:").replace(" ", "\\ ")


def burn_subtitles(video_path: Path, scenes: list, output_path: Path,
                   is_kids: bool = False):
    """
    Burn captions into the video using ffmpeg drawtext.
    Uses textfile= (temp .txt file per subtitle) instead of text='...'
    This completely avoids ALL special character escaping issues:
    apostrophes, colons, backslashes, exclamation marks, quotes, etc.
    """
    log.info("[Subtitles] Burning captions")
    total_dur = get_audio_duration(video_path)
    n = len(scenes)

    if n == 0 or total_dur <= 0:
        shutil.copy2(video_path, output_path)
        return

    per_scene = total_dur / n
    font_size  = 52 if is_kids else 40
    font_size_big = font_size + 10

    # Find a font file
    font_candidates = [
        r"C:/Windows/Fonts/arialbd.ttf",
        r"C:/Windows/Fonts/arial.ttf",
        r"C:/Windows/Fonts/DejaVuSans-Bold.ttf",
        r"C:/Windows/Fonts/DejaVuSans.ttf",
    ]
    font_path = next((f for f in font_candidates if Path(f).exists()), "")
    font_opt  = f"fontfile='{_ffmpeg_escape_path(font_path)}':" if font_path else ""

    # Temp dir for subtitle text files  (avoids ALL escaping headaches)
    sub_dir = video_path.parent / "_subtitles"
    sub_dir.mkdir(parents=True, exist_ok=True)

    filters = []
    for i, scene in enumerate(scenes):
        raw_text = scene.get("subtitle", scene.get("text", ""))[:120]
        raw_text = raw_text.strip().replace("\n", " ")
        if not raw_text:
            continue

        t0 = i * per_scene
        t1 = t0 + per_scene

        # Write subtitle text to a temp file — sidesteps all escaping
        txt_file = sub_dir / f"sub_{i}.txt"
        txt_file.write_text(raw_text, encoding="utf-8")
        tf_escaped = _ffmpeg_escape_path(str(txt_file))

        filters.append(
            f"drawtext={font_opt}"
            f"textfile='{tf_escaped}':"
            f"fontcolor=white:fontsize={font_size}:"
            f"x=(w-text_w)/2:y=h-th-60:"
            f"box=1:boxcolor=black@0.6:boxborderw=8:"
            f"enable='between(t,{t0:.2f},{t1:.2f})'"
        )

        # Kids screen-text overlay (top-center, bigger, yellow)
        st = scene.get("screen_text", "").strip()
        if st and is_kids:
            st_file = sub_dir / f"st_{i}.txt"
            st_file.write_text(st[:60], encoding="utf-8")
            stf_escaped = _ffmpeg_escape_path(str(st_file))
            end_st = min(t0 + 2.5, t1)
            filters.append(
                f"drawtext={font_opt}"
                f"textfile='{stf_escaped}':"
                f"fontcolor=yellow:fontsize={font_size_big}:"
                f"x=(w-text_w)/2:y=80:"
                f"box=1:boxcolor=black@0.5:boxborderw=6:"
                f"enable='between(t,{t0:.2f},{end_st:.2f})'"
            )

    if not filters:
        shutil.copy2(video_path, output_path)
        return

    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-i", str(video_path),
        "-vf", ",".join(filters),
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-c:a", "copy",
        str(output_path),
    ]
    try:
        subprocess.run(cmd, check=True)
        log.info(f"[Subtitles] ✅ {output_path.name}")
    except subprocess.CalledProcessError as e:
        log.error(f"[Subtitles] ffmpeg failed: {e}")
        shutil.copy2(video_path, output_path)
    finally:
        # Clean up temp subtitle text files
        try:
            shutil.rmtree(sub_dir, ignore_errors=True)
        except Exception:
            pass



# ══════════════════════════════════════════════════════════════════════════════
#  STEP 9 — THUMBNAIL  GENERATION
# ══════════════════════════════════════════════════════════════════════════════

def generate_thumbnail(thumbnail_prompt: str, niche_cfg, output_path: Path) -> Path:
    """
    Generate a 1280x720 YouTube thumbnail.
    Primary  : Nano Banana 2 (gemini-3.1-flash-image-preview)
    Fallback : Pollinations.ai (free)
    """
    style = niche_cfg.image_style if niche_cfg else ""
    full  = (
        f"YouTube thumbnail design: {thumbnail_prompt}, "
        f"bold title text overlay, high contrast colors, eye-catching, "
        f"{style}, professional 4K thumbnail"
    )

    key = _pick_key()
    if key:
        try:
            ok = _image_nanobanana(full, 1280, 720, output_path, key)
            if ok:
                log.info(f"[Thumbnail] Nano Banana 2 ✅ {output_path.name}")
                return output_path
        except Exception:
            pass

    # Pollinations fallback
    _image_pollinations(full, 1280, 720, output_path)
    log.info(f"[Thumbnail] Pollinations ✅ {output_path.name}")
    return output_path


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 5b — AUTO-CLIP  (standard video → Shorts)
# ══════════════════════════════════════════════════════════════════════════════

def auto_clip_video_to_shorts(input_video: Path, output_dir: Path,
                               max_dur: int = 59) -> list:
    """Segment a 16:9 video into 9:16 Shorts clips of ≤max_dur seconds."""
    log.info(f"[AutoClip] Clipping {input_video.name} into ≤{max_dur}s Shorts")
    total = get_audio_duration(input_video)
    output_dir.mkdir(parents=True, exist_ok=True)
    clips = []
    num   = max(1, int(total // max_dur) + (1 if total % max_dur > 5 else 0))

    for i in range(num):
        out = output_dir / f"{input_video.stem}_pt{i+1}.mp4"
        cmd = [
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-ss", str(i * max_dur), "-t", str(max_dur),
            "-i", str(input_video),
            "-vf", "crop=ih*9/16:ih,scale=1080:1920",
            "-c:v", "libx264", "-preset", "veryfast",
            "-c:a", "aac", "-b:a", "192k",
            str(out),
        ]
        try:
            subprocess.run(cmd, check=True)
            clips.append(out)
        except Exception as e:
            log.error(f"[AutoClip] Clip {i+1} failed: {e}")

    return clips
