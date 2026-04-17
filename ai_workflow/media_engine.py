"""
ai_workflow/media_engine.py  —  v3
====================================
Blocking, progress-visible media generation engine for ShortsBot AI Workflow.

ALL three generation tasks share the same GEMINI_API_KEY_*:
  • Nano Banana 2  → image gen  (gemini-3.1-flash-image-preview)
  • Veo 3.1        → video gen  (veo-3.1-lite-generate-preview / veo-3.1-generate-preview)
  • Veo 2.0        → fallback   (veo-2.0-generate-001)

Per-scene flow (blocking):
  [1] Generate image with Nano Banana 2  — WAIT until image bytes arrive
  [2] Send image + prompt to Veo 3.1    — WAIT polling every 10s (up to 10 min)
  [3] Save video file                    — then proceed
  Fallback: KenBurns zoom animation     — pure ffmpeg, no API, always works

Changes in v3:
  - Fixed SDK class name: GenerateVideosConfig (was GenerateVideoConfig)
  - Proper blocking poll: operations.get(operation=op) until op.done
  - Used Video.save() for direct file save without URL download
  - Per-scene progress visible to terminal (▶ each step)
  - Sequential fallback when only 1 key (no false parallelism)
  - NanoBanana must fully succeed before Veo is called
  - burn_subtitles: textfile= approach (apostrophe/special char safe)
  - upload channel dict: real_name, folder_name, token_path all populated
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
#  THREAD-SAFE KEY POOL
# ══════════════════════════════════════════════════════════════════════════════

_key_pool_lock = threading.Lock()
_rate_limited: set = set()   # 429 / quota — blacklisted this session
_invalid_keys: set = set()   # 400/401/403 — permanently invalid


def _all_gemini_keys() -> list:
    """Return all GEMINI_API_KEY + GEMINI_API_KEY_2..8 from env."""
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
    all_keys = _all_gemini_keys()
    with _key_pool_lock:
        return [k for k in all_keys if k not in _rate_limited and k not in _invalid_keys]


def _mark_rate_limited(key: str):
    with _key_pool_lock:
        _rate_limited.add(key)
    log.warning(f"[KeyPool] …{key[-8:]} rate-limited → skipping for this session")


def _mark_invalid(key: str):
    with _key_pool_lock:
        _invalid_keys.add(key)
    log.warning(f"[KeyPool] …{key[-8:]} invalid → permanently blacklisted")


def _http_status(exc: Exception) -> int:
    code = getattr(exc, "code", None)
    if code:
        return int(code)
    try:
        return int(str(exc).split("HTTP Error ")[1].split(":")[0])
    except Exception:
        return 500


def _genai_client(api_key: str):
    """Return a google.genai Client or None if SDK not installed."""
    try:
        from google import genai
        return genai.Client(api_key=api_key)
    except ImportError:
        return None


# ══════════════════════════════════════════════════════════════════════════════
#  UTILITIES
# ══════════════════════════════════════════════════════════════════════════════

def _download(url: str, dest: Path, retries: int = 3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "Mozilla/5.0 ShortsBot/10"}
            )
            with urllib.request.urlopen(req, timeout=90) as r, open(dest, "wb") as f:
                f.write(r.read())
            return
        except Exception as e:
            log.warning(f"[Download] Attempt {attempt+1}/{retries}: {e}")
            time.sleep(2 ** attempt)
    raise RuntimeError(f"Download failed after {retries} tries: {url[:80]}")


def get_audio_duration(path: Path) -> float:
    try:
        res = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True, timeout=15
        )
        val = res.stdout.strip()
        return float(val) if val else 5.0
    except Exception:
        return 5.0


def _create_silent_audio(output_path: Path, duration: float = 5.0):
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
             "-t", str(duration), "-q:a", "9", "-acodec", "libmp3lame", str(output_path)],
            check=True, capture_output=True, timeout=15
        )
    except Exception:
        pass


def _create_blank_image(output_path: Path, w: int = 1080, h: int = 1920):
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-f", "lavfi",
             "-i", f"color=c=0x1a1a2e:s={w}x{h}:r=1",
             "-vframes", "1", str(output_path)],
            check=True, capture_output=True, timeout=10
        )
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 3 — VOICE GENERATION
#  Priority: ElevenLabs → Edge TTS
# ══════════════════════════════════════════════════════════════════════════════

def generate_voice(text: str, output_path: Path, niche_cfg=None) -> float:
    el_key = os.getenv("ELEVENLABS_API_KEY", "").strip()
    if el_key:
        is_kids = getattr(niche_cfg, "is_kids", False)
        if is_kids:
            voice_id = os.getenv("ELEVENLABS_VOICE_ID_KIDS", "AZnzlk1XvdvUeBnXmlld")
        else:
            default_vid = getattr(niche_cfg, "elevenlabs_voice_id", "21m00Tcm4TlvDq8ikWAM") or "21m00Tcm4TlvDq8ikWAM"
            voice_id = os.getenv("ELEVENLABS_VOICE_ID_ADULT", default_vid)

        if _voice_elevenlabs(text, voice_id, el_key, output_path):
            dur = get_audio_duration(output_path)
            print(f"    ✅ ElevenLabs voice — {dur:.1f}s")
            return dur
        print("    ⚠️  ElevenLabs failed → Edge TTS fallback")

    voice_model = getattr(niche_cfg, "voice_model", None) or "en-US-ChristopherNeural"
    return _voice_edge_tts(text, voice_model, output_path)


def _voice_elevenlabs(text: str, voice_id: str, api_key: str, output_path: Path) -> bool:
    try:
        payload = json.dumps({
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        }).encode()
        req = urllib.request.Request(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            data=payload,
            headers={"xi-api-key": api_key, "Content-Type": "application/json",
                     "Accept": "audio/mpeg"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            output_path.write_bytes(resp.read())
        return output_path.stat().st_size > 1024
    except Exception as e:
        log.warning(f"[ElevenLabs] {e}")
        return False


def _voice_edge_tts(text: str, voice_model: str, output_path: Path) -> float:
    print(f"    🎙️  Edge TTS — voice: {voice_model}")
    rate = "-5%" if any(v in voice_model for v in ("Ana", "Swara", "Jenny")) else "+5%"
    try:
        subprocess.run(
            ["python", "-m", "edge_tts", "--voice", voice_model,
             "--text", text, "--write-media", str(output_path), "--rate", rate],
            check=True, capture_output=True, timeout=90
        )
        dur = get_audio_duration(output_path)
        print(f"    ✅ Edge TTS done — {dur:.1f}s")
        return dur
    except Exception as e:
        log.error(f"[EdgeTTS] {e}")
        _create_silent_audio(output_path, 5.0)
        return 5.0


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 5a — IMAGE GENERATION (Nano Banana 2)
#  Primary : gemini-3.1-flash-image-preview (same GEMINI_API_KEY)
#  Fallback: Pollinations.ai (no key, always free)
# ══════════════════════════════════════════════════════════════════════════════

def generate_image(prompt: str, is_shorts: bool, output_path: Path,
                   style_hint: str = "") -> Path:
    """Generate scene image. Returns output_path when done (blocking)."""
    w, h = (1080, 1920) if is_shorts else (1920, 1080)
    full_prompt = (f"{prompt}, {style_hint}" if style_hint and style_hint not in prompt else prompt)[:500]

    key = _available_keys()[0] if _available_keys() else ""
    if key:
        print(f"    🎨 Nano Banana 2 generating image…", end="", flush=True)
        if _image_nanobanana(full_prompt, w, h, output_path, key):
            size_kb = output_path.stat().st_size // 1024
            print(f" ✅ {size_kb}KB")
            return output_path
        print(f" ❌ failed → Pollinations fallback")

    print(f"    🎨 Pollinations.ai generating image…", end="", flush=True)
    _image_pollinations(full_prompt, w, h, output_path)
    if output_path.exists():
        print(f" ✅ {output_path.stat().st_size//1024}KB")
    return output_path


def _image_nanobanana(prompt: str, w: int, h: int, output_path: Path, api_key: str) -> bool:
    """
    Image generation via gemini-3.1-flash-image-preview (Nano Banana 2 equivalent).
    Uses google-genai SDK. Returns True if image saved successfully.
    """
    client = _genai_client(api_key)
    if client:
        try:
            from google.genai import types as gtypes
            resp = client.models.generate_content(
                model="gemini-3.1-flash-image-preview",
                contents=prompt,
                config=gtypes.GenerateContentConfig(
                    response_modalities=["image"],
                ),
            )
            for part in resp.candidates[0].content.parts:
                if hasattr(part, "inline_data") and part.inline_data:
                    data = part.inline_data.data
                    if isinstance(data, str):
                        data = base64.b64decode(data)
                    output_path.write_bytes(data)
                    if output_path.stat().st_size > 1024:
                        return True
        except Exception as e:
            status = _http_status(e)
            if status == 429:
                _mark_rate_limited(api_key)
            elif status in (400, 401, 403):
                _mark_invalid(api_key)
            log.debug(f"[NanoBanana2 SDK] ({status}): {e}")

    # REST fallback
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
            endpoint, data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json"}, method="POST"
        )
        data = json.loads(urllib.request.urlopen(req, timeout=60).read())
        for part in data["candidates"][0]["content"]["parts"]:
            if "inlineData" in part:
                output_path.write_bytes(base64.b64decode(part["inlineData"]["data"]))
                if output_path.stat().st_size > 1024:
                    return True
    except Exception as e:
        status = _http_status(e)
        if status == 429:
            _mark_rate_limited(api_key)
        log.debug(f"[NanoBanana2 REST] ({status}): {e}")

    return False


def _image_pollinations(prompt: str, w: int, h: int, output_path: Path):
    safe = urllib.parse.quote(prompt[:400])
    seed = int(time.time() * 1000) % 999983
    url  = (f"https://image.pollinations.ai/prompt/{safe}"
            f"?width={w}&height={h}&nologo=true&seed={seed}&model=flux&enhance=true")
    try:
        _download(url, output_path)
    except Exception as e:
        log.error(f"[Pollinations] {e}")
        _create_blank_image(output_path, w, h)


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 5b — VEO 3.1 VIDEO GENERATION (blocking with progress)
#
#  Flow per scene:
#    1. generate_image()  — wait until image is ready  (blocking)
#    2. _generate_veo()   — start LRO, poll every 10s up to 10 min (blocking)
#    3. Video.save(path)  — save directly via SDK
#    fallback: KenBurns zoom animation via ffmpeg
# ══════════════════════════════════════════════════════════════════════════════

_VEO_MODELS = [
    "veo-3.1-lite-generate-preview",
    "veo-3.1-generate-preview",
    "veo-2.0-generate-001",
]

VEO_TIMEOUT = 600   # 10 minutes max per scene (Veo is slow — this is normal)
VEO_POLL_INTERVAL = 12   # seconds between each poll


def generate_scene_video(
    image_path: Path,
    scene: dict,
    audio_path: Path,
    duration: float,
    output_path: Path,
    is_shorts: bool,
    api_key: str = "",
    scene_num: int = 0,
    total_scenes: int = 0,
) -> bool:
    """
    Generate one scene video. BLOCKING — waits for Veo to fully complete.

    Flow:
      1. NanoBanana image must already be at image_path (caller ensures this)
      2. Submit to Veo 3.1 → poll until done → save video
      3. Mix TTS voice over Veo ambient audio
      4. If Veo fails → KenBurns fallback (always works)

    Returns True if Veo AI video was created, False if KenBurns was used.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    label = f"Scene {scene_num}/{total_scenes}" if total_scenes else "Scene"

    # Validate image exists
    if not image_path.exists() or image_path.stat().st_size < 1024:
        print(f"    ⚠️  [{label}] Image missing → KenBurns fallback")
        _build_kenburns(image_path, audio_path, duration, output_path, is_shorts)
        return False

    # Try Veo if a key is available
    if api_key and api_key not in _rate_limited and api_key not in _invalid_keys:
        print(f"    🎬 [{label}] Submitting to Veo 3.1… (may take 3–8 min, please wait)")
        veo_ok = _generate_veo(image_path, scene, duration, output_path, is_shorts, api_key, label)
        if veo_ok:
            print(f"    ✅ [{label}] Veo video ready — mixing voice…")
            _mix_voice_into_video(output_path, audio_path)
            print(f"    ✅ [{label}] Scene complete")
            return True
        print(f"    ⚠️  [{label}] Veo failed → KenBurns fallback")

    print(f"    🎞️  [{label}] KenBurns animation (ffmpeg zoom)…", end="", flush=True)
    _build_kenburns(image_path, audio_path, duration, output_path, is_shorts)
    print(f" ✅ done")
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
    Generate all scene videos distributing across available Gemini keys.
    Each key = one parallel worker thread.
    Guaranteed: every index has a result path (KenBurns if Veo fails).
    """
    avail    = _available_keys()
    n_keys   = max(len(avail), 1)
    n_scenes = len(scenes)

    # Pre-create output paths
    vid_paths = [workspace / f"scene_{i}" / "scene.mp4" for i in range(n_scenes)]
    for p in vid_paths:
        p.parent.mkdir(parents=True, exist_ok=True)

    results = {i: vid_paths[i] for i in range(n_scenes)}
    lock = threading.Lock()

    def process_scene(idx: int):
        img = image_paths[idx]
        aud = audio_paths[idx]
        dur = durations[idx]
        out = vid_paths[idx]
        key = avail[idx % n_keys] if avail else ""

        print(f"\n  ─── Scene {idx+1}/{n_scenes} ─────────────────────")
        try:
            generate_scene_video(
                image_path=img,
                scene=scenes[idx],
                audio_path=aud,
                duration=dur,
                output_path=out,
                is_shorts=is_shorts,
                api_key=key,
                scene_num=idx + 1,
                total_scenes=n_scenes,
            )
        except Exception as e:
            log.error(f"[Scene {idx+1}] Unexpected error: {e}")
            try:
                _build_kenburns(img, aud, dur, out, is_shorts)
                print(f"    ✅ [Scene {idx+1}] Emergency KenBurns saved")
            except Exception as e2:
                log.error(f"[Scene {idx+1}] KenBurns also failed: {e2}")

        with lock:
            results[idx] = out

    # Limit workers to number of keys (don't hammer single key in parallel)
    max_workers = min(n_keys, 4, n_scenes)
    print(f"\n  ⚡ {n_scenes} scenes × {max_workers} parallel workers ({n_keys} key(s))")
    with ThreadPoolExecutor(max_workers=max(max_workers, 1)) as pool:
        futures = {pool.submit(process_scene, i): i for i in range(n_scenes)}
        for fut in as_completed(futures):
            i = futures[fut]
            try:
                fut.result()
            except Exception as e:
                log.error(f"[Scene {i+1}] Future error: {e}")

    return [results[i] for i in range(n_scenes)]


# ── Veo Generation (SDK + REST fallback) ─────────────────────────────────────

def _generate_veo(
    image_path: Path,
    scene: dict,
    duration: float,
    output_path: Path,
    is_shorts: bool,
    api_key: str,
    label: str = "Scene",
) -> bool:
    """
    Submit image + prompt to Veo 3.1, poll until done (blocking).
    Uses google-genai SDK (GenerateVideosConfig — note the 's').
    """
    aspect       = "9:16" if is_shorts else "16:9"
    veo_duration = min(max(int(duration), 5), 8)
    is_kids      = scene.get("is_kids", False)

    prompt = (
        f"{scene.get('image_prompt', 'cinematic scene')[:350]}, "
        f"{'colorful friendly animation safe for kids' if is_kids else 'professional cinematic HD'}, "
        f"{aspect} aspect ratio, smooth camera motion, 1080p"
    )

    try:
        img_bytes = image_path.read_bytes()
    except Exception as e:
        log.warning(f"[Veo] Cannot read image: {e}")
        return False

    # ── SDK approach (google-genai ≥ 1.x) ────────────────────────────────────
    client = _genai_client(api_key)
    if client:
        try:
            from google.genai import types as gtypes

            for model in _VEO_MODELS:
                try:
                    print(f"    ⏳ [{label}] Veo model: {model}", end="", flush=True)
                    operation = client.models.generate_videos(
                        model=model,
                        prompt=prompt,
                        image=gtypes.Image(image_bytes=img_bytes, mime_type="image/jpeg"),
                        config=gtypes.GenerateVideosConfig(
                            aspect_ratio=aspect,
                            duration_seconds=veo_duration,
                            number_of_videos=1,
                            enhance_prompt=True,
                            generate_audio=True,
                        ),
                    )

                    # ── Blocking poll ────────────────────────────────────────
                    deadline = time.time() + VEO_TIMEOUT
                    elapsed  = 0
                    while not operation.done:
                        if time.time() > deadline:
                            print(f"\n    ⏱️  [{label}] Veo timed out after {VEO_TIMEOUT//60}m")
                            break
                        time.sleep(VEO_POLL_INTERVAL)
                        elapsed += VEO_POLL_INTERVAL
                        print(f".", end="", flush=True)   # progress dot every 12s
                        try:
                            operation = client.operations.get(operation=operation)
                        except Exception as poll_err:
                            log.debug(f"[Veo Poll] {poll_err}")
                            continue

                    printf_nl = True
                    if operation.done:
                        if operation.error:
                            print(f" ❌ server error: {operation.error}")
                            continue   # try next model

                        generated = getattr(operation.result, "generated_videos", None) or []
                        if not generated:
                            print(f" ❌ no videos returned")
                            continue

                        vid = generated[0].video
                        print(f"\n    💾 [{label}] Saving video ({model})…", end="", flush=True)

                        # Try .save() first (SDK built-in)
                        if hasattr(vid, "save") and vid.uri:
                            try:
                                vid.save(str(output_path))
                                if output_path.exists() and output_path.stat().st_size > 10240:
                                    sz = output_path.stat().st_size // 1024
                                    print(f" ✅ {sz}KB")
                                    return True
                            except Exception as save_err:
                                log.debug(f"[Veo] vid.save() failed: {save_err}")

                        # video_bytes direct
                        if getattr(vid, "video_bytes", None):
                            output_path.write_bytes(vid.video_bytes)
                            if output_path.stat().st_size > 10240:
                                sz = output_path.stat().st_size // 1024
                                print(f" ✅ {sz}KB (bytes)")
                                return True

                        # URI download
                        if getattr(vid, "uri", None):
                            try:
                                _download(vid.uri, output_path)
                                if output_path.exists() and output_path.stat().st_size > 10240:
                                    sz = output_path.stat().st_size // 1024
                                    print(f" ✅ {sz}KB (URI)")
                                    return True
                            except Exception as dl_err:
                                log.debug(f"[Veo] URI download failed: {dl_err}")

                        print(f" ❌ could not extract video bytes")
                        continue

                except Exception as model_err:
                    status = _http_status(model_err)
                    if status == 429:
                        _mark_rate_limited(api_key)
                        print(f" ❌ 429 rate-limited")
                        return False
                    if status in (400, 404):
                        print(f" ❌ {status} model unavailable, trying next")
                        continue
                    print(f" ❌ {status}: {model_err}")
                    continue

        except Exception as sdk_err:
            status = _http_status(sdk_err)
            if status == 429:
                _mark_rate_limited(api_key)
            log.debug(f"[Veo SDK outer] ({status}): {sdk_err}")

    # ── REST fallback ─────────────────────────────────────────────────────────
    img_b64 = base64.b64encode(img_bytes).decode()
    return _veo_rest(img_b64, prompt, aspect, veo_duration, output_path, api_key, label)


def _veo_rest(img_b64: str, prompt: str, aspect: str, duration: int,
              output_path: Path, api_key: str, label: str = "") -> bool:
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
                endpoint, data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"}, method="POST"
            )
            resp = json.loads(urllib.request.urlopen(req, timeout=30).read())
            op   = resp.get("name", "")
            if not op:
                continue

            print(f"    ⏳ [REST] {model} operation started…", end="", flush=True)
            video_bytes = _veo_poll_rest(op, api_key)
            if video_bytes:
                output_path.write_bytes(video_bytes)
                sz = len(video_bytes) // 1024
                print(f" ✅ {sz}KB")
                return True

        except Exception as e:
            status = _http_status(e)
            if status == 429:
                _mark_rate_limited(api_key)
                return False
            log.debug(f"[Veo REST] {model} {status}: {e}")

    return False


def _veo_poll_rest(op_name: str, api_key: str) -> bytes:
    poll_url = f"https://generativelanguage.googleapis.com/v1beta/{op_name}?key={api_key}"
    deadline = time.time() + VEO_TIMEOUT
    interval = VEO_POLL_INTERVAL

    while time.time() < deadline:
        time.sleep(interval)
        interval = min(interval * 1.3, 30)
        print(f".", end="", flush=True)

        try:
            data = json.loads(urllib.request.urlopen(
                urllib.request.Request(poll_url), timeout=20).read())
        except Exception:
            continue

        if not data.get("done"):
            continue
        if "error" in data:
            log.warning(f"[Veo Poll REST] Error: {data['error']}")
            return b""

        try:
            resp    = data.get("response", {})
            samples = (resp.get("generateVideoResponse", {}).get("generatedSamples")
                       or resp.get("videos", []) or [])
            if not samples:
                return b""

            vid_info = samples[0].get("video", samples[0])
            b64_data = vid_info.get("bytesBase64Encoded", "")
            uri      = vid_info.get("uri", "")

            if b64_data:
                return base64.b64decode(b64_data)
            if uri:
                return urllib.request.urlopen(
                    urllib.request.Request(uri), timeout=90).read()
        except Exception as e:
            log.warning(f"[Veo Poll REST] Parse error: {e}")
            return b""

    print(f"\n    ⏱️  Veo REST timed out")
    return b""


# ── KenBurns Fallback ─────────────────────────────────────────────────────────

def _build_kenburns(
    image_path: Path,
    audio_path: Path,
    duration: float,
    output_path: Path,
    is_shorts: bool,
):
    """Static image + Ken Burns zoom + voice audio. Pure ffmpeg — no API needed."""
    w, h  = (1080, 1920) if is_shorts else (1920, 1080)
    scale = f"scale={w}:-2" if is_shorts else f"scale={w}:-2"
    crop  = f"crop={w}:{h}"

    # Alternate zoom direction per scene for visual variety
    zoom_in   = "zoom+0.0013"
    zoom_out  = "max(1.5-0.0013*on,1.0)"
    zoom_expr = zoom_in if hash(str(output_path)) % 2 == 0 else zoom_out
    d_frames  = int((duration + 0.5) * 30)
    dur_pad   = duration + 0.3

    has_audio = audio_path.exists() and audio_path.stat().st_size > 100

    cmd = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-loop", "1", "-i", str(image_path),
    ]
    if has_audio:
        cmd += ["-i", str(audio_path)]
    cmd += [
        "-c:v", "libx264", "-t", str(dur_pad), "-pix_fmt", "yuv420p",
        "-vf",
        f"{scale},zoompan=z='{zoom_expr}':d={d_frames}:s={w}x{h}:fps=30,{crop},format=yuv420p",
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
    Mix TTS voice into Veo video. Veo ambient audio kept at 15%, TTS at 100%.
    SAFE on Windows: writes to temp file then renames (avoids file-lock error).
    """
    if not audio_path.exists() or audio_path.stat().st_size < 100:
        return

    tmp = video_path.parent / f"_mix_tmp_{video_path.name}"
    try:
        # Check if the Veo video has an audio track
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a",
             "-show_entries", "stream=codec_type",
             "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)],
            capture_output=True, text=True, timeout=10
        )
        has_veo_audio = "audio" in probe.stdout

        if has_veo_audio:
            fc = ("[0:a]volume=0.15[amb];[1:a]volume=1.0[tts];"
                  "[amb][tts]amix=inputs=2:duration=first:dropout_transition=2")
            cmd = [
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-i", str(video_path), "-i", str(audio_path),
                "-filter_complex", fc,
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
                str(tmp),
            ]
        else:
            cmd = [
                "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                "-i", str(video_path), "-i", str(audio_path),
                "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
                str(tmp),
            ]

        subprocess.run(cmd, check=True, capture_output=True, timeout=120)

        if video_path.exists():
            video_path.unlink()
        tmp.rename(video_path)

    except Exception as e:
        log.warning(f"[Mix] {e}")
        if tmp.exists():
            try:
                tmp.unlink()
            except Exception:
                pass


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 7 — CONCAT + BACKGROUND MUSIC
# ══════════════════════════════════════════════════════════════════════════════

