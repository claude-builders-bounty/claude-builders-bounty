---
name: provider-endpoint-quirks
description: "Verify catalog + inference before adding model aliases."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [provider, model, verification, troubleshooting, nvidia, moonshot, catalog-vs-inference]
    related_skills: [hermes-agent, configure-nvidia-fallback]
---

# Provider Endpoint Quirks

**Purpose**: Document known gaps between provider model catalogs and actual inference availability. Prevents wasted time configuring aliases for models that exist in `/v1/models` but fail at `/v1/chat/completions`.

## Verification Protocol (mandatory before adding any alias)

```bash
# 1. Check catalog
curl -H "Authorization: Bearer $KEY" https://<provider>/v1/models | grep <model-id>

# 2. Test inference (non-streaming, tiny payload)
curl -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" \
  -d '{"model":"<model-id>","messages":[{"role":"user","content":"hi"}],"max_tokens":10,"stream":false}' \
  https://<provider>/v1/chat/completions

# 3. Only if BOTH succeed → add alias
hermes config set model.aliases.<name> <provider>/<model-id>
```

**Never trust the catalog alone.** Catalog = marketing; inference endpoint = reality.

## Known Quirks

### NVIDIA (`integrate.api.nvidia.com`)

| Model ID | Catalog | Inference | Notes |
|----------|---------|-----------|-------|
| `nvidia/nemotron-3-ultra-550b-a55b` | ✅ | ✅ | Primary model, works reliably |
| `moonshotai/kimi-k3` | ✅ | ❌ **TIMEOUT** | Listed in catalog, inference hangs indefinitely (tested 2026-10-10 with two different API keys, stream + non-stream, with/without `reasoning_effort`) |
| `meta/llama-3.2-90b-vision-instruct` | ✅ | ❌ **TIMEOUT** | Same pattern as Kimi-K3 |

**Root cause hypothesis**: These are third-party models hosted on NVIDIA's platform that require special provisioning/entitlement not granted to standard API keys. The catalog is a superset of what's actually callable.

**Workaround**: Use the model's native provider instead:
- Kimi-K3 → `moonshotai` provider (`api.moonshot.cn/v1`, needs `KIMI_API_KEY`)
- Or via OpenRouter (`openrouter/moonshotai/kimi-k3`, needs `OPENROUTER_API_KEY`)

### General Pattern to Watch For

Any provider that aggregates third-party models (NVIDIA, Fireworks, Together, DeepInfra, etc.) may list models they don't actually serve to your tier/key. Always run the 2-step verification above.

## NVIDIA 429 Diagnosis Protocol (Mandatory Before Assuming Rate Limit)

When NVIDIA `integrate.api.nvidia.com` returns HTTP 429, determine if it's **rate-based** (retry works) or **account-level hard block/quota exhaustion** (must wait or rotate key). Never assume — probe empirically.

### 3-Step Verification (Run in Order)

```bash
# 1. Isolate single request from cc-switch proxy (bypass retry amplification)
# Read key from cc-switch.db at runtime (never print/log it)
python3 -c "
import sqlite3, json, urllib.request, time, sys
DB = r'D:\Ai\claude code\cc-switch.db'
URL = 'https://integrate.api.nvidia.com/v1/chat/completions'
MODEL = 'nvidia/nemotron-3-ultra-550b-a55b'

con = sqlite3.connect('file:%s?mode=ro' % DB.replace('\\\\', '/'), uri=True)
rows = list(con.execute(
    'select id,name,settings_config from providers where settings_config like \"%nvapi-%\"'))
for pid, name, sc in rows:
    env = json.loads(sc).get('env', {})
    tok = env.get('ANTHROPIC_AUTH_TOKEN', '')
    if tok.startswith('nvapi-'):
        print('Provider:', name, 'key=%s...%s len=%d' % (tok[:9], tok[-4:], len(tok)))
        # Single isolated request
        body = json.dumps({'model': MODEL, 'messages': [{'role': 'user', 'content': 'ok'}], 'max_tokens': 8, 'stream': False}).encode()
        req = urllib.request.Request(URL, data=body, method='POST', headers={
            'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json', 'Accept': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                print('  SINGLE: %s  %.1fs  %s' % (r.status, 0, r.read(200).decode()[:120]))
        except urllib.error.HTTPError as e:
            print('  SINGLE: %s  %s' % (e.code, e.read(200).decode()[:120]))
"

# 2. Check if key itself is still valid (distinguishes auth failure from rate limit)
curl -H "Authorization: Bearer <nvapi-key>" https://integrate.api.nvidia.com/v1/models
# 200 + model count = key valid; 401/403 = key dead

# 3. Interval test: 3 requests spaced 5s apart — stable 200 = rate-based; stable 429 = hard block
for i in 1 2 3; do sleep 5; curl -H "Authorization: Bearer <key>" -d '{"model":"<model>","messages":[{"role":"user","content":"ok"}],"max_tokens":8}' https://integrate.api.nvidia.com/v1/chat/completions; done
```

### Interpretation Matrix

| Single Request | `/v1/models` | Interval 3×5s | Conclusion | Action |
|----------------|--------------|---------------|------------|--------|
| 200 | 200 (N models) | 200,200,200 | **No 429 now** — was transient burst | Resume, add backoff |
| 429 | 200 (N models) | 429,429,429 | **Hard account block** (quota/cooldown) | Wait 30-60 min or rotate key |
| 429 | 401/403 | N/A | **Key invalid/expired** | Get new key from user |
| 200 | 200 | 200,429,200 | **Rate-based** (burst sensitivity) | Add jitter/backoff, reduce concurrency |

### Key Insights from Production (2026-10-18)

- **Single isolated request 200 + interval test 429** = our retry logic (cc-switch `max_retries=6` + no backoff) amplifies burst into sustained 429. Fix: add retry-after respect + exponential backoff in proxy.
- **`x-ratelimit-remaining-requests` header** often missing on 429 responses — don't rely on it.
- **`/v1/models` returning 200 with 81 models** proves key is valid; 429 is purely rate/quota.
- **`z-ai/glm-5.3-flash` consistently times out (601s)** — listed in catalog but inference unavailable. Always verify inference before adding alias.

## References

- `references/nvidia-integrate-api.md` — detailed test transcript for NVIDIA integrate API
- `references/nvidia-429-diagnosis.md` — this protocol with full test transcripts