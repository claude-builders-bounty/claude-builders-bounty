---
name: configure-modelscope-vision
description: Add ModelScope Qwen/Qwen3-VL-8B-Instruct as vision provider with explicit delegate_task alias.
version: 0.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [modelscope, vision, multimodal, provider, delegate]
    related_skills: [configure-ollama-wsl, verify-hermes-setup]
---

# configure-modelscope-vision Skill

Configure ModelScope-hosted `Qwen/Qwen3-VL-8B-Instruct` as an **auxiliary vision provider** while keeping Nemotron 3 Ultra as primary. Uses explicit `delegate_task(role="vision")` for image/multimodal tasks — no automatic fallback.

## When to Use

- Primary model (Nemotron 3 Ultra) lacks multimodal support
- Need vision/image analysis without switching main model
- Want free-tier ModelScope inference (8B params, Chinese-friendly)
- Prefer explicit delegation over passive fallback chain

## Prerequisites

- ModelScope account + API key (Inference API enabled)
- Hermes config: `~/.hermes/config.yaml`
- Environment variable: `HERMES_CUSTOM_API_INFERENCE_MODELSCOPE_CN_API_KEY` in `~/.hermes/.env`
- Network access to `https://api-inference.modelscope.cn/v1`

## How to Run

```bash
# 1. Set API key in .env (once)
echo 'HERMES_CUSTOM_API_INFERENCE_MODELSCOPE_CN_API_KEY=ms-xxxxxxxx' >> ~/.hermes/.env

# 2. Configure provider + alias via Hermes CLI
hermes config set model.providers.modelscope_vision.type openai_compatible
hermes config set model.providers.modelscope_vision.base_url https://api-inference.modelscope.cn/v1
hermes config set model.providers.modelscope_vision.api_key \${HERMES_CUSTOM_API_INFERENCE_MODELSCOPE_CN_API_KEY}
hermes config set model.aliases.vision modelscope_vision:Qwen/Qwen3-VL-8B-Instruct

# 3. Verify
hermes config get model.providers.modelscope_vision
hermes config get model.aliases.vision
```

## Quick Reference

| Action | Command |
|--------|---------|
| Add key to .env | `echo 'HERMES_CUSTOM_API_INFERENCE_MODELSCOPE_CN_API_KEY=ms-...' >> ~/.hermes/.env` |
| Set provider type | `hermes config set model.providers.modelscope_vision.type openai_compatible` |
| Set base_url | `hermes config set model.providers.modelscope_vision.base_url https://api-inference.modelscope.cn/v1` |
| Set api_key ref | `hermes config set model.providers.modelscope_vision.api_key \${HERMES_CUSTOM_API_INFERENCE_MODELSCOPE_CN_API_KEY}` |
| Set alias | `hermes config set model.aliases.vision modelscope_vision:Qwen/Qwen3-VL-8B-Instruct` |
| Verify all | `hermes config get model.providers.modelscope_vision && hermes config get model.aliases.vision` |
| Test delegation | `delegate_task goal="describe this image" role=vision context="image_url:..."` |

## Procedure

1. **Get ModelScope API Key** — Visit `https://modelscope.cn/my/myaccesstoken`, create token with "Inference API" permission.
2. **Persist key in .env** — Append to `~/.hermes/.env`:
   ```bash
   HERMES_CUSTOM_API_INFERENCE_MODELSCOPE_CN_API_KEY=ms-3c26e9a3-0741-4819-8574-c6446bdb64fb
   ```
   (Use your actual key; this example is redacted.)
3. **Register provider** — Run the three `hermes config set` commands for `type`, `base_url`, `api_key`.
4. **Create alias** — `hermes config set model.aliases.vision modelscope_vision:Qwen/Qwen3-VL-8B-Instruct`.
5. **Verify persistence** — `hermes config get model.providers.modelscope_vision` shows all three fields; `model.aliases.vision` shows the full model string.
6. **Test in conversation** — When user sends an image, invoke:
   ```python
   delegate_task(
       goal="Describe the image in detail",
       role="vision",
       context="image_url: https://example.com/image.jpg"
   )
   ```

## Pitfalls

- **Key must be in `.env`, not hardcoded in config.yaml** — config.yaml uses `${VAR}` interpolation.
- **Alias format is `provider:model`** — `modelscope_vision:Qwen/Qwen3-VL-8B-Instruct` (colon, not slash).
- **No automatic fallback** — Primary model never silently switches; you must explicitly `delegate_task(role="vision")`.
- **Free tier has rate limits** — `Qwen3-VL-8B-Instruct` is free but throttled; handle 429s gracefully.
- **Domestic China network** — `api-inference.modelscope.cn` resolves fast in CN; overseas may need proxy.

## Verification

```bash
# Config check
hermes config get model.providers.modelscope_vision
# Expected: type=openai_compatible, base_url=https://api-inference.modelscope.cn/v1, api_key=${HERMES_CUSTOM_API_INFERENCE_MODELSCOPE_CN_API_KEY}

hermes config get model.aliases.vision
# Expected: modelscope_vision:Qwen/Qwen3-VL-8B-Instruct

# Live test (requires network)
curl -s -H "Authorization: Bearer $HERMES_CUSTOM_API_INFERENCE_MODELSCOPE_CN_API_KEY" \
  https://api-inference.modelscope.cn/v1/models | jq '.data[] | select(.id=="Qwen/Qwen3-VL-8B-Instruct")'
```

Success = config persists, alias resolves, API returns model metadata.