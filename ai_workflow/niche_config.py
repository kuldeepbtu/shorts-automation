"""
ai_workflow/niche_config.py
============================
Central registry of all supported YouTube channel niches.
Each niche drives the script style, voice, visual style, video length,
SEO keywords, and monetization/policy rules throughout the pipeline.

Kids niches enforce COPPA + YouTube Made-for-Kids (YPP) compliance.
"""

from dataclasses import dataclass, field
from typing import List, Tuple


@dataclass
class NicheConfig:
    # ── Identity ──────────────────────────────────────────────────────────────
    display_name: str
    description: str
    is_kids: bool

    # ── Content rules ─────────────────────────────────────────────────────────
    tone: str               # cheerful | authoritative | mysterious | calm | energetic | warm | awe
    script_style: str       # storytelling | educational | musical | tutorial | motivational

    # ── Video length targets (seconds) ───────────────────────────────────────
    target_length_sec: Tuple[int, int]   # (min, max) standard video
    shorts_length_sec: Tuple[int, int]   # (min, max) YouTube Shorts

    # ── Media style hints ────────────────────────────────────────────────────
    voice_model: str        # Edge-TTS voice name (fallback when ElevenLabs unavailable)
    elevenlabs_voice_id: str = ""          # ElevenLabs voice ID (adult or kids)
    image_style: str = ""                  # Image generation style descriptor for AI prompts

    # ── SEO + Policy ─────────────────────────────────────────────────────────
    seo_keywords: List[str] = field(default_factory=list)
    forbidden_topics: List[str] = field(default_factory=list)
    monetization_notes: str = ""

    # ── Localisation ─────────────────────────────────────────────────────────
    language_hint: str = "english"         # Prompt hint for non-English niches


# ══════════════════════════════════════════════════════════════════════════════
#  NICHE REGISTRY
#  Order matters: kids niches first (shown grouped in menu).
# ══════════════════════════════════════════════════════════════════════════════

