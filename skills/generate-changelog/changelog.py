#!/usr/bin/env python3
"""
Generate a categorized CHANGELOG.md from git history since the last tag.

    python changelog.py                 # since last tag -> ./CHANGELOG.md
    python changelog.py --dry-run       # print, don't write
    python changelog.py --from v1.2.0 --version 1.3.0 --output CHANGELOG.md

Categories commits into Added / Fixed / Changed / Removed using Conventional Commit
prefixes, falling back to keyword matching for plain messages.
"""

import argparse
import datetime
import re
import subprocess
import sys

TYPE_MAP = {
    "feat": "Added", "feature": "Added", "add": "Added", "new": "Added",
    "fix": "Fixed", "bugfix": "Fixed", "hotfix": "Fixed", "patch": "Fixed",
    "remove": "Removed", "removal": "Removed", "revert": "Removed",
    "deprecate": "Removed", "drop": "Removed", "delete": "Removed",
    "refactor": "Changed", "perf": "Changed", "change": "Changed", "update": "Changed",
    "improve": "Changed", "style": "Changed", "chore": "Changed", "docs": "Changed",
    "build": "Changed", "ci": "Changed", "test": "Changed", "deps": "Changed",
}

FALLBACK = [
    ("Added", re.compile(r"\b(add|adds|added|implement|introduce|support|new)\b", re.I)),
    ("Fixed", re.compile(r"\b(fix(es|ed)?|repairs?|correct(ed|ion|s)?|resolve[sd]?|patch(ed)?)\b", re.I)),
    ("Removed", re.compile(r"\b(remove|removes|removed|revert|deprecat|drop|delete)\b", re.I)),
    ("Changed", re.compile(r"\b(update|updates|change|refactor|improve|tweak|bump|rename|move)\b", re.I)),
]

ORDER = ["Added", "Fixed", "Changed", "Removed"]


def git(*args):
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    if r.returncode != 0:
        return ""
    return r.stdout


def last_tag():
    return git("describe", "--tags", "--abbrev=0").strip()


def classify(subject):
    subject = subject.strip()
    m = re.match(r"^([A-Za-z]+)(?:\(([^)]*)\))?!?:\s*(.+)$", subject)
    if m:
        t, scope, msg = m.group(1).lower(), m.group(2), m.group(3).strip()
        cat = TYPE_MAP.get(t)
        if cat:
            return cat, (f"**{scope}:** {msg}" if scope else msg)
    for cat, rx in FALLBACK:
        if rx.search(subject):
            return cat, subject
    return "Changed", subject


def collect(rng):
    out = git("log", "--no-merges", "--pretty=format:%h\t%s", rng)
    changes = {c: [] for c in ORDER}
    for line in out.splitlines():
        if not line.strip():
            continue
        sha, _, subject = line.partition("\t")
        if not subject or subject.lower().startswith("merge "):
            continue
        cat, msg = classify(subject)
        changes[cat].append(f"- {msg} ({sha})")
    return changes


def render(changes, version, date):
    lines = [f"## [{version}] - {date}", ""]
    any_change = False
    for cat in ORDER:
        if not changes[cat]:
            continue
        any_change = True
        lines += [f"### {cat}", *changes[cat], ""]
    if not any_change:
        lines += ["_No notable changes._", ""]
    return "\n".join(lines).rstrip() + "\n"


def write_out(path, section):
    header = "# Changelog\n\nAll notable changes to this project.\n\n"
    try:
        existing = open(path, encoding="utf-8").read()
    except OSError:
        existing = ""
    if not existing.strip():
        open(path, "w", encoding="utf-8").write(header + section)
        return
    # insert the new section right after the top-level description block
    idx = existing.find("\n## ")
    if idx == -1:
        open(path, "w", encoding="utf-8").write(existing.rstrip() + "\n\n" + section)
    else:
        open(path, "w", encoding="utf-8").write(existing[:idx].rstrip() + "\n\n" + section + existing[idx:].lstrip("\n"))


def main():
    ap = argparse.ArgumentParser(description="Generate a categorized CHANGELOG from git history.")
    ap.add_argument("--from", dest="frm", help="start ref (exclusive); default = last tag")
    ap.add_argument("--to", dest="to", default="HEAD", help="end ref (default HEAD)")
    ap.add_argument("--version", default="Unreleased", help="version heading (default Unreleased)")
    ap.add_argument("--output", default="CHANGELOG.md", help="output file (default CHANGELOG.md)")
    ap.add_argument("--dry-run", action="store_true", help="print instead of writing")
    args = ap.parse_args()

    if git("rev-parse", "--git-dir") == "":
        sys.exit("not a git repository")

    start = args.frm or last_tag()
    rng = f"{start}..{args.to}" if start else args.to
    changes = collect(rng)

    today = datetime.date.today().isoformat()
    section = render(changes, args.version, today)

    if args.dry_run:
        sys.stdout.write(section)
        return
    write_out(args.output, section)
    total = sum(len(v) for v in changes.values())
    print(f"wrote {args.output} — {total} commits since {start or 'the beginning'}")


if __name__ == "__main__":
    main()
