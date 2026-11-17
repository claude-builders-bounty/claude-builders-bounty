---
name: multi-session-creative-workflow
description: "Manage long-running creative projects across multiple Hermes sessions with context preservation. [DISABLED]"
version: 0.1.0
author: User (Hermes Agent)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [workflow, session-management, creative, long-running, context-preservation]
    related_skills: [session-librarian, hermes-agent-skill-authoring, memory-local, plan]
---

# Multi-Session Creative Workflow

Manage creative projects (novel adaptation, worldbuilding, character creation) that span multiple Hermes sessions while preserving context, progress, and decision history.

## When to Use

- Creative project exceeds single session context (100+ turns, large files)
- Need to pause/resume work across days with full context recovery
- Multiple related sessions on same project (analysis, drafting, refinement)
- Collaborative handoff between sessions with structured summaries
- Prevent context loss from model provider failures or network issues

## Prerequisites

- Hermes Agent with `session_search` tool enabled
- `memory-local` skill active (auto-injects relevant memories)
- Project workspace directory (e.g., `/home/user01/projects/<project-name>/`)
- Consistent session naming convention

## How to Run

```bash
# Start new project session
hermes chat -q "Project: <name> | Phase: <phase> | Context: <summary>"

# Resume from last session
hermes --resume <session_id>

# Or fork from a specific session
hermes --branch <session_id> -q "Continue from <milestone>"
```

## Quick Reference

| Action | Command/Tool |
|--------|--------------|
| Save progress checkpoint | `session_search` + manual summary to project log |
| Resume with full context | `session_search(session_id="...")` + read key files |
| Fork parallel workstream | `delegate_task` with project context |
| Archive completed phase | `hermes sessions archive` + export markdown |
| Cross-session memory | `memory-local` auto-injection (bge-m3 + ChromaDB) |

## Procedure

### 1. Project Initialization (Session 0)

**Completion criterion**: Project structure created, baseline context documented

```markdown
# Project: <name>
## Created: YYYY-MM-DD
## Goal: One-sentence objective
## Source Material: <files/URLs>
## Phases:
  1. Analysis & Extraction
  2. Architecture & Design
  3. Drafting/Generation
  4. Validation & Polish
  5. Export & Delivery
## Key Decisions: (append as made)
## Open Questions: (append as found)
```

Create in project workspace: `PROJECT.md`, `PHASES/`, `OUTPUTS/`, `SESSIONS/`

### 2. Phase Execution Pattern (Per Session)

**Completion criterion**: Phase deliverable written to `OUTPUTS/`, session summary appended to `SESSIONS/<session_id>.md`

Each session follows:
1. **Context Load** (5 min): Read `PROJECT.md`, latest `SESSIONS/*.md`, relevant `OUTPUTS/*`
2. **Work** (main): Execute phase tasks, write intermediate files to `WORK/`
3. **Checkpoint** (last 10 min):
   - Write session summary to `SESSIONS/<session_id>.md`
   - Update `PROJECT.md` with decisions/questions
   - Copy final deliverables to `OUTPUTS/`
   - Note next session's starting point

### 3. Session Summary Template

```markdown
# Session: <session_id> | <date> | Phase <N>
## Goal: <what this session aimed to achieve>
## Completed:
- <task 1 with output file>
- <task 2 with output file>
## Decisions Made:
- <decision 1 with rationale>
## Blockers/Questions:
- <issue 1>
## Next Session Start:
- <exact next step>
- <files to read first>
## Key Files Modified:
- <path>: <what changed>
```

### 4. Context Recovery (Resuming)

**Completion criterion**: Full working context restored in < 5 minutes

```python
# Recovery checklist:
# 1. Read PROJECT.md (current state, decisions, open questions)
# 2. Read latest 2-3 SESSIONS/*.md (recent progress)
# 3. Read relevant OUTPUTS/* (current deliverables)
# 4. Run session_search(query="<project keywords>", limit=5) for cross-session memories
# 5. Load any skill context needed (skill_view)
# 6. Confirm working directory and file paths
```

### 5. Parallel Workstreams (When Needed)

**Completion criterion**: Subagent results synthesized into main project

```python
# Use delegate_task for independent sub-tasks:
delegate_task(tasks=[
  {"goal": "Extract all character dialogues from chapters 500-600", "context": "Project: NovelToTavern, Source: novel_utf8.txt, Output: WORK/dialogues_500_600.json"},
  {"goal": "Build location index with chapter references", "context": "Project: NovelToTavern, Source: novel_utf8.txt, Output: WORK/locations.json"},
], role="leaf")

# Synthesize results in parent session, write to OUTPUTS/
```

### 6. Phase Gate & Archival

**Completion criterion**: Phase deliverable validated, archived, next phase planned

At phase completion:
1. Validate deliverable against acceptance criteria
2. Export session chain: `hermes sessions export --session-id <id> --format md > SESSIONS/phase<N>_export.md`
3. Archive sessions: `hermes sessions archive --source cron --older-than 7d` (keep project sessions)
4. Update `PROJECT.md` with phase completion, next phase plan
5. Commit to git if version controlled

## Pitfalls

| Issue | Prevention |
|-------|------------|
| Context loss on provider failure | Checkpoint every 30 min; write summaries to disk |
| Drift from original goal | `PROJECT.md` as north star; review at session start |
| Duplicate work across sessions | Search `SESSIONS/` before starting; use `session_search` |
| File path confusion | Absolute paths in `PROJECT.md`; use project workspace root |
| Memory pollution | `memory-local` auto-filters; manually add only stable facts |
| Session naming chaos | Convention: `<project>-<phase>-<desc>` (e.g., `novel2tavern-p2-worldbook`) |

## Verification

- Can resume any session from last 7 days and reach full productivity in < 5 min
- No repeated work across sessions (verified by session_search)
- All phase deliverables traceable to source material with citations
- Project `PROJECT.md` reflects current reality (decisions, blockers, next steps)
- Cross-session memories (`memory-local`) contain project-relevant facts

## Pattern Source

Derived from 7-day session analysis (Sep 1-7, 2026):
- 4+ sessions on same novel→SillyTavern project across 3 days
- Repeated context recovery needs after provider failures/timeouts
- Session summaries in Feishu messages used as ad-hoc checkpoints
- `session_search` used to recover lost context
- Parallel sub-tasks (entity extraction, chapter analysis) delegated
- Need for structured phase gates and archival process