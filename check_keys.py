"""
ShortsBot — Quick Gemini Key Health Check
Reads all GEMINI_API_KEY* from .env and tests each one.
"""
import os, json, urllib.request, time

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

keys = []
k0 = os.getenv("GEMINI_API_KEY", "")
if k0: keys.append(("Key 1", k0))
for i in range(2, 10):
    k = os.getenv(f"GEMINI_API_KEY_{i}", "")
    if k: keys.append((f"Key {i}", k))

model    = "gemini-2.5-flash-lite"
endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
prompt   = "Reply with the single word: OK"

SEP = "-" * 60
print(f"\n{SEP}")
print(f"  Gemini Key Health Check — model: {model}")
print(f"  Testing {len(keys)} key(s) found in .env")
print(SEP)

working = []
for label, key in keys:
    short = key[-8:]
    try:
        data = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode()
        req  = urllib.request.Request(
            endpoint, data=data,
            headers={"Content-Type": "application/json", "x-goog-api-key": key},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            resp  = json.loads(r.read())
        reply = resp["candidates"][0]["content"]["parts"][0]["text"].strip()
        print(f"  {label}  (...{short})  OK   WORKING  -> replied: {reply!r}")
        working.append(label)
    except Exception as e:
        msg = str(e)
        if "429" in msg:
            status = "429 RATE-LIMITED  (key is valid, quota hit — will recover)"
            working.append(label + " [rate-limited]")
        elif "403" in msg:
            status = "403 FORBIDDEN     (key invalid OR project blocked)"
        elif "401" in msg:
            status = "401 UNAUTHORIZED  (wrong or expired key)"
        elif "400" in msg:
            status = "400 BAD REQUEST   (check key format — must start AIza)"
        else:
            status = f"ERROR: {msg[:70]}"
        print(f"  {label}  (...{short})  FAIL {status}")
    time.sleep(2)   # small gap between calls

print(SEP)
print(f"\n  Summary: {len(working)}/{len(keys)} key(s) usable")
for w in working:
    print(f"    -> {w}")
print()
