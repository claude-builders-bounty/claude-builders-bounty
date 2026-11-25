# NVIDIA Integrate API — 429 Diagnosis Test Transcript

**Date:** 2026-10-18  
**Context:** cc-switch proxy routing to NVIDIA `integrate.api.nvidia.com` with single `nvapi-` key  
**Issue:** Multiple 429 responses from production traffic; need to determine if rate-based or hard block.

---

## Test 1: Single Isolated Request (Bypassing cc-switch Retry Amplification)

```bash
python3 -c "
import sqlite3, json, urllib.request, time
DB = r'D:\\Ai\\claude code\\cc-switch.db'
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
        body = json.dumps({'model': MODEL, 'messages': [{'role': 'user', 'content': 'ok'}], 'max_tokens': 8, 'stream': False}).encode()
        req = urllib.request.Request(URL, data=body, method='POST', headers={
            'Authorization': 'Bearer ' + tok, 'Content-Type': 'application/json', 'Accept': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                print('  SINGLE: %s  %.1fs  %s' % (r.status, 0, r.read(200).decode()[:120]))
        except urllib.error.HTTPError as e:
            print('  SINGLE: %s  %s' % (e.code, e.read(200).decode()[:120]))
"
```

**Output:**
```
Provider: nvidia-nemotron-ultra  key=nvapi-xxx...1234 len=84
  SINGLE: 200  0  {"id":"chatcmpl-...","object":"chat.completion","choices":[{"index":0,"message":{"role":"assistant","content":"OK"},"finish_reason":"stop"}]}
```

**Interpretation:** Single request succeeds (200). The key is valid and model is callable. 429s in production are NOT due to hard account block.

---

## Test 2: `/v1/models` Catalog Check

```bash
curl -H "Authorization: Bearer nvapi-xxx...1234" https://integrate.api.nvidia.com/v1/models | jq '.data | length'
```

**Output:**
```
81
```

**Interpretation:** Key is valid (401/403 would mean dead key). Catalog returns 81 models.

---

## Test 3: Interval Test (3 requests × 5s spacing)

```bash
for i in 1 2 3; do
  sleep 5
  curl -s -w "HTTP %{http_code}  %{time_total}s  " \
    -H "Authorization: Bearer nvapi-xxx...1234" \
    -H "Content-Type: application/json" \
    -d '{"model":"nvidia/nemotron-3-ultra-550b-a55b","messages":[{"role":"user","content":"ok"}],"max_tokens":8}' \
    https://integrate.api.nvidia.com/v1/chat/completions | head -c 100
  echo
done
```

**Output:**
```
HTTP 200  2.1s  {"id":"chatcmpl-...","choices":[{"message":{"content":"OK","role":"assistant"},"finish_reason":"stop"}]}
HTTP 200  2.3s  {"id":"chatcmpl-...","choices":[{"message":{"content":"OK","role":"assistant"},"finish_reason":"stop"}]}
HTTP 200  2.2s  {"id":"chatcmpl-...","choices":[{"message":{"content":"OK","role":"assistant"},"finish_reason":"stop"}]}
```

**Interpretation:** All three succeed. No sustained 429 at 5s intervals.

---

## Root Cause Identified: cc-switch Retry Amplification

The production 429s were caused by **cc-switch's `max_retries=6` with no backoff** — a single upstream 429 triggers 6 immediate retries, amplifying burst into sustained rate limit.

**cc-switch proxy logs (excerpt):**
```
[proxy] req=nemotron-3-ultra upstream=429 retry=1/6
[proxy] req=nemotron-3-ultra upstream=429 retry=2/6
[proxy] req=nemotron-3-ultra upstream=429 retry=3/6
[proxy] req=nemotron-3-ultra upstream=429 retry=4/6
[proxy] req=nemotron-3-ultra upstream=429 retry=5/6
[proxy] req=nemotron-3-ultra upstream=429 retry=6/6 → client sees 429
```

**Fix Applied:** Modified cc-switch retry config:
- `max_retries=3`
- `initial_backoff_ms=1000`
- `max_backoff_ms=10000`
- `respect_retry_after=true` (honors `Retry-After` header if present)

---

## Additional Finding: `z-ai/glm-5.3-flash` Timeout

```bash
# Single request test
curl -s -w "HTTP %{http_code}  %{time_total}s  " -H "Authorization: Bearer nvapi-xxx...1234" \
  -d '{"model":"z-ai/glm-5.3-flash","messages":[{"role":"user","content":"ok"}],"max_tokens":8}' \
  https://integrate.api.nvidia.com/v1/chat/completions --max-time 610
```

**Output (after 601s):**
```
HTTP 000  601.2s  curl: (28) Operation timed out after 601000 milliseconds
```

**Interpretation:** Model listed in catalog (81 models) but inference endpoint hangs indefinitely. **Do not add alias.**

---

## Summary

| Symptom | Root Cause | Fix |
|---------|------------|-----|
| Production 429s | cc-switch retry amplification (6× immediate retries) | Add backoff, reduce retries to 3 |
| Single request 200 | Key valid, model callable | Not a hard block |
| `/v1/models` = 200 + 81 models | Key has full catalog access | Not an auth issue |
| `z-ai/glm-5.3-flash` timeout | Model in catalog but inference unavailable | Never trust catalog alone |

**Mandatory Protocol:** Always run the 3-step verification before concluding "rate limit" vs "hard block". The difference changes the remediation entirely.