NICHES: dict[str, NicheConfig] = {

    # ─────────────────────────────────────────────────────────────────────────
    #  K I D S   N I C H E S
    # ─────────────────────────────────────────────────────────────────────────

    "kids_learning": NicheConfig(
        display_name="Kids Learning & Stories (English)",
        description="Fun educational stories and facts for children aged 3–8.",
        is_kids=True,
        tone="cheerful",
        script_style="storytelling",
        target_length_sec=(240, 480),    # 4–8 min
        shorts_length_sec=(45, 58),
        voice_model="en-US-AnaNeural",
        elevenlabs_voice_id="AZnzlk1XvdvUeBnXmlld",   # Domi – friendly female
        image_style=(
            "colorful cartoon illustration, child-friendly, bright primary colors, "
            "Cocomelon / Disney animation style, cute characters, soft lighting"
        ),
        seo_keywords=[
            "kids learning", "educational videos for kids", "stories for children",
            "toddler learning", "kids education", "learn for kids", "children stories",
            "kindergarten", "preschool", "abc for kids",
        ],
        forbidden_topics=[
            "violence", "scary content", "horror", "adult themes", "gambling",
            "weapons", "death", "blood", "war", "drugs", "romance",
        ],
        monetization_notes=(
            "Set Made-for-Kids=True on YouTube. Grade 3 reading level (~550 Lexile). "
            "Every video must end with a positive takeaway or lesson. "
            "No personal data collection prompts in script. No ad targeting."
        ),
    ),

    "kids_nursery_english": NicheConfig(
        display_name="English Nursery Rhymes & Songs",
        description="Classic and original English nursery rhymes for babies and toddlers.",
        is_kids=True,
        tone="cheerful",
        script_style="musical",
        target_length_sec=(90, 240),     # 1.5–4 min
        shorts_length_sec=(30, 58),
        voice_model="en-US-AnaNeural",
        elevenlabs_voice_id="AZnzlk1XvdvUeBnXmlld",
        image_style=(
            "cute cartoon characters, pastel candy colors, nursery rhyme illustration style, "
            "Cocomelon inspired, bouncy and joyful, animated storybook look"
        ),
        seo_keywords=[
            "nursery rhymes", "rhymes for kids", "kids songs", "baby songs",
            "toddler songs", "english rhymes", "nursery rhymes for babies",
            "kids music", "playground songs", "children's songs",
        ],
        forbidden_topics=[
            "violence", "scary content", "adult themes", "gambling", "weapons",
        ],
        monetization_notes=(
            "Set Made-for-Kids=True. Short repetitive lyrics for high retention. "
            "Include on-screen lyrics text for engagement. Rhyme AABB or ABAB structure."
        ),
    ),

    "kids_nursery_hindi": NicheConfig(
        display_name="Hindi Nursery Rhymes / बालगीत",
        description="Hindi bal geet and nursery rhymes for Indian children.",
        is_kids=True,
        tone="cheerful",
        script_style="musical",
        target_length_sec=(90, 240),
        shorts_length_sec=(30, 58),
        voice_model="hi-IN-SwaraNeural",
        elevenlabs_voice_id="AZnzlk1XvdvUeBnXmlld",
        image_style=(
            "cute colorful cartoon with Indian cultural elements, traditional Indian clothing, "
            "vibrant festival colors, Hindi children's animation style, Chota Bheem inspired"
        ),
        seo_keywords=[
            "hindi rhymes", "hindi bal geet", "बालगीत", "hindi nursery rhymes",
            "hindi kids songs", "hindi cartoons", "bachon ke geet", "hindi poems for kids",
        ],
        forbidden_topics=[
            "violence", "scary content", "adult themes", "gambling",
        ],
        monetization_notes=(
            "Set Made-for-Kids=True. Write lyrics in simple Hindi (Devanagari optional). "
            "Include English transliteration in the description for wider reach."
        ),
        language_hint="hindi",
    ),

    "kids_moral_stories": NicheConfig(
        display_name="Kids Moral Stories (English)",
        description="Short moral stories with positive values: honesty, kindness, courage.",
        is_kids=True,
        tone="warm",
        script_style="storytelling",
        target_length_sec=(180, 360),    # 3–6 min
        shorts_length_sec=(45, 58),
        voice_model="en-US-JennyNeural",
        elevenlabs_voice_id="AZnzlk1XvdvUeBnXmlld",
        image_style=(
            "storybook watercolor illustration, warm earthy tones, friendly animal characters, "
            "children's book art style, soft glow, Aesop's fables aesthetic"
        ),
        seo_keywords=[
            "moral stories for kids", "stories for children", "bedtime stories",
            "kids tales", "children moral stories", "stories with moral",
            "short stories for kids", "good habits for kids",
        ],
        forbidden_topics=[
            "violence", "scary content", "death", "adult themes", "gambling",
            "horror", "weapons", "blood",
        ],
        monetization_notes=(
            "Set Made-for-Kids=True. Every story must end with a stated moral lesson. "
            "Characters must be clearly good vs bad with a resolution."
        ),
    ),

    "kids_islamic_stories": NicheConfig(
        display_name="Islamic Kids Stories & Duas",
        description="Islamic stories, prophet stories, and duas for Muslim children.",
        is_kids=True,
        tone="warm",
        script_style="storytelling",
        target_length_sec=(180, 360),
        shorts_length_sec=(45, 58),
        voice_model="en-US-JennyNeural",
        elevenlabs_voice_id="AZnzlk1XvdvUeBnXmlld",
        image_style=(
            "Islamic geometric patterns, soft golden tones, mosque silhouettes, "
            "crescent moon and stars, halal children's animation, Arabic calligraphy accents"
        ),
        seo_keywords=[
            "islamic stories for kids", "muslim kids", "islamic cartoons",
            "quran for kids", "duas for kids", "prophet stories", "islamic education",
            "halal content", "islamic moral stories",
        ],
        forbidden_topics=[
            "violence", "haram content", "adult themes", "gambling",
            "music with instruments (if strict)", "magic",
        ],
        monetization_notes=(
            "Set Made-for-Kids=True. Reference authentic Islamic sources (Quran/Hadith). "
            "Include the dua text and its meaning in the description."
        ),
    ),

    "kids_diy_crafts": NicheConfig(
        display_name="Kids DIY & Crafts",
        description="Simple crafts and creative activities children can do at home.",
        is_kids=True,
        tone="enthusiastic",
        script_style="tutorial",
        target_length_sec=(300, 600),    # 5–10 min
        shorts_length_sec=(45, 58),
        voice_model="en-US-AnaNeural",
        elevenlabs_voice_id="AZnzlk1XvdvUeBnXmlld",
        image_style=(
            "bright craft workspace, colorful materials, step-by-step tutorial style, "
            "cheerful lighting, top-down and side angles, art supply flat lay"
        ),
        seo_keywords=[
            "kids crafts", "diy for kids", "easy crafts for children", "kids activities",
            "art for kids", "paper crafts", "easy DIY", "creative kids",
        ],
        forbidden_topics=[
            "dangerous tools", "toxic materials", "fire", "sharp knives unattended",
        ],
        monetization_notes=(
            "Set Made-for-Kids=True. Always include: 'Ask a grown-up for help with sharp tools.' "
            "List all materials needed in first 30 seconds."
        ),
    ),

    # ─────────────────────────────────────────────────────────────────────────
    #  A D U L T   N I C H E S
    # ─────────────────────────────────────────────────────────────────────────

    "finance": NicheConfig(
        display_name="Personal Finance / Wealth",
        description="Investing, wealth building, passive income — high-RPM faceless content.",
        is_kids=False,
        tone="authoritative",
        script_style="educational",
        target_length_sec=(480, 900),    # 8–15 min
        shorts_length_sec=(50, 58),
        voice_model="en-US-ChristopherNeural",
        elevenlabs_voice_id="21m00Tcm4TlvDq8ikWAM",   # Rachel
        image_style=(
            "cinematic 8k, financial charts, gold coins, luxury lifestyle, "
            "dark navy and gold tones, corporate professional, stock market data"
        ),
        seo_keywords=[
            "personal finance", "investing", "wealth building", "passive income",
            "money tips", "how to get rich", "financial freedom", "stocks", "crypto",
        ],
        monetization_notes=(
            "High RPM ($8–$20 CPM). End every video with CTA to subscribe. "
            "Add disclaimer: 'This is not financial advice.'"
        ),
    ),

    "ai_tech": NicheConfig(
        display_name="AI & Tech Innovations",
        description="Latest AI breakthroughs, tech news, gadgets, and future technology.",
        is_kids=False,
        tone="energetic",
        script_style="educational",
        target_length_sec=(360, 720),    # 6–12 min
        shorts_length_sec=(50, 58),
        voice_model="en-US-AndrewNeural",
        elevenlabs_voice_id="21m00Tcm4TlvDq8ikWAM",
        image_style=(
            "futuristic sci-fi, neon blue circuit boards, holographic displays, "
            "glowing AI neural networks, high-tech lab, cyberpunk aesthetic"
        ),
        seo_keywords=[
            "artificial intelligence", "ai news", "tech innovations", "gadgets 2025",
            "future technology", "chatgpt", "ai tools", "tech facts",
        ],
        monetization_notes="High RPM ($6–$15 CPM). Stay factual — cite AI news sources in description.",
    ),

    "dark_psychology": NicheConfig(
        display_name="Dark Psychology / Mindset",
        description="Psychological facts, persuasion, human behavior — mysterious and educational.",
        is_kids=False,
        tone="mysterious",
        script_style="educational",
        target_length_sec=(480, 720),    # 8–12 min
        shorts_length_sec=(50, 58),
        voice_model="en-US-ChristopherNeural",
        elevenlabs_voice_id="21m00Tcm4TlvDq8ikWAM",
        image_style=(
            "dark atmospheric, dramatic chiaroscuro lighting, silhouettes, "
            "noir psychological thriller mood, chess pieces, shadowy figures"
        ),
        seo_keywords=[
            "dark psychology", "manipulation tricks", "human behavior", "psychology facts",
            "mind manipulation", "persuasion", "psychology tips", "dark habits",
        ],
        monetization_notes="Stay educational. Never promote harmful manipulation. Good RPM ($5–$12).",
    ),

    "history_mysteries": NicheConfig(
        display_name="Unknown History / Mysteries",
        description="Hidden history, unsolved mysteries, and ancient civilizations.",
        is_kids=False,
        tone="mysterious",
        script_style="storytelling",
        target_length_sec=(480, 900),
        shorts_length_sec=(50, 58),
        voice_model="en-GB-RyanNeural",
        elevenlabs_voice_id="21m00Tcm4TlvDq8ikWAM",
        image_style=(
            "ancient ruins, dramatic storm sky, documentary style wide shots, "
            "sepia and cinematic tones, old maps, candlelight mystery atmosphere"
        ),
        seo_keywords=[
            "history mysteries", "unsolved mysteries", "ancient civilizations",
            "hidden history", "mystery facts", "conspiraciones", "ancient secrets",
        ],
        monetization_notes="Fact-based content. Label speculation clearly. Good RPM ($4–$10).",
    ),

    "stoicism": NicheConfig(
        display_name="Stoicism / Motivation",
        description="Stoic philosophy, self-improvement, and mindset content.",
        is_kids=False,
        tone="calm",
        script_style="motivational",
        target_length_sec=(300, 600),    # 5–10 min
        shorts_length_sec=(45, 58),
        voice_model="en-US-GuyNeural",
        elevenlabs_voice_id="21m00Tcm4TlvDq8ikWAM",
        image_style=(
            "minimalist mountain landscape, golden hour, lone silhouetted figure, "
            "Stoic Greek temple, philosophical atmosphere, calm and powerful"
        ),
        seo_keywords=[
            "stoicism", "motivation", "mindset", "self improvement",
            "Marcus Aurelius", "epictetus", "philosophy", "discipline",
        ],
        monetization_notes="Broad appeal, good retention. Quote ancient philosophers for credibility.",
    ),

    "science_space": NicheConfig(
        display_name="Mindblowing Science / Space",
        description="Space discoveries, physics facts, biology—science that blows your mind.",
        is_kids=False,
        tone="awe",
        script_style="educational",
        target_length_sec=(360, 720),
        shorts_length_sec=(50, 58),
        voice_model="en-US-AndrewNeural",
        elevenlabs_voice_id="21m00Tcm4TlvDq8ikWAM",
        image_style=(
            "stunning 8k astrophotography, colorful nebulae, glowing planets, "
            "NASA-style imagery, deep space, particle physics visualization"
        ),
        seo_keywords=[
            "space facts", "science facts", "nasa discoveries", "universe facts",
            "physics facts", "mind blowing science", "black holes", "galaxy",
        ],
        monetization_notes="High engagement content. Cite NASA / peer-reviewed sources in description.",
    ),

    "cooking": NicheConfig(
        display_name="Cooking & Food Recipes",
        description="Quick recipes, cooking tips, food facts, and meal prep guides.",
        is_kids=False,
        tone="warm",
        script_style="tutorial",
        target_length_sec=(300, 720),
        shorts_length_sec=(30, 58),
        voice_model="en-US-JennyNeural",
        elevenlabs_voice_id="21m00Tcm4TlvDq8ikWAM",
        image_style=(
            "professional food photography with steam, vibrant ingredient colors, "
            "rustic kitchen background, top-down and 45-degree angle shots"
        ),
        seo_keywords=[
            "easy recipe", "cooking tips", "quick meals", "food hacks",
            "meal prep", "dinner ideas", "breakfast recipes",
        ],
        monetization_notes="Broad audience. List ingredients in description for SEO boost.",
    ),

    "fitness": NicheConfig(
        display_name="Fitness & Health",
        description="Workout routines, health tips, diet advice, and fitness motivation.",
        is_kids=False,
        tone="energetic",
        script_style="educational",
        target_length_sec=(300, 900),
        shorts_length_sec=(30, 58),
        voice_model="en-US-AndrewNeural",
        elevenlabs_voice_id="21m00Tcm4TlvDq8ikWAM",
        image_style=(
            "gym environment, athletic physique, bright studio lighting, "
            "sports photography, motivational atmosphere, sweat and effort"
        ),
        seo_keywords=[
            "workout routine", "gym tips", "weight loss", "fitness motivation",
            "exercise at home", "health tips", "diet plan",
        ],
        monetization_notes=(
            "Add disclaimer: 'Consult a doctor before starting any exercise program.' "
            "Good RPM with fitness product affiliate potential."
        ),
    ),
}

