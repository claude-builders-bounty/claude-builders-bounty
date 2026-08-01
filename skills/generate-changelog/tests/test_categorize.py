#!/usr/bin/env python3
"""
test_categorize.py — 16 unit tests for the categorize function.

These tests cover the Conventional Commits → Keep a Changelog mapping
documented in SKILL.md. They run against the Python implementation; the
bash implementation has equivalent logic in `categorize()` inside
changelog.sh.

Run: python3 tests/test_categorize.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make the scripts/ directory importable
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "scripts"))

from changelog import categorize, Commit  # noqa: E402

PASS = 0
FAIL = 0
RESULTS = []


def check(name: str, expected: str, got: str) -> None:
    global PASS, FAIL
    if expected == got:
        PASS += 1
        RESULTS.append(f"  ✓ {name}")
    else:
        FAIL += 1
        RESULTS.append(f"  ✗ {name}  expected={expected!r}  got={got!r}")


def c(subject: str, body: str = "") -> Commit:
    return Commit(subject=subject, body=body)


# --- 1-4: feat* → added -----------------------------------------
check("feat bare",            "added",  categorize(c("feat: add login page")))
check("feat scoped",          "added",  categorize(c("feat(auth): add OAuth flow")))
check("feat with bang",       "added",  categorize(c("feat!: drop legacy API")))
check("feat in body, no body BREAKING", "added",
      categorize(c("feat: new dashboard", "long description\nno breaking change")))

# --- 5-7: fix* → fixed ------------------------------------------
check("fix bare",             "fixed",  categorize(c("fix: crash on empty input")))
check("fix scoped",           "fixed",  categorize(c("fix(api): handle 401")))
check("fix with exclamation", "fixed",  categorize(c("fix!: require explicit --yes")))

# --- 8-11: refactor/perf/style/docs → changed or ignored --------
check("refactor",             "changed", categorize(c("refactor: extract helper")))
check("perf",                 "changed", categorize(c("perf: cache lookup results")))
check("docs",                 "ignored", categorize(c("docs: update README")))
check("test",                 "ignored", categorize(c("test: add unit tests")))

# --- 12-13: revert/removed → removed -----------------------------
check("revert",               "removed", categorize(c("revert: undo v2 schema")))
check("removed",              "removed", categorize(c("removed: drop legacy endpoint")))

# --- 14: BREAKING CHANGE in body → changed (promoted) ----------
check("BREAKING in body",     "changed", categorize(c("feat: new auth",
                                                       "BREAKING CHANGE: tokens rotate every hour")))
check("BREAKING wins over feat","changed", categorize(c("feat: small thing",
                                                          "BREAKING CHANGE: removes v1 endpoint")))

# --- 15: no conventional prefix → changed (default) ------------
check("no prefix lower",      "changed", categorize(c("polish the spinner")))
check("no prefix uppercase",  "changed", categorize(c("Update package.json")))

# --- 16: chore → ignored ----------------------------------------
check("chore",                "ignored", categorize(c("chore: bump deps")))


def main() -> int:
    print(f"Running 16 categorize() tests...\n")
    for line in RESULTS:
        print(line)
    print(f"\n{PASS} passed, {FAIL} failed (total {len(RESULTS)})")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())