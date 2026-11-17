---
name: inkos-modelscope-quota-fallback
description: "Handle ModelScope 429 quota with fallback chain for InkOS."
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
    - inkos
    - modelscope
    - quota
    - fallback
    - novel-pipeline
    related_skills:
    - novel-generation-pipeline
    - configure-nvidia-fallback
    - novel-workspace-workflow
---

# InkOS ModelScope Quota Fallback Handling

Handle ModelScope API 429 (quota exceeded) errors by automatically switching to fallback models in the InkOS novel generation pipeline. Ensures uninterrupted novel generation when primary ModelScope model (qwen397b/Qwen3.5-397B-A17B) hits rate limits.

## When to Use

- Novel pipeline step 3 (InkOS generation) fails with 429/rate limit errors
- ModelScope qwen397b model returns quota exceeded responses
- Need automatic fallback to Nemotron 3 Ultra or DeepSeek-V4-Pro for writing
- Configuring fallback chain in `novel-workspace/config/system.yaml`

**Don't use for:** General NVIDIA API fallback (use `configure-nvidia-fallback`), non-novel ModelScope usage.

## Prerequisites

- Novel workspace at `/home/user01/novel-workspace/`
- `config/system.yaml` with models section:
  ```yaml
  models:
    primary: "nvidia/nemotron-3-ultra-550b-a55b"
    writer: "qwen397b"              # ModelScope Qwen3.5-397B-A17B
    vision: "local_vision/qwen2.5-vl:7b"
    fallback: "ds4pro"               # DeepSeek-V4-Pro-0813
  ```
- ModelScope API key in `~/.hermes/.env` (MODESCOPE_API_KEY)
- `novel-generation-pipeline` skill for context

## How to Run

```bash
# Check current model config
cat /home/user01/novel-workspace/config/system.yaml | grep -A 10 "models:"

# Test ModelScope connectivity
curl -H "Authorization: Bearer $MODESCOPE_API_KEY" https://api-inference.modelscope.cn/v1/models/qwen/Qwen3.5-397B-A17B

# Verify fallback chain in skill_loader.py
grep -A 20 "fallback" /home/user01/novel-workspace/skill_loader.py
```

## Quick Reference

| Task | Command |
|------|---------|
| View model config | `cat ~/novel-workspace/config/system.yaml` |
| Test ModelScope API | `curl -H "Authorization: Bearer $MODESCOPE_API_KEY" https://api-inference.modelscope.cn/v1/models/qwen/Qwen3.5-397B-A17B` |
| Check fallback logic | `grep -n "fallback" ~/novel-workspace/skill_loader.py` |
| Manual fallback test | `MODEL=ds4pro python3 -c "from hermes_tools import execute_code; ..."` |

## Procedure

### 1. Verify Current Fallback Configuration

```bash
# Read system.yaml models section
cat /home/user01/novel-workspace/config/system.yaml

# Expected structure:
# models:
#   primary: "nvidia/nemotron-3-ultra-550b-a55b"
#   writer: "qwen397b"
#   vision: "local_vision/qwen2.5-vl:7b"
#   fallback: "ds4pro"
```

**Completion criterion:** Config shows 4-model chain with writer=qwen397b and fallback=ds4pro.

### 2. Detect 429 Errors in Pipeline Logs

```bash
# Check recent novel pipeline runs for 429 errors
grep -r "429\|quota\|rate.limit" /home/user01/novel-workspace/workspace/00_*/reviews/ 2>/dev/null | head -20

# Check skill_loader.py for fallback handling
grep -B 5 -A 15 "429\|quota" /home/user01/novel-workspace/skill_loader.py
```

**Completion criterion:** 429 errors identified; fallback trigger logic located.

### 3. Implement Automatic Fallback in skill_loader.py

**Location:** `/home/user01/novel-workspace/skill_loader.py`

