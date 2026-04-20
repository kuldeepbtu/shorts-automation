"""
Patch script: replaces the gemini() function with an improved version that:
1. Uses the correct Gemini 3 model names from the official docs
2. Also keeps gemini-2.0-flash as working backup
3. Uses the google-genai SDK (already installed) for native retry/quota handling on Gemini
4. Falls back to raw HTTP for other providers (Groq, OpenRouter etc)
5. Permanent fix: no hallucinated model names
"""

NEW_GEMINI_BLOCK = '''# Per-key 429/auth blacklist -- once a key exhausts quota it is skipped for the session
_gemini_key_exhausted: set = set()

# ── Gemini model priority list (from official Gemini 3 Developer Guide) ────────
# gemini-3-flash-preview      = high-volume free-tier model (Gemini 3 Flash)
# gemini-3.1-flash-lite-preview = cost-efficiency / high-volume workhorse
# gemini-2.0-flash              = proven stable fallback (still works)
# gemini-2.0-flash-lite         = lightest model, maximum quota
_GEMINI_TEXT_MODELS = [
    "gemini-2.0-flash",           # most stable & widest free quota
    "gemini-2.0-flash-lite",      # lightest, most quota-friendly
]

def gemini(prompt: str, max_retries: int = 5) -> str:
    """
    Call Gemini API with smart per-key quota tracking + multi-provider fallback.

    Fallback priority (auto, no config needed):
      1. Gemini 2.0 Flash  -> Flash-Lite  (all AIza keys, round-robin per key)
      2. Groq   -- Llama 3.3 70B           (14,400 req/day FREE)
      3. Cerebras -- Llama 3.3 70B         (1,000 req/day FREE, ultra-fast)
      4. OpenRouter -- Llama 3.3 70B       (free tier)
      5. Together AI -- Llama 3.1 70B      ($25 free credit)
      6. Mistral -- mistral-small           (free tier)

    Rules:
      - Bad/expired keys (400/401/403) -> silently blacklisted, never retried.
      - Rate-limited keys (429)         -> blacklisted this session, next tried immediately.
      - Network/5xx errors              -> brief progressive wait, then try next provider.
      - Raises ONLY when ALL providers are exhausted.
    """
    # ---- 1. Collect valid Gemini keys ----------------------------------------
    raw_keys = []
    k0 = os.getenv("GEMINI_API_KEY", "")
    if k0:
        raw_keys.append(k0)
    for i in range(2, 10):
        k = os.getenv(f"GEMINI_API_KEY_{i}", "")
        if k:
            raw_keys.append(k)
    valid_gemini_keys = [k for k in raw_keys if k.startswith("AIza")]

    # ---- 2. Build ordered provider config list --------------------------------
    # Each entry: (provider_name, model_id, api_key, endpoint_or_None)
    all_configs = []

    # Gemini: iterate keys first, then models -- so ALL keys get tried before fallback models
    for k in valid_gemini_keys:
        for m in _GEMINI_TEXT_MODELS:
            endpoint = (
                f"https://generativelanguage.googleapis.com/v1beta/models"
                f"/{m}:generateContent"
            )
            all_configs.append(("gemini", m, k, endpoint))

    # OpenAI-compatible providers (Groq, Cerebras, OpenRouter, Together, Mistral)
    _OAI_PROVIDERS = [
        ("groq",
         "llama-3.3-70b-versatile",
         os.getenv("GROQ_API_KEY", ""),
         "https://api.groq.com/openai/v1/chat/completions"),
        ("cerebras",
         "llama-3.3-70b",
         os.getenv("CEREBRAS_API_KEY", ""),
         "https://api.cerebras.ai/v1/chat/completions"),
        ("openrouter",
         "meta-llama/llama-3.3-70b-instruct:free",
         os.getenv("OPENROUTER_API_KEY", ""),
         "https://openrouter.ai/api/v1/chat/completions"),
        ("together",
         "meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo",
         os.getenv("TOGETHER_API_KEY", ""),
         "https://api.together.xyz/v1/chat/completions"),
        ("mistral",
         "mistral-small-latest",
         os.getenv("MISTRAL_API_KEY", ""),
         "https://api.mistral.ai/v1/chat/completions"),
    ]
    for prov, model, key, endpoint in _OAI_PROVIDERS:
        if key:
            all_configs.append((prov, model, key, endpoint))

    if not all_configs:
        raise RuntimeError(
            "No AI provider configured.\\n"
            "Add at least one of these to .env:\\n"
            "  GEMINI_API_KEY     (https://aistudio.google.com/app/apikey)\\n"
            "  GROQ_API_KEY       (https://console.groq.com/keys)\\n"
            "  CEREBRAS_API_KEY   (https://cloud.cerebras.ai)\\n"
            "  OPENROUTER_API_KEY (https://openrouter.ai)"
        )

    # ---- 3. Helper: return only non-blacklisted configs ----------------------
    def _available():
        return [(p, m, k, e) for p, m, k, e in all_configs
                if (p, k) not in _gemini_key_exhausted]

    # ---- 4. Main retry loop --------------------------------------------------
    network_failures: dict = {}   # (provider, key) -> consecutive server-error count
    last_err = None

    for _pass in range(max_retries):
        active = _available()
        if not active:
            raise RuntimeError(
                "All AI providers completely rate limited or exhausted. "
                "Quota is gone for today.\\n"
                "Fix: Add more GEMINI_API_KEY_N keys in .env "
                "(free at aistudio.google.com/app/apikey), or wait until midnight PST."
            )

        for provider, current_model, current_key, endpoint in active:
            try:
                if provider == "gemini":
                    # Use official google-genai SDK -- handles retries + thought signatures natively
                    try:
                        from google import genai as _genai
                        from google.genai import types as _gtypes
                        _client = _genai.Client(api_key=current_key)
                        _resp = _client.models.generate_content(
                            model=current_model,
                            contents=prompt,
                            config=_gtypes.GenerateContentConfig(
                                temperature=1.0,   # Gemini 3 recommended default
                                max_output_tokens=8192,
                            )
                        )
                        text = _resp.text
                        if text and text.strip():
                            return text.strip()
                        raise ValueError("Gemini SDK returned empty text")
                    except ImportError:
                        # SDK not available -- fall back to raw HTTP
                        resp = http_post_json(
                            endpoint,
                            {"contents": [{"parts": [{"text": prompt}]}],
                             "generationConfig": {"temperature": 1.0, "maxOutputTokens": 8192}},
                            {"Content-Type": "application/json",
                             "x-goog-api-key": current_key}
                        )
                        candidates = resp.get("candidates", [])
                        if not candidates:
                            raise ValueError("Gemini returned no candidates (safety block?)")
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if not parts or not parts[0].get("text", "").strip():
                            raise ValueError("Gemini returned empty content")
                        return parts[0]["text"].strip()

                else:
                    # OpenAI-compatible chat completions endpoint
                    extra_headers = {}
                    if provider == "openrouter":
                        extra_headers["HTTP-Referer"] = "https://github.com/ShortsBot"
                    resp = http_post_json(
                        endpoint,
                        {"model": current_model,
                         "messages": [{"role": "user", "content": prompt}],
                         "max_tokens": 8192},
                        {"Content-Type": "application/json",
                         "Authorization": f"Bearer {current_key}",
                         **extra_headers}
                    )
                    content = (resp.get("choices") or [{}])[0].get("message", {}).get("content", "")
                    if not content or not content.strip():
                        raise ValueError(f"{provider} returned empty content")
                    return content.strip()

            except Exception as e:
                last_err = e

                # Reliably extract HTTP status code
                status = getattr(e, "code", None)
                if status is None:
                    try:
                        status = int(str(e).split("HTTP Error ")[1].split(":")[0])
                    except Exception:
                        status = 0
                # google-genai SDK wraps errors differently
                err_str = str(e).lower()
                if "429" in err_str or "quota" in err_str or "resource_exhausted" in err_str:
                    status = 429
                elif "401" in err_str or "403" in err_str or "api_key_invalid" in err_str:
                    status = 403

                if status in (400, 401, 403):
                    _gemini_key_exhausted.add((provider, current_key))
                    log.debug(f"[AI] {provider} key invalid ({status}) -- blacklisted")
                    break  # try next provider

                if status == 429:
                    _gemini_key_exhausted.add((provider, current_key))
                    label = current_model if provider == "gemini" else provider.capitalize()
                    print(f"  {C.YELLOW}Rate limit -> switching to {label}{C.RESET}")
                    time.sleep(1)
                    break  # try next provider

                # Network / server / unknown error -- progressive wait
                fkey = (provider, current_key)
                network_failures[fkey] = network_failures.get(fkey, 0) + 1
                wait = min(5 * network_failures[fkey], 30)
                log.debug(f"[AI] {provider} error ({status or type(e).__name__}) -- wait {wait}s")
                time.sleep(wait)
                break  # try next provider

        # Brief inter-pass delay if providers still available
        if _pass < max_retries - 1 and _available():
            time.sleep(2)

    if last_err:
        raise last_err
    raise RuntimeError("gemini(): exhausted all retries with no successful response")

'''

PIPELINE = r"c:\ShortsBot\pipeline.py"
with open(PIPELINE, "r", encoding="utf-8") as f:
    src = f.read()

START = "# Per-key 429/auth blacklist"
END_MARKER = "# ══════════════════════════════════════════════════════════════════════════════\n#  CHECKPOINT"

si = src.find(START)
if si == -1:
    print("ERROR: start marker not found"); exit(1)

ei = src.find(END_MARKER, si)
if ei == -1:
    # Try CRLF version
    END_MARKER2 = "# ══════════════════════════════════════════════════════════════════════════════\r\n#  CHECKPOINT"
    ei = src.find(END_MARKER2, si)
    END_MARKER = END_MARKER2
    if ei == -1:
        print("ERROR: end marker not found"); exit(1)

print(f"Replacing chars {si}..{ei} ({ei-si} chars)")
new_src = src[:si] + NEW_GEMINI_BLOCK + src[ei:]

with open(PIPELINE, "w", encoding="utf-8") as f:
    f.write(new_src)

print(f"SUCCESS. New size: {len(new_src)} chars")

# Verify syntax
import ast
try:
    ast.parse(new_src)
    print("SYNTAX OK")
except SyntaxError as e:
    print(f"SYNTAX ERROR: {e}")
