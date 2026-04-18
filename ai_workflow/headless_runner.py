"""
ai_workflow/headless_runner.py
================================
Non-interactive version of the full 11-step AI workflow.
Called by auto_scheduler.py on AWS — no input() prompts, no terminal interaction.

KEY ENHANCEMENT: Smart Video Timeline Planning
==============================================
Instead of generating a fixed number of scenes, this runner:
1. Asks AI to plan a FULL VIDEO TIMELINE first (scenes, durations, arc, total length)
2. Targets 8–12 min for long-form (optimal YouTube algorithm sweet spot)
3. For each planned scene:
   a. Nano Banana 2 generates a UNIQUE image for that exact scene
   b. Veo 3.1 generates a video clip from that image
4. Repeats steps 2a/2b for every scene until all are done
5. Assembles all clips → BGM → Subtitles → Thumbnail → Upload

This gives each scene its own tailored visual — no repeated or generic imagery.
"""

import os
import sys
import shutil
import logging
import json
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(BASE_DIR))

try:
    from dotenv import load_dotenv
    load_dotenv(BASE_DIR / ".env")
except ImportError:
    pass

from pipeline import (
    gemini, upload_all, save_report, ensure_music, C, hdr, ok, warn, log as pl_log
)
from ai_workflow.generator import (
    generate_topic, generate_metadata, load_saved_niche, _strip_json
)
from ai_workflow.media_engine import (
    generate_voice, generate_image, generate_all_scenes_parallel,
    concat_scenes, add_background_music, burn_subtitles,
    generate_thumbnail, auto_clip_video_to_shorts,
    generate_music_lyria,
    _all_gemini_keys, _available_keys,
)

log = logging.getLogger("ShortsBot.Headless")


# ══════════════════════════════════════════════════════════════════════════════
#  YOUTUBE-OPTIMIZED VIDEO LENGTH TARGETS
# ══════════════════════════════════════════════════════════════════════════════
#
#  Research-backed optimal lengths for YouTube algorithm & monetization:
#    • Shorts        : 30–58 seconds  (algorithm favors under 60s)
#    • Mid-form      : 6–8 minutes    (good watch time, less ad revenue)
#    • Long-form     : 8–12 minutes   (★ SWEET SPOT — 2 mid-rolls + high retention)
#    • Deep-dive     : 15–20 minutes  (needs strong hook, niche audiences)
#
#  We target 10 minutes (600s) for long-form as the default.
#
SHORTS_TARGET_SEC   = 45        # 30–58 target  → 45 centre
LONGFORM_MIN_SEC    = 480       # 8 min
LONGFORM_TARGET_SEC = 600       # 10 min  ← default
LONGFORM_MAX_SEC    = 720       # 12 min

# Word count targets (2.3 words/second narration speed)
WORDS_PER_SEC       = 2.3
LONGFORM_MIN_WORDS  = int(LONGFORM_MIN_SEC * WORDS_PER_SEC)    # ~1104
LONGFORM_MAX_WORDS  = int(LONGFORM_MAX_SEC * WORDS_PER_SEC)    # ~1656


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 1 — SMART VIDEO TIMELINE PLANNING
# ══════════════════════════════════════════════════════════════════════════════

