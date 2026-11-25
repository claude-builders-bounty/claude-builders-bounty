---
name: qbook-ranking-scraper
description: "Scrape 番茄 rankings and AI-deconstruct novels via Qbook API."
version: 0.1.0
author: User (Hermes Agent)
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - qbook
    - fanqie
    - ranking
    - novel-pipeline
    - scraping
    related_skills:
    - novel-generation-pipeline
    - humanifyme-integration
---

# Qbook Ranking Scraper & AI Deconstruction

Scrape 番茄小说 (Fanqie) rankings via Qbook API and AI-deconstruct top novels for structure/hooks/pacing analysis. Novel pipeline step 2 (扫榜单/拆书).

## When to Use

- Need to scan 番茄榜单 for trending novels (category/gender/type)
- Need AI deconstruction of top novels (structure, hooks, pacing, characters)
- Qbook service not running or returning empty responses
- Need to integrate with Nemotron 3 Ultra for AI deconstruction

**Don't use for:**
- Non-番茄 platforms (起点, 晋江, etc.)
- Direct novel content scraping (Qbook only provides metadata/rankings)

## Prerequisites

- Qbook service running at `http://localhost:8765` (Python Flask app)
- ModelScope API key (`ms-...`) in `~/.hermes/.env` as `HERMES_CUSTOM_API_INFERENCE_MODELSCOPE_CN_API_KEY`
- NVIDIA Nemotron 3 Ultra API key for AI deconstruction
- Python venv with `jieba`, `pillow`, `numpy`, `fonttools` (in `~/qbook/venv`)

## How to Run

```bash
# 1. Start Qbook service (if not running)
cd ~/qbook && source venv/bin/activate && python app.py &

# 2. Test rankings API
curl -s "http://localhost:8765/api/rankings/fanqie?type=read&gender=male&category=东方仙侠" | jq '.books[:3]'

# 3. AI deconstruct top novel (via Nemotron)
python3 -c "
import json, os
from openai import OpenAI
client = OpenAI(base_url='https://integrate.api.nvidia.com/v1', api_key=os.getenv('NVIDIA_API_KEY'))
prompt = '你是网文拆书专家。分析《书名》结构，输出JSON：structure, hooks, pacing, characters, core_conflict, golden_opening, climax_design, ending_type'
resp = client.chat.completions.create(model='nvidia/nemotron-3-ultra-550b-a55b', messages=[{'role':'user','content':prompt}], temperature=0.3, max_tokens=8000)
print(resp.choices[0].message.content)
"
```

## Quick Reference

| Task | Command |
|------|---------|
| Start Qbook | `cd ~/qbook && source venv/bin/activate && python server.py &` |
| Get rankings | `curl -s "http://localhost:8765/api/rankings/fanqie?type=read&gender=male&category=东方仙侠" \| jq '.books'` |
| Check service | `curl -s http://localhost:8765/health` |
| AI deconstruct | Use Nemotron 3 Ultra with structured prompt (see Procedure) |
| Install deps | `cd ~/qbook && pip install --index-url https://pypi.tuna.tsinghua.edu.cn/simple jieba pillow numpy fonttools` |

## Procedure

### 1. Ensure Qbook Service Running

**Completion criterion**: `curl http://localhost:8765/health` returns OK.

```bash
# Check if running
curl -s http://localhost:8765/health

# If not running, start it (entry is server.py, not app.py)
cd ~/qbook
source venv/bin/activate
nohup python server.py > qbook.log 2>&1 &
sleep 3
curl -s http://localhost:8765/health
# Should return: {"status": "ok"}
```

### 2. Fetch Rankings for Category

**Completion criterion**: JSON response with `books` array (title, author, url, read_count, category).

```bash
# Male 东方仙侠 (typical target)
curl -s "http://localhost:8765/api/rankings/fanqie?type=read&gender=male&category=东方仙侠" \
  | jq '.books[:10] | map({title, author, url, read_display, category})' > /tmp/bangdan.json

# Female 古代言情
curl -s "http://localhost:8765/api/rankings/fanqie?type=read&gender=female&category=古代言情" \
  | jq '.books[:10]' > /tmp/bangdan_female.json
```

### 3. AI Deconstruct Top Novel (Nemotron 3 Ultra)

**Completion criterion**: Structured JSON with structure, hooks, pacing, characters, core_conflict, golden_opening, climax_design, ending_type.

