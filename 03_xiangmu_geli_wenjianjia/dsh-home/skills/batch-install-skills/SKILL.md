---
name: batch-install-skills
description: Batch-install Hermes skills from zip directory with dependency resolution and OpenClaw adaptation.
version: 0.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [skills, batch, install, openclaw, automation]
    related_skills: [hermes-agent-skill-authoring, verify-hermes-setup]
---

# batch-install-skills Skill

Bulk-install multiple skill packages from a directory (e.g., Feishu download zip folder), filter out API-dependent skills, adapt OpenClaw-specific paths, and register usable skills in `~/.hermes/skills/`.

## When to Use

- Received a batch of skill zips (e.g., from Feishu/colleague)
- Want to install all at once, not one-by-one
- Need to skip skills requiring external API keys
- Want to adapt OpenClaw hardcoded paths (`~/.codex/skills/`) to Hermes (`~/.hermes/skills/`)
- Prefer single atomic Python script over manual extraction

## Prerequisites

- Zip files in a directory (e.g., `~/Downloads/飞书20260825-164104/`)
- Python 3.10+ with `zipfile`, `shutil`, `json` (stdlib)
- Target: `~/.hermes/skills/` (created if missing)
- Optional: `skill_view` to verify each after install

## How to Run

```bash
# One-liner (replace path)
python3 <<'PY'
import zipfile, shutil, os, json
from pathlib import Path

SRC = Path(os.path.expanduser("~/Downloads/飞书20260825-164104"))
DST = Path(os.path.expanduser("~/.hermes/skills"))
DST.mkdir(parents=True, exist_ok=True)

SKIP = {"nano-banana-pro", "openclaw-tavily-search", "summarize-1-0-0", "memory-setup", "openclaw-find-skills", "agent-browser-clawdbot"}

for zip_path in SRC.glob("*.zip"):
    name = zip_path.stem
    if name in SKIP:
        print(f"[SKIP] {name} (API-dependent or OpenClaw-only)")
        continue
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(DST / name)
    # Adapt OpenClaw paths if any
    skill_md = DST / name / "SKILL.md"
    if skill_md.exists():
        content = skill_md.read_text()
        content = content.replace("~/.codex/skills", "~/.hermes/skills")
        content = content.replace("{baseDir}", str(DST / name))
        skill_md.write_text(content)
    print(f"[OK] {name}")

print("Done. Installed:")
for d in DST.iterdir():
    if d.is_dir(): print(f"  - {d.name}")
PY
```

## Quick Reference

| Action | Command |
|--------|---------|
| Run batch install | `python3 -c "$(cat <<'PY' ... PY)"` (see above) |
| List installed | `ls -1 ~/.hermes/skills/` |
| Verify one | `hermes skill view <name>` |
| Remove junk | `rm -rf ~/.hermes/skills/{nano-banana-pro,openclaw-tavily-search,...}` |

## Procedure

1. **Locate zip directory** — e.g., `~/Downloads/飞书20260825-164104/` (user-specific).
2. **Define skip list** — Skills needing API keys or OpenClaw CLI (`npx skills`, `agent-browser`):
   - `nano-banana-pro` (needs Nano Banana API)
   - `openclaw-tavily-search` (needs Tavily API)
   - `summarize-1-0-0` (needs LLM API)
   - `memory-setup` (docs only)
   - `openclaw-find-skills` (needs `npx skills`)
   - `agent-browser-clawdbot` (needs `agent-browser` CLI)
3. **Run Python batch script** — Extracts each zip to `~/.hermes/skills/<name>/`, rewrites hardcoded paths.
3. **Verify** — `ls ~/.hermes/skills/` shows 4 keepers: `web-content-fetcher`, `agent-memory`, `proactive-agent`, `self-improving-agent`.
4. **Optional: Create Hermes-native skills** — Adapt OpenClaw concepts (`proactive-agent` → `proactive-hermes`, `self-improving-agent` → `learning-capture`) with proper SKILL.md.

## Pitfalls

- **Zips may have nested folders** — script assumes flat `skill_name/SKILL.md`; adjust if structure differs.
- **OpenClaw skills reference `{baseDir}`** — replace with actual Hermes path.
- **Some skills are Python packages** — may need `pip install -e ~/.hermes/skills/<name>` (not handled here).
- **API-dependent skills waste space** — skip list prevents clutter; delete if already extracted.
- **No version pinning** — installs whatever is in zip; review SKILL.md after.

## Verification

```bash
# Count installed
ls -1 ~/.hermes/skills/ | wc -l
# Should be 4 (web-content-fetcher, agent-memory, proactive-agent, self-improving-agent)

# Each has SKILL.md
for s in ~/.hermes/skills/*/; do test -f "$s/SKILL.md" && echo "✓ $(basename $s)" || echo "✗ $(basename $s)"; done

# Test one
hermes skill view web-content-fetcher
```

Success = 4 skills with valid SKILL.md, no API-dependent leftovers.