"""LLM backend: Ollama (free/local) first, then Anthropic/OpenRouter."""

import json
import re
import urllib.request

def _ollama_chat(model, messages, timeout=120):
    host = __import__("os").environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
    payload = json.dumps({"model": model, "messages": messages, "stream": False, "options": {"temperature": 0.3, "num_predict": 2048}}).encode()
    req = urllib.request.Request(host + "/api/chat", data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode()).get("message", {}).get("content", "")

def _anthropic_chat(model, messages, api_key, timeout=120):
    import anthropic
    c = anthropic.Anthropic(api_key=api_key)
    r = c.messages.create(model=model, max_tokens=2048, temperature=0.3, messages=messages)
    return r.content[0].text

def _openrouter_chat(model, messages, api_key, timeout=120):
    payload = json.dumps({"model": model, "messages": messages, "temperature": 0.3, "max_tokens": 2048}).encode()
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions", data=payload, headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}", "HTTP-Referer": "https://github.com/claude-builders-bounty", "X-Title": "claude-review"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())["choices"][0]["message"]["content"]

def _check_ollama():
    try:
        host = __import__("os").environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
        urllib.request.urlopen(host + "/api/tags", timeout=5)
        return True
    except Exception:
        return False

def review_diff(diff_text, pr_meta, model="gemma4:e4b"):
    sys_prompt = "You are an expert code reviewer. Analyze the diff and output EXACTLY this structure:\n\n## Summary\n2-3 sentences.\n\n## Risks\n- item\n- item\n\n## Suggestions\n- item\n- item\n\n## Confidence\nLow / Medium / High"
    user_msg = f"PR: {pr_meta.get('title','')}\nAuthor: {pr_meta.get('author','')}\n\nDiff:\n```\n{diff_text[:30000]}\n```"
    messages = [{"role":"system","content": sys_prompt}, {"role":"user","content": user_msg}]
    if _check_ollama():
        try:
            content = _ollama_chat(model, messages)
            return _parse(content, "Ollama")
        except Exception:
            pass
    ak = __import__("os").environ.get("ANTHROPIC_API_KEY", "")
    if ak:
        try:
            content = _anthropic_chat("claude-sonnet-4-20250514", messages, ak)
            return _parse(content, "Anthropic")
        except Exception:
            pass
    ok = __import__("os").environ.get("OPENROUTER_API_KEY", "")
    if ok:
        try:
            content = _openrouter_chat("openai/gpt-oss-120b", messages, ok)
            return _parse(content, "OpenRouter")
        except Exception:
            pass
    raise RuntimeError("No LLM backend available")

def _parse(text, backend):
    def section(name):
        m = re.search(rf"## {name}\n(.*?)(?=\n## |\Z)", text, re.DOTALL)
        return m.group(1).strip() if m else ""
    summary = section("Summary")
    risks = [l.lstrip("- * ").strip() for l in section("Risks").split("\n") if l.strip()]
    suggestions = [l.lstrip("- * ").strip() for l in section("Suggestions").split("\n") if l.strip()]
    cm = re.search(r"## Confidence\n(\w+)", text)
    confidence = cm.group(1) if cm else "Medium"
    return {"summary": summary, "risks": risks, "suggestions": suggestions, "confidence": confidence, "backend": backend}
