#!/usr/bin/env bash
# The shell entry point can be copied into any repository.
exec python3 - "$@" <<'PY'
import argparse
import html
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile

parser = argparse.ArgumentParser(prog="changelog.sh")
parser.add_argument("--stdout", action="store_true", help="preview the generated Markdown")
args = parser.parse_args()


def git(*arguments):
    return subprocess.check_output(["git", *arguments])


def category(subject):
    prefix = re.match(r"^([a-z]+)(?:\([^)]*\))?!?:\s*(.*)$", subject, re.I)
    kind, text = (prefix[1].lower(), prefix[2]) if prefix else ("", subject)
    if kind in {"fix", "bugfix", "hotfix"}:
        return "Fixed"
    if kind in {"remove", "removed", "drop"} or re.match(r"(?:remove[ds]?|drop(?:ped)?|delete[ds]?)\b", text, re.I):
        return "Removed"
    if kind == "feat" or re.match(r"(?:add(?:s|ed)?|introduce[ds]?)\b", text, re.I):
        return "Added"
    if re.match(r"(?:fix(?:es|ed)?|repair(?:s|ed)?)\b", text, re.I):
        return "Fixed"
    return "Changed"


def render():
    if git("rev-parse", "--is-shallow-repository").strip() == b"true":
        raise ValueError("Complete the checkout first with git fetch --unshallow --tags.")
    # Use the full ref in the range so a tag may share a branch's name.
    tag = subprocess.run(["git", "describe", "--tags", "--abbrev=0", "HEAD"],
                         stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    start = tag.stdout.rstrip(b"\r\n").decode() if tag.returncode == 0 else ""
    revision = f"refs/tags/{start}..HEAD" if start else "HEAD"
    log = git("log", "--no-merges", "--reverse", "-z", "--format=%H%x00%s", revision, "--")
    fields = log.rstrip(b"\0").split(b"\0") if log else []
    sections = {name: [] for name in ("Added", "Fixed", "Changed", "Removed")}
    for i in range(0, len(fields), 2):
        commit = fields[i].decode("ascii")
        subject = fields[i + 1].decode("utf-8", errors="replace") if i + 1 < len(fields) else ""
        # Treat subjects as text, even when a contributor used Markdown or HTML.
        escaped = re.sub(r"([\\`*_\[\]~|])", r"\\\1", html.escape(subject, quote=False))
        sections[category(subject)].append(f"- {escaped or '(no subject)'} (`{commit[:12]}`)")
    lines = ["## Unreleased"]
    for name, entries in sections.items():
        if entries:
            lines += ["", f"### {name}", "", *entries]
    if not any(sections.values()):
        lines += ["", "No changes since the latest tag."]
    return "\n".join(lines)


begin = "<!-- changelog.sh:begin -->"
end = "<!-- changelog.sh:end -->"


def save(path, block):
    if path.is_symlink():
        raise ValueError(f"Refusing to replace symlink {path}. Use --stdout to preview.")
    if path.exists():
        old = path.read_bytes()
        newline = b"\r\n" if b"\r\n" in old else b"\n"
        markers = list(re.finditer(rb"(?m)^<!-- changelog\.sh:(begin|end) -->\r?$", old))
        if [m[1] for m in markers] != [b"begin", b"end"]:
            raise ValueError(f"{path} has no unique managed block. Use --stdout to preview.")
        # Leave the user's surrounding commentary and release history byte-for-byte intact.
        closing = markers[1].end() - int(markers[1][0].endswith(b"\r"))
        data = old[:markers[0].start()] + block.encode().replace(b"\n", newline) + old[closing:]
        if data == old:
            return
    else:
        data = ("# Changelog\n\n" + block + "\n").encode()
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as f:
        tmp = Path(f.name)
    try:
        tmp.write_bytes(data)
        if path.exists():
            tmp.chmod(stat.S_IMODE(path.stat().st_mode))
        os.replace(tmp, path)
    finally:
        tmp.unlink(missing_ok=True)


try:
    root = Path(os.fsdecode(git("rev-parse", "--show-toplevel").rstrip(b"\r\n")))
    content = render()
    block = "\n".join([begin, content, end])
    if args.stdout:
        sys.stdout.buffer.write(("# Changelog\n\n" + block + "\n").encode())
    else:
        save(root / "CHANGELOG.md", block)
except (OSError, ValueError, subprocess.CalledProcessError) as err:
    sys.exit(str(err))
PY
