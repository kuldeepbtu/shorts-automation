"""
Apply final model name fix:
Put gemini-3-flash-preview and gemini-3.1-flash-lite-preview FIRST
(they work even when gemini-2.0-flash is rate limited).
"""

PIPELINE = r"c:\ShortsBot\pipeline.py"
with open(PIPELINE, "r", encoding="utf-8") as f:
    src = f.read()

# Fix the model priority list
OLD_MODELS = '''_GEMINI_TEXT_MODELS = [
    "gemini-2.0-flash",           # most stable & widest free quota
    "gemini-2.0-flash-lite",      # lightest, most quota-friendly
]'''

NEW_MODELS = '''_GEMINI_TEXT_MODELS = [
    # Gemini 3 series -- separate quota bucket, works even when gemini-2.0 is rate-limited
    "gemini-3-flash-preview",         # Gemini 3 Flash (high-volume, fast, FREE)
    "gemini-3.1-flash-lite-preview",  # Gemini 3.1 Flash-Lite (cost-efficiency workhorse, FREE)
    # Gemini 2.0 series -- fallback when Gemini 3 preview quota is also hit
    "gemini-2.0-flash",               # Proven stable, wide free quota
    "gemini-2.0-flash-lite",          # Lightest Gemini 2.0 model
]'''

if OLD_MODELS not in src:
    print("ERROR: Old model list not found -- check pipeline.py")
    # Print what IS there
    idx = src.find("_GEMINI_TEXT_MODELS")
    print(repr(src[idx:idx+300]))
    exit(1)

new_src = src.replace(OLD_MODELS, NEW_MODELS, 1)
with open(PIPELINE, "w", encoding="utf-8") as f:
    f.write(new_src)

print("SUCCESS: Model list updated")

# Verify syntax
import ast
try:
    ast.parse(new_src)
    print("SYNTAX OK")
except SyntaxError as e:
    print(f"SYNTAX ERROR: {e}")
