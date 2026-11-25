---
name: nvidia-nemotron-streaming-error-handling
description: "Catch Nemotron streaming errors, retry with fallback chain."
version: 0.1.0
author: Teknium (teknium1), Hermes Agent
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - nvidia
    - nemotron
    - streaming
    - error-handling
    - fallback
    related_skills:
    - configure-nvidia-fallback
    - inkos-modelscope-quota-fallback
    - novel-workspace-workflow
---

# NVIDIA Nemotron Streaming Error Handling

Catch NVIDIA Nemotron 3 Ultra streaming failures (ReadError, StreamError, TimeoutException) and convert them to ProviderStreamError for automatic retry/fallback. Prevents mid-generation crashes during novel planning, writing, and review stages.

## When to Use

- NVIDIA Nemotron streaming response fails with `httpx.ReadError`, `httpx.StreamError`, `httpcore.ReadError`, `httpcore.NetworkError`
- Streaming chunk iteration breaks mid-generation
- Need automatic fallback to ModelScope (ds4pro) or local model on streaming failure
- Fixing `chat_completion_helpers.py` and `relay_llm.py` streaming error handling

**Don't use for:** ModelScope quota errors (use `inkos-modelscope-quota-fallback`), non-streaming API errors.

## Prerequisites

- Hermes Agent source access (typically in repo or installed package)
- `chat_completion_helpers.py` with `_iter_provider_stream_chunks` function
- `relay_llm.py` with `_complete_logical` function
- Fallback chain configured: Nemotron → ModelScope DeepSeek-V4-Pro → Local qwen2.5-vl:7b
- Python environment with `httpx`, `httpcore` available

## How to Run

```bash
# Locate Hermes source files
find / -name "chat_completion_helpers.py" -type f 2>/dev/null | head -5
find / -name "relay_llm.py" -type f 2>/dev/null | head -5

# Check current streaming error handling
grep -n "ReadError\|StreamError\|_iter_provider_stream_chunks" /path/to/chat_completion_helpers.py

# Test Nemotron streaming
python3 -c "
import httpx
client = httpx.Client(timeout=30)
resp = client.post('https://integrate.api.nvidia.com/v1/chat/completions', 
    headers={'Authorization': 'Bearer \$NVIDIA_API_KEY'},
    json={'model': 'nvidia/nemotron-3-ultra-550b-a55b', 'messages': [{'role': 'user', 'content': 'test'}], 'stream': True})
for chunk in resp.iter_text(): print(chunk[:100])
"
```

## Quick Reference

| Task | Command |
|------|---------|
| Find Hermes source | `find / -name "chat_completion_helpers.py" 2>/dev/null` |
| Check streaming errors | `grep -n "ReadError\|StreamError\|TimeoutException" chat_completion_helpers.py` |
| Patch streaming handler | Edit `_iter_provider_stream_chunks` in chat_completion_helpers.py |
| Verify fallback chain | Check `configure-nvidia-fallback` skill |
| Test streaming | `python3 -c "import httpx; ..."` with stream=true |

## Procedure

### 1. Locate and Inspect Streaming Code

```bash
# Find the actual file locations
CHAT_HELPERS=$(find /home/user01 -name "chat_completion_helpers.py" 2>/dev/null | head -1)
RELAY_LLM=$(find /home/user01 -name "relay_llm.py" 2>/dev/null | head -1)

echo "chat_completion_helpers.py: $CHAT_HELPERS"
echo "relay_llm.py: $RELAY_LLM"

# Inspect streaming chunk iterator
grep -n -A 30 "_iter_provider_stream_chunks" "$CHAT_HELPERS"

# Inspect logical completion handler
grep -n -A 30 "_complete_logical" "$RELAY_LLM"
```

**Completion criterion:** Both files located, streaming functions identified.

### 2. Verify Current Error Handling Gaps

```bash
# Check for missing error types in _is_conn_err
grep -B 5 -A 20 "_is_conn_err" "$CHAT_HELPERS"

# Should include: httpx.ReadError, httpx.StreamError, httpcore.ReadError, httpcore.NetworkError
# Common gap: only catches httpx.ConnectError, httpx.TimeoutException
```

**Completion criterion:** Missing error types identified in connection error checker.

### 3. Patch chat_completion_helpers.py - Extended Connection Errors

```bash
# Backup first
cp "$CHAT_HELPERS" "${CHAT_HELPERS}.bak"

# Add imports at top of file (if not present)
grep -q "import httpcore" "$CHAT_HELPERS" || sed -i '1i import httpcore as _httpcore' "$CHAT_HELPERS"
grep -q "import httpx" "$CHAT_HELPERS" || sed -i '1i import httpx as _httpx' "$CHAT_HELPERS"

# Patch _is_conn_err function to include streaming errors
# Find the function and extend the error tuple
sed -i '/def _is_conn_err/,/return/ {
    /_httpx\.ConnectError/ a\        _httpx.ReadError, _httpx.StreamError, _httpcore.ReadError, _httpcore.NetworkError,
}' "$CHAT_HELPERS"
```

**Completion criterion:** `_is_conn_err` catches all streaming error types.

### 4. Patch _iter_provider_stream_chunks - Preserve Diagnostics

