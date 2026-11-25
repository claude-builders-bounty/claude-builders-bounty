---
name: novel-style-fingerprint-extraction
description: Extract novel style fingerprints for AI writing calibration.
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
    - novel-writing
    - style-analysis
    - fingerprint-extraction
    - de-ai
    - calibration
    related_skills:
    - novel-workspace-workflow
    - novel-distillation-pipeline
    - director-driven-novel-workflow
    requires_toolsets:
    - terminal
    - file
    - skills
---

# Novel Style Fingerprint Extraction

Extract 36-dimension structural style fingerprints from reference novels (5+ books, 100K-1M words each) to calibrate AI writing output. Zero AI contamination — only human-authored reference texts used.

## When to Use

- Starting a new novel project requiring specific authorial voice
- Calibrating `style_rules.yaml`, `style_profile.json`, `review_checklist.md` for writing pipeline
- Building de-AI rules from real human prose patterns
- Validating AI output against human baseline

**Don't use for:** Character/plot extraction, worldbuilding, specific IP elements — only *structural* style patterns transfer.

## Prerequisites

- Reference novels as `.txt` files (UTF-8 or GBK, auto-detected)
- `scripts/guard.py` environment (WSL2, `~/ai/python`, Windows drives RO)
- Python 3.11+ with `chardet`, `jieba` (optional, for Chinese segmentation)
- Theory references: McKee *Story*, *Dialogue*; Narrative Techniques; King *On Writing*

## How to Run

```bash
# 1. Place reference novels in a directory
# 2. Run extraction pipeline (3 phases)
cd /home/user01/novel-workspace
python3 scripts/extract_fingerprint.py --input-dir /path/to/novels --output config/

# Or manual step-by-step:
# Phase 1: Encoding normalization & chapter detection
# Phase 2: 36-dimension pattern extraction
# Phase 3: Generate config artifacts (style_rules.yaml, style_profile.json, review_checklist_v4.md)
```

## Quick Reference

| Task | Command |
|------|---------|
| Normalize encoding | `python3 -c "import chardet; ..." < file.txt > file_utf8.txt` |
| Detect chapters | `grep -nE '^第[一二三四五六七八九十百千万\d]+章' file.txt` |
| Sample segments | `sed -n '1000,2000p' file.txt` (opening/middle/climax) |
| Extract 36 dimensions | See Procedure below |
| Write configs | `write_file` to `config/style_rules.yaml` etc. |

## Procedure

### 1. Prepare Reference Corpus (5+ novels, diverse but genre-aligned)

**Target profile for military apocalypse:**
- 《末世首长，开局一个精锐步兵班！》— 现代军事末世、系统金手指、硬核装备
- 《炮火弧线》— 穿越军事、RTS视角、即时战略微操
- 《牧神记》— 玄幻但文风极强、口语化叙事、碎句节奏
- 《这游戏也太真实了》— 废土游戏化、第一人称、网络亚文化语感
- 《惊涛落日》— 穿越海战、军事迷视角、硬核参数

**Encoding fix (GBK → UTF-8):**
```bash
for f in *.txt; do
  encoding=$(chardet "$f" | awk '{print $2}')
  if [[ "$encoding" != "utf-8" && "$encoding" != "ascii" ]]; then
    iconv -f "$encoding" -t utf-8 "$f" > "${f%.txt}_utf8.txt"
  fi
done
```

### 2. Extract 36 Dimensions (Manual Reading + Pattern Mining)

Read 3 segments per novel (opening 200 lines, middle 500 lines, climax 500 lines). For each dimension, record: **rule**, **positive example**, **negative example**, **source novel+location**.

