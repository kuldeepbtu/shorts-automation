"""
ai_workflow/main.py
====================
Full 11-Step AI YouTube Automation Workflow Orchestrator.

Pipeline Steps (matching reference):
  1.  Niche Selection    → ask_niche()                  [stored per-channel, not asked every run]
  2.  Idea / Topic       → generate_topic()
  3.  Script Writing     → generate_script()
  4.  Voice Generation   → generate_voice()             [ElevenLabs free → Edge TTS]
  5.  Image Generation   → generate_image()             [Nano Banana 2 (gemini-3.1-flash-image-preview) → Pollinations]
  6.  Video Generation   → generate_all_scenes_parallel() [Veo 3.1 (veo-3.1-lite-generate-preview) → KenBurns]
  7.  Assembly + BGM     → concat_scenes() + add_background_music()
  8.  Subtitles          → burn_subtitles()              [ffmpeg drawtext — free, no API]
  9.  Thumbnail          → generate_thumbnail()         [Nano Banana 2 → Pollinations]
  10. SEO Metadata       → generate_metadata()          [Gemini AI]
  11. Upload             → upload_all()                 [YouTube API + Made-for-Kids flag if kids niche]

Niche is saved in the channel's account folder (accounts/<name>/niche.json)
and is NOT asked on every run. A "Change Niche" option is offered at startup.
"""

import sys
import os
import shutil
import logging
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from pipeline import yn, menu, upload_all, save_report, ensure_music, C, box, hdr, ok, warn

from ai_workflow.niche_config import NICHES
from ai_workflow.generator import (
    ask_niche, generate_topic, generate_script, generate_metadata, load_saved_niche
)
from ai_workflow.media_engine import (
    generate_voice, generate_image, generate_all_scenes_parallel,
    concat_scenes, add_background_music, burn_subtitles,
    generate_thumbnail, auto_clip_video_to_shorts,
    _all_gemini_keys, _available_keys,
)

log = logging.getLogger("ShortsBot.AIWorkflow.Main")

AI_WORKSPACE = Path(__file__).parent / "workspace"
AI_OUTPUT    = Path(__file__).parent / "output"
AI_ACCOUNTS  = Path(__file__).parent / "accounts"


# ══════════════════════════════════════════════════════════════════════════════
#  CHANNEL  PICKER  (ai_workflow/accounts/)
# ══════════════════════════════════════════════════════════════════════════════

def _scan_ai_channels() -> list[dict]:
    """
    Scan ai_workflow/accounts/ for configured channel folders.
    Each folder needs client_secrets.json or token.json.
    """
    AI_ACCOUNTS.mkdir(parents=True, exist_ok=True)
    channels = []
    for folder in sorted(AI_ACCOUNTS.iterdir()):
        if not folder.is_dir():
            continue
        has_secrets = (folder / "client_secrets.json").exists()
        has_token   = (folder / "token.json").exists()
        if has_secrets or has_token:
            saved_key, saved_cfg = load_saved_niche(folder)
            niche_label = saved_cfg.display_name if saved_cfg else "Not set"
            channels.append({
                "folder"      : folder,
                "name"        : folder.name,
                "real_name"   : folder.name,         # needed by upload_all + Telegram
                "folder_name" : folder.name,
                "secrets_path": folder / "client_secrets.json",
                "token_path"  : str(folder / "token.json"),  # upload_all uses this
                "niche"       : saved_key or "not_set",
                "niche_label" : niche_label,
            })
    return channels


def _pick_channel() -> dict:
    """Show channel selection menu + option to change niche."""
    channels = _scan_ai_channels()
    if not channels:
        box("❌  No AI Channels Found", [
            f"Create a folder inside:  {AI_ACCOUNTS}",
            "Drop your client_secrets.json inside that folder.",
            "Then run again.",
        ])
        sys.exit(1)

    if len(channels) == 1:
        ch = channels[0]
        icon = "👶" if "kids" in ch["niche"] else "📺"
        print(f"\n  🤖 AI Channel: {C.BOLD}{ch['name']}{C.RESET}  |  Niche: {icon} {ch['niche_label']}")
        return ch

    opts = [f"{ch['name']}  [{ch['niche_label']}]" for ch in channels]
    idx = menu("SELECT AI WORKFLOW CHANNEL", opts) - 1
    return channels[idx]


# ══════════════════════════════════════════════════════════════════════════════
#  STARTUP  BANNER
# ══════════════════════════════════════════════════════════════════════════════

