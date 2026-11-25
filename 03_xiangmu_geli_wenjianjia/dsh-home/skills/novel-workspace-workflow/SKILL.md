---
name: novel-workspace-workflow
description: "Enforce novel workspace AGENTS.md: 5-option planning."
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
    - workflow
    - planning
    - approval
    - theory-integration
    related_skills:
    - novel_pipeline
    - writing_robert_mckee_story
    - writing_narrative_techniques_guide
    - writing_robert_mckee_dialogue
    - writing_stephen_king_on_writing
    - novel-distillation-pipeline
---

# Novel Workspace Workflow Enforcement

Enforce the novel workspace AGENTS.md workflow rules: single workspace root, no auto-generation, 1 book = 1 folder, 5-option planning with explicit approval, theory skill integration, and style profile enforcement.

## When to Use

- Starting a new novel chapter in `/home/user01/novel-workspace/workspace/00_<book>/`
- User requests "write chapter N" or "plan chapter N"
- Any novel generation task in the novel-workspace directory
- Need to enforce AGENTS.md rules before generating content

**Don't use for:** General writing tasks outside the novel-workspace, or non-novel content generation.

## Prerequisites

- Novel workspace root: `/home/user01/novel-workspace/` (唯一权威根)
- AGENTS.md at workspace root with workflow rules
- Theory skills installed:
  - `writing_robert_mckee_story` (Planning stage)
  - `writing_narrative_techniques_guide` (Writing stage)
  - `writing_robert_mckee_dialogue` (Writing stage)
  - `writing_stephen_king_on_writing` (Reviewing stage)
- Style profile: `/home/user01/novel-workspace/scripts/style_profile.json`
- Guardrails config: `/home/user01/novel-workspace/config/guardrails_config.yaml`
- De-AI script: `/home/user01/novel-workspace/scripts/nemotron_humanify.py`

## How to Run

```bash
# Check workspace structure
ls -la /home/user01/novel-workspace/workspace/

# Read current book AGENTS.md
cat /home/user01/novel-workspace/AGENTS.md

# Read theory skills for current stage
skill_view name="writing_robert_mckee_story"
skill_view name="writing_narrative_techniques_guide"
skill_view name="writing_robert_mckee_dialogue"
skill_view name="writing_stephen_king_on_writing"

# Read style profile
cat /home/user01/novel-workspace/scripts/style_profile.json

# Read guardrails
cat /home/user01/novel-workspace/config/guardrails_config.yaml
```

## Quick Reference

| Task | Command/Action |
|------|----------------|
| Verify workspace root | `ls /home/user01/novel-workspace/workspace/` |
| List books | `ls /home/user01/novel-workspace/workspace/00_*/` |
| Check AGENTS.md | `cat /home/user01/novel-workspace/AGENTS.md` |
| Load theory skill (Planning) | `skill_view name="writing_robert_mckee_story"` |
| Load theory skill (Writing) | `skill_view name="writing_narrative_techniques_guide"` |
| Load theory skill (Dialogue) | `skill_view name="writing_robert_mckee_dialogue"` |
| Load theory skill (Reviewing) | `skill_view name="writing_stephen_king_on_writing"` |
| Check style profile | `cat /home/user01/novel-workspace/scripts/style_profile.json` |
| Check guardrails | `cat /home/user01/novel-workspace/config/guardrails_config.yaml` |

## Procedure

### 1. Verify Workspace Root and Book Structure

```bash
# Must be /home/user01/novel-workspace/ only
ls -la /home/user01/novel-workspace/workspace/
# Should show only 00_<book_name>/ directories
```

**Completion criterion:** Only the single workspace root exists, each book in its own `00_<name>/` folder.

### 2. Read Book-Specific Configuration

```bash
# For current book (e.g., 00_红警现代华夏军工库)
cat /home/user01/novel-workspace/workspace/00_红警现代华夏军工库/book.yaml
cat /home/user01/novel-workspace/workspace/00_红警现代华夏军工库/planning/deconstruction.json
cat /home/user01/novel-workspace/workspace/00_红警现代华夏军工库/planning/golden_finger_v3.md
```

**Completion criterion:** Book metadata, deconstruction, and golden finger settings loaded.

### 3. Load Theory Skills by Pipeline Stage

