"""Multi-provider LLM with free-tier fallback + key rotation. Plain HTTP, no SDKs."""
import os, httpx

def _post(url, headers, body):
    r = httpx.post(url, headers=headers, json=body, timeout=90); r.raise_for_status(); return r.json()

def _oai(base):
    def f(key, model, p):
        j = _post(base + "/chat/completions", {"Authorization": "Bearer " + key},
                  {"model": model, "messages": [{"role": "user", "content": p}]})
        return j["choices"][0]["message"]["content"]
    return f

def _gemini(key, model, p):
    j = _post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
              {}, {"contents": [{"parts": [{"text": p}]}]})
    return j["candidates"][0]["content"]["parts"][0]["text"]

def _claude(key, model, p):
    j = _post("https://api.anthropic.com/v1/messages", {"x-api-key": key, "anthropic-version": "2023-06-01"},
              {"model": model, "max_tokens": 2000, "messages": [{"role": "user", "content": p}]})
    return j["content"][0]["text"]

PROVIDERS = [
    ("GEMINI", _gemini, "gemini-2.5-flash"),
    ("GROQ", _oai("https://api.groq.com/openai/v1"), "llama-3.3-70b-versatile"),
    ("OPENROUTER", _oai("https://openrouter.ai/api/v1"), "meta-llama/llama-3.3-70b-instruct:free"),
    ("OPENAI", _oai("https://api.openai.com/v1"), "gpt-4o-mini"),
    ("ANTHROPIC", _claude, "claude-sonnet-4-6"),
]

def ask(prompt):
    for name, fn, default in PROVIDERS:
        model = os.getenv(name + "_MODEL", default)
        for key in [k.strip() for k in os.getenv(name + "_API_KEY", "").split(",") if k.strip()]:
            try: return fn(key, model, prompt)
            except Exception as e: print(f"[{name}] failed:", e)
    return None