| # | Dimension | What to Capture |
|---|-----------|-----------------|
| 1 | 句式与断句习惯 | 平均句长、碎句密度、长短句震荡模式 |
| 2 | 叙事视角与注意力模式 | 限制视角严度、注意力跳转逻辑、上帝视角渗透度 |
| 3 | 标点符号使用 | 破折号/省略号/冒号/分号频率、内部停顿标记 |
| 4 | 心理活动写法 | 独白vs碎念比例、分析式vs生理载体、四类触发器 |
| 5 | 动作描写表达逻辑 | 本能动词链vs教程拆解、专业术语配额、打击感三要素 |
| 6 | 用词、比喻与词汇偏好 | 网络口语/军事黑话/生理动词/程度副词白名单 |
| 7 | 对话写法 | 短句化、潜台词比例、称谓系统、零客套 |
| 8 | 叙事节奏与过渡 | 小/中/大高潮间距、张力曲线、硬切转场标记 |
| 9 | 信息披露方式 | 主角有限认知vs旁白、零科普、零背景铺垫 |
| 10 | 情绪表达载体 | 生理侧写清单、零情绪标签词、幽默/吐槽触发器 |
| 11 | 意象、重复母题 | 核心意象簇、母题复现三拍法则 |
| 12 | 留白习惯 | 显性省略标记、次要动作一笔带过、跳跃密度 |
| 13 | 叙事冗余度 | 环境/动作/心理/设定/对话五类冗余上限 |
| 14 | 因果陈述习惯 | 隐性因果vs显性连接词、战术/系统因果特权 |
| 15 | 对"疼痛、感官"描写倾向 | 选择性放大/屏蔽清单、战斗时感官分层 |
| 16 | 视角漂移容忍度 | 零漂移硬规则、工具词承接大场面 |
| 17 | 幽默感/内心吐槽风格 | 四类触发器、插入方式（破折号/碎句/动作尾部） |
| 18 | 伏笔预埋方式 | 三次法则、标注字段、母题复现对应表 |
| 19 | 名词/代词选用习惯 | 称谓系统、指代链、零古风/修仙词汇 |
| 20 | 修饰词位置与密度 | 的/地/得≤35/千字、前置形容词极少、强动词替代 |
| 21 | "预判与后知"叙事倾向 | 伏笔埋设→强化→爆发/回收链路 |
| 22 | 对"无关感官信号"取舍 | 战斗时屏蔽清单、放大清单 |
| 23 | 数字、量化描写写法 | 军事/系统/生产参数必须带单位、模糊词仅非关键 |
| 24 | 重复与节奏复现 | 韵律指纹：碎句/拟声词/动词链周期性复现 |
| 25 | 时间感知描写 | 仅硬性锚点（倒计时/时限/窗口/天黑天亮） |
| 26 | 省略逻辑缺口 | 显性省略标记、动作跳跃无连接词 |
| 27 | 人称视角细微语感 | 三人称限制硬规则、零叙事疑问句 |
| 28 | 对巧合、突发转折处理 | 六类归因源头、三章内可追溯 |
| 29 | 取舍"次要动作" | 一笔带过标记、例行公事/按流程/照例 |
| 30 | 疑问句用法 | 叙事零疑问、对话仅自然短问、内心极短反问 |
| 31 | 程度副词密度 | ≤5/万字、仅很/挺/蛮/老/特/超/极/顶/死 |
| 32 | 被动句/主动句偏好 | 被动≤2%且仅受害语境、主动动词链零连接词 |
| 33 | 身体感知选择性屏蔽 | 战斗时放大/屏蔽双清单 |
| 34 | 题外话联想 | 每场景≤1处≤3句、六类触发源、硬切回主线 |
| 35 | 对声音的描写方式 | 拟声词重、材质绑定、分层、方向标记、沉默即声音 |
| 36 | 信息权重分配 | 动作/冲突>面板/系统>对话/人物>环境/氛围>内心/杂念>设定 |

### 3. Generate Config Artifacts

**Output 1: `config/style_rules.yaml`** — 机器可执行规则集（禁用词表、白名单、硬指标、句式/视角/场景/节奏/伏笔/声纹/硬禁止/现代术语/动作/情绪/省略/量化/修饰/因果/叙事/冗余/巧合/身体感知/联想/声音/信息权重/签名模式/审核清单）

**Output 2: `scripts/style_profile_v4.json`** — 写作执行器 prompt 模板（36维度结构化参数，压缩版喂模型）

**Output 3: `scripts/review_checklist_v4.md`** — 审核端硬核清单（10大类36条硬指标+4遍审核流程+12项一票否决）

**Output 4: `scripts/style_fingerprint_v4.md`** — 人类可读完整说明书（36维度×规则/正例/反例/实测依据/来源小说）

### 4. Validate Against Reference Corpus

```bash
# Spot-check: run review checklist on 3 random segments from reference novels
# All 36 hard indicators should PASS on human text
# If any FAIL → rule is over-fitted, relax it
```

## Pitfalls

- **Don't mix genres** — military apocalypse ≠ xianxia ≠ romance. Style fingerprints are genre-bound.
- **Don't extract character/plot/IP** — only *structural* patterns (sentence rhythm, verb chains, sensory filters, etc.) transfer.
- **GBK encoding** — Chinese web novels often GBK. Must normalize to UTF-8 before processing.
- **Sample size** — Minimum 3 segments × 5 novels × 200+ lines each. Single chapter = biased.
- **AI contamination check** — Scan reference texts for AI markers (sudden transitions, hedging, analysis-speak). Discard contaminated chapters.
- **Over-fitting** — If human reference text fails the review checklist, the rules are too strict. Relax until human text passes.

## Verification

```bash
# 1. All 4 config files exist
ls -la config/style_rules.yaml scripts/style_profile_v4.json scripts/review_checklist_v4.md scripts/style_fingerprint_v4.md

# 2. YAML/JSON syntax valid
python3 -c "import yaml; yaml.safe_load(open('config/style_rules.yaml'))"
python3 -c "import json; json.load(open('scripts/style_profile_v4.json'))"

# 3. Review checklist passes on human reference segments
# Pick 3 random 500-line segments from reference novels, run checklist manually
# All 36 indicators = PASS

# 4. Forbidden AI patterns NOT in reference texts
grep -f config/forbidden_ai_patterns.txt reference_novel_segment.txt
# Should return empty (or only in obviously translated/edited sections)

# 5. Signature patterns ≥5 per chapter in reference novels
# Verify on 3 chapters from each novel
```

---

*Skill distilled from 3 sessions (20261010_212502, 20261011_021028, 20261012_085137) analyzing 5 novels (942K total lines) for military apocalypse style calibration. Pattern: manual segment reading → 36-dimension pattern table → 4 config artifacts → validation on human text.*