```bash
# Check current implementation
grep -n -A 50 "def _iter_provider_stream_chunks" "$CHAT_HELPERS"

# Key requirements for patch:
# 1. Preserve _diag, last_chunk_time, _touch_activity variables
# 2. Catch streaming errors inside the chunk loop
# 3. Convert to ProviderStreamError with raw_text for fallback
# 4. Maintain activity tracking for timeout detection

# Example patch structure (apply manually after review):
cat > /tmp/streaming_patch.py << 'PATCH_EOF'
# In _iter_provider_stream_chunks:
# - Add try/except around chunk iteration
# - Catch: _httpx.ReadError, _httpx.StreamError, _httpcore.ReadError, _httpcore.NetworkError, TimeoutError
# - On catch: log error, yield ProviderStreamError(raw_text=accumulated_text, original_error=e)
# - Preserve: _diag dict, last_chunk_time updates, _touch_activity() calls
PATCH_EOF
cat /tmp/streaming_patch.py
```

**Completion criterion:** Chunk iterator handles streaming errors without losing diagnostics.

### 5. Patch relay_llm.py - Fallback on ProviderStreamError

```bash
# Inspect _complete_logical for fallback handling
grep -n -A 30 "_complete_logical" "$RELAY_LLM"

# Ensure it catches ProviderStreamError and triggers fallback
# Should call _try_fallback with the accumulated raw_text
```

**Completion criterion:** `_complete_logical` falls back on streaming errors with context preserved.

### 6. Validate Syntax and Test

```bash
# Syntax check
python3 -m py_compile "$CHAT_HELPERS"
python3 -m py_compile "$RELAY_LLM"

# Import test
python3 -c "import chat_completion_helpers; import relay_llm; print('Imports OK')"

# Restart Hermes gateway to pick up changes
systemctl --user restart hermes-gateway
sleep 3
systemctl --user status hermes-gateway --no-pager | head -10
```

**Completion criterion:** Syntax valid, imports clean, gateway restarts successfully.

### 7. Verify with Live Streaming Test

```bash
# Test streaming with a long prompt to trigger potential timeouts
python3 -c "
import httpx, json, os
client = httpx.Client(timeout=60)
resp = client.post('https://integrate.api.nvidia.com/v1/chat/completions',
    headers={'Authorization': f'Bearer {os.environ[\"NVIDIA_API_KEY\"]}'},
    json={'model': 'nvidia/nemotron-3-ultra-550b-a55b', 
          'messages': [{'role': 'user', 'content': 'Write a 500 word story about a space battle'}], 
          'stream': True})
chunks = 0
for chunk in resp.iter_text():
    chunks += 1
    if chunks % 50 == 0:
        print(f'Received {chunks} chunks...')
print(f'Total chunks: {chunks} - Streaming OK')
"
```

**Completion criterion:** Streaming completes without ReadError/StreamError crashes.

### 8. Add Monitoring to Proactive Patrol

```bash
# Add check for streaming errors in logs
grep -c "ProviderStreamError\|ReadError\|StreamError" ~/.local/share/hermes/logs/*.log 2>/dev/null | awk -F: '$2 > 0 {print $1 ": " $2 " streaming errors"}'
```

**Completion criterion:** Patrol detects streaming error patterns.

## Pitfalls

| Issue | Solution |
|-------|----------|
| SyntaxError: duplicate keyword arg | Check `ProviderStreamError(status_code=502, status_code=502)` - remove duplicate |
| Missing `raw_text` in ProviderStreamError | Ensure constructor accepts `raw_text` param for fallback context |
| Using `httpx.ReadError` instead of `_httpx.ReadError` | Use local alias `_httpx` defined at module top |
| Losing `_diag`/`last_chunk_time` in rewrite | Preserve all diagnostic variables from original implementation |
| Fallback not triggered on streaming error | Verify `_complete_logical` catches `ProviderStreamError` and calls `_try_fallback` |
| Activity timeout fires during legitimate slow streaming | Increase `TimeoutSec` in systemd service (see `configure-systemd-timeouts`) |

## Verification

```bash
# 1. Syntax valid
python3 -m py_compile /path/to/chat_completion_helpers.py && echo "✅ chat_completion_helpers OK"
python3 -m py_compile /path/to/relay_llm.py && echo "✅ relay_llm OK"

# 2. All streaming error types caught
grep -c "_httpx.ReadError\|_httpx.StreamError\|_httpcore.ReadError\|_httpcore.NetworkError" /path/to/chat_completion_helpers.py
# Should show ≥4 in _is_conn_err

# 3. ProviderStreamError has raw_text
grep -A 10 "class ProviderStreamError" /path/to/chat_completion_helpers.py | grep "raw_text"

# 4. Gateway streams without crash (5 min test)
timeout 300 python3 -c "
import httpx, os, json
client = httpx.Client(timeout=120)
resp = client.post('https://integrate.api.nvidia.com/v1/chat/completions',
    headers={'Authorization': f'Bearer {os.environ[\"NVIDIA_API_KEY\"]}'},
    json={'model': 'nvidia/nemotron-3-ultra-550b-a55b',
          'messages': [{'role': 'user', 'content': 'x'*2000}],  # Long prompt
          'stream': True})
for _ in resp.iter_text(): pass
print('✅ Long streaming completed')
"

# 5. No streaming errors in recent logs
! grep -q "ReadError\|StreamError" ~/.local/share/hermes/logs/hermes-gateway.log 2>/dev/null && echo "✅ No streaming errors in logs"
```

---

*Skill distilled from 3+ occurrences (Oct 7-8, 2026): NVIDIA Nemotron 3 Ultra streaming failures (ReadError, StreamError, TimeoutException) crashing novel pipeline steps 1 (planning) and 3 (writing). Fixed via minimal patches to chat_completion_helpers.py (_is_conn_err, _iter_provider_stream_chunks) and relay_llm.py (_complete_logical fallback). Pattern in sessions 20261007_124819_584d1789, 20261008_122846_61ba03, 20261009_135143_f6546c.*