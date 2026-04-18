"""
ai_workflow/generator.py
=========================
Niche-aware AI content generator for the ShortsBot AI Workflow.

Handles:
  - Niche selection UI (shown only when channel is NEW or niche not saved)
  - Per-channel niche storage  (accounts/<folder>/niche.json)
  - Topic ideation tuned to the niche
  - Script writing with kids-safety enforcement
  - SEO metadata with niche-specific tags + thumbnail prompt

Reference pipeline:
  Step 1 → Idea Generation   (generate_topic)
  Step 2 → Script Writing    (generate_script)
  Step 8 → Title+Description (generate_metadata)
  Step 9 → SEO Tags          (generate_metadata)
"""

import json
import logging
import sys
import os
from pathlib import Path

# ── Add parent so we can import pipeline helpers ──────────────────────────────
sys.path.append(str(Path(__file__).parent.parent))
from pipeline import gemini, menu, get_input, C

from ai_workflow.niche_config import (
    NICHES, NICHE_KEYS, NicheConfig,
    get_niche_menu_lines, get_niche_by_index,
)

log = logging.getLogger("ShortsBot.AIWorkflow.Generator")


# ══════════════════════════════════════════════════════════════════════════════
#  NICHE  STORAGE  (per channel folder)
# ══════════════════════════════════════════════════════════════════════════════

def _niche_file(channel_folder: Path) -> Path:
    return channel_folder / "niche.json"


def load_saved_niche(channel_folder: Path) -> tuple[str, NicheConfig] | tuple[None, None]:
    """
    Read niche saved in the channel's folder.
    Returns (niche_key, NicheConfig) or (None, None) if not set yet.
    """
    nf = _niche_file(channel_folder)
    if nf.exists():
        try:
            data = json.loads(nf.read_text(encoding="utf-8"))
            key = data.get("niche_key", "")
            if key in NICHES:
                return (key, NICHES[key])
        except Exception:
            pass
    # Also check legacy settings.json used by the main pipeline
    sf = channel_folder / "settings.json"
    if sf.exists():
        try:
            data = json.loads(sf.read_text(encoding="utf-8"))
            key = data.get("niche", "")
            if key in NICHES:
                return (key, NICHES[key])
        except Exception:
            pass
    return (None, None)


def save_niche(channel_folder: Path, niche_key: str, custom_label: str = ""):
    """Persist niche selection inside the channel folder."""
    channel_folder.mkdir(parents=True, exist_ok=True)
    nf = _niche_file(channel_folder)
    nf.write_text(
        json.dumps({"niche_key": niche_key, "custom_label": custom_label}, indent=2),
        encoding="utf-8"
    )
    # Also sync back to settings.json so the main pipeline sees it
    sf = channel_folder / "settings.json"
    try:
        existing = json.loads(sf.read_text(encoding="utf-8")) if sf.exists() else {}
    except Exception:
        existing = {}
    existing["niche"] = niche_key
    sf.write_text(json.dumps(existing, indent=2), encoding="utf-8")
    log.info(f"[Generator] Niche saved → {niche_key} in {channel_folder.name}")


# ══════════════════════════════════════════════════════════════════════════════
#  NICHE  PICKER  UI
# ══════════════════════════════════════════════════════════════════════════════