def generate_video_plan(niche_cfg, topic_data: dict, is_shorts: bool,
                        target_duration_min: int = 10) -> list[dict]:
    """
    Ask AI to plan the COMPLETE video timeline BEFORE generating any media.

    The plan specifies:
    - Total scenes
    - Each scene's narration text, duration, visual description, and mood
    - Narrative arc (hook → problem → content → CTA)

    This ensures the video hits the optimal YouTube runtime (8–12 min).
    Returns a list of scene dicts ready for media generation.
    """
    if is_shorts:
        target_sec  = SHORTS_TARGET_SEC
        word_target = int(target_sec * WORDS_PER_SEC)
        format_desc = "YouTube Short (9:16 vertical, under 58 seconds total)"
        scenes_hint = "3–5 scenes, very fast-paced, hooky every second"
        arc_hint    = "Hook (3s) → Reveal → Mic drop ending"
    else:
        target_sec  = target_duration_min * 60
        target_sec  = max(LONGFORM_MIN_SEC, min(target_sec, LONGFORM_MAX_SEC))
        word_target = int(target_sec * WORDS_PER_SEC)
        format_desc = f"YouTube long-form video (16:9), target {target_duration_min} minutes"
        n_scenes    = max(8, target_duration_min * 1)   # ~1 scene per min of content, min 8
        scenes_hint = f"Plan exactly {n_scenes}–{n_scenes + 4} scenes to fill ~{target_duration_min} minutes"
        arc_hint    = "Hook (30s) → Problem/Setup (1 min) → Main Content (7 min) → Key Takeaways (1 min) → CTA (30s)"

    image_style_hint = getattr(niche_cfg, "image_style",
                                "cinematic 8K, highly detailed, professional photography")
    is_kids = getattr(niche_cfg, "is_kids", False)

    kids_rules = ""
    if is_kids:
        forbidden = getattr(niche_cfg, "forbidden_topics", [])
        kids_rules = f"""
KIDS CONTENT RULES (MANDATORY):
- All narration: Grade-3 vocabulary, simple sentences.
- Forbidden in any scene: {', '.join(forbidden)}.
- All visuals: colorful, cartoon/animated, child-safe, no scary elements.
- Every scene ends with positive energy. Final scene = moral lesson.
- Language style: {getattr(niche_cfg, 'language_hint', 'English')}.
"""

    prompt = f"""You are an expert YouTube content planner for a faceless "{niche_cfg.display_name}" channel.

TASK: Plan a complete, high-retention video timeline with INDIVIDUAL scene details.

VIDEO TOPIC: "{topic_data['topic']}"
HOOK LINE: "{topic_data['hook']}"
VIBE/TONE: {topic_data['vibe']}
FORMAT: {format_desc}
TOTAL WORD COUNT: {word_target - 50}–{word_target + 50} words across ALL scenes.
NARRATIVE ARC: {arc_hint}
{scenes_hint}
{kids_rules}

PLANNING RULES:
1. Each scene = one distinct visual moment + narration chunk.
2. Scene duration should vary naturally: hook scenes 10–15s, content scenes 45–90s.
3. image_prompt must be EXTREMELY DETAILED and UNIQUE per scene (camera angle, subject, action, lighting, color palette, style).
   Base image style: "{image_style_hint}"
4. screen_text = a short (1–6 word) bold on-screen overlay or key stat. Empty string if none.
5. subtitle = trimmed caption version (max 10 words).
6. mood = one word describing the emotional feel of THIS scene.

RESPOND ONLY WITH A VALID JSON ARRAY — no markdown fences, no extra text:
[
  {{
    "scene_number": 1,
    "duration_sec": 15,
    "text": "Exact narration the voice-over will speak for this scene.",
    "image_prompt": "Extremely detailed unique visual prompt for this specific scene...",
    "subtitle": "Short caption (max 10 words)",
    "screen_text": "BOLD OVERLAY",
    "mood": "mysterious"
  }}
]

Make every scene COMPELLING. Viewers must be hooked from scene 1 to scene end.
Vary pacing: short punchy scenes early, longer detailed scenes in the middle, emotional close."""

    try:
        raw    = gemini(prompt)
        raw    = _strip_json(raw)
        scenes = json.loads(raw)
        if not isinstance(scenes, list) or not scenes:
            raise ValueError("Not a list")

        # Validate and clean each scene
        cleaned = []
        for s in scenes:
            cleaned.append({
                "scene_number": s.get("scene_number", len(cleaned) + 1),
                "duration_sec": max(5, int(s.get("duration_sec", 30))),
                "text"        : str(s.get("text", "")),
                "image_prompt": str(s.get("image_prompt", topic_data.get("topic", ""))),
                "subtitle"    : str(s.get("subtitle", ""))[:80],
                "screen_text" : str(s.get("screen_text", "")),
                "mood"        : str(s.get("mood", "engaging")),
                "is_kids"     : is_kids,
            })

        total_words = sum(len(s["text"].split()) for s in cleaned)
        total_sec   = sum(s["duration_sec"] for s in cleaned)
        log.info(
            f"[Plan] ✅ {len(cleaned)} scenes | "
            f"~{total_words} words | "
            f"~{total_sec//60}m {total_sec%60}s planned"
        )
        print(f"\n  📋 Video Plan: {len(cleaned)} scenes | ~{total_words} words | "
              f"~{total_sec//60}m {total_sec%60}s")
        return cleaned

    except Exception as e:
        log.error(f"[Plan] Timeline generation failed: {e} — using fallback")
        return _fallback_scene_plan(niche_cfg, topic_data, is_shorts, target_duration_min)


