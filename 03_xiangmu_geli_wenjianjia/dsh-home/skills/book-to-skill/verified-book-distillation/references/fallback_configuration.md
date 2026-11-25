# Hermes Model Fallback Configuration Reference

## Fallback Chain Config (config.yaml)

The fallback chain is read from `fallback_providers` (preferred) and `fallback_model` (legacy) keys.

```yaml
model:
  default: nvidia/nemotron-3-ultra-550b-a55b
  provider: nvidia
  providers:
    modelscope:
      base_url: "https://api-inference.modelscope.cn/v1"
      api_key_env: "HERMES_CUSTOM_API_INFERENCE_MODELSCOPE_CN_API_KEY"
  aliases:
    vision: local_vision/qwen2.5-vl:7b
    kimi: moonshotai/kimi-k3
    lightning: nvidia/nemotron-3.5-lightning-30b-a3b
    deepseek-v4-flash: modelscope/deepseek-ai/DeepSeek-V4.1-Flash

fallback_providers:
  - provider: nvidia
    model: nvidia/nemotron-3-ultra-550b-a55b
  - provider: modelscope
    model: deepseek-ai/DeepSeek-V4.1-Flash
  - provider: openrouter
    model: google/gemini-3.6-flash

auxiliary:
  vision:
    provider: ollama
    model: qwen2.5-vl:7b
  compression:
    provider: nvidia
```

## How It Works

1. **Config Loading** (`hermes_cli/fallback_config.py::get_fallback_chain()`):
   - Reads `fallback_providers` list first (primary source of truth)
   - Then reads `fallback_model` (legacy single dict or list)
   - Merges, deduplicating by `(provider, model, base_url)`

2. **Agent Initialization** (`agent/agent_init.py`):
   - `fallback_model` parameter passed to `init_agent()`
   - Builds `agent._fallback_chain` list of dicts with `provider` + `model`
   - Sets `agent._fallback_index = 0`, `agent._fallback_activated = False`

3. **Runtime Fallback** (`agent/error_classifier.py`, `agent/conversation_loop.py`):
   - On retryable errors (rate limit, overload, timeout), increments `_fallback_index`
   - Re-initializes with next provider/model in chain
   - Preserves conversation context

## Key Files

| File | Role |
|------|------|
| `hermes_cli/fallback_config.py` | Config parsing, merging, deduplication |
| `agent/agent_init.py:1540-1563` | Fallback chain construction in agent init |
| `gateway/run.py:9832-9894` | Gateway-level fallback loading for cron/agent runs |
| `agent/error_classifier.py` | Error classification → fallback trigger |

## CLI Commands

```bash
# View current fallback chain
hermes config get fallback_providers

# Set fallback chain (JSON array)
hermes config set fallback_providers '[{"provider": "nvidia", "model": "nvidia/nemotron-3-ultra-550b-a55b"}, {"provider": "modelscope", "model": "deepseek-ai/DeepSeek-V4.1-Flash"}]'

# Add ModelScope provider
hermes config set model.providers.modelscope.base_url "https://api-inference.modelscope.cn/v1"
hermes config set model.providers.modelscope.api_key_env "HERMES_CUSTOM_API_INFERENCE_MODELSCOPE_CN_API_KEY"

# Add alias
hermes config set model.aliases.deepseek-v4-flash "modelscope/deepseek-ai/DeepSeek-V4.1-Flash"
```

## Common Pitfalls

| Issue | Cause | Fix |
|-------|-------|-----|
| Fallback not triggering | `fallback_providers` key misspelled or wrong YAML format | Use `hermes config set fallback_providers ' [...] '` with valid JSON |
| ModelScope 401 | Wrong `api_key_env` or key not in `.env` | Check `.env` has `HERMES_CUSTOM_API_INFERENCE_MODELSCOPE_CN_API_KEY=ms-xxx` |
| DeepSeek reasoning only | Model outputs `reasoning_content` but `content` is null | Use non-streaming or handle both fields; InkOS needs `content` |
| Alias not resolving | Alias format wrong | Must be `provider/model-id` e.g. `modelscope/deepseek-ai/DeepSeek-V4.1-Flash` |

## DeepSeek-V4.1-Flash Specific Notes

- **Streaming**: Returns `reasoning_content` + `content` (may be null initially)
- **Non-streaming**: Returns full response with both fields
- **InkOS compatibility**: Currently only reads `content` field → use non-streaming mode (`INKOS_LLM_STREAM=false`) or patch provider to fall back `reasoning_content` → `content`
- **Timeout**: Non-streaming requests can hit 60s timeout on ModelScope