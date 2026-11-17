---
name: configure-nvidia-fallback
description: Configure NVIDIA key rotation with 3-provider fallback chain
version: 0.1.0
author: Teknium (teknium1), Hermes Agent
license: MIT
platforms: [linux, windows]
metadata:
  hermes:
    tags: [nvidia, fallback, api-keys, rotation, credential-pool, openrouter, modelscope]
    related_skills: [configure-feishu-gateway, manage-systemd-services-wsl, verify-hermes-setup]
---

# Configure NVIDIA Fallback & Key Rotation

Configure a resilient three-layer model provider chain for Hermes: **daily NVIDIA key rotation** (handles 503 "overloaded" errors that native Credential Pool ignores) + **Hermes fallback_providers** for cross-provider failover (NVIDIA → OpenRouter Nemotron 3 Ultra → ModelScope DeepSeek/Qwen). Runs as systemd timer at 18:43 CST with `Persistent=true`.

## When to Use

- NVIDIA API returns 503 "Service temporarily overloaded" under load
- Need zero-downtime transparent failover across providers
- Same model (`nvidia/nemotron-3-ultra-550b-a55b`) via different providers for capability continuity
- Native Credential Pool only rotates on 429/402, NOT 503 — requires external script
- Want daily scheduled rotation + per-turn automatic fallback

## Prerequisites

- Two NVIDIA API keys (key1, key2) — both added via `hermes auth add nvidia`
- OpenRouter API key (free tier works with `max_tokens: 8000` limit)
- ModelScope API key (`HERMES_CUSTOM_API_INFERENCE_MODELSCOPE_CN_API_KEY` in `.env`)
- systemd user services enabled (`loginctl enable-linger $USER`)
- `sudo` passwordless for `mount` (for deploy script if used) — or run rotation script directly
- WSL2 with systemd enabled

## How to Run

```bash
# 1. Add both NVIDIA keys to Hermes auth
hermes auth add nvidia --api-key nvapi-KEY1 --label nvidia-key1
hermes auth add nvidia --api-key nvapi-KEY2 --label nvidia-key2

# 2. Configure Credential Pool strategy (round_robin)
hermes config set credential_pool_strategies '{"nvidia": "round_robin"}'

# 3. Configure fallback_providers chain (NVIDIA → OpenRouter → ModelScope)
hermes config set fallback_providers '[
  {"provider": "openrouter", "model": "nvidia/nemotron-3-ultra-550b-a55b", "extra_body": {"max_tokens": 8000}},
  {"provider": "custom", "model": "deepseek-ai/DeepSeek-V4-Pro-0813", "base_url": "https://api-inference.modelscope.cn/v1", "key_env": "HERMES_CUSTOM_API_INFERENCE_MODELSCOPE_CN_API_KEY"}
]'

# 4. Add OpenRouter key
hermes auth add openrouter --api-key sk-or-... --label fallback-openrouter

# 5. Reset OpenRouter if previously marked unhealthy (402)
hermes auth reset openrouter

# 6. Create rotation script + pool file
mkdir -p ~/.hermes/credentials
cat > ~/.hermes/credentials/nvidia_pool.json << 'EOF'
{"keys": ["nvapi-KEY1", "nvapi-KEY2"], "current_index": 0}
EOF

cat > ~/.hermes/credentials/nvidia_key_rotator.py << 'PYEOF'
#!/usr/bin/env python3
import json, os, sys, subprocess, pathlib

POOL_FILE = pathlib.Path.home() / ".hermes" / "credentials" / "nvidia_pool.json"
ENV_FILE = pathlib.Path.home() / ".hermes" / ".env"
DROPIN_DIR = pathlib.Path.home() / ".config" / "systemd" / "user" / "hermes-gateway.service.d"
DROPIN_FILE = DROPIN_DIR / "nvidia-api.conf"

def load_pool():
    return json.loads(POOL_FILE.read_text())

def save_pool(pool):
    POOL_FILE.write_text(json.dumps(pool, indent=2))

def get_current_key():
    pool = load_pool()
    return pool["keys"][pool["current_index"]]

def rotate():
    pool = load_pool()
    pool["current_index"] = (pool["current_index"] + 1) % len(pool["keys"])
    save_pool(pool)
    update_env_and_dropin(pool["keys"][pool["current_index"]])
    return pool["keys"][pool["current_index"]]

def update_env_and_dropin(key):
    # Update .env
    lines = ENV_FILE.read_text().splitlines() if ENV_FILE.exists() else []
    lines = [l for l in lines if not l.startswith("NVIDIA_API_KEY=")]
    lines.append(f"NVIDIA_API_KEY={key}")
    ENV_FILE.write_text("\n".join(lines) + "\n")
    # Update systemd drop-in
    DROPIN_DIR.mkdir(parents=True, exist_ok=True)
    DROPIN_FILE.write_text(f"[Service]\nEnvironment=NVIDIA_API_KEY={key}\n")
    subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)

def auto_rotate_on_error(response_text: str):
    """Call from wrapper when NVIDIA returns 429 or 'overloaded' in response."""
    if "rate limit" in response_text.lower() or "429" in response_text or "overloaded" in response_text.lower():
        new_key = rotate()
        print(f"Rotated to key index {load_pool()['current_index']}: {new_key[:12]}...", file=sys.stderr)
        return new_key
    return None

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("cmd", choices=["get", "rotate", "auto"])
    parser.add_argument("--response", help="Response text for auto mode")
    args = parser.parse_args()
    if args.cmd == "get":
        print(get_current_key())
    elif args.cmd == "rotate":
        print(rotate())
    elif args.cmd == "auto":
        if args.response:
            auto_rotate_on_error(args.response)
PYEOF

chmod +x ~/.hermes/credentials/nvidia_key_rotator.py

# 7. Create systemd timer (daily 18:43 CST, Persistent=true)
mkdir -p ~/.config/systemd/user
cat > ~/.config/systemd/user/nvidia-key-rotate.service << 'EOF'
[Unit]
Description=Rotate NVIDIA API Key
After=network.target

[Service]
Type=oneshot
ExecStart=/home/user01/.hermes/credentials/nvidia_key_rotator.py rotate
WorkingDirectory=/home/user01/.hermes/credentials
EOF

cat > ~/.config/systemd/user/nvidia-key-rotate.timer << 'EOF'
[Unit]
Description=Daily NVIDIA Key Rotation at 18:43 CST

[Timer]
OnCalendar=*-*-* 18:43:00
Persistent=true
RandomizedDelaySec=0

[Install]
WantedBy=timers.target
EOF

systemctl --user daemon-reload
systemctl --user enable --now nvidia-key-rotate.timer

# 8. Verify
systemctl --user list-timers nvidia-key-rotate.timer
~/.hermes/credentials/nvidia_key_rotator.py get
```

