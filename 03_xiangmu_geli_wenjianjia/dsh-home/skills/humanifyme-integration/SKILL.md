---
name: humanifyme-integration
description: "Integrate HumanifyMe MCP for writing style learning."
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
    - humanifyme
    - mcp
    - style-learning
    - novel-pipeline
    - writing
    related_skills:
    - novel-generation-pipeline
    - configure-mcp-servers
---

# HumanifyMe MCP Integration

Integrate HumanifyMe MCP server for writing style fingerprint extraction and AI-to-human text rewriting. Used in novel pipeline step 1 (文风学习) and step 4 (降AI率).

## When to Use

- Need to learn user's writing style from samples (novel pipeline step 1)
- Need to rewrite AI-generated text to sound human (novel pipeline step 4)
- HumanifyMe MCP server not configured or failing
- CLI parameter errors when calling HumanifyMe commands

**Don't use for:**
- Initial HumanifyMe setup without samples (need 5-10 chapters first)
- Non-writing style tasks

## Prerequisites

- Node.js + npm (for `npx humanifyme`)
- Writing samples in `/home/user01/writing_samples/` (5-10 chapters, your actual writing)
- ModelScope API key for Qbook (`ms-...` format) in `~/.hermes/.env` as `HERMES_CUSTOM_API_INFERENCE_MODELSCOPE_CN_API_KEY`
- MCP server `humanifyme` configured in Hermes

## How to Run

```bash
# 1. Configure HumanifyMe MCP server (one-time)
hermes config set mcp_servers.humanifyme '{"command": "npx", "args": ["-y", "humanifyme", "mcp"], "env": {}}'

# 2. Train style profile with samples
npx -y humanifyme setup --samples /home/user01/writing_samples

# 3. Test style learning
npx -y humanifyme rewrite --input "/home/user01/writing_samples/sample.txt" --output /tmp/style_test.json

# 4. Verify MCP server works
hermes chat -q "List available HumanifyMe MCP tools"
```

## Quick Reference

| Task | Command |
|------|---------|
| Configure MCP server | `hermes config set mcp_servers.humanifyme '{"command": "npx", "args": ["-y", "humanifyme", "mcp"]}'` |
| Train style profile | `npx -y humanifyme setup --samples /home/user01/writing_samples` |
| Rewrite text (CLI) | `npx -y humanifyme rewrite --input <file> --output <out.json>` |
| Check MCP tools | `hermes chat -q "List HumanifyMe MCP tools"` |
| View style profile | `cat ~/.humanifyme/profile.json` |

## Procedure

### 1. Configure HumanifyMe MCP Server

**Completion criterion**: `humanifyme` appears in `hermes config get mcp_servers` and tools are listed.

```bash
# Add to Hermes config
hermes config set mcp_servers.humanifyme '{"command": "npx", "args": ["-y", "humanifyme", "mcp"], "env": {}}'

# Verify
hermes config get mcp_servers.humanifyme
# Should show the config object
```

### 2. Train Style Profile with Samples

**Completion criterion**: `~/.humanifyme/profile.json` created with style fingerprint.

```bash
# Ensure samples exist
ls -la /home/user01/writing_samples/
# Should show .txt files (e.g., 《炮火弧线》.txt, 《惊涛落日》.txt)

# Run training (one-time, takes 1-2 minutes)
npx -y humanifyme setup --samples /home/user01/writing_samples

# Verify profile created
cat ~/.humanifyme/profile.json | head -50
# Should show: {"fingerprint": {...}, "samples": [...], "version": "..."}
```

### 3. Test Style Learning (Rewrite)

**Completion criterion**: Output JSON contains rewritten text with style fingerprint applied.

```bash
# Test with a sample AI-generated text
echo "这是一段AI生成的测试文本，用来验证HumanifyMe是否能按你的文风重写。" > /tmp/test_ai.txt

# Rewrite using trained profile
npx -y humanifyme rewrite --input /tmp/test_ai.txt --output /tmp/rewritten.json

# Check output
cat /tmp/rewritten.json
# Should contain: {"original": "...", "rewritten": "...", "style_fingerprint": {...}}
```

### 4. Verify MCP Server Tools Available

**Completion criterion**: `humanifyme_humanify_text` and related tools listed.

```bash
hermes chat -q "List available HumanifyMe MCP tools"
# Should show: humanifyme_humanify_text, humanifyme_build_profile, humanifyme_get_profile, etc.
```

### 5. Use in Novel Pipeline (Automated)

**Completion criterion**: Pipeline step 1 produces valid `style_fingerprint.json`.

```python
# In pipeline script (run_pipeline.py learn_style function):
import subprocess
import json

def learn_style_humanifyme(samples_dir: str, output_file: str) -> bool:
    """Use HumanifyMe MCP via CLI for style learning."""
    cmd = f"npx -y humanifyme rewrite --input {samples_dir} --output {output_file}"
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
    return result.returncode == 0 and Path(output_file).exists()
```

## Pitfalls

| Issue | Solution |
|-------|----------|
| **CLI 参数错误** (`rewrite` 不支持 `--input` 目录) | HumanifyMe CLI 可能需单文件输入；遍历目录下所有 .txt 合并为一个大样本文件，或用 MCP `humanifyme_import_text_files` 工具 |
| **MCP 服务器未启动** | `hermes config get mcp_servers.humanifyme` 确认配置，重启 gateway: `systemctl --user restart hermes-gateway` |
| **ModelScope 401** | 更新 `HERMES_CUSTOM_API_INFERENCE_MODELSCOPE_CN_API_KEY`（见 `refresh-modelscope-mcp-token`） |
| **样本不足** | 至少 5 章亲笔正文（每章 2000+ 字），放在 `/home/user01/writing_samples/` |
| **npm 全局路径** | `npx` 在 cron/后台需用绝对路径或确保 PATH 含 `~/.npm-global/bin` |

## Verification

```bash
# 1. MCP server configured
hermes config get mcp_servers.humanifyme | grep -q npx && echo "✅ MCP configured"

# 2. Style profile exists
test -f ~/.humanifyme/profile.json && echo "✅ Profile trained"

# 3. Rewrite works
npx -y humanifyme rewrite --input /home/user01/writing_samples/炮火弧线.txt --output /tmp/test.json 2>&1 | grep -q "rewritten" && echo "✅ Rewrite works"

# 4. MCP tools listed
hermes chat -q "List HumanifyMe tools" 2>&1 | grep -q humanifyme_humanify_text && echo "✅ MCP tools available"
```

---

*Distilled from session 20261004_100635_3c5af9a0 (Oct 4, 2026) — HumanifyMe CLI parameter errors during novel pipeline run. Pattern: HumanifyMe CLI `rewrite --input` expects file not directory; MCP server needs config in Hermes; style training requires 5-10 chapters of actual writing samples. Occurs in novel pipeline step 1 (文风学习).*