| Stage | Theory Skill | Purpose |
|-------|-------------|---------|
| Planning | `writing_robert_mckee_story` | Story structure, acts, beats, climax design |
| Writing | `writing_narrative_techniques_guide` | Prose techniques, POV, scene construction |
| Writing | `writing_robert_mckee_dialogue` | Dialogue subtext, character voice, compression |
| Reviewing | `writing_stephen_king_on_writing` | Cutting fluff, active verbs, reading aloud test |

**Completion criterion:** All 4 theory skills loaded and relevant sections noted.

### 4. Generate 5 Options with Standard Format

Each option MUST include:
- **Option name** (A/B/C/D/E)
- **Conflict line** (核心冲突)
- **Shuang dian** (爽点 - emotional payoff)
- **Hook** (钩子 - chapter ending hook)
- **Word count** (目标字数)
- **Risk** (风险点)

**Completion criterion:** 5 distinct options presented, no auto-selection.

### 5. Wait for Explicit User Approval

- Present options to user
- User selects ONE option or requests combination
- Only proceed after explicit "go with A" or similar confirmation
- Record selection in planning file

**Completion criterion:** User has explicitly confirmed the chosen option.

### 6. Write Chapter with Theory Integration

Apply loaded theory skills during generation:
- McKee: Scene beats, turning points, gap between expectation/result
- Narrative Techniques: POV control, sensory details, scene-sequel structure
- McKee Dialogue: Subtext, compression, character voice differentiation
- King: Cut adjectives/adverbs, active verbs, read-aloud rhythm check

**Completion criterion:** Chapter draft written with theory integration.

### 7. Run De-AI and Guardrails Check

```bash
# De-AI pass
python3 /home/user01/novel-workspace/scripts/nemotron_humanify.py --input chapter_draft.txt --output chapter_clean.txt

# Guardrails check (genre: modern_military_apocalypse)
python3 /home/user01/novel-workspace/scripts/check_hard_guardrails.py --genre modern_military_apocalypse --input chapter_clean.txt
```

**Completion criterion:** De-AI pass complete, guardrails show 0 violations (or ≤3 with warnings).

### 8. Save to Manuscript and Update State

```bash
# Save to manuscript/
mkdir -p /home/user01/novel-workspace/workspace/00_红警现代华夏军工库/manuscript/
cp chapter_clean.txt /home/user01/novel-workspace/workspace/00_红警现代华夏军工库/manuscript/ch01.txt

# Update book.yaml current_chapter and total_words
# Update memory/state.json with new chapter info
```

**Completion criterion:** Chapter saved to manuscript/, metadata updated.

## Pitfalls

| Issue | Solution |
|-------|----------|
| Auto-generating without 5 options | STOP - always generate 5 options first, wait for approval |
| Using wrong workspace root | Only `/home/user01/novel-workspace/` is valid |
| Skipping theory skills | Load all 4 theory skills by stage before writing |
| Not running de-AI/guardrails | Mandatory for every chapter - no exceptions |
| Mixing books in one folder | Each book strictly in its own `00_<name>/` |
| Writing to wrong paths | All products go to `planning/`, `manuscript/`, `memory/`, `reviews/` |

## Verification

```bash
# 1. Workspace structure correct
ls /home/user01/novel-workspace/workspace/ | grep -E '^00_' && echo "✅ Books in correct format"

# 2. AGENTS.md exists
[[ -f /home/user01/novel-workspace/AGENTS.md ]] && echo "✅ AGENTS.md present"

# 3. Theory skills all load
for s in writing_robert_mckee_story writing_narrative_techniques_guide writing_robert_mckee_dialogue writing_stephen_king_on_writing; do
    skill_view name="$s" >/dev/null 2>&1 && echo "✅ $s loads" || echo "❌ $s failed"
done

# 4. Style profile exists
[[ -f /home/user01/novel-workspace/scripts/style_profile.json ]] && echo "✅ Style profile exists"

# 5. Guardrails config exists
[[ -f /home/user01/novel-workspace/config/guardrails_config.yaml ]] && echo "✅ Guardrails config exists"

# 6. De-AI script exists
[[ -f /home/user01/novel-workspace/scripts/nemotron_humanify.py ]] && echo "✅ De-AI script exists"
```

---

*Skill distilled from 5+ sessions (Oct 7-10, 2026): novel workspace AGENTS.md enforcement, 5-option planning with explicit approval, 4 theory skill integration by pipeline stage, de-AI + guardrails mandatory pass, single workspace root discipline. Pattern occurred in sessions 20261007_124819_584d1789, 20261010_090131_66e90711, 20261010_102643_a758dd, 20261010_212502_289db841, and multiple planning interactions.*