def ask_niche(channel_folder: Path, force_ask: bool = False) -> tuple[str, NicheConfig]:
    """
    Interactive niche picker.

    - Shows saved niche if already set → asks whether to keep or change.
    - If no niche saved (new channel) → shows full menu.
    - force_ask=True → always show menu (for the "Change Niche" option).

    Returns (niche_key, NicheConfig).
    For 'custom' niche → returns ("custom", synthetic NicheConfig).
    """
    # 1. Check if already saved
    saved_key, saved_cfg = load_saved_niche(channel_folder)

    if saved_cfg and not force_ask:
        icon = "👶" if saved_cfg.is_kids else "📺"
        print(f"\n  {C.CYAN}🎯 Current niche:{C.RESET} {icon} {C.BOLD}{saved_cfg.display_name}{C.RESET}")
        ans = input(f"  Keep this niche? [Y/n / c=change]: ").strip().lower()
        if ans in ("", "y", "yes"):
            return (saved_key, saved_cfg)
        # Fall through to picker

    # 2. Show picker menu
    w = 64
    print(f"\n╔{'═'*w}╗")
    print(f"║  {'SELECT YOUR CHANNEL NICHE':<{w-2}} ║")
    print(f"╠{'═'*w}╣")

    kids_done = False
    for i, key in enumerate(NICHE_KEYS, 1):
        cfg = NICHES[key]
        if not cfg.is_kids and not kids_done:
            kids_done = True
            print(f"║  {'─'*58}  ║")
            print(f"║  {'📺  ADULT / GENERAL NICHES':<{w-2}} ║")
            print(f"║  {'─'*58}  ║")
        if cfg.is_kids and i == 1:
            print(f"║  {'👶  KIDS CHANNEL NICHES (COPPA-Safe)':<{w-2}} ║")
            print(f"║  {'─'*58}  ║")
        icon = "👶" if cfg.is_kids else "📺"
        line = f"{i:2}.  {icon}  {cfg.display_name}"
        print(f"║  {line:<{w-2}} ║")

    n_custom = len(NICHE_KEYS) + 1
    print(f"║  {n_custom:2}.  ✏️   Custom (type your own niche){'':>{w-38}} ║")
    print(f"╚{'═'*w}╝")

    while True:
        raw = input(f"\n  Enter number (1–{n_custom}): ").strip()
        try:
            idx = int(raw)
            if 1 <= idx <= n_custom:
                break
        except ValueError:
            pass
        print(f"  ⚠  Enter a number 1–{n_custom}")

    # 3. Handle custom
    if idx == n_custom:
        custom_label = get_input("Describe your niche (e.g. 'Arabic cooking', 'Cricket highlights')")
        # Build a synthetic NicheConfig from the custom description
        cfg = _build_custom_niche(custom_label)
        save_niche(channel_folder, "custom", custom_label)
        return ("custom", cfg)

    niche_key, cfg = get_niche_by_index(idx)
    save_niche(channel_folder, niche_key)
    icon = "👶" if cfg.is_kids else "📺"
    print(f"\n  ✅ Niche set: {icon} {C.BOLD}{cfg.display_name}{C.RESET}")
    return (niche_key, cfg)


def _build_custom_niche(label: str) -> NicheConfig:
    """Create a generic NicheConfig for a user-defined custom niche."""
    return NicheConfig(
        display_name=f"Custom: {label}",
        description=label,
        is_kids=False,
        tone="engaging",
        script_style="educational",
        target_length_sec=(300, 600),
        shorts_length_sec=(45, 58),
        voice_model="en-US-ChristopherNeural",
        elevenlabs_voice_id="21m00Tcm4TlvDq8ikWAM",
        image_style="cinematic 8k, highly detailed, professional videography, dynamic composition",
        seo_keywords=[label.lower(), "facts", "trending", "viral", "youtube"],
        monetization_notes="Custom niche – manually review content for monetization compliance.",
    )


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 1 — TOPIC / IDEA  GENERATION
# ══════════════════════════════════════════════════════════════════════════════