def _print_banner():
    w = 64
    print(f"\n{C.CYAN}╔{'═'*w}╗{C.RESET}")
    print(f"{C.CYAN}║{C.RESET}  {C.BOLD}{C.WHITE}🚀  Complete AI YouTube Workflow  v2.0{C.RESET}{'':>{w-38}}{C.CYAN}║{C.RESET}")
    print(f"{C.CYAN}╠{'═'*w}╣{C.RESET}")
    steps = [
        "1. Niche Selection    7.  Assembly + BGM",
        "2. Topic Idea         8.  Auto Subtitles (ffmpeg)",
        "3. Script Writing     9.  AI Thumbnail (Nano Banana 2)",
        "4. Voice (ElevenLabs/EdgeTTS)   10. SEO Metadata",
        "5. AI Images (gemini-3.1-flash-image-preview)",
        "6. Veo 3.1 HD Videos  11. YouTube Upload",
    ]
    for s in steps:
        print(f"{C.CYAN}║{C.RESET}  {s:<{w-2}}{C.CYAN}║{C.RESET}")
    print(f"{C.CYAN}╚{'═'*w}╝{C.RESET}\n")


# ══════════════════════════════════════════════════════════════════════════════
#  MAIN  RUN
# ══════════════════════════════════════════════════════════════════════════════

