# NVIDIA Integrate API — Test Transcript (2026-10-10)

**Endpoint**: `https://integrate.api.nvidia.com/v1`
**Key tested**: `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` and `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`

## Catalog (`/v1/models`) — SUCCESS

Returns 100+ models including:
- `nvidia/nemotron-3-ultra-550b-a55b` ✅
- `moonshotai/kimi-k3` ✅
- `meta/llama-3.2-90b-vision-instruct` ✅
- `moonshotai/kimi-k2.6` ✅
- Many others

## Inference (`/v1/chat/completions`) — MIXED

### ✅ WORKING: `nvidia/nemotron-3-ultra-550b-a55b`

```bash
curl -H "Authorization: Bearer $KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"nvidia/nemotron-3-ultra-550b-a55b","messages":[{"role":"user","content":"hi"}],"max_tokens":10,"stream":false}' \
  https://integrate.api.nvidia.com/v1/chat/completions
```

**Response** (200 OK, ~500ms):
```json
{
  "id": "chatcmpl-e72141eb-6585-4f92-a5be-6ebfbce2042b",
  "choices": [{
    "index": 0,
    "message": {
      "content": "The user said \"hi\". This is a standard",
      "role": "assistant",
      "reasoning_content": "The user said \"hi\". This is a standard"
    },
    "finish_reason": "length"
  }],
  "model": "nvidia/nemotron-3-ultra-550b-a55b",
  "usage": {"prompt_tokens": 17, "completion_tokens": 10, "total_tokens": 27}
}
```

### ❌ FAILING: `moonshotai/kimi-k3`

**All variants tested — ALL timeout (120s+):**

| Variant | Stream | reasoning_effort | Result |
|---------|--------|------------------|--------|
| Non-stream | false | (none) | Timeout |
| Stream | true | (none) | Timeout |
| Non-stream | false | `max` | Timeout |
| Stream | true | `max` | Timeout |
| With image payload | true | `max` | Timeout |
| **Second API key** | all | all | Timeout |

**Symptom**: TCP connection establishes, TLS handshake completes, request sent — then **zero bytes returned** until client timeout. No HTTP status, no error body, no partial stream.

### ❌ FAILING: `meta/llama-3.2-90b-vision-instruct`

Same timeout pattern as Kimi-K3.

## Hypothesis

NVIDIA's integrate endpoint acts as a **model marketplace catalog** (aggregator). The `/v1/models` list reflects *all models published to the platform*, but `/v1/chat/completions` only routes to models **your API key is entitled to invoke**.

`nvidia/nemotron-3-ultra-550b-a55b` is a first-party NVIDIA model → included in base entitlement.

`moonshotai/kimi-k3`, `meta/llama-3.2-90b-vision-instruct` are third-party models → require separate provisioning/entitlement/enterprise agreement not granted to standard keys.

## Workaround

Use the model's **native provider**:

| Model | Native Provider | Base URL | Auth Env Var |
|-------|-----------------|----------|--------------|
| Kimi-K3 | `moonshotai` | `https://api.moonshot.cn/v1` | `KIMI_API_KEY` |
| Kimi-K3 | `openrouter` | `https://openrouter.ai/api/v1` | `OPENROUTER_API_KEY` |

Then alias in Hermes:
```bash
hermes config set model.aliases.kimi moonshotai/kimi-k3
# or
hermes config set model.aliases.kimi openrouter/moonshotai/kimi-k3
```