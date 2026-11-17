---
name: novel-distillation-pipeline
description: "拆书蒸馏网文为 novel_distill 技能：章节检测、分块、确定性与 API 降级分析。"
version: 0.1.0
author: User, Hermes Agent
license: MIT
platforms:
- linux
- macos
- windows
metadata:
  hermes:
    tags:
    - novel
    - distillation
    - webnovel
    - chapter-detection
    - nemotron
    - fallback
    related_skills:
    - novel-generation-pipeline
    - qbook-ranking-scraper
    - humanifyme-integration
    - book-to-skill
    - verified-book-distillation
---

# 网文拆书蒸馏管线（novel_distill 技能生成）

把一本全文网文（txt）蒸馏成 `novel_distill_<name>` 技能，产出**黄金三章 + 节奏模板 + 爽点地图 + 柔性笔记**四类结构化档案，供 novel_pipeline 的文风学习与生成指导注入。它不是 `book-to-skill`（通用书→框架），也不是 `novel-generation-pipeline`（用 InkOS 生成），而是**拆解已有爆款 → 提取可复用的商业结构**这一步。

## When to Use
- 用户要求「拆书」「蒸馏」「提取黄金三章/爽点/节奏模板」某本网文
- 为一本爆款生成 `novel_distill_<name>` 技能供 novel_pipeline 注入
- 批量处理多本同类小说（≥2 本时复用同一套脚本/流程）
- Don't use for: 生成新小说（用 `novel-generation-pipeline`）；把技术书/理论书转技能（用 `book-to-skill`）

## Prerequisites
- 原文 txt 在本地（如 `~/writing_samples/《书名》作者.txt`），**必须有真实全文**——严禁用模型记忆 + web 片段伪造蒸馏（见 `verified-book-distillation`）
- Python3 标准库（`re`, `pathlib`, `json`）即可，无需第三方包
- （可选）NVIDIA 网关 Nemotron 3 Ultra 做语义分析；无 key 时退化为确定性本地分析
- 写权限：`~/.hermes/skills/novel_distill_<name>/`

## How to Run
```bash
# 1. 章节边界检测（先探格式，再决定正则）
terminal(command="python3 /tmp/detect_chapters.py '<书路径>'")

# 2. 分块（~78k 字符/块，跨章不截断）
terminal(command="python3 /tmp/chunk_novel.py '<书路径>'")

# 3. 逐块分析（Nemotron API 或确定性本地降级）
terminal(command="python3 /tmp/distill_chunks.py --text-block-dir <dir>")

# 4. 生成 novel_distill_<name> 技能 + 注入扫描
skill_manage(action="create", name="novel_distill_<name>", category="<novel-distill>", content=...)
```

## Quick Reference
| 任务 | 命令/正则 |
|------|-----------|
| 数字标题 `第一章` / `第123章` | `^第[0-9一二三四五六七八九十百千万]+\s*[章回]` |
| 特殊格式 `=第一章 天黑别出门===` | `=第.*?=` |
| 首章锚定（全角/带 BOM） | `\ufeff=第一章` 也需匹配 |
| 分块大小 | ~78,000 字符/块（约 27–30 章） |
| NVIDIA 无 key 检查 | `python3 -c "import os;print(len(os.environ.get('NVIDIA_API_KEY','')))"` → 0 则找备份 |

## Procedure
1. **核实原文真实**：`read_file` 原文头部确认有正文（非 134 行手打摘要）。真实网文单本常 > 几十万字。
2. **章节边界检测**（完成标准：`Total chapters detected: N` 且 N 与书名预期量级一致）：跑 3 个正则逐一 report matches 数，选命中数最多且无重叠的那个。
3. **分块**（完成标准：`chunk_0..chunk_N` 每块 ~78k 字符、跨章不截断）：按章节索引切块，保留章标题做锚。
4. **逐块分析**（完成标准：每块产出 golden/ shuang_map/ flex_notes 三段 markdown）：
   - 优先 Nemotron API（`call_nemotron` 加重试 5 次指数退避 15/30/60/120/240s）
   - API 不可用（503/无 key）→ **确定性本地分析**：直接对块文本做模式提取（章节事件、爽点类型、角色原型、硬护栏关键词），不依赖 LLM
5. **汇总生成技能**（完成标准：`skill_manage` create 成功，chapters/ 下四文件存在）：`SKILL.md` + `chapters/golden_three.md` + `rhythm_template.md` + `shuang_dian_map.md` + `flex_notes.md`
6. **注入扫描**（完成标准：`Generated-skill scan passed`）：用 `book-to-skill/tools/scan_generated_skill.py` 扫新建目录。

## Pitfalls
- **NVIDIA API 503 过载** → 走降级链：Nemotron → 本地 Ollama `qwen2.5-vl:7b` → 确定性本地分析。别在 503 上死循环。
- **`NVIDIA_API_KEY` length=0** → 搜 `~/.hermes/.env.bak.*` 里的旧 key（`search_files pattern="NVIDIA_API_KEY"`），`export NVIDIA_API_KEY=...` 后重跑。
- **WSL 里 `ollama` 未装**（`Command 'ollama' not found`）→ 别再折腾安装，直接确定性本地分析；这本就是离线兜底路径。
- **章节格式各异**：牧神记用 `=第一章===`，其他多是 `第一章`；必须先 detect 再切块，否则 `Total chapters detected: 1`（整本当一章）。
- **输出目录空** = 块没落盘或 API 静默失败 → 先用 `search_files(target="files", pattern="*.txt")` 确认块文件实际存在，再判断是「没写」还是「没分析」。
- **不要伪造蒸馏**：`verified-book-distillation` 的铁律在此同样生效——无真实全文就直说，不糊弄。

## Verification
```bash
# 1. 四文件存在
search_files(pattern="*.md", target="files", path="~/.hermes/skills/novel_distill_<name>/chapters")
# 期望：golden_three.md, rhythm_template.md, shuang_dian_map.md, flex_notes.md

# 2. 章节数合理
terminal(command="wc -c ~/writing_samples/<书名>.txt")  # 原文应在几十万字符级

# 3. 注入扫描通过
terminal(command="python3 ~/.hermes/skills/book-to-skill/tools/scan_generated_skill.py ~/.hermes/skills/novel_distill_<name>")

# 4. 技能可加载（新会话生效）
skill_view(name="novel_distill_<name>")
```

---
*Skill distilled from 4 occurrences in last 7 days (炮火弧线 / 惊涛落日 / 牧神记 / 这游戏也太真实了).*