def generate_topic(niche_cfg: NicheConfig, custom_label: str = "") -> dict:
    """
    AI-powered topic ideation tuned to the niche.

    Returns:
      {
        "niche": str,
        "topic": str,
        "hook": str,
        "vibe": str,
        "is_kids": bool,
        "language": str,
      }
    """
    niche_label = custom_label if custom_label else niche_cfg.display_name

    kids_extra = ""
    if niche_cfg.is_kids:
        kids_extra = f"""
IMPORTANT — KIDS CONTENT RULES:
- Content MUST be appropriate for children aged 3–8 years old.
- Vocabulary must be simple (Grade 3 level, ~550 Lexile score).
- Absolutely NO: {', '.join(niche_cfg.forbidden_topics)}.
- Every idea must end with a positive takeaway or lesson.
- Language hint: {niche_cfg.language_hint}
"""

    script_style_hints = {
        "musical": "The idea should be a catchy song/rhyme concept with a memorable chorus idea.",
        "storytelling": "The idea should be a short story with a clear beginning/middle/end.",
        "tutorial": "The idea should be a simple step-by-step activity or how-to.",
        "educational": "The idea should be a fascinating fact or concept explained simply.",
        "motivational": "The idea should be a powerful life lesson or philosophical insight.",
    }
    style_hint = script_style_hints.get(niche_cfg.script_style, "")

    prompt = f"""You are a top YouTube content strategist specializing in "{niche_label}" content.
Your goal: brainstorm ONE highly engaging, viral-worthy video topic for a faceless YouTube channel.

Niche: {niche_label}
Script style: {niche_cfg.script_style}
Tone: {niche_cfg.tone}
{style_hint}
{kids_extra}

Research context — what is currently trending in this niche:
- Focus on topics that have HIGH search volume but LOW competition
- Consider what top channels in this niche are covering this week
- Pick something timeless OR ultra-timely (trending right now)

Respond ONLY with valid JSON (no markdown fences, no extra text):
{{
  "niche": "{niche_label}",
  "topic": "<specific video title — compelling and SEO-friendly>",
  "hook": "<1 sentence opening hook that grabs attention in 3 seconds>",
  "vibe": "<one word: e.g. mysterious | cheerful | shocking | inspiring | educational>",
  "is_kids": {"true" if niche_cfg.is_kids else "false"},
  "language": "{niche_cfg.language_hint}"
}}"""

    try:
        raw = gemini(prompt)
        raw = _strip_json(raw)
        data = json.loads(raw)
        data.setdefault("is_kids", niche_cfg.is_kids)
        data.setdefault("language", niche_cfg.language_hint)
        log.info(f"[Generator] Topic: {data.get('topic')}")
        return data
    except Exception as e:
        log.error(f"[Generator] Topic generation failed: {e}")
        # Fallback
        fallback_topics = {
            "kids_learning": "Why Do Stars Twinkle? A Fun Science Story for Kids",
            "kids_nursery_english": "Twinkle Twinkle Little Star — Full Nursery Rhyme with Actions",
            "kids_nursery_hindi": "चंदा मामा दूर के — हिंदी बालगीत",
            "kids_moral_stories": "The Honest Woodcutter — A Story About Honesty",
            "finance": "7 Money Rules the Rich Never Tell You",
            "ai_tech": "5 AI Tools That Will Replace Your Job in 2025",
            "science_space": "The Terrifying True Scale of the Universe",
        }
        return {
            "niche": niche_label,
            "topic": fallback_topics.get(
                next((k for k in NICHES if NICHES[k].display_name == niche_label), ""),
                f"Amazing Facts About {niche_label}"
            ),
            "hook": "You won't believe this...",
            "vibe": niche_cfg.tone,
            "is_kids": niche_cfg.is_kids,
            "language": niche_cfg.language_hint,
        }


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 2 — SCRIPT  GENERATION
# ══════════════════════════════════════════════════════════════════════════════

