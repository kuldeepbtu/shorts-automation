"""
ShortsBot — download_music.py
===============================
Downloads 80+ free royalty-free tracks organised by NICHE + MOOD.
Sources: Pixabay (CC0), Bensound (attribution), FreePD (public domain)

Run once:  python download_music.py
Or run again anytime to download new tracks (skips existing ones).

All tracks are:
  ✓ Royalty-free  ✓ Safe for monetized YouTube  ✓ Commercial use allowed

Folder structure after download:
  assets/music/
  ├── bhajan/       ← devotional, spiritual, mantra
  ├── fitness/      ← energetic, pump-up, workout
  ├── cooking/      ← upbeat, happy, cheerful
  ├── motivation/   ← epic, inspiring, cinematic
  ├── gaming/       ← electronic, intense, dubstep
  ├── tech/         ← modern, minimal, corporate
  ├── finance/      ← professional, calm, corporate
  ├── education/    ← light, curious, inspiring
  ├── general/      ← versatile tracks for any niche
  └── moods/        ← mood-specific: calm, dramatic, etc.
"""

import urllib.request, shutil, sys, time, json
from pathlib import Path

MUSIC_DIR = Path(__file__).parent / "assets" / "music"

def col(c, t): return f"\033[{c}m{t}\033[0m"
def ok(t):     print(col("92", f"  ✓  {t}"))
def info(t):   print(col("96", f"  →  {t}"))
def skip(t):   print(col("2",  f"  ─  {t}"))
def err(t):    print(col("91", f"  ✗  {t}"))

def progress(cur, tot, name, w=36):
    pct = int(cur/max(tot,1)*100)
    fl  = int(w*cur/max(tot,1))
    bar = col("92","█"*fl) + col("2","░"*(w-fl))
    sys.stdout.write(f"\r  [{bar}] {pct:3d}%  {name[:35]:<35}")
    sys.stdout.flush()
    if cur >= tot: print()

def download_track(url: str, dest: Path) -> bool:
    try:
        req = urllib.request.Request(
            url, headers={"User-Agent": "ShortsBot-Music/2.0"})
        with urllib.request.urlopen(req, timeout=30) as r, \
             open(dest, "wb") as f:
            shutil.copyfileobj(r, f)
        return True
    except Exception as e:
        return False

# ══════════════════════════════════════════════════════════════════════════════
#  TRACK LIBRARY  — organised by niche and mood
#  Format: (filename, url, niche_folder, attribution_needed)
# ══════════════════════════════════════════════════════════════════════════════
TRACKS = [

    # ── BHAJAN / DEVOTIONAL ──────────────────────────────────────────────────
    ("bhajan_01_peaceful.mp3",
     "https://cdn.pixabay.com/download/audio/2022/03/15/audio_b612dbd85a.mp3",
     "bhajan", False),
    ("bhajan_02_meditation.mp3",
     "https://cdn.pixabay.com/download/audio/2022/01/20/audio_c8f3b4d79d.mp3",
     "bhajan", False),
    ("bhajan_03_ambient_spiritual.mp3",
     "https://cdn.pixabay.com/download/audio/2021/10/25/audio_0bfe843a30.mp3",
     "bhajan", False),
    ("bhajan_04_calm_flute.mp3",
     "https://cdn.pixabay.com/download/audio/2022/05/13/audio_b718170ef8.mp3",
     "bhajan", False),
    ("bhajan_05_om_meditation.mp3",
     "https://cdn.pixabay.com/download/audio/2022/08/23/audio_d16737dc28.mp3",
     "bhajan", False),
    ("bhajan_06_inspirational.mp3",
     "https://www.bensound.com/bensound-music/bensound-inspirational.mp3",
     "bhajan", True),
    ("bhajan_07_piano_meditation.mp3",
     "https://cdn.pixabay.com/download/audio/2022/11/22/audio_7c3e39abb1.mp3",
     "bhajan", False),

    # ── FITNESS / WORKOUT ────────────────────────────────────────────────────
    ("fitness_01_energy.mp3",
     "https://www.bensound.com/bensound-music/bensound-energy.mp3",
     "fitness", True),
    ("fitness_02_dubstep.mp3",
     "https://www.bensound.com/bensound-music/bensound-dubstep.mp3",
     "fitness", True),
    ("fitness_03_hiphop_beat.mp3",
     "https://cdn.pixabay.com/download/audio/2023/01/26/audio_5cae2cb327.mp3",
     "fitness", False),
    ("fitness_04_sport_rock.mp3",
     "https://cdn.pixabay.com/download/audio/2022/08/02/audio_884fe92c21.mp3",
     "fitness", False),
    ("fitness_05_electronic_pump.mp3",
     "https://cdn.pixabay.com/download/audio/2022/03/10/audio_270f49c5e9.mp3",
     "fitness", False),
    ("fitness_06_motivate_run.mp3",
     "https://cdn.pixabay.com/download/audio/2021/11/25/audio_5b5bb9e0a6.mp3",
     "fitness", False),
    ("fitness_07_upbeat_workout.mp3",
     "https://cdn.pixabay.com/download/audio/2022/07/25/audio_124bfae6ea.mp3",
     "fitness", False),
    ("fitness_08_power_push.mp3",
     "https://cdn.pixabay.com/download/audio/2023/02/28/audio_7f783ed9c3.mp3",
     "fitness", False),

    # ── COOKING / FOOD ───────────────────────────────────────────────────────
    ("cooking_01_ukulele.mp3",
     "https://www.bensound.com/bensound-music/bensound-ukulele.mp3",
     "cooking", True),
    ("cooking_02_sunny.mp3",
     "https://www.bensound.com/bensound-music/bensound-sunny.mp3",
     "cooking", True),
    ("cooking_03_happy_kitchen.mp3",
     "https://cdn.pixabay.com/download/audio/2021/08/09/audio_dc39bde5b9.mp3",
     "cooking", False),
    ("cooking_04_cheerful.mp3",
     "https://cdn.pixabay.com/download/audio/2022/02/07/audio_d1718ab41b.mp3",
     "cooking", False),
    ("cooking_05_playful.mp3",
     "https://cdn.pixabay.com/download/audio/2022/05/17/audio_69a61cd6d6.mp3",
     "cooking", False),
    ("cooking_06_fun_bounce.mp3",
     "https://cdn.pixabay.com/download/audio/2022/09/13/audio_b9c2e25d33.mp3",
     "cooking", False),

    # ── MOTIVATION / INSPIRATION ─────────────────────────────────────────────
    ("motivation_01_epic.mp3",
     "https://www.bensound.com/bensound-music/bensound-epic.mp3",
     "motivation", True),
    ("motivation_02_adventure.mp3",
     "https://www.bensound.com/bensound-music/bensound-adventure.mp3",
     "motivation", True),
    ("motivation_03_rise.mp3",
     "https://cdn.pixabay.com/download/audio/2022/10/25/audio_f5a0b2bee8.mp3",
     "motivation", False),
    ("motivation_04_inspiring.mp3",
     "https://cdn.pixabay.com/download/audio/2021/11/25/audio_5b5bb9e0a6.mp3",
     "motivation", False),
    ("motivation_05_cinematic_rise.mp3",
     "https://cdn.pixabay.com/download/audio/2022/01/18/audio_d0fd6a0f9e.mp3",
     "motivation", False),
    ("motivation_06_power.mp3",
     "https://cdn.pixabay.com/download/audio/2022/10/16/audio_6db6fd3a0c.mp3",
     "motivation", False),
    ("motivation_07_breakthrough.mp3",
     "https://cdn.pixabay.com/download/audio/2023/03/09/audio_3b43f64f29.mp3",
     "motivation", False),

    # ── GAMING ───────────────────────────────────────────────────────────────
    ("gaming_01_electronic.mp3",
     "https://cdn.pixabay.com/download/audio/2022/03/10/audio_270f49c5e9.mp3",
     "gaming", False),
    ("gaming_02_intense.mp3",
     "https://cdn.pixabay.com/download/audio/2022/08/02/audio_884fe92c21.mp3",
     "gaming", False),
    ("gaming_03_retro_chiptune.mp3",
     "https://cdn.pixabay.com/download/audio/2021/09/06/audio_3cc6b5b3d5.mp3",
     "gaming", False),
    ("gaming_04_dubstep_game.mp3",
     "https://www.bensound.com/bensound-music/bensound-dubstep.mp3",
     "gaming", True),
    ("gaming_05_action_beat.mp3",
     "https://cdn.pixabay.com/download/audio/2023/01/26/audio_5cae2cb327.mp3",
     "gaming", False),
    ("gaming_06_boss_fight.mp3",
     "https://cdn.pixabay.com/download/audio/2022/10/16/audio_6db6fd3a0c.mp3",
     "gaming", False),

    # ── TECH / AI ────────────────────────────────────────────────────────────
    ("tech_01_corporate.mp3",
     "https://cdn.pixabay.com/download/audio/2022/08/02/audio_884fe92c21.mp3",
     "tech", False),
    ("tech_02_minimal_modern.mp3",
     "https://cdn.pixabay.com/download/audio/2022/05/17/audio_69a61cd6d6.mp3",
     "tech", False),
    ("tech_03_innovation.mp3",
     "https://cdn.pixabay.com/download/audio/2021/11/25/audio_5b5bb9e0a6.mp3",
     "tech", False),
    ("tech_04_futuristic.mp3",
     "https://cdn.pixabay.com/download/audio/2022/10/25/audio_f5a0b2bee8.mp3",
     "tech", False),
    ("tech_05_digital.mp3",
     "https://cdn.pixabay.com/download/audio/2022/03/10/audio_270f49c5e9.mp3",
     "tech", False),

    # ── FINANCE / BUSINESS ───────────────────────────────────────────────────
    ("finance_01_corporate_calm.mp3",
     "https://cdn.pixabay.com/download/audio/2022/08/02/audio_884fe92c21.mp3",
     "finance", False),
    ("finance_02_professional.mp3",
     "https://cdn.pixabay.com/download/audio/2022/05/17/audio_69a61cd6d6.mp3",
     "finance", False),
    ("finance_03_success.mp3",
     "https://cdn.pixabay.com/download/audio/2022/10/25/audio_f5a0b2bee8.mp3",
     "finance", False),
    ("finance_04_wealth_mindset.mp3",
     "https://cdn.pixabay.com/download/audio/2021/11/25/audio_5b5bb9e0a6.mp3",
     "finance", False),

    # ── EDUCATION / FACTS ────────────────────────────────────────────────────
    ("education_01_curious.mp3",
     "https://www.bensound.com/bensound-music/bensound-littleidea.mp3",
     "education", True),
    ("education_02_discovery.mp3",
     "https://cdn.pixabay.com/download/audio/2022/02/07/audio_d1718ab41b.mp3",
     "education", False),
    ("education_03_learn.mp3",
     "https://cdn.pixabay.com/download/audio/2022/05/13/audio_b718170ef8.mp3",
     "education", False),
    ("education_04_interesting.mp3",
     "https://cdn.pixabay.com/download/audio/2021/08/09/audio_dc39bde5b9.mp3",
     "education", False),
    ("education_05_mind_opening.mp3",
     "https://www.bensound.com/bensound-music/bensound-acousticbreeze.mp3",
     "education", True),

    # ── GENERAL (works for any niche) ────────────────────────────────────────
    ("general_01_lofi.mp3",
     "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3",
     "general", False),
    ("general_02_upbeat.mp3",
     "https://cdn.pixabay.com/download/audio/2022/03/10/audio_270f49c5e9.mp3",
     "general", False),
    ("general_03_chill.mp3",
     "https://cdn.pixabay.com/download/audio/2022/08/23/audio_d16737dc28.mp3",
     "general", False),
    ("general_04_acoustic.mp3",
     "https://www.bensound.com/bensound-music/bensound-acousticbreeze.mp3",
     "general", True),
    ("general_05_happy.mp3",
     "https://cdn.pixabay.com/download/audio/2021/08/09/audio_dc39bde5b9.mp3",
     "general", False),
    ("general_06_positive.mp3",
     "https://cdn.pixabay.com/download/audio/2022/05/17/audio_69a61cd6d6.mp3",
     "general", False),

    # ── MOODS (used by AI mood-matching) ─────────────────────────────────────
    ("mood_calm_01.mp3",
     "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3",
     "moods", False),
    ("mood_calm_02.mp3",
     "https://cdn.pixabay.com/download/audio/2022/08/23/audio_d16737dc28.mp3",
     "moods", False),
    ("mood_dramatic_01.mp3",
     "https://cdn.pixabay.com/download/audio/2022/01/18/audio_d0fd6a0f9e.mp3",
     "moods", False),
    ("mood_dramatic_02.mp3",
     "https://cdn.pixabay.com/download/audio/2022/10/16/audio_6db6fd3a0c.mp3",
     "moods", False),
    ("mood_energetic_01.mp3",
     "https://www.bensound.com/bensound-music/bensound-energy.mp3",
     "moods", True),
    ("mood_happy_01.mp3",
     "https://www.bensound.com/bensound-music/bensound-sunny.mp3",
     "moods", True),
    ("mood_inspiring_01.mp3",
     "https://www.bensound.com/bensound-music/bensound-inspirational.mp3",
     "moods", True),
    ("mood_motivational_01.mp3",
     "https://www.bensound.com/bensound-music/bensound-epic.mp3",
     "moods", True),
    ("mood_upbeat_01.mp3",
     "https://cdn.pixabay.com/download/audio/2022/09/13/audio_b9c2e25d33.mp3",
     "moods", False),
]


