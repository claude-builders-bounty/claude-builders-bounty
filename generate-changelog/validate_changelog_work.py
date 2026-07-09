#!/usr/bin/env python3
"""Deterministic acceptance check for the generate-changelog skill.

Exit 0 iff every bounty acceptance criterion is met:
  - required deliverable files exist,
  - `bash changelog.sh` runs on a seeded git repo,
  - commits since the last tag are categorized into Added/Fixed/Changed/Removed
    with each seeded commit placed in the correct section.

Run from the repository root:  python validate_changelog_work.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
# Repo root = wherever changelog.sh lives (this file may sit under generate-changelog/).
REPO = ROOT
for _ in range(3):
    if (REPO / "changelog.sh").is_file():
        break
    REPO = REPO.parent

REQUIRED = [
    "changelog.sh",
    ".claude/skills/generate-changelog/SKILL.md",
    "generate-changelog/README.md",
    "generate-changelog/CHANGELOG.sample.md",
]


def fail(msg: str) -> "int":
    print(f"VALIDATION_FAILED: {msg}")
    return 1


def _bash() -> str | None:
    b = shutil.which("bash")
    if b:
        return b
    for c in (r"C:\Program Files\Git\bin\bash.exe", r"C:\Program Files\Git\usr\bin\bash.exe"):
        if Path(c).is_file():
            return c
    return None


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True,
                   encoding="utf-8", errors="replace")


def _section(text: str, name: str) -> list[str]:
    """Return the bullet lines under '### <name>' up to the next '### '."""
    lines = text.splitlines()
    out, grab = [], False
    for ln in lines:
        if ln.strip().startswith("### "):
            grab = ln.strip() == f"### {name}"
            continue
        if grab and ln.strip().startswith("- "):
            out.append(ln.strip()[2:])
    return out


def main() -> int:
    for rel in REQUIRED:
        p = REPO / rel
        if not p.is_file() or p.stat().st_size < 20:
            return fail(f"missing/empty deliverable: {rel}")

    bash = _bash()
    if bash is None:
        return fail("bash not found (required to run changelog.sh)")

    with tempfile.TemporaryDirectory() as td:
        repo = Path(td)
        _git(repo, "init", "-q")
        _git(repo, "config", "user.email", "v@v")
        _git(repo, "config", "user.name", "v")
        _git(repo, "commit", "-q", "--allow-empty", "-m", "chore: initial")
        _git(repo, "tag", "v0.1.0")
        seeded = {
            "feat: add export command": "Added",
            "feat(api): support pagination": "Added",
            "fix: crash on empty input": "Fixed",
            "refactor: tidy internals": "Changed",
            "docs: expand usage": "Changed",
            "remove: drop deprecated flag": "Removed",
        }
        for msg in seeded:
            _git(repo, "commit", "-q", "--allow-empty", "-m", msg)

        out = repo / "OUT.md"
        proc = subprocess.run([bash, str(REPO / "changelog.sh"), str(repo), str(out)],
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=60)
        if proc.returncode != 0:
            return fail(f"changelog.sh exit {proc.returncode}: {proc.stderr.strip()[:300]}")
        if not out.is_file():
            return fail("changelog.sh did not write the output file")
        text = out.read_text(encoding="utf-8")

        for cat in ("Added", "Fixed", "Changed", "Removed"):
            if f"### {cat}" not in text:
                return fail(f"output missing category: {cat}")

        buckets = {cat: _section(text, cat) for cat in ("Added", "Fixed", "Changed", "Removed")}
        for msg, expected_cat in seeded.items():
            if not any(msg in item for item in buckets[expected_cat]):
                return fail(f"commit not categorized as {expected_cat}: {msg!r} "
                            f"(buckets={ {k: len(v) for k, v in buckets.items()} })")

    print("VALIDATION_OK: deliverables present; changelog.sh categorized all seeded "
          "commits into Added/Fixed/Changed/Removed correctly.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
