---
name: novel-to-sillytavern-pipeline
description: "Convert novels to SillyTavern character cards + worldbooks with MVU variable system."
version: 0.1.0
author: User (Hermes Agent)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [creative, writing, sillytavern, novel-processing, worldbuilding, mvu]
    related_skills: [hermes-agent-skill-authoring, memory-local, session-librarian]
---

# Novel to SillyTavern Pipeline

Transform long-form novels (1000+ chapters) into production-ready SillyTavern character cards and worldbooks with MVU variable systems, following the "师兄太稳健" technical architecture.

## When to Use

- Convert a novel to SillyTavern format (character card + worldbook)
- Need MVU variable system for stateful roleplay (identity, realm, artifacts, abilities, party, current_quest)
- Process large GBK/UTF-8 encoded Chinese novels (multi-MB files)
- Extract entities, plot arcs, and worldbuilding from long-form text
- Maintain zero-hallucination, source-traceable content

## Prerequisites

- Python 3.10+ with `chardet`, `tqdm`, `json` stdlib
- WSL2 with Windows file access (`/mnt/c/Users/...`)
- Novel text file (GBK or UTF-8 encoded)
- Reference SillyTavern card for technical architecture (e.g., "师兄太稳健 v1.3.1.png")

## How to Run

```bash
# 1. Prepare novel file (GBK -> UTF-8 conversion if needed)
iconv -f GBK -t UTF-8 "novel.txt" > "novel_utf8.txt"

# 2. Analyze novel structure
python3 scripts/analyze_novel.py novel_utf8.txt

# 3. Extract entities and build worldbook
python3 scripts/build_worldbook.py novel_utf8.txt reference_card.png output_worldbook.json

# 4. Generate character card
python3 scripts/generate_card.py novel_utf8.txt worldbook.json output_card.json

# 5. Validate outputs
python3 scripts/validate_outputs.py output_card.json output_worldbook.json
```

## Quick Reference

| Script | Purpose |
|--------|---------|
| `analyze_novel.py` | Chapter detection, entity frequency, plot arc segmentation |
| `build_worldbook.py` | Worldbook entries (constant + selective), MVU schema |
| `generate_card.py` | Character card JSON (spec v2, personality, first_mes, mes_example) |
| `validate_outputs.py` | JSON schema validation, cross-reference check |

## Procedure

### 1. Novel Analysis & Encoding Handling

**Completion criterion**: UTF-8 text file with verified chapter markers

```python
# Key steps:
# - Detect encoding (GBK/GB18030/UTF-8) with chardet
# - Convert to UTF-8 preserving Chinese characters
# - Extract chapter headers: "第X章.标题" pattern
# - Build chapter index: [(title, byte_offset, char_count), ...]
# - Identify major plot arcs (every 50-100 chapters)
# - Output: novel_analysis.json with structure metadata
```

### 2. Reference Card Technical Extraction

**Completion criterion**: Technical architecture documented (no content copied)

```python
# From reference PNG (SillyTavern card with embedded JSON):
# - Extract worldbook structure: entries[] with id, keys, content, constant, selective, selective_logic
# - Extract MVU variable schema from extensions.depth_prompt
# - Extract character card fields: spec, personality, first_mes, mes_example, creator_notes, extensions
# - Document: entry groups, priority scheme, trigger logic (AND/OR), cooldown/sticky settings
# - Output: reference_architecture.json
```

### 3. Entity Extraction & Worldbook Construction

**Completion criterion**: Worldbook JSON with 20+ entries covering all domains

```python
# Domains (matching 师兄太稳健 architecture):
# 1. 核心设定 - World overview, core rules, timeline (constant)
# 2. 核心人物 - Protagonist, key allies, family, antagonists (constant)
# 3. 核心装备/生物 - Weapons, pets, special items (constant)
# 4. 世界地理 - Locations, terrain terms, landmarks (constant)
# 5. 世界观/文化 - Customs, rules, daily life details (constant)
# 6. 猎物档案 - Creatures with biology, tactics, key battles (selective, AND logic)
# 7. 特殊猎物 - Boss entities with unique mechanics (selective, AND logic)
# 8. 关键剧情 - Major plot arcs with chapter ranges (selective, AND logic)
# 9. 技能体系 - Skills with progression (selective, OR logic)
# 10. 物资经济 - Resources, trade, value tiers (selective, OR logic)
# 11. 重要配角 - Supporting cast quick reference (selective, OR logic)
# 12. MVU变量系统 - State schema for dynamic roleplay (constant)
# 13. 扮演准则 - AI behavior rules (constant, highest priority)

# Each entry must have:
# - keys[]: trigger keywords (Chinese + variants)
# - content: source-traceable markdown with chapter citations
# - constant: true for always-on, false for selective
# - selective: true + selective_logic (AND/OR) for conditional
# - priority: 10 (highest) to 1 (lowest)
# - group: categorization for debugging
```

### 4. Character Card Generation

**Completion criterion**: Valid `chara_card_v2` spec JSON with all required fields

```python
# Required fields:
# - spec: "chara_card_v2", spec_version: "2.0"
# - data.name, description, personality, first_mes, mes_example[]
# - creator_notes: production principles, architecture notes, version history
# - tags[], creator, character_version
# - extensions: talkativeness, fav, world (worldbook name), depth_prompt (MVU + behavior rules)
```

### 5. Validation & Quality Gates

**Completion criterion**: All checks pass

```bash
# Validation checklist:
# 1. JSON schema valid (chara_card_v2 + worldbook format)
# 2. All worldbook entries reference actual chapter ranges
# 3. No hallucinated entities/events (cross-check with novel text)
# 4. MVU schema matches depth_prompt in card
# 5. Selective entries have proper trigger logic
# 6. File sizes reasonable (< 50KB card, < 100KB worldbook)
# 7. UTF-8 encoding verified
```

## Pitfalls

| Issue | Solution |
|-------|----------|
| GBK encoding fails on rare chars | Use `GB18030` fallback; `errors='replace'` for unrecoverable |
| Chapter detection misses variants | Support "第X章", "第X章.", "第X章·", "Chapter X" patterns |
| Worldbook too large for token budget | Set `token_budget: 4096`, use `priority` + `scan_depth` to trim |
| Selective entries never trigger | Test with sample conversations; adjust `keys[]` and `selective_logic` |
| MVU variables not updating | Ensure `depth_prompt` instructs AI to output JSON block at turn end |
| Reference card content leaked | Audit: every worldbook `content` must cite chapter ranges from novel |

## Verification

```bash
# 1. Import card.json + worldbook.json into SillyTavern
# 2. Start chat, verify:
#    - Worldbook entries inject on keyword triggers
#    - MVU JSON block appears at response ends (when prompted)
#    - Character voice matches novel (third-person narrator, Northeast dialect)
#    - NPCs have distinct voices (赵军=稳重, 李宝玉=莽直, 赵有财=护短)
#    - Plot-accurate responses (no knowledge of future chapters)
# 3. Stress test: 20+ turns covering multiple plot arcs
# 4. Check token usage stays within budget
```

## Pattern Source

Derived from 7-day session analysis (Sep 1-7, 2026):
- 3 sessions on novel→SillyTavern conversion (1072 chapters, 8MB GBK text)
- Repeated: encoding conversion, chapter extraction, entity tracking, MVU design
- Reference architecture: "师兄太稳健 v1.3.1" (constant + selective entries, MVU in depth_prompt)
- Quality gates: zero-hallucination, chapter citations, SillyTavern spec compliance