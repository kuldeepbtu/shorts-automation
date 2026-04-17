import json
import random
import logging
import sys
import os

from pathlib import Path

# Add parent directory to path so we can import pipeline
sys.path.append(str(Path(__file__).parent.parent))
from pipeline import gemini

log = logging.getLogger("ShortsBot.AIWorkflow")

def generate_niche_and_topic() -> dict:
    """Uses the AI to pick a highly monetizable or viral niche and generate a specific topic idea."""
    prompt = '''
You are a master YouTube strategist. Your goal is to brainstorm a highly engaging, viral, and easily monetizable topic for a "faceless" channel.
Provide a JSON response with no other text.

Select a niche from the following high-RPM categories:
- Personal Finance / Wealth
- Dark Psychology / Manipulation Facts
- AI & Tech Innovations
- Unknown History / Mysteries
- Stoicism / Motivation
- Mindblowing Science / Space Facts

Output Format:
{
  "niche": "The name of the niche",
  "topic": "The specific video topic title",
  "hook": "A 1-sentence description of the opening hook",
  "vibe": "E.g., mysterious, energetic, professional"
}
'''
    try:
        response_text = gemini(prompt)
        # Strip markdown if present
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        data = json.loads(response_text.strip())
        log.info(f"[Generator] Picked Niche: {data.get('niche')} - Topic: {data.get('topic')}")
        return data
    except Exception as e:
        log.error(f"[Generator] Failed to generate topic: {e}")
        # Fallback
        return {
            "niche": "Mindblowing Science",
            "topic": "The terrifying scale of the universe",
            "hook": "You think the Earth is big? Think again.",
            "vibe": "mysterious"
        }

def generate_script_and_prompts(topic_data: dict, is_shorts: bool) -> list:
    """
    Generates a script and visual prompts for Pollinations.ai.
    Returns a list of scenes: [{"text": "...", "image_prompt": "..."}, ...]
    """
    duration_guidance = "25-50 seconds (about 60-90 words)" if is_shorts else "2-3 minutes (about 300-450 words)"
    format_guidance = "fast-paced short vertical video (9:16)" if is_shorts else "horizontal cinematic video (16:9)"

    prompt = f'''
You are an expert YouTube script writer for faceless channels.
Write a script for a {format_guidance} about: "{topic_data['topic']}"
The vibe should be: {topic_data['vibe']}.
Target duration: {duration_guidance}. Do not write too much.

Break the script down into distinct SCENES. For each scene, provide:
1. The exactly spoken 'text'.
2. An 'image_prompt' that vividly describes what should be shown on screen. The image prompt must be very detailed, cinematic, high quality, and descriptive. (e.g., "cinematic 8k render of a black hole consuming a star, neon purple and orange, highly detailed")

Output ONLY valid JSON in this format, with no markdown formatting:
[
  {{
    "text": "Did you know that...",
    "image_prompt": "Cinematic shot of..."
  }},
  {{
    "text": "Here is why...",
    "image_prompt": "Close up camera angle of..."
  }}
]
'''
    try:
        response_text = gemini(prompt)
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        elif response_text.startswith("```"):
            response_text = response_text[3:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

        scenes = json.loads(response_text.strip())
        log.info(f"[Generator] Generated a script with {len(scenes)} scenes.")
        # Ensure we don't have too many scenes for shorts to keep pacing fast
        return scenes
    except Exception as e:
        log.error(f"[Generator] Failed to generate script: {e}")
        # Fallback scene
        return [{
            "text": "The universe is unimaginably massive. A place full of mysteries we may never comprehend.",
            "image_prompt": "Cinematic 8k render of a glowing galaxy surrounded by dark space, highly detailed, visually stunning"
        }]

def generate_metadata(topic_data: dict) -> dict:
    """Generates the Youtube upload title, description, and tags."""
    prompt = f'''
Generate Youtube metadata for a video titled: "{topic_data['topic']}" in the niche "{topic_data['niche']}".
The goal is maximum virality, SEO optimization, and click-through rate.

Output ONLY valid JSON:
{{
  "title": "<Catchy title under 60 chars>",
  "description": "<Engaging 2-paragraph description with keywords>",
  "tags": ["tag1", "tag2", "tag3"]
}}
'''
    try:
        response_text = gemini(prompt)
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]

        return json.loads(response_text.strip())
    except Exception as e:
        return {
            "title": topic_data["topic"],
            "description": f"An amazing video about {topic_data['topic']}.",
            "tags": ["viral", "trending", "facts", "youtube"]
        }