# Ordered list for menu display
NICHE_KEYS: List[str] = list(NICHES.keys())
KIDS_NICHES: List[str] = [k for k, v in NICHES.items() if v.is_kids]
ADULT_NICHES: List[str] = [k for k, v in NICHES.items() if not v.is_kids]


def get_niche_menu_lines() -> List[str]:
    """Returns formatted menu lines for the niche picker UI."""
    lines: List[str] = []
    lines.append(f"{'─'*58}")
    lines.append(f"  👶  KIDS CHANNEL NICHES  (Made-for-Kids / COPPA safe)")
    lines.append(f"{'─'*58}")
    for i, key in enumerate(NICHE_KEYS, 1):
        cfg = NICHES[key]
        if not cfg.is_kids and NICHES[NICHE_KEYS[i - 2]].is_kids if i > 1 else False:
            lines.append("")
            lines.append(f"{'─'*58}")
            lines.append(f"  📺  ADULT / GENERAL CHANNEL NICHES")
            lines.append(f"{'─'*58}")
        icon = "👶" if cfg.is_kids else "📺"
        lines.append(f"  {i:2}.  {icon}  {cfg.display_name}")
    lines.append("")
    lines.append(f"  {len(NICHE_KEYS)+1:2}.  ✏️   Custom (type your own niche)")
    return lines


def get_niche_by_index(idx: int) -> tuple:
    """idx is 1-based. Returns (key, NicheConfig) or ('custom', None)."""
    if idx == len(NICHE_KEYS) + 1:
        return ("custom", None)
    key = NICHE_KEYS[idx - 1]
    return (key, NICHES[key])