def _fallback_scene_plan(niche_cfg, topic_data: dict, is_shorts: bool,
                          target_min: int) -> list[dict]:
    """Simple fallback if AI plan fails — generates generic scene stubs."""
    image_style = getattr(niche_cfg, "image_style", "cinematic 8K, professional")
    topic = topic_data.get("topic", "Amazing Facts")
    hook  = topic_data.get("hook", "You won't believe this…")

    if is_shorts:
        return [
            {"scene_number": 1, "duration_sec": 5,  "text": hook,
             "image_prompt": f"Dramatic opening shot — {topic}, {image_style}, extreme close-up, vibrant lighting",
             "subtitle": "Wait for it…", "screen_text": "WATCH NOW", "mood": "dramatic", "is_kids": False},
            {"scene_number": 2, "duration_sec": 25, "text": f"Here's everything you need to know about {topic}.",
             "image_prompt": f"Main content — {topic}, {image_style}, dynamic composition, bold colors",
             "subtitle": topic[:50], "screen_text": "", "mood": "engaging", "is_kids": False},
            {"scene_number": 3, "duration_sec": 12, "text": "Follow for more amazing content like this every day!",
             "image_prompt": f"Subscribe call to action — bright neon colors, notification bell, social media icons, {image_style}",
             "subtitle": "Follow for more!", "screen_text": "FOLLOW ❤️", "mood": "cheerful", "is_kids": False},
        ]
    else:
        scenes = []
        for i in range(target_min):
            scenes.append({
                "scene_number": i + 1,
                "duration_sec": 55,
                "text": (hook if i == 0 else f"Part {i+1} of our deep dive into {topic}."),
                "image_prompt": f"Scene {i+1} — {topic}, {image_style}, unique angle {i+1}, professional lighting",
                "subtitle"    : f"Part {i+1}" if i > 0 else "Let's dive in",
                "screen_text" : "",
                "mood"        : "engaging",
                "is_kids"     : False,
            })
        return scenes


# ══════════════════════════════════════════════════════════════════════════════
#  HEADLESS PIPELINE RUNNER (main entry point)
# ══════════════════════════════════════════════════════════════════════════════