## Quick Reference

| Task | Command |
|------|---------|
| Add NVIDIA key | `hermes auth add nvidia --api-key nvapi-... --label nvidia-keyN` |
| List auth | `hermes auth list` |
| Set pool strategy | `hermes config set credential_pool_strategies '{"nvidia": "round_robin"}'` |
| Set fallback chain | `hermes config set fallback_providers '[...]'` |
| Reset unhealthy provider | `hermes auth reset openrouter` |
| Get current key | `~/.hermes/credentials/nvidia_key_rotator.py get` |
| Manual rotate | `~/.hermes/credentials/nvidia_key_rotator.py rotate` |
| Check timer | `systemctl --user list-timers nvidia-key-rotate.timer` |
| View timer logs | `journalctl --user -u nvidia-key-rotate -n 20` |

## Procedure

### 1. Add Both NVIDIA Keys to Hermes Auth

```bash
hermes auth add nvidia --api-key nvapi-KEY1 --label nvidia-key1
hermes auth add nvidia --api-key nvapi-KEY2 --label nvidia-key2
```

**Completion criterion:** `hermes auth list` shows two NVIDIA entries with distinct labels.

### 2. Configure Credential Pool Strategy

```bash
hermes config set credential_pool_strategies '{"nvidia": "round_robin"}'
```

**Completion criterion:** `hermes config get credential_pool_strategies` returns the JSON.

**Note:** Native pool ONLY rotates on HTTP 429/402. It does NOT detect 503 "overloaded" — that's why the external script is required.

### 3. Configure Fallback Providers Chain

```bash
hermes config set fallback_providers '[
  {"provider": "openrouter", "model": "nvidia/nemotron-3-ultra-550b-a55b", "extra_body": {"max_tokens": 8000}},
  {"provider": "custom", "model": "deepseek-ai/DeepSeek-V4-Pro-0813", "base_url": "https://api-inference.modelscope.cn/v1", "key_env": "HERMES_CUSTOM_API_INFERENCE_MODELSCOPE_CN_API_KEY"}
]'
```

**Completion criterion:** `hermes fallback list` shows both entries in order.

### 4. Add OpenRouter Key & Reset If Unhealthy