```python
#!/usr/bin/env python3
# deconstruct.py — AI deconstruction using Nemotron 3 Ultra
import json, os, re
from openai import OpenAI

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY")  # nvapi-... from ~/.hermes/.env
)

def deconstruct_novel(novel_url: str, title: str) -> dict:
    prompt = f"""你是网文拆书专家。请分析这本小说的结构：
URL: {novel_url}
书名: {title}

请输出 JSON（不要其他内容）：
{{
  "structure": "三幕式/多线并行/...",
  "hooks": ["开篇悬念", "中段反转", "高潮爆发", "..."],
  "pacing": "前快中慢后快/...",
  "characters": [{{"name": "", "role": "", "arc": ""}}],
  "core_conflict": "",
  "golden_opening": "",
  "climax_design": "",
  "ending_type": ""
}}"""
    
    resp = client.chat.completions.create(
        model="nvidia/nemotron-3-ultra-550b-a55b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=8000,
        top_p=0.95,
    )
    
    content = resp.choices[0].message.content
    # Extract JSON from response
    match = re.search(r'\{[\s\S]*\}', content)
    if match:
        return json.loads(match.group())
    return {}

# Usage
if __name__ == "__main__":
    import sys
    url = sys.argv[1] if len(sys.argv) > 1 else "https://fanqienovel.com/novel/12345"
    result = deconstruct_novel(url, "目标小说")
    print(json.dumps(result, ensure_ascii=False, indent=2))
```

### 4. Save Deconstruction Results

**Completion criterion**: `deconstruction_<book_id>.json` saved for pipeline use.

```bash
python3 deconstruct.py "https://fanqienovel.com/novel/xxx" > /home/user01/novel-pipeline/deconstruction.json
# Verify
cat /home/user01/novel-pipeline/deconstruction.json | jq .
```

## Pitfalls

| Issue | Solution |
|-------|----------|
| **Qbook 服务没跑** | 启动命令是 `python server.py`（非 `app.py`）；检查端口 8765 |
| **返回空响应** | 番茄反爬或 API 变更；检查 `qbook/logs/server.log`，可能需更新 cookies/headers |
| **`category=` 返回 total=0 脏缓存** | **关键坑**：`?category=东方仙侠` 命中一个 total=0 的 24h 缓存（首次启动缓存未预热时被写入空结果）。修复：改用 `?type=read&gender=male`（返回全部 ~570 本），再本地过滤 `sub_category == "东方仙侠"`，绕开 category 参数 |
| **首次启动返回空** | 服务重启后缓存需 60-120s 预热，`fanqie_meta` 要先从 fanqienovel.com 拉取分类列表；不要在预热前手动 curl（会把 total=0 写进磁盘缓存）；流水线重试要 ≥10 次 × 20s |
| **分类参数错误** | 类型: `read`/`new`/`finish`；性别: `male`/`female`；分类需匹配番茄官方分类名 |
| **ModelScope 401** | 更新 `HERMES_CUSTOM_API_INFERENCE_MODELSCOPE_CN_API_KEY`（见 `refresh-modelscope-mcp-token`） |
| **Nemotron 超时** | `max_tokens=8000` 较大；若超时改 `max_tokens=4000` 或分批请求 |
| **中文编码** | 确保 `ensure_ascii=False` 和终端 UTF-8 |

## Verification

```bash
# 1. Qbook service healthy
curl -s http://localhost:8765/health | grep -q '"status":"ok"' && echo "✅ Qbook running"

# 2. Rankings fetch works
curl -s "http://localhost:8765/api/rankings/fanqie?type=read&gender=male&category=东方仙侠" | jq -e '.books | length > 0' && echo "✅ Rankings fetched"

# 3. Deconstruction produces valid JSON
python3 -c "
import json, os, re
from openai import OpenAI
client = OpenAI(base_url='https://integrate.api.nvidia.com/v1', api_key=os.getenv('NVIDIA_API_KEY'))
r = client.chat.completions.create(model='nvidia/nemotron-3-ultra-550b-a55b', messages=[{'role':'user','content':'测试：输出{\"test\":1}'}], max_tokens=100)
print('✅ Nemotron works' if 'test' in r.choices[0].message.content else '❌ Failed')
"
```

---

*Distilled from session 20261004_100635_3c5af9a0 (Oct 4, 2026) — Qbook service may not be running or returning empty responses during novel pipeline step 2 (扫榜单/拆书). Pattern: Qbook runs on localhost:8765, provides 番茄 rankings API; AI deconstruction uses Nemotron 3 Ultra with structured JSON prompt. Occurs ≥3 times in novel pipeline runs.*