def generate_script(niche_cfg: NicheConfig, topic_data: dict, is_shorts: bool) -> list[dict]:
    """
    Generates a scene-by-scene script with visual AI image prompts and subtitle text.

    Each scene:
      {
        "text":         str,   # spoken narration
        "image_prompt": str,   # Pollinations / Veo 3 prompt
        "subtitle":     str,   # on-screen text (may differ from full narration)
        "screen_text":  str,   # short catchy overlay (for kids: rhyme lyrics etc.)
      }
    """
    # Calculate word count target from niche + format
    if is_shorts:
        lo, hi = niche_cfg.shorts_length_sec
        word_min = int(lo * 2.3)    # ~2.3 words/sec narration
        word_max = int(hi * 2.3)
        format_desc = "ultra-fast-paced vertical Short (9:16). Keep UNDER 58 seconds total."
    else:
        lo, hi = niche_cfg.target_length_sec
        word_min = int(lo * 2.3)
        word_max = int(hi * 2.3)
        format_desc = f"horizontal video (16:9). Target {lo//60}–{hi//60} minutes."

    # Kids-specific constraints
    kids_rules = ""
    if niche_cfg.is_kids:
        kids_rules = f"""
CRITICAL KIDS RULES — MANDATORY:
1. Vocabulary: Grade 3 level (simple, short sentences, no jargon).
2. Forbidden in ANY scene: {', '.join(niche_cfg.forbidden_topics)}.
3. Tone: Always positive, encouraging, never scary or dark.
4. Every scene image_prompt must be: child-safe, colorful, cartoon/animated style.
5. Last scene must include a moral lesson or positive message.
6. Language: {niche_cfg.language_hint} (write narration in this language if not English).
"""
    if niche_cfg.script_style == "musical":
        kids_rules += "\nSCRIPT STYLE: Write as a SONG/RHYME. Include chorus that repeats. AABB or ABAB rhyme scheme."

    image_style_hint = niche_cfg.image_style or "cinematic 8k, highly detailed, professional"

    prompt = f"""You are an expert YouTube scriptwriter for faceless "{niche_cfg.display_name}" channels.

VIDEO TOPIC: "{topic_data['topic']}"
HOOK: "{topic_data['hook']}"
VIBE/TONE: {topic_data['vibe']}
FORMAT: {format_desc}
SCRIPT STYLE: {niche_cfg.script_style}
WORD COUNT TARGET: {word_min}–{word_max} words total across all scenes.
Generate exactly {max(2, word_min // 50)} to {word_max // 40} scenes. Each scene should have 30–60 words of narration.
{kids_rules}

SCENE RULES:
- Each scene = 1 visual shot + spoken narration for that shot.
- image_prompt: Keep it under 15 words. VERY specific visual description for AI generation (lighting, subject, action).
  Base style to use: "{image_style_hint}"
- subtitle: Short version of the text for on-screen captions (max 10 words).
- screen_text: A 1–5 word catchy overlay or key fact shown on screen (empty string if not needed).

Respond ONLY with a valid JSON array (no markdown, no extra text):
[
  {{
    "text": "The exact words the narrator will speak for this scene.",
    "image_prompt": "Specific visual prompt for AI video generation...",
    "subtitle": "Short caption text (max 10 words)",
    "screen_text": "KEY FACT" 
  }}
]"""

    try:
        raw = gemini(prompt)
        raw = _strip_json(raw)
        scenes = json.loads(raw)
        if not isinstance(scenes, list) or not scenes:
            raise ValueError("Not a list")
        log.info(f"[Generator] Script: {len(scenes)} scenes, est. {sum(len(s.get('text','').split()) for s in scenes)} words")
        return scenes
    except Exception as e:
        log.error(f"[Generator] Script generation failed: {e}")
        return [
            {
                "text": topic_data.get("hook", "This is amazing. Let's find out more."),
                "image_prompt": f"{image_style_hint}, dramatic cinematic opening shot",
                "subtitle": "Let's find out!",
                "screen_text": "",
            },
            {
                "text": f"Today we explore: {topic_data['topic']}. Stay with us till the end!",
                "image_prompt": f"{image_style_hint}, wide establishing shot, vibrant colors",
                "subtitle": topic_data["topic"][:50],
                "screen_text": "WATCH TILL END",
            },
        ]


# ══════════════════════════════════════════════════════════════════════════════
#  STEP 8+9 — METADATA  GENERATION
# ══════════════════════════════════════════════════════════════════════════════

