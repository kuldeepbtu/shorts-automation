import re
with open(r"c:\ShortsBot\pipeline.py", "r", encoding="utf-8") as f:
    src = f.read()
lines = src.split("\n")
for i, line in enumerate(lines, 1):
    if "gemini-" in line.lower() or "veo" in line.lower() or "imagen" in line.lower() or "nano" in line.lower():
        print(f"Line {i}: {line.strip()}")
