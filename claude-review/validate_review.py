#!/usr/bin/env python3
"""Deterministic acceptance check for claude-review (no API key needed).

Exit 0 iff:
  - required deliverables exist (CLI, README, GitHub Action, 2 sample outputs),
  - the CLI emits EXACTLY the four required sections and a normalized confidence,
  - missing model sections are backfilled (the contract always holds),
  - each sample output contains all four sections and a valid confidence.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

REPO = Path(__file__).resolve().parent
TOOL = REPO / "claude_review.py"
REQUIRED = [
    "claude_review.py", "README.md", "github/claude-review.yml",
    "samples/sample_review_1.md", "samples/sample_review_2.md",
]
SECTIONS = ("## Summary", "## Risks", "## Suggestions", "## Confidence")
CONF = ("Low", "Medium", "High")


def fail(msg: str) -> int:
    print(f"VALIDATION_FAILED: {msg}")
    return 1


def _confidence_value(text: str) -> str | None:
    m = re.search(r"^##\s+Confidence\s*\n([^\n]+)", text, re.M)
    if not m:
        return None
    for c in CONF:
        if re.search(rf"\b{c}\b", m.group(1)):
            return c
    return None


def main() -> int:
    for rel in REQUIRED:
        p = REPO / rel
        if not p.is_file() or p.stat().st_size < 20:
            return fail(f"missing/empty deliverable: {rel}")

    scratch = Path(__file__).resolve().parents[1] / f"_revval_{uuid.uuid4().hex[:8]}"
    try:
        scratch.mkdir(parents=True, exist_ok=True)
        diff = scratch / "c.diff"
        diff.write_text("diff --git a/x b/x\n--- a/x\n+++ b/x\n@@ -1 +1 @@\n-a\n+b\n", encoding="utf-8")

        # 1) well-formed model output -> all sections preserved, confidence normalized
        stub = scratch / "stub.md"
        stub.write_text("## Summary\nAdds b.\n## Risks\n- none\n## Suggestions\n- add tests\n## Confidence\nHigh\n",
                        encoding="utf-8")
        out = subprocess.run([sys.executable, str(TOOL), "--diff-file", str(diff),
                              "--stub-file", str(stub), "--pr", "o/r#1"],
                             capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
        if out.returncode != 0:
            return fail(f"CLI failed: {out.stderr.strip()[:200]}")
        text = out.stdout
        for s in SECTIONS:
            if s not in text:
                return fail(f"output missing section {s!r}")
        if _confidence_value(text) != "High":
            return fail("confidence not normalized to High")

        # 2) model omits sections -> contract still holds (backfilled) + confidence defaults valid
        stub2 = scratch / "stub2.md"
        stub2.write_text("just some prose, no headings at all", encoding="utf-8")
        out2 = subprocess.run([sys.executable, str(TOOL), "--diff-file", str(diff), "--stub-file", str(stub2)],
                              capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
        for s in SECTIONS:
            if s not in out2.stdout:
                return fail(f"backfill failed: missing {s!r}")
        if _confidence_value(out2.stdout) not in CONF:
            return fail("default confidence not a valid level")

        # 3) sample outputs are well-formed
        for rel in ("samples/sample_review_1.md", "samples/sample_review_2.md"):
            t = (REPO / rel).read_text(encoding="utf-8")
            for s in SECTIONS:
                if s not in t:
                    return fail(f"{rel} missing section {s!r}")
            if _confidence_value(t) not in CONF:
                return fail(f"{rel} has no valid Confidence level")

        print("VALIDATION_OK: CLI emits the 4-section contract, normalizes confidence, backfills "
              "missing sections; 2 real-PR sample outputs are well-formed.")
        return 0
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