def generate_metadata(niche_cfg: NicheConfig, topic_data: dict) -> dict:
    """
    Generates YouTube upload metadata: title, description, tags, kids flag, thumbnail prompt.

    Returns:
      {
        "title":                str,
        "description":          str,
        "tags":                 list[str],
        "is_made_for_kids":     bool,
        "thumbnail_prompt":     str,   ← used by media_engine to generate thumbnail image
      }
    """
    keyword_str = ", ".join(niche_cfg.seo_keywords[:8])
    kids_tag_instruction = ""
    if niche_cfg.is_kids:
        kids_tag_instruction = (
            "MANDATORY tags to include: ['kidsvideo', 'forkids', 'educational', "
            "'childrencontent', 'kidschannel', 'learningforkids']"
        )

    prompt = f"""Generate complete YouTube metadata for this video.

Niche: {niche_cfg.display_name}
Topic: "{topic_data['topic']}"
Hook: "{topic_data['hook']}"
Tone: {topic_data['vibe']}
Is Kids Content: {"YES — Made for Kids / COPPA" if niche_cfg.is_kids else "No"}
Core SEO keywords to weave in: {keyword_str}
{kids_tag_instruction}

Rules:
- Title: Under 60 characters. Use numbers, power words, and curiosity gaps. No clickbait lies.
- Description: 2 paragraphs. Natural keyword density. CTA in last sentence. Include timestamps if relevant.
- Tags: 20 highly relevant tags mixing broad + specific + long-tail keywords.
- thumbnail_prompt: A detailed prompt for an AI image generator to create a YouTube thumbnail.
  Style: Bold text overlay, high contrast, emotional face or dramatic scene, eye-catching colors.
  Reference niche image style: {niche_cfg.image_style}

Respond ONLY with valid JSON (no markdown):
{{
  "title": "<under 60 chars>",
  "description": "<2 paragraphs with keywords>",
  "tags": ["tag1", "tag2"],
  "thumbnail_prompt": "<detailed AI image prompt for thumbnail>"
}}"""

    try:
        raw = gemini(prompt)
        raw = _strip_json(raw)
        data = json.loads(raw)
        # Ensure kids tags
        if niche_cfg.is_kids:
            kids_tags = ["kidsvideo", "forkids", "educational", "childrencontent",
                         "kidschannel", "learningforkids", "kids", "children"]
            existing = [t.lower() for t in data.get("tags", [])]
            for kt in kids_tags:
                if kt not in existing:
                    data["tags"].append(kt)
        data["is_made_for_kids"] = niche_cfg.is_kids
        data.setdefault("thumbnail_prompt",
                        f"YouTube thumbnail: {topic_data['topic']}, {niche_cfg.image_style}, bold title text")
        log.info(f"[Generator] Metadata: '{data.get('title')}'  {len(data.get('tags',[]))} tags")
        return data
    except Exception as e:
        log.error(f"[Generator] Metadata generation failed: {e}")
        base_tags = list(niche_cfg.seo_keywords[:10]) + ["viral", "trending", "shorts", "youtube"]
        if niche_cfg.is_kids:
            base_tags += ["kidsvideo", "forkids", "educational"]
        return {
            "title": topic_data["topic"][:59],
            "description": f"Watch this amazing video about {topic_data['topic']}. Like & Subscribe!",
            "tags": base_tags[:20],
            "is_made_for_kids": niche_cfg.is_kids,
            "thumbnail_prompt": (
                f"YouTube thumbnail for '{topic_data['topic']}', "
                f"{niche_cfg.image_style}, bold white text, vibrant"
            ),
        }


# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════

def _strip_json(text: str) -> str:
    """Strip markdown fences from AI JSON responses."""
    t = text.strip()
    if t.startswith("```json"):
        t = t[7:]
    elif t.startswith("```"):
        t = t[3:]
    if t.endswith("```"):
        t = t[:-3]
    return t.strip()
