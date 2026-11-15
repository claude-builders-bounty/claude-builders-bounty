#!/usr/bin/env python3
"""Claude Builders Bounty #3 (PreToolUse Bash Safety Hook) & #1 (Git Changelog Generator)."""
import argparse, datetime as dt, json, re, subprocess, sys

RULES = [
    ("CC-BASH-001", "Recursive forced deletion on root/home/wildcard", re.compile(r"(?:^|[;&|]\s*|\bsudo\s+)rm\s+(?:-[a-zA-Z]*[rf][a-zA-Z]*\s+|--(?:recursive|force|no-preserve-root)\s+)+(?:/(?:\s|$|\*)|~(?:/|\s|$)|\$HOME\b|\.\.(?:/|\s|$)|\*)", re.I)),
    ("CC-BASH-002", "Filesystem format or raw block device write", re.compile(r"(?:^|[;&|]\s*|\bsudo\s+)(?:mkfs(?:\.[a-z0-9]+)?\b|wipefs\b|dd\s+[^;&|]*\bof=/dev/(?:sd[a-z]|nvme\d+n\d+|vd[a-z]|disk\d+))", re.I)),
    ("CC-BASH-003", "Shell fork bomb", re.compile(r":\s*\(\s*\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", re.I)),
    ("CC-BASH-004", "Remote script piped to shell", re.compile(r"\b(?:curl|wget)\b[^|;&]*\|\s*(?:sudo\s+)?(?:ba|z|da|k)?sh\b", re.I)),
    ("CC-BASH-005", "Force push to main/master", re.compile(r"\bgit\s+push\b(?=[^;&|]*(?:--force(?!-with-lease)|-f\b))(?=[^;&|]*\b(?:main|master)\b)", re.I)),
    ("CC-BASH-006", "Recursive chmod 777 on root", re.compile(r"(?:^|[;&|]\s*|\bsudo\s+)chmod\s+(?:-[a-zA-Z]*R[a-zA-Z]*\s+)?777\s+/(?:\s|$|[a-zA-Z])", re.I)),
    ("CC-BASH-007", "Destructive SQL statement", re.compile(r"\b(?:DROP\s+(?:DATABASE|SCHEMA|TABLE)|TRUNCATE\s+TABLE)\b", re.I)),
]

def evaluate_bash(cmd: str) -> dict:
    hits = [{"id": r[0], "desc": r[1]} for r in RULES if r[2].search(cmd.strip())]
    if hits:
        return {"decision": "block", "allowed": False, "violations": hits, "command": cmd.strip()}
    return {"decision": "approve", "allowed": True, "violations": [], "command": cmd.strip()}

def generate_changelog(repo_path: str = ".") -> str:
    proc = subprocess.run(["git", "-C", repo_path, "log", "--max-count=100", "--date=short", "--pretty=format:%h|%ad|%an|%s"], capture_output=True, text=True)
    lines = ["# Changelog", "", f"## [Unreleased] - {dt.date.today().isoformat()}", ""]
    for row in proc.stdout.splitlines():
        if "|" in row:
            sha, date_s, author, subj = row.split("|", 3)
            lines.append(f"- {subj} (`{sha}` by {author}, {date_s})")
    return "\n".join(lines)

def run_hook() -> int:
    if len(sys.argv) > 1 and sys.argv[1] == "changelog":
        print(generate_changelog(sys.argv[2] if len(sys.argv) > 2 else "."))
        return 0
    raw = sys.stdin.read().strip()
    if not raw:
        return 0
    payload = json.loads(raw)
    cmd = str((payload.get("tool_input") or {}).get("command", ""))
    res = evaluate_bash(cmd)
    if not res["allowed"]:
        print(json.dumps(res), file=sys.stderr)
        return 2
    print(json.dumps(res))
    return 0

if __name__ == "__main__":
    sys.exit(run_hook())
