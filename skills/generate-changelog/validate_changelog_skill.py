#!/usr/bin/env python3
"""Validate the generate-changelog skill files."""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "skills" / "generate-changelog" / "scripts" / "changelog.sh"


def main() -> int:
    required = [
        ROOT / "skills" / "generate-changelog" / "SKILL.md",
        ROOT / "skills" / "generate-changelog" / "README.md",
        SCRIPT,
        ROOT / "skills" / "generate-changelog" / "samples" / "claude-builders-bounty.md",
    ]
    for path in required:
        if not path.exists():
            raise SystemExit(f"missing {path}")

    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], cwd=repo, check=True)
        (repo / "app.txt").write_text("one\n", encoding="utf-8")
        subprocess.run(["git", "add", "app.txt"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-m", "feat: add dashboard"], cwd=repo, check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["git", "tag", "v0.1.0"], cwd=repo, check=True)
        (repo / "app.txt").write_text("two\n", encoding="utf-8")
        subprocess.run(["git", "add", "app.txt"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-m", "fix: handle empty state"], cwd=repo, check=True, stdout=subprocess.DEVNULL)
        subprocess.run(["bash", str(SCRIPT)], cwd=repo, check=True, stdout=subprocess.DEVNULL)
        changelog = (repo / "CHANGELOG.md").read_text(encoding="utf-8")
        if "fix: handle empty state" not in changelog:
            raise SystemExit("generated changelog missing commit since latest tag")
        if "feat: add dashboard" in changelog:
            raise SystemExit("generated changelog included commit before latest tag")
        if "### Fixed" not in changelog:
            raise SystemExit("generated changelog missing Fixed section")

    print("generate changelog skill validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