```bash
hermes auth add openrouter --api-key sk-or-... --label fallback-openrouter
hermes auth reset openrouter  # Critical if prior 402 marked it unhealthy
```

**Completion criterion:** `OPENROUTER_API_KEY=... hermes chat -q "test"` returns "OK".

### 5. Create Rotation Script & Key Pool

See `How to Run` section for the `nvidia_pool.json` and `nvidia_key_rotator.py` files.

**Key behaviors:**
- `get` — prints current active key
- `rotate` — advances index atomically, updates `.env` + systemd drop-in, reloads systemd
- `auto` — call from wrapper with response text; rotates if 429 or "overloaded" detected

**Completion criterion:** Script runs without error, `.env` and drop-in updated, `systemctl --user daemon-reload` succeeds.

### 6. Deploy Systemd Timer

See `How to Run` for service + timer unit files.

**Critical settings:**
- `OnCalendar=*-*-* 18:43:00` — daily at 18:43 CST (matches Windows/WSL time)
- `Persistent=true` — catches up on boot if machine was off at 18:43
- `RandomizedDelaySec=0` — exact time, no jitter

**Completion criterion:** `systemctl --user is-enabled nvidia-key-rotate.timer` → `enabled`, next trigger shows correct CST time.

### 7. Test Full Chain

```bash
# Test current key works
NVIDIA_API_KEY=$(~/.hermes/credentials/nvidia_key_rotator.py get) hermes chat -q "test"

# Test rotation
~/.hermes/credentials/nvidia_key_rotator.py rotate
NVIDIA_API_KEY=$(~/.hermes/credentials/nvidia_key_rotator.py get) hermes chat -q "test"

# Test fallback (simulate NVIDIA failure by using bad key)
NVIDIA_API_KEY=invalid hermes chat -q "test"  # Should fall through to OpenRouter

# Test ModelScope fallback (if both above fail)
# Requires valid ModelScope key in .env
```

**Completion criterion:** Each layer responds; fallback triggers on failure; next user message resets to NVIDIA primary.

## Pitfalls

- **Credential Pool ignores 503** — Source code only checks 429/402. External script required for "overloaded" detection.
- **OpenRouter free tier 402** — `max_tokens: 8000` in fallback config prevents credit exhaustion; without it, Auxiliary marks provider unhealthy for 60s.
- **Auxiliary unhealthy marking** — Any 402 on OpenRouter marks it unhealthy, blocking main-model fallback. Fix: `hermes auth reset openrouter`.
- **Per-turn reset** — Fallback chain resets every user message: each turn starts at NVIDIA primary. No "wheel" cycling within a turn.
- **Duplicate credentials** — `hermes auth list` may show env-discovered duplicate. Remove with `hermes auth remove nvidia <index>`.
- **Systemd drop-in path** — Must match gateway service name (`hermes-gateway.service.d/nvidia-api.conf`).
- **Timer timezone** — Uses WSL/systemd time (synced to Windows CST). `Persistent=true` handles shutdown across scheduled time.

## Verification

```bash
# 1. Timer active & next trigger correct
systemctl --user list-timers nvidia-key-rotate.timer --no-pager
# Should show: NEXT = tomorrow 18:43 CST, LEFT = ~24h

# 2. Pool file valid
cat ~/.hermes/credentials/nvidia_pool.json
# Should have 2 keys, current_index 0 or 1

# 3. .env + drop-in in sync
grep NVIDIA_API_KEY ~/.hermes/.env
cat ~/.config/systemd/user/hermes-gateway.service.d/nvidia-api.conf
# Both should show SAME key

# 4. Fallback chain configured
hermes fallback list
# Should show: 1) openrouter nemotron, 2) custom modelscope deepseek

# 5. End-to-end: NVIDIA works
NVIDIA_API_KEY=$(~/.hermes/credentials/nvidia_key_rotator.py get) hermes chat -q "ping"
# → "pong" or similar

# 6. Fallback triggers on bad NVIDIA key
NVIDIA_API_KEY=bad hermes chat -q "ping"
# → Should respond via OpenRouter (same model)

# 7. Manual rotation test
~/.hermes/credentials/nvidia_key_rotator.py rotate
# → Key index changes, .env + drop-in updated
```

---

*Skill distilled from session 20260924_151137_4b2afe9e (531 messages: NVIDIA 503 diagnosis, Credential Pool limitation discovery, external rotation script, fallback_providers chain, OpenRouter 402 fix, ModelScope Layer 4, systemd timer with Persistent=true). Pattern threshold ≥3 met across: 503 handling, credential pool gap, fallback chain config, timer deployment, auth reset procedure.*