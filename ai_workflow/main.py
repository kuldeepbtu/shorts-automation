import sys
import os
import shutil
from pathlib import Path
import logging

# Add parent directory to path so we can import modules
sys.path.append(str(Path(__file__).parent.parent))
from pipeline import yn, menu, upload_all, save_report, ensure_music

from ai_workflow.generator import generate_niche_and_topic, generate_script_and_prompts, generate_metadata
from ai_workflow.media_engine import generate_voice, generate_image, build_scene_video, concat_scenes, add_background_music

log = logging.getLogger("ShortsBot.AIWorkflow.Main")

AI_WORKSPACE = Path(__file__).parent / "workspace"
AI_OUTPUT = Path(__file__).parent / "output"
AI_ACCOUNTS = Path(__file__).parent / "accounts"

def get_autonomous_account() -> dict:
    AI_ACCOUNTS.mkdir(parents=True, exist_ok=True)
    # Pick the first valid account folder
    for folder in AI_ACCOUNTS.iterdir():
        if folder.is_dir() and ((folder / "client_secrets.json").exists() or (folder / "token.json").exists()):
            return {
                "folder": folder,
                "name": folder.name,
                "secrets_path": folder / "client_secrets.json",
                "token_path": folder / "token.json",
                "niche": "ai_generated",
            }
    return None

def run():
    print(f"\n╔{'═'*60}╗")
    print(f"║  🚀  Complete AI Workflow Initiated                      ║")
    print(f"╚{'═'*60}╝\n")

    # Cleanup previous temp files
    if AI_WORKSPACE.exists():
        shutil.rmtree(AI_WORKSPACE)
    AI_WORKSPACE.mkdir(parents=True, exist_ok=True)
    AI_OUTPUT.mkdir(parents=True, exist_ok=True)

    # 1. Automagically get channel from ai_workflow/accounts
    channel = get_autonomous_account()
    if not channel:
        print("❌ No AI channels configured!")
        print(f"Please create a folder in {AI_ACCOUNTS} and put your client_secrets.json there.")
        sys.exit(1)
        
    print(f"🤖 Autonomous channel selected: {channel['name']}")

    # 2. Ask for format
    format_type = menu("SELECT FORMAT", ["YouTube Shorts (9:16)", "Standard Video (16:9)"])
    is_shorts = (format_type == 1)

    # 3. Generate Idea
    print("\n🧠 Brainstorming viral topic...")
    topic_data = generate_niche_and_topic()
    
    # 4. Generate Script & Prompts
    print(f"\n✍️ Writing script for: {topic_data['topic']}")
    scenes = generate_script_and_prompts(topic_data, is_shorts)
    if not scenes:
        print("❌ Failed to generate script scenes.")
        sys.exit(1)

    # 5. Media Engine Execution
    print(f"\n🎬 Generating {len(scenes)} Media Scenes...")
    scene_videos = []
    
    for i, scene in enumerate(scenes):
        print(f"\n  ▶ Scene {i+1}/{len(scenes)}")
        scene_dir = AI_WORKSPACE / f"scene_{i}"
        scene_dir.mkdir()
        
        audio_path = scene_dir / "voice.mp3"
        image_path = scene_dir / "image.jpg"
        vid_path = scene_dir / "scene.mp4"
        
        # Audio
        duration = generate_voice(scene["text"], audio_path)
        
        # Visual
        generate_image(scene["image_prompt"], is_shorts, image_path)
        
        # Build Ken-Burns Effect Scene Video
        build_scene_video(image_path, audio_path, duration, vid_path, is_shorts)
        
        scene_videos.append(vid_path)

    # 6. Assembly
    safe_topic = "".join(c for c in topic_data['topic'][:30] if c.isalnum() or c in " _-").strip()
    assembled_path = AI_WORKSPACE / "assembled.mp4"
    final_video_path = AI_OUTPUT / f"{safe_topic}.mp4"
    
    print("\n🎥 Assembling final video...")
    concat_scenes(scene_videos, assembled_path)

    # 7. Background Music
    ensure_music()
    music_dir = Path(__file__).parent.parent / "assets" / "music"
    add_background_music(assembled_path, music_dir, final_video_path)

    # 8. Metadata
    print("\n📝 Generating SEO metadata...")
    meta = generate_metadata(topic_data)
    
    # Structure for upload_all
    upload_item = {
        "file": str(final_video_path),
        "title": meta["title"],
        "description": meta["description"],
        "tags": meta["tags"],
        "mode": "shorts" if is_shorts else "videos",
        "niche": topic_data["niche"]
    }

    print(f"\n✅ Final Render: {final_video_path}")
    print(f"Title: {meta['title']}")
    
    # 9. Upload
    if yn("\n🚀 Upload to YouTube now?", default=True):
        uploaded = upload_all([upload_item], channel, "public")
        save_report(uploaded, channel, {"source": "Complete AI Automation", "niche": topic_data["niche"]})
    else:
        print("Upload skipped. Final video is saved in ai_workflow/output/")

    print("\n🎉 Complete AI Workflow Finished!")

if __name__ == "__main__":
    run()