**Required fallback logic (Writing stage):**
```python
# Pseudocode - actual implementation in skill_loader.py
def get_writer_model():
    primary_writer = config['models']['writer']      # qwen397b
    fallback_writer = config['models']['fallback']   # ds4pro
    primary_model = config['models']['primary']      # nemotron
    
    try:
        response = call_model(primary_writer, prompt)
        if response.status == 429:
            log.warning(f"ModelScope quota exceeded for {primary_writer}, trying fallback")
            response = call_model(fallback_writer, prompt)
            if response.status == 429:
                log.warning(f"Fallback {fallback_writer} also quota exceeded, trying primary")
                response = call_model(primary_model, prompt)
        return response
    except Exception as e:
        # Final fallback to primary
        return call_model(primary_model, prompt)
```

**Completion criterion:** skill_loader.py handles 429 on writer → fallback → primary chain.

### 4. Configure ModelScope Retry Policy

```bash
# Add to system.yaml under models:
# models:
#   writer: "qwen397b"
#   writer_retry:
#     max_attempts: 2
#     backoff_seconds: 5
#     fallback_on: [429, 503, 504]
#   fallback: "ds4pro"
#   fallback_retry:
#     max_attempts: 1
#     backoff_seconds: 3
#     final_fallback: "nvidia/nemotron-3-ultra-550b-a55b"
```

**Completion criterion:** Retry/fallback policy defined in config.

### 5. Test Fallback Chain

```bash
# Simulate 429 by temporarily invalidating ModelScope key
export MODESCOPE_API_KEY="invalid"
python3 -c "
from skill_loader import get_writer_model
result = get_writer_model('test prompt')
print(f'Used model: {result.model}')
assert result.model in ['ds4pro', 'nvidia/nemotron-3-ultra-550b-a55b']
"
export MODESCOPE_API_KEY="<real_key>"
```

**Completion criterion:** Fallback triggers correctly, novel generation continues.

### 6. Monitor and Alert

```bash
# Add to proactive_patrol.py checks
# Check for repeated 429s in last hour
grep -c "429" /home/user01/novel-workspace/workspace/00_*/reviews/*.log 2>/dev/null | awk -F: '$2 > 5 {print $1 " has " $2 " quota errors"}'
```

**Completion criterion:** Patrol alerts on repeated quota failures.

## Pitfalls

| Issue | Solution |
|-------|----------|
| Fallback model also hits 429 | Chain: qwen397b → ds4pro → nemotron (3-tier) |
| Fallback changes output style | Accept style variance; de-AI pass normalizes |
| ModelScope key not in .env | Add `MODESCOPE_API_KEY=xxx` to `~/.hermes/.env` |
| skill_loader.py not importing config | Ensure `yaml.safe_load(open('config/system.yaml'))` at module top |
| ds4pro not available on ModelScope | Verify `modelscope/deepseek-ai/DeepSeek-V4.1-Flash` or `DeepSeek-V4-Pro-0813` alias |

## Verification

```bash
# 1. Config has complete fallback chain
grep -A 15 "models:" /home/user01/novel-workspace/config/system.yaml | grep -E "writer|fallback|primary" | wc -l
# Should show 4 lines

# 2. skill_loader.py has fallback logic
grep -c "429\|quota\|fallback" /home/user01/novel-workspace/skill_loader.py
# Should show ≥3 matches

# 3. Manual test: force 429, verify fallback
MODESCOPE_API_KEY="test" python3 -c "
import sys
sys.path.insert(0, '/home/user01/novel-workspace')
from skill_loader import get_model_for_stage
m = get_model_for_stage('writing')
print(f'Writing model resolved to: {m}')
assert m in ['ds4pro', 'nvidia/nemotron-3-ultra-550b-a55b']
"
# Should print fallback model

# 4. Pipeline runs without 429 blocking
cd /home/user01/novel-workspace && python3 -m novel_pipeline --step 3 --dry-run 2>&1 | grep -v "429"
# Should complete without quota errors
```

---

*Skill distilled from 5+ occurrences (Oct 7-10, 2026): ModelScope qwen397b 429 quota errors during novel pipeline step 3 (InkOS generation), requiring fallback to ds4pro (DeepSeek-V4-Pro) then nemotron. Pattern in sessions 20261007_124819_584d1789, 20261008_193635_4a0c2424, 20261009_135143_f6546c, 20261010_212502_289db841, and multiple pipeline runs.*