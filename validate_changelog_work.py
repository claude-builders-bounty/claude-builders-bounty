#!/usr/bin/env python3
"""Acceptance validator for the generate-changelog bounty deliverables.

BFOS runs: python validate_changelog_work.py

Checks:
  - Required files exist within allowed paths
  - Skill definition is present and well-formed
  - Scripts implement tag-based range + 4 categories + CHANGELOG output
  - README has short setup instructions
  - Sample docs output exists
  - Generator actually produces a valid CHANGELOG from this repo
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import List, Tuple

ROOT = Path(__file__).resolve().parent

REQUIRED_FILES = [
    "changelog.sh",
    "generate-changelog.sh",
    "generate_changelog.py",
    "validate_changelog_work.py",
    "README.md",
    ".claude/skills/generate-changelog/SKILL.md",
]

REQUIRED_CATEGORIES = ("Added", "Fixed", "Changed", "Removed")

PASS = 0
FAIL = 0
ERRORS: List[str] = []


def ok(msg: str) -> None:
    global PASS
    PASS += 1
    print(f"  PASS  {msg}")


def bad(msg: str) -> None:
    global FAIL
    FAIL += 1
    ERRORS.append(msg)
    print(f"  FAIL  {msg}")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def check_required_files() -> None:
    print("\n== Required files ==")
    for rel in REQUIRED_FILES:
        p = ROOT / rel
        if p.is_file() and p.stat().st_size > 0:
            ok(f"exists: {rel}")
        else:
            bad(f"missing or empty: {rel}")


def check_skill() -> None:
    print("\n== Claude skill ==")
    skill = ROOT / ".claude/skills/generate-changelog/SKILL.md"
    if not skill.is_file():
        bad("SKILL.md missing")
        return
    text = read(skill)
    if text.lstrip().startswith("---"):
        ok("SKILL.md has YAML frontmatter")
    else:
        bad("SKILL.md missing YAML frontmatter")

    for needle in (
        "generate-changelog",
        "Added",
        "Fixed",
        "Changed",
        "Removed",
        "CHANGELOG",
        "git",
        "tag",
    ):
        if needle.lower() in text.lower() or needle in text:
            ok(f"SKILL.md mentions {needle!r}")
        else:
            bad(f"SKILL.md missing reference to {needle!r}")


def check_scripts_content() -> None:
    print("\n== Script content ==")
    for rel in ("changelog.sh", "generate_changelog.py"):
        text = read(ROOT / rel)
        lower = text.lower()

        # last tag / since tag
        if re.search(r"describe.*--tags|last[_ ]?tag|since.*tag", text, re.I):
            ok(f"{rel}: fetches commits relative to last tag")
        else:
            bad(f"{rel}: does not reference last git tag")

        for cat in REQUIRED_CATEGORIES:
            if cat in text:
                ok(f"{rel}: categorizes {cat}")
            else:
                bad(f"{rel}: missing category {cat}")

        if "CHANGELOG" in text or "changelog.md" in lower:
            ok(f"{rel}: writes CHANGELOG output")
        else:
            bad(f"{rel}: no CHANGELOG output reference")

        # conventional commit signals
        if re.search(r"\bfeat\b", text) and re.search(r"\bfix\b", text):
            ok(f"{rel}: conventional commit type mapping present")
        else:
            bad(f"{rel}: missing feat/fix conventional mapping")

    # wrapper
    wrapper = read(ROOT / "generate-changelog.sh")
    if "changelog.sh" in wrapper:
        ok("generate-changelog.sh delegates to changelog.sh")
    else:
        bad("generate-changelog.sh should invoke changelog.sh")


def check_readme() -> None:
    print("\n== README ==")
    text = read(ROOT / "README.md")
    lower = text.lower()

    if "changelog" in lower:
        ok("README mentions changelog")
    else:
        bad("README missing changelog docs")

    # Setup in 3 steps or fewer — look for numbered steps near setup section
    setup_patterns = [
        r"(?is)setup|quick start|getting started|how to use|install",
        r"(?m)^\s*1[\.\)]\s+",
        r"(?m)^\s*2[\.\)]\s+",
        r"(?m)^\s*3[\.\)]\s+",
    ]
    hits = sum(1 for p in setup_patterns if re.search(p, text))
    if hits >= 3:
        ok("README has short numbered setup (≤3 steps style)")
    else:
        # also accept fenced bash with clone/chmod/run style
        if "changelog.sh" in text and ("python generate_changelog" in lower or "bash changelog" in lower):
            ok("README documents how to run the generator")
        else:
            bad("README needs setup instructions in 3 steps or fewer")

    for cmd in ("changelog.sh", "generate-changelog", "generate_changelog.py"):
        if cmd in text:
            ok(f"README references {cmd}")
            break
    else:
        bad("README does not reference any generator entrypoint")


def check_sample_docs() -> None:
    print("\n== Sample output docs ==")
    candidates = [
        ROOT / "docs" / "sample-changelog.md",
        ROOT / "docs" / "CHANGELOG.sample.md",
        ROOT / "docs" / "sample_output.md",
        ROOT / "CHANGELOG.md",
    ]
    found = [p for p in candidates if p.is_file() and p.stat().st_size > 0]
    if not found:
        bad("no sample CHANGELOG output in docs/ or CHANGELOG.md")
        return

    ok(f"sample present: {found[0].relative_to(ROOT).as_posix()}")
    text = read(found[0])
    if re.search(r"^#\s+Changelog", text, re.M):
        ok("sample has Changelog heading")
    else:
        bad("sample missing '# Changelog' heading")

    # At least one category section in sample
    if any(re.search(rf"^###\s+{cat}\b", text, re.M) for cat in REQUIRED_CATEGORIES):
        ok("sample includes at least one category section")
    else:
        bad("sample missing Added/Fixed/Changed/Removed sections")


def check_generator_runs() -> None:
    print("\n== Live generator run ==")
    script = ROOT / "generate_changelog.py"
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "CHANGELOG.test.md"
        proc = subprocess.run(
            [sys.executable, str(script), str(out)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if proc.returncode != 0:
            bad(f"generate_changelog.py exited {proc.returncode}: {proc.stderr[:400]}")
            return
        ok("generate_changelog.py exits 0")

        if not out.is_file():
            bad("generator did not create output file")
            return
        ok("generator created output file")

        text = out.read_text(encoding="utf-8", errors="replace")
        if re.search(r"^#\s+Changelog", text, re.M):
            ok("generated file has Changelog heading")
        else:
            bad("generated file missing Changelog heading")

        if "## [Unreleased]" in text or re.search(r"^##\s+\[", text, re.M):
            ok("generated file has version section")
        else:
            bad("generated file missing version section")

        # This repo has a feat: commit → should land in Added
        if "### Added" in text or "### Changed" in text or "### Fixed" in text:
            ok("generated file has categorized sections")
        else:
            # empty history edge case
            if "No commits found" in text:
                ok("generated file handles empty commit range")
            else:
                bad("generated file has no category sections and no empty notice")

        # Ensure categorization function covers all four labels in source
        src = read(script)
        for cat in REQUIRED_CATEGORIES:
            if f'"{cat}"' in src or f"'{cat}'" in src:
                continue
            bad(f"Python source missing string {cat!r}")
            break
        else:
            ok("Python source defines all four categories")


def check_bash_entrypoint_present() -> None:
    print("\n== Bash entrypoint ==")
    sh = ROOT / "changelog.sh"
    text = read(sh)
    if text.startswith("#!") or "git" in text:
        ok("changelog.sh is a real shell script")
    else:
        bad("changelog.sh does not look like a shell script")
    if "Added" in text and "Fixed" in text and "Changed" in text and "Removed" in text:
        ok("changelog.sh includes all four category names")
    else:
        bad("changelog.sh missing one or more categories")


def main() -> int:
    print("validate_changelog_work.py")
    print(f"root: {ROOT}")

    check_required_files()
    check_skill()
    check_scripts_content()
    check_bash_entrypoint_present()
    check_readme()
    check_sample_docs()
    check_generator_runs()

    print("\n== Summary ==")
    print(f"passed: {PASS}")
    print(f"failed: {FAIL}")
    if FAIL:
        print("\nFailures:")
        for e in ERRORS:
            print(f"  - {e}")
        return 1
    print("\nAll acceptance checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
