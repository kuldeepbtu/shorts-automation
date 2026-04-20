"""Test new Gemini 3 models -- these have separate quota from Gemini 2.0."""
import os
from dotenv import load_dotenv
load_dotenv(r"c:\ShortsBot\.env")

# Correct Gemini 3 model names from official Google documentation
MODELS_TO_TEST = [
    "gemini-3-flash-preview",         # Gemini 3 Flash -- high-volume free tier
    "gemini-3.1-flash-lite-preview",  # Gemini 3.1 Flash-Lite -- cost-efficiency workhorse
    "gemini-3.1-flash-preview",       # Gemini 3.1 Flash -- Pro-level intelligence
    "gemini-2.5-flash-preview",       # Gemini 2.5 Flash (alternate name sometimes used)
    "gemini-2.5-pro-preview",         # Gemini 2.5 Pro
    "gemini-2.0-flash-exp",           # Experimental / may have separate quota
    "gemini-1.5-flash",               # Older but very reliable free tier
    "gemini-1.5-flash-8b",            # Cheapest, most quota
    "gemini-1.5-pro",                 # Pro, less quota but works
]

try:
    from google import genai
    from google.genai import types

    key = os.getenv("GEMINI_API_KEY", "")
    client = genai.Client(api_key=key)

    print(f"Testing with key: {key[:12]}...\n")
    for model in MODELS_TO_TEST:
        try:
            resp = client.models.generate_content(
                model=model,
                contents="Say OK.",
                config=types.GenerateContentConfig(temperature=1.0, max_output_tokens=5)
            )
            text = resp.text.strip() if resp.text else "(empty)"
            print(f"  WORKS: {model:40s} -> '{text}'")
        except Exception as e:
            err = str(e)
            if "429" in err or "quota" in err.lower() or "exhausted" in err.lower():
                print(f"  RATE LIMIT: {model}")
            elif "404" in err or "not found" in err.lower():
                print(f"  NOT FOUND: {model}")
            else:
                print(f"  ERROR: {model}: {err[:80]}")

except ImportError:
    print("SDK not installed: pip install google-genai")