def run_headless(
    channel: dict,
    niche_key: str,
    niche_cfg,
    is_shorts: bool        = False,
    auto_clip: bool        = True,
    auto_upload: bool      = True,
    visibility: str        = "public",
    target_duration_min: int = 10,
) -> dict:
    """
    Full headless 11-step AI pipeline with smart scene planning.

    Pipeline:
      1. Generate topic idea (AI)
      2. Plan full video timeline (AI) — scenes, durations, image prompts
      3. For each scene:
         a. Generate UNIQUE image (Nano Banana 2)
         b. Generate voice (ElevenLabs / EdgeTTS)
      4. For each scene: Generate video clip (Veo 3.1 / KenBurns)
      5. Assemble all clips + background music
      6. Burn subtitles
      7. Generate thumbnail (AI)
      8. Generate SEO metadata (AI)
      9. Upload to YouTube
      10. Auto-clip Shorts from full video (if enabled)
      11. Return result dict

    Returns:
      {"success": bool, "title": str, "url": str, "error": str}
    """
    AI_WORKSPACE = BASE_DIR / "ai_workflow" / "workspace"
    AI_OUTPUT    = BASE_DIR / "ai_workflow" / "output"

    # Clean workspace
    if AI_WORKSPACE.exists():
        shutil.rmtree(AI_WORKSPACE)
    AI_WORKSPACE.mkdir(parents=True, exist_ok=True)
    AI_OUTPUT.mkdir(parents=True, exist_ok=True)

    channel_name = channel.get("real_name", channel.get("name", "channel"))
    log.info(f"[Headless] ═══ Starting headless pipeline ═══")
    log.info(f"[Headless] Channel: {channel_name} | Niche: {niche_key} | Shorts: {is_shorts}")

    try:
        # ────────────────────────────────────────────────────────────────────
        #  STEP 1 — TOPIC / IDEA
        # ────────────────────────────────────────────────────────────────────
        log.info("[Headless] Step 1 — Generating topic idea…")
        topic_data = generate_topic(niche_cfg)
        log.info(f"[Headless] Topic: {topic_data['topic']}")

        # ────────────────────────────────────────────────────────────────────
        #  STEP 2 — SMART VIDEO TIMELINE PLAN
        # ────────────────────────────────────────────────────────────────────
        log.info("[Headless] Step 2 — Planning full video timeline…")
        scenes = generate_video_plan(
            niche_cfg,
            topic_data,
            is_shorts,
            target_duration_min=target_duration_min,
        )
        if not scenes:
            raise RuntimeError("Scene plan returned empty — cannot continue")

        total_planned_sec = sum(s.get("duration_sec", 30) for s in scenes)
        log.info(f"[Headless] Plan: {len(scenes)} scenes, ~{total_planned_sec//60}m {total_planned_sec%60}s")

        # ────────────────────────────────────────────────────────────────────
        #  STEPS 3a + 3b — VOICE + IMAGE for EACH SCENE (sequential)
        #  Each scene gets its own UNIQUE image from Nano Banana 2
        # ────────────────────────────────────────────────────────────────────
        log.info(f"[Headless] Steps 3+4 — Generating voice + image for {len(scenes)} scenes…")
        audio_paths  = []
        image_paths  = []
        durations    = []

        for i, scene in enumerate(scenes):
            scene_dir = AI_WORKSPACE / f"scene_{i}"
            scene_dir.mkdir(parents=True, exist_ok=True)

            audio_path = scene_dir / "voice.mp3"
            image_path = scene_dir / "image.jpg"

            # Voice generation
            log.info(f"[Headless]   Scene {i+1}/{len(scenes)} — Voice…")
            dur = generate_voice(scene["text"], audio_path, niche_cfg)
            log.info(f"[Headless]   Scene {i+1} voice: {dur:.1f}s")

            # Image generation — UNIQUE per scene using scene's own image_prompt
            log.info(f"[Headless]   Scene {i+1}/{len(scenes)} — Image (Nano Banana 2)…")
            generate_image(
                scene["image_prompt"],       # unique prompt for THIS scene
                is_shorts,
                image_path,
                style_hint=getattr(niche_cfg, "image_style", ""),
            )
            img_size = image_path.stat().st_size // 1024 if image_path.exists() else 0
            log.info(f"[Headless]   Scene {i+1} image: {img_size}KB")

            audio_paths.append(audio_path)
            image_paths.append(image_path)
            durations.append(dur)

        # ────────────────────────────────────────────────────────────────────
        #  STEP 5 — VIDEO GENERATION (Veo 3.1 per scene)
        #  Each scene: image (already generated) → Veo video clip
        # ────────────────────────────────────────────────────────────────────
        log.info(f"[Headless] Step 5 — Veo video generation for {len(scenes)} scenes…")
        avail_keys = _available_keys()
        if avail_keys:
            log.info(f"[Headless] {len(avail_keys)} Gemini key(s) → distributing Veo across scenes")
        else:
            log.info("[Headless] No Gemini keys — KenBurns fallback for all scenes")

        scene_videos = generate_all_scenes_parallel(
            scenes      = scenes,
            image_paths = image_paths,
            audio_paths = audio_paths,
            durations   = durations,
            workspace   = AI_WORKSPACE,
            is_shorts   = is_shorts,
        )
        log.info(f"[Headless] ✅ {len(scene_videos)} scene videos ready")

        # ────────────────────────────────────────────────────────────────────
        #  STEP 6 — ASSEMBLY + BACKGROUND MUSIC
        # ────────────────────────────────────────────────────────────────────
        log.info("[Headless] Step 6 — Assembling scenes + background music…")
        safe_topic = "".join(
            c for c in topic_data["topic"][:35] if c.isalnum() or c in " _-"
        ).strip().replace(" ", "_")
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
        safe_name = f"{safe_topic}_{ts}"

        assembled  = AI_WORKSPACE / "assembled.mp4"
        with_bgm   = AI_WORKSPACE / "with_bgm.mp4"
        with_subs  = AI_WORKSPACE / "with_subs.mp4"
        final_path = AI_OUTPUT / f"{safe_name}.mp4"

        concat_scenes(scene_videos, assembled)
        log.info("[Headless] Scenes assembled")

        ensure_music()
        music_dir = BASE_DIR / "assets" / "music"
        specific_bgm = None
        key = avail_keys[0] if avail_keys else ""
        if key:
            log.info("[Headless] Generating custom Lyria 3 BGM…")
            lyria_out = AI_WORKSPACE / f"{safe_name}_bgm.mp3"
            bgm_prompt = f"Instrumental only, no vocals. {topic_data.get('vibe', 'engaging')} background music tailored for: {topic_data.get('topic', 'YouTube Video')}."
            if generate_music_lyria(bgm_prompt, lyria_out, key):
                specific_bgm = lyria_out

        add_background_music(assembled, music_dir, with_bgm, specific_bgm)
        log.info("[Headless] Background music added")

        # ────────────────────────────────────────────────────────────────────
        #  STEP 7 — SUBTITLES
        # ────────────────────────────────────────────────────────────────────
        log.info("[Headless] Step 7 — Burning subtitles…")
        burn_subtitles(with_bgm, scenes, with_subs, is_kids=getattr(niche_cfg, "is_kids", False))
        shutil.copy2(with_subs, final_path)
        log.info(f"[Headless] Final video: {final_path.name}")

        # ────────────────────────────────────────────────────────────────────
        #  STEP 8 — SEO METADATA
        # ────────────────────────────────────────────────────────────────────
        log.info("[Headless] Step 8 — Generating SEO metadata…")
        meta = generate_metadata(niche_cfg, topic_data)
        log.info(f"[Headless] Title: '{meta['title']}'")

        # ────────────────────────────────────────────────────────────────────
        #  STEP 9 — THUMBNAIL
        # ────────────────────────────────────────────────────────────────────
        log.info("[Headless] Step 9 — Generating AI thumbnail…")
        thumb_path = AI_OUTPUT / f"{safe_name}_thumb.jpg"
        generate_thumbnail(meta.get("thumbnail_prompt", topic_data["topic"]), niche_cfg, thumb_path)
        log.info(f"[Headless] Thumbnail: {thumb_path.name}")

        # ────────────────────────────────────────────────────────────────────
        #  STEP 10 — BUILD UPLOAD QUEUE
        # ────────────────────────────────────────────────────────────────────
        upload_items = [{
            "path"            : str(final_path),
            "thumb_path"      : str(thumb_path) if thumb_path.exists() else "",
            "title"           : meta["title"],
            "description"     : meta["description"],
            "tags"            : meta["tags"],
            "mode"            : "shorts" if is_shorts else "videos",
            "niche"           : niche_key,
            "is_made_for_kids": meta.get("is_made_for_kids", False),
        }]

        # Auto-clip Shorts from full video
        if auto_clip and not is_shorts and final_path.exists():
            log.info("[Headless] Auto-clipping Shorts from full video…")
            try:
                clips_dir = AI_OUTPUT / f"{safe_name}_shorts"
                clips = auto_clip_video_to_shorts(final_path, clips_dir)
                for j, clip in enumerate(clips):
                    upload_items.append({
                        "path"            : str(clip),
                        "thumb_path"      : "",
                        "title"           : f"{meta['title'][:55]} - Pt {j+1} #shorts",
                        "description"     : meta["description"],
                        "tags"            : meta["tags"] + ["shorts", f"part{j+1}"],
                        "mode"            : "shorts",
                        "niche"           : niche_key,
                        "is_made_for_kids": meta.get("is_made_for_kids", False),
                    })
                log.info(f"[Headless] {len(clips)} Shorts clips ready")
            except Exception as clip_err:
                log.warning(f"[Headless] Auto-clip failed (non-fatal): {clip_err}")

        # ────────────────────────────────────────────────────────────────────
        #  STEP 11 — UPLOAD
        # ────────────────────────────────────────────────────────────────────
        uploaded_ids = []
        first_url    = ""

        if auto_upload:
            log.info(f"[Headless] Step 11 — Uploading {len(upload_items)} item(s) to YouTube…")
            uploaded = upload_all(upload_items, channel, visibility)
            save_report(uploaded, channel, {
                "source" : "Headless AI Automation",
                "niche"  : niche_key,
                "is_kids": meta.get("is_made_for_kids", False),
            })
            for item in uploaded:
                vid_id = item.get("video_id", "")
                if vid_id:
                    uploaded_ids.append(vid_id)
                    if not first_url:
                        is_short = item.get("mode") == "shorts"
                        first_url = (
                            f"https://youtube.com/shorts/{vid_id}" if is_short
                            else f"https://www.youtube.com/watch?v={vid_id}"
                        )
            log.info(f"[Headless] ✅ Uploaded {len(uploaded_ids)} video(s)")
        else:
            log.info(f"[Headless] Auto-upload disabled — files saved in {AI_OUTPUT}")

        return {
            "success"    : True,
            "title"      : meta["title"],
            "url"        : first_url,
            "video_ids"  : uploaded_ids,
            "final_path" : str(final_path),
            "scenes"     : len(scenes),
            "planned_sec": total_planned_sec,
        }

    except Exception as e:
        import traceback
        log.error(f"[Headless] ❌ Pipeline error: {e}\n{traceback.format_exc()}")
        return {
            "success": False,
            "error"  : str(e),
            "title"  : "",
            "url"    : "",
        }