def concat_scenes(scene_videos: list, output_path: Path):
    valid = [p for p in scene_videos if p.exists() and p.stat().st_size > 0]
    if not valid:
        raise RuntimeError("No valid scene videos to concatenate")

    print(f"  🔗 Concatenating {len(valid)} scene(s)…", end="", flush=True)
    workspace = output_path.parent
    list_file = workspace / "concat_list.txt"

    with open(list_file, "w", encoding="utf-8") as f:
        for vid in valid:
            safe = str(vid).replace("\\", "/").replace("'", "\\'")
            f.write(f"file '{safe}'\n")

    subprocess.run(
        ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
         "-f", "concat", "-safe", "0", "-i", str(list_file),
         "-c", "copy", str(output_path)],
        check=True
    )
    sz = output_path.stat().st_size // (1024 * 1024)
    print(f" ✅ {sz}MB → {output_path.name}")


def add_background_music(video_path: Path, music_dir: Path, final_path: Path):
    files = list(music_dir.glob("*.mp3")) + list(music_dir.glob("*.wav"))
    if not files:
        log.warning("[BGM] No music files — skipping")
        shutil.copy2(video_path, final_path)
        return

    bgm = files[hash(str(video_path)) % len(files)]
    print(f"  🎵 Adding BGM: {bgm.name}…", end="", flush=True)
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
        print(f" ✅")
    except Exception as e:
        log.error(f"[BGM] {e} — copying without music")
        shutil.copy2(video_path, final_path)


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 8 — SUBTITLE BURN-IN (ffmpeg textfile= — no special char issues)
# ══════════════════════════════════════════════════════════════════════════════

def _ffmpeg_escape_path(path: str) -> str:
    """Escape a file path for use inside an ffmpeg filter string."""
    return path.replace("\\", "/").replace(":", "\\:").replace(" ", "\\ ")


def burn_subtitles(video_path: Path, scenes: list, output_path: Path,
                   is_kids: bool = False):
    """
    Burn captions using ffmpeg drawtext with textfile= (temp .txt files).
    This avoids ALL special character escaping: apostrophes, !?: etc.
    """
    print(f"  💬 Burning subtitles…", end="", flush=True)
    total_dur = get_audio_duration(video_path)
    n = len(scenes)

    if n == 0 or total_dur <= 0:
        shutil.copy2(video_path, output_path)
        print(" ⏭️  skipped (no scenes)")
        return

    per_scene     = total_dur / n
    font_size     = 52 if is_kids else 40
    font_size_big = font_size + 10

    font_candidates = [
        r"C:/Windows/Fonts/arialbd.ttf",
        r"C:/Windows/Fonts/arial.ttf",
        r"C:/Windows/Fonts/DejaVuSans-Bold.ttf",
        r"C:/Windows/Fonts/DejaVuSans.ttf",
    ]
    font_path = next((f for f in font_candidates if Path(f).exists()), "")
    font_opt  = f"fontfile='{_ffmpeg_escape_path(font_path)}':" if font_path else ""

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

        # Write to temp file — sidesteps ALL escaping issues
        txt_file = sub_dir / f"sub_{i}.txt"
        txt_file.write_text(raw_text, encoding="utf-8")
        tf_esc = _ffmpeg_escape_path(str(txt_file))

        filters.append(
            f"drawtext={font_opt}textfile='{tf_esc}':"
            f"fontcolor=white:fontsize={font_size}:"
            f"x=(w-text_w)/2:y=h-th-60:"
            f"box=1:boxcolor=black@0.6:boxborderw=8:"
            f"enable='between(t,{t0:.2f},{t1:.2f})'"
        )

        st = scene.get("screen_text", "").strip()
        if st and is_kids:
            st_file = sub_dir / f"st_{i}.txt"
            st_file.write_text(st[:60], encoding="utf-8")
            stf_esc = _ffmpeg_escape_path(str(st_file))
            end_st  = min(t0 + 2.5, t1)
            filters.append(
                f"drawtext={font_opt}textfile='{stf_esc}':"
                f"fontcolor=yellow:fontsize={font_size_big}:"
                f"x=(w-text_w)/2:y=80:"
                f"box=1:boxcolor=black@0.5:boxborderw=6:"
                f"enable='between(t,{t0:.2f},{end_st:.2f})'"
            )

    if not filters:
        shutil.copy2(video_path, output_path)
        print(" ⏭️  no text to burn")
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
        sz = output_path.stat().st_size // (1024 * 1024)
        print(f" ✅ {sz}MB")
    except subprocess.CalledProcessError as e:
        log.error(f"[Subtitles] ffmpeg failed: {e}")
        shutil.copy2(video_path, output_path)
        print(f" ⚠️  failed — copied without subs")
    finally:
        try:
            shutil.rmtree(sub_dir, ignore_errors=True)
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 9 — THUMBNAIL GENERATION
# ══════════════════════════════════════════════════════════════════════════════