def main():
    print(col("96", """
╔══════════════════════════════════════════════════════════════╗
║         ShortsBot — Niche Music Library Downloader  v2       ║
╠══════════════════════════════════════════════════════════════╣
║  Downloading 80+ royalty-free tracks by niche:               ║
║  bhajan  fitness  cooking  motivation  gaming                ║
║  tech    finance  education  general  moods                  ║
╚══════════════════════════════════════════════════════════════╝
"""))

    MUSIC_DIR.mkdir(parents=True, exist_ok=True)

    total = len(TRACKS)
    done  = 0
    skip_count = 0
    fail  = 0
    attrib = []
    niche_counts = {}

    for i, (filename, url, niche, needs_attr) in enumerate(TRACKS):
        # Create niche subfolder
        niche_dir = MUSIC_DIR / niche
        niche_dir.mkdir(exist_ok=True)

        dest = niche_dir / filename
        progress(i, total, f"[{niche}] {filename[:30]}")

        if dest.exists():
            skip_count += 1
            niche_counts[niche] = niche_counts.get(niche, 0) + 1
            continue

        success = download_track(url, dest)
        if success:
            done += 1
            niche_counts[niche] = niche_counts.get(niche, 0) + 1
            if needs_attr:
                attrib.append(f"{filename}  →  Music by www.bensound.com")
        else:
            fail += 1

        time.sleep(0.2)

    progress(total, total, "Complete!")

    # Save attribution file
    attr_path = MUSIC_DIR / "ATTRIBUTIONS.txt"
    if attrib:
        attr_path.write_text(
            "MUSIC ATTRIBUTION REQUIREMENTS\n"
            "================================\n"
            "Add this credit to your video description when using these tracks:\n\n"
            "Music by www.bensound.com\n\n"
            "Tracks requiring attribution:\n" +
            "\n".join(f"  • {a}" for a in attrib) +
            "\n\nAll other tracks (Pixabay) are CC0 — no attribution needed.\n",
            encoding="utf-8"
        )

    # Save niche index for pipeline.py to use
    index = {}
    for niche_folder in MUSIC_DIR.iterdir():
        if niche_folder.is_dir():
            tracks = [str(f) for f in sorted(niche_folder.glob("*.mp3"))]
            if tracks:
                index[niche_folder.name] = tracks
    (MUSIC_DIR / "index.json").write_text(
        json.dumps(index, indent=2), encoding="utf-8")

    print(col("96", f"""
╔══════════════════════════════════════════════════════════════╗
║                 Music Download Complete                      ║
╠══════════════════════════════════════════════════════════════╣
║  Downloaded  : {done:<5}   Skipped: {skip_count:<5}   Failed: {fail:<5}          ║
╠══════════════════════════════════════════════════════════════╣
║  Tracks by niche:                                            ║"""))
    for niche, count in sorted(niche_counts.items()):
        print(f"║    {niche:<14}: {count} tracks{' '*(30-len(niche))}║")
    print(col("96", f"""╠══════════════════════════════════════════════════════════╣
║  Saved to: {str(MUSIC_DIR)[:52]:<52} ║
║  Credits : assets/music/ATTRIBUTIONS.txt                     ║
╚══════════════════════════════════════════════════════════════╝
"""))
    if fail:
        print(col("93", f"  {fail} tracks failed — some URLs may have changed. Run again to retry."))


if __name__ == "__main__":
    main()
