#!/usr/bin/env python3
"""End-to-end test for changelog.py against a real throwaway git repo.

    python test_changelog.py     -> prints results, exits 1 on any failure
"""

import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "changelog.py")

COMMITS = [
    "feat(auth): add OAuth login",
    "feat: new dark mode toggle",
    "fix(api): resolve null deref on 404",
    "fix typo in error message",
    "refactor(db): change connection pool",
    "chore: bump deps",
    "docs: update README",
    "perf: speed up list rendering",
    "remove legacy /v1 route",
    "revert: drop the beta flag",
    "add CSV export",          # plain message -> Added via fallback
    "corrected rounding bug",  # plain message -> Fixed via fallback
]


def run(args, cwd):
    return subprocess.run(
        [sys.executable, SCRIPT, *args], cwd=cwd, capture_output=True, text=True
    )


def git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=True)


def main():
    fails = 0
    with tempfile.TemporaryDirectory() as td:
        git(td, "init", "-q")
        git(td, "config", "user.email", "t@t.t")
        git(td, "config", "user.name", "t")

        # baseline, then tag it — commits before the tag must be excluded
        open(os.path.join(td, "f.txt"), "w").write("x")
        git(td, "add", "-A")
        git(td, "commit", "-q", "-m", "chore: initial scaffold")
        git(td, "tag", "v1.0.0")

        for msg in COMMITS:
            open(os.path.join(td, "f.txt"), "a").write(".")
            git(td, "add", "-A")
            git(td, "commit", "-q", "-m", msg)

        # 1) dry-run emits every category and strips conventional prefixes
        p = run(["--dry-run", "--version", "1.1.0"], td)
        ok = p.returncode == 0 and "## [1.1.0]" in p.stdout
        fails += 0 if ok else 1
        print(("OK  " if ok else "FAIL") + "  dry-run exits 0 with a version heading")

        for cat in ("Added", "Fixed", "Changed", "Removed"):
            present = re.search(rf"^### {cat}$", p.stdout, re.M) is not None
            fails += 0 if present else 1
            print(("OK  " if ok and present else "FAIL") + f"  category present: {cat}")

        body = p.stdout
        checks = {
            "prefix stripped to message": "- **auth:** add OAuth login" in body,
            "plain message categorized": "CSV export" in body and "rounding bug" in body,
            "commit sha attached": bool(re.search(r"\([0-9a-f]{7,}\)", body)),
            "tagged baseline excluded": "initial scaffold" not in body,
            "changed bucket has refactor": bool(re.search(r"### Changed[\s\S]*- .*connection pool", body)),
            "fallback puts plain bug in Fixed": bool(re.search(r"### Fixed[\s\S]*- .*rounding bug", body)),
        }
        for name, good in checks.items():
            fails += 0 if good else 1
            print(("OK  " if good else "FAIL") + f"  {name}")

        # 2) default run writes CHANGELOG.md, then a second run inserts above
        p2 = run(["--version", "1.1.0"], td)
        out = os.path.join(td, "CHANGELOG.md")
        wrote = p2.returncode == 0 and os.path.exists(out)
        fails += 0 if wrote else 1
        print(("OK  " if wrote else "FAIL") + "  writes CHANGELOG.md")

        git(td, "tag", "v1.1.0")
        open(os.path.join(td, "f.txt"), "a").write(".")
        git(td, "add", "-A")
        git(td, "commit", "-q", "-m", "feat: insert-me-below")
        run(["--version", "1.2.0"], td)
        text = open(out, encoding="utf-8").read()
        ordered = text.find("## [1.2.0]") < text.find("## [1.1.0]") and "insert-me-below" in text
        fails += 0 if ordered else 1
        print(("OK  " if ordered else "FAIL") + "  second run inserts newest section on top")

        # 3) --from range works explicitly
        p3 = run(["--dry-run", "--from", "v1.0.0", "--to", "v1.1.0"], td)
        ranged = p3.returncode == 0 and "OAuth login" in p3.stdout and "insert-me-below" not in p3.stdout
        fails += 0 if ranged else 1
        print(("OK  " if ranged else "FAIL") + "  --from/--to range is respected")

        # 4) non-repo error path
        with tempfile.TemporaryDirectory() as empty:
            p4 = run(["--dry-run"], empty)
            errored = p4.returncode != 0 and "not a git repository" in (p4.stdout + p4.stderr)
            fails += 0 if errored else 1
            print(("OK  " if errored else "FAIL") + "  non-repo exits non-zero with a clear message")

        print("\n--- sample output (first category block) ---")
        print("\n".join(body.splitlines()[:14]))

    print("\n" + ("ALL PASS" if fails == 0 else f"{fails} FAILED"))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