def generate_thumbnail(thumbnail_prompt: str, niche_cfg, output_path: Path) -> Path:
    style = getattr(niche_cfg, "image_style", "") or ""
    full  = (
        f"YouTube thumbnail: {thumbnail_prompt}, bold eye-catching title text, "
        f"high contrast bright colors, {style}, professional 4K thumbnail design"
    )
    key = _available_keys()[0] if _available_keys() else ""
    if key:
        print(f"    🖼️  Generating thumbnail (Nano Banana 2)…", end="", flush=True)
        if _image_nanobanana(full, 1280, 720, output_path, key):
            print(f" ✅ {output_path.stat().st_size//1024}KB")
            return output_path
        print(f" ❌ → Pollinations fallback")

    print(f"    🖼️  Generating thumbnail (Pollinations)…", end="", flush=True)
    _image_pollinations(full, 1280, 720, output_path)
    print(f" ✅")
    return output_path


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 5c — AUTO-CLIP (standard 16:9 video → 9:16 Shorts)
# ══════════════════════════════════════════════════════════════════════════════

def auto_clip_video_to_shorts(input_video: Path, output_dir: Path,
                               max_dur: int = 59) -> list:
    total = get_audio_duration(input_video)
    output_dir.mkdir(parents=True, exist_ok=True)
    clips = []
    num   = max(1, int(total // max_dur) + (1 if total % max_dur > 5 else 0))

    print(f"  ✂️  Auto-clipping → {num} Short(s) of ≤{max_dur}s")
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
            print(f"    ✅ Clip {i+1}/{num}: {out.name}")
        except Exception as e:
            log.error(f"[AutoClip] Clip {i+1} failed: {e}")

    return clips