def run():
    _print_banner()

    # ── Clean workspace ───────────────────────────────────────────────────────
    if AI_WORKSPACE.exists():
        shutil.rmtree(AI_WORKSPACE)
    AI_WORKSPACE.mkdir(parents=True, exist_ok=True)
    AI_OUTPUT.mkdir(parents=True, exist_ok=True)

    # ── STEP 0: Pick channel ──────────────────────────────────────────────────
    hdr("STEP 0 — Channel Selection")
    channel = _pick_channel()
    print(f"  📺 Channel: {C.BOLD}{channel['name']}{C.RESET}")

    # ════════════════════════════════════════════════════════════════════════
    #  STEP 1 — NICHE  SELECTION
    #  Asked only if niche not saved. Otherwise shows current niche + option
    #  to keep or change. This avoids re-asking every run.
    # ════════════════════════════════════════════════════════════════════════
    hdr("STEP 1 — Niche Selection")
    change_niche = False
    saved_key, saved_cfg = load_saved_niche(channel["folder"])
    if saved_cfg:
        icon = "👶" if saved_cfg.is_kids else "📺"
        print(f"  Current niche: {icon} {C.BOLD}{saved_cfg.display_name}{C.RESET}")
        ans = input("  [Enter] Keep  |  [c] Change niche: ").strip().lower()
        change_niche = ans in ("c", "change")

    niche_key, niche_cfg = ask_niche(channel["folder"], force_ask=change_niche)
    custom_label = niche_cfg.description if niche_key == "custom" else ""
    icon = "👶" if niche_cfg.is_kids else "📺"
    print(f"\n  {C.GREEN}✅ Niche: {icon} {niche_cfg.display_name}{C.RESET}")
    if niche_cfg.is_kids:
        print(f"  {C.YELLOW}🔒 Kids Mode: COPPA + Made-for-Kids enforcement ON{C.RESET}")
        print(f"     Target length: {niche_cfg.target_length_sec[0]//60}–{niche_cfg.target_length_sec[1]//60} min standard | {niche_cfg.shorts_length_sec[0]}–{niche_cfg.shorts_length_sec[1]}s Shorts")

    # ── Format selection ──────────────────────────────────────────────────────
    format_choice = menu("SELECT VIDEO FORMAT", [
        "YouTube Shorts (9:16) — vertical under 60s",
        "Standard Video (16:9) — horizontal long form",
        "Standard Video (16:9) + Auto-Clip to Shorts",
    ])
    is_shorts = (format_choice == 1)
    auto_clip  = (format_choice == 3)

    # ════════════════════════════════════════════════════════════════════════
    #  STEP 2 — TOPIC / IDEA  GENERATION
    # ════════════════════════════════════════════════════════════════════════
    hdr("STEP 2 — AI Idea Generation")
    print(f"  🧠 Brainstorming viral topic for: {niche_cfg.display_name}…")
    topic_data = generate_topic(niche_cfg, custom_label)
    print(f"\n  📌 Topic: {C.BOLD}{topic_data['topic']}{C.RESET}")
    print(f"  🎯 Hook : {topic_data['hook']}")
    print(f"  🎭 Vibe : {topic_data['vibe']}")

    # ════════════════════════════════════════════════════════════════════════
    #  STEP 3 — SCRIPT  WRITING
    # ════════════════════════════════════════════════════════════════════════
    hdr("STEP 3 — Script Writing")
    print(f"  ✍️  Writing {'shorts' if is_shorts else 'standard'} script…")
    scenes = generate_script(niche_cfg, topic_data, is_shorts)
    if not scenes:
        print("  ❌ Script generation failed.")
        sys.exit(1)
    total_words = sum(len(s.get("text", "").split()) for s in scenes)
    print(f"  ✅ {len(scenes)} scenes | ~{total_words} words | "
          f"est. {total_words//150:.1f}–{total_words//130:.1f} min")

    if niche_cfg.is_kids:
        print(f"  {C.YELLOW}🔒 Kids safety: Grade-3 vocabulary, no forbidden topics{C.RESET}")

    # ════════════════════════════════════════════════════════════════════════
    #  STEPS 4 + 5 — VOICE  AND  IMAGE  GENERATION  (per scene)
    # ════════════════════════════════════════════════════════════════════════
    hdr("STEPS 4+5 — Voice & Image Generation")
    audio_paths  = []
    image_paths  = []
    durations    = []

    for i, scene in enumerate(scenes):
        print(f"\n  [{i+1}/{len(scenes)}] Generating voice + image…")
        scene_dir = AI_WORKSPACE / f"scene_{i}"
        scene_dir.mkdir(parents=True, exist_ok=True)

        audio_path = scene_dir / "voice.mp3"
        image_path = scene_dir / "image.jpg"

        # Step 4: Voice
        dur = generate_voice(scene["text"], audio_path, niche_cfg)
        print(f"       🎙  Voice: {dur:.1f}s")

        # Step 5: Image
        generate_image(
            scene["image_prompt"],
            is_shorts,
            image_path,
            style_hint=niche_cfg.image_style,
        )
        print(f"       🖼  Image: {image_path.stat().st_size // 1024}KB")

        audio_paths.append(audio_path)
        image_paths.append(image_path)
        durations.append(dur)

    # ════════════════════════════════════════════════════════════════════════
    #  STEP 6 — VIDEO  GENERATION  (Parallel Veo 3.1 / KenBurns)
    # ════════════════════════════════════════════════════════════════════════
    hdr("STEP 6 — AI Video Generation (Veo 3.1 / KenBurns)")
    all_keys  = _all_gemini_keys()
    avail_keys = _available_keys()
    if avail_keys:
        print(f"  ⚡ {len(avail_keys)} AI Studio key(s) ready — distributing {len(scenes)} scenes in parallel")
        print(f"  🎬 Veo 3.1 via model: veo-3.1-lite-generate-preview (same GEMINI_API_KEY)")
    else:
        print(f"  ℹ️  No available Gemini keys — using KenBurns zoom animation (free, no API)")
        print(f"  💡 Add more GEMINI_API_KEY_3..8 in .env for HD Veo 3.1 video generation")

    scene_videos = generate_all_scenes_parallel(
        scenes, image_paths, audio_paths, durations, AI_WORKSPACE, is_shorts
    )
    ok(f"All {len(scene_videos)} scene videos ready")


    # ════════════════════════════════════════════════════════════════════════
    #  STEP 7 — ASSEMBLY  +  BACKGROUND  MUSIC
    # ════════════════════════════════════════════════════════════════════════
    hdr("STEP 7 — Assembly + Background Music")
    safe_topic    = "".join(c for c in topic_data["topic"][:30] if c.isalnum() or c in " _-").strip()
    assembled     = AI_WORKSPACE / "assembled.mp4"
    with_bgm      = AI_WORKSPACE / "with_bgm.mp4"
    with_subs     = AI_WORKSPACE / "with_subs.mp4"
    final_path    = AI_OUTPUT / f"{safe_topic}.mp4"

    print("  🎬 Concatenating scenes…")
    concat_scenes(scene_videos, assembled)
    ok("Scenes assembled")

    ensure_music()
    music_dir = Path(__file__).parent.parent / "assets" / "music"
    print("  🎵 Mixing background music…")
    add_background_music(assembled, music_dir, with_bgm)
    ok("Background music added")

    # ════════════════════════════════════════════════════════════════════════
    #  STEP 8 — SUBTITLES  (auto-captions via ffmpeg)
    # ════════════════════════════════════════════════════════════════════════
    hdr("STEP 8 — Auto Subtitles")
    print("  💬 Burning captions into video…")
    burn_subtitles(with_bgm, scenes, with_subs, is_kids=niche_cfg.is_kids)
    ok("Subtitles burned in")

    # ════════════════════════════════════════════════════════════════════════
    #  STEP 9 — THUMBNAIL
    # ════════════════════════════════════════════════════════════════════════
    hdr("STEP 9 — AI Thumbnail Generation")
    thumb_path = AI_OUTPUT / f"{safe_topic}_thumb.jpg"
    # Generate metadata first to get thumbnail_prompt if available
    print("  📝 Generating SEO metadata…")
    meta = generate_metadata(niche_cfg, topic_data)

    print(f"\n  Title: {C.BOLD}{meta['title']}{C.RESET}")
    print(f"  Tags : {', '.join(meta['tags'][:8])}…")
    if niche_cfg.is_kids:
        print(f"  {C.YELLOW}👶 Made-for-Kids: {meta.get('is_made_for_kids', True)}{C.RESET}")

    print("  🖼  Generating thumbnail…")
    generate_thumbnail(meta.get("thumbnail_prompt", topic_data["topic"]), niche_cfg, thumb_path)
    ok(f"Thumbnail saved: {thumb_path.name}")

    # ── Copy finalize ─────────────────────────────────────────────────────────
    shutil.copy2(with_subs, final_path)
    ok(f"Final video: {final_path}")

    # ════════════════════════════════════════════════════════════════════════
    #  OPTIONAL: Auto-clip to Shorts
    # ════════════════════════════════════════════════════════════════════════
    upload_items = []
    upload_items.append({
        "path"            : str(final_path),
        "thumb_path"      : str(thumb_path) if thumb_path.exists() else "",
        "title"           : meta["title"],
        "description"     : meta["description"],
        "tags"            : meta["tags"],
        "mode"            : "shorts" if is_shorts else "videos",
        "niche"           : niche_key,
        "is_made_for_kids": meta.get("is_made_for_kids", False),
    })

    if auto_clip:
        hdr("Auto-Clip → Shorts")
        print("  ✂️  Clipping standard video into 9:16 Shorts…")
        clips_dir = AI_OUTPUT / f"{safe_topic}_shorts"
        clips = auto_clip_video_to_shorts(final_path, clips_dir)
        for j, clip in enumerate(clips):
            upload_items.append({
                "path"            : str(clip),
                "thumb_path"      : "",
                "title"           : f"{meta['title']} - Pt {j+1} #shorts",
                "description"     : meta["description"],
                "tags"            : meta["tags"] + ["shorts", f"part{j+1}"],
                "mode"            : "shorts",
                "niche"           : niche_key,
                "is_made_for_kids": meta.get("is_made_for_kids", False),
            })
        ok(f"Generated {len(clips)} additional Shorts clips")

    # ════════════════════════════════════════════════════════════════════════
    #  STEP 11 — UPLOAD
    # ════════════════════════════════════════════════════════════════════════
    hdr("STEP 11 — YouTube Upload")
    print(f"  📦 {len(upload_items)} item(s) ready to upload")
    print(f"  Title: {meta['title']}")
    if meta.get("is_made_for_kids"):
        print(f"  {C.YELLOW}👶 Made-for-Kids flag will be set on upload{C.RESET}")

    # Analytics hint (Step 11 from reference — VidIQ substitute)
    print(f"\n  {C.DIM}📊 Analytics Tips (post-upload):{C.RESET}")
    print(f"  {C.DIM}• Check CTR in YouTube Studio after 24h (target >4%){C.RESET}")
    print(f"  {C.DIM}• Monitor AVD (Average View Duration) — aim for >40%{C.RESET}")
    print(f"  {C.DIM}• Use VidIQ extension for keyword tracking{C.RESET}")
    if niche_cfg.is_kids:
        print(f"  {C.DIM}• Kids channels: check 'Made for Kids' toggle in YouTube Studio{C.RESET}")
        print(f"  {C.DIM}• {niche_cfg.monetization_notes}{C.RESET}")

    if yn("\n  🚀 Upload to YouTube now?", default=True):
        uploaded = upload_all(upload_items, channel, "public")
        save_report(uploaded, channel, {
            "source": "Complete AI Automation",
            "niche" : niche_key,
            "is_kids": niche_cfg.is_kids,
        })
    else:
        print(f"  ⏭  Upload skipped. Files saved in: {AI_OUTPUT}")

    # ── Done ──────────────────────────────────────────────────────────────────
    w = 64
    print(f"\n{C.GREEN}╔{'═'*w}╗{C.RESET}")
    print(f"{C.GREEN}║  🎉  AI Workflow Complete!{' '*(w-26)}║{C.RESET}")
    print(f"{C.GREEN}╠{'═'*w}╣{C.RESET}")
    print(f"{C.GREEN}║  Topic    : {topic_data['topic'][:w-14]:<{w-14}}║{C.RESET}")
    print(f"{C.GREEN}║  Niche    : {niche_cfg.display_name[:w-14]:<{w-14}}║{C.RESET}")
    print(f"{C.GREEN}║  Video    : {final_path.name[:w-14]:<{w-14}}║{C.RESET}")
    print(f"{C.GREEN}║  Thumbnail: {thumb_path.name[:w-14]:<{w-14}}║{C.RESET}")
    print(f"{C.GREEN}╚{'═'*w}╝{C.RESET}\n")


if __name__ == "__main__":
    run()
