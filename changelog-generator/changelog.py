"""Generate a deterministic changelog snapshot from local Git history."""

import argparse
import html
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile


SECTIONS = ("Added", "Fixed", "Changed", "Removed")


class ChangelogError(Exception):
    pass


def git(repo, *args, allowed=(0,)):
    env = os.environ.copy()
    for name in ("GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR"):
        env.pop(name, None)
    result = subprocess.run(
        ["git", "--no-pager", "-C", str(repo), "-c", "log.showSignature=false", *args],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, check=False,
    )
    if result.returncode not in allowed:
        message = result.stderr.decode("utf-8", "replace").strip()
        raise ChangelogError(message or "Git could not read the repository.")
    return result


def text(repo, *args):
    value = git(repo, *args).stdout.decode("utf-8", "replace")
    return value[:-1] if value.endswith("\n") else value


def category(subject):
    conventional = re.match(r"^([a-z]+)(?:\([^\r\n]*?\))?!?:\s+", subject, re.I)
    word = conventional.group(1).lower() if conventional else re.split(r"[\s:]+", subject.lower(), 1)[0]
    if word in {"feat", "feature", "add", "adds", "added", "create", "creates", "created"}:
        return "Added"
    if word in {"fix", "fixes", "fixed", "bugfix", "repair", "repairs", "resolve", "resolves", "resolved"}:
        return "Fixed"
    if word in {"remove", "removes", "removed", "delete", "deletes", "deleted", "drop", "drops", "dropped"}:
        return "Removed"
    # Reverts may restore functionality: do not automatically call them removals.
    return "Changed"


def markdown(value):
    value = " ".join(value.split())
    value = html.escape(value, quote=False)
    return re.sub(r"([\\`*_{}\[\]#!|])", r"\\\1", value)


def snapshot(repo):
    root = Path(text(repo, "rev-parse", "--show-toplevel"))
    if text(root, "rev-parse", "--is-shallow-repository") == "true":
        raise ChangelogError("Shallow history cannot establish the last tag; fetch complete history and tags first.")
    head_result = git(root, "rev-parse", "--verify", "HEAD^{commit}", allowed=(0, 128))
    head = head_result.stdout.decode("ascii").strip()
    if head_result.returncode:
        if text(root, "for-each-ref", "--format=%(refname)"):
            raise ChangelogError("HEAD does not identify a commit; existing refs were not used as a substitute.")
        head = None
    tag = None
    commits = []
    if head:
        if text(root, "tag", "--merged", head):
            tag = text(root, "describe", "--tags", "--abbrev=0", head)
            boundary = text(root, "rev-parse", "--verify", "refs/tags/" + tag + "^{commit}")
            revision = boundary + ".." + head
        else:
            revision = head
        raw = git(root, "log", "--encoding=UTF-8", "--topo-order", "--reverse", "-z",
                  "--format=%H%x00%s", revision, "--").stdout
        fields = raw.split(b"\0")
        if fields[-1] == b"":
            fields.pop()
        if len(fields) % 2:
            raise ChangelogError("Unexpected Git log record format.")
        for offset in range(0, len(fields), 2):
            commit = fields[offset].decode("ascii")
            if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", commit):
                raise ChangelogError("Unexpected Git commit identifier.")
            subject = fields[offset + 1].decode("utf-8", "replace") or "(empty commit subject)"
            commits.append((commit, subject))
    groups = {section: [] for section in SECTIONS}
    for commit, subject in commits:
        groups[category(subject)].append(f"- {markdown(subject)} (`{commit[:12]}`)")
    lines = ["# Changelog", "", "## Unreleased", ""]
    if tag:
        lines.append(f"Since tag **{markdown(tag)}** (exclusive), through `{head}`.")
    elif head:
        lines.append(f"No reachable tag; all commits through `{head}`.")
    else:
        lines.append("This repository has no commits yet.")
    lines.extend(["", f"{len(commits)} commit(s). Oldest first within each section.", ""])
    for section in SECTIONS:
        lines.extend(["### " + section, "", *(groups[section] or ["- None."]), ""])
    return root, "\n".join(lines)


def write_snapshot(root, output, content):
    target = Path(output)
    if not target.is_absolute():
        target = root / target
    if target.is_symlink():
        raise ChangelogError("Refusing to replace a symbolic-link output file.")
    target = target.resolve()
    if target == root / ".git":
        raise ChangelogError("Output must not replace Git's metadata pointer.")
    for option in ("--absolute-git-dir", "--git-common-dir"):
        directory = Path(text(root, "rev-parse", option))
        if not directory.is_absolute():
            directory = root / directory
        directory = directory.resolve()
        if target == directory or directory in target.parents:
            raise ChangelogError("Output must not be inside Git's metadata directory.")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n",
                                         dir=target.parent, prefix=".changelog-", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(content)
        if target.exists():
            mode = stat.S_IMODE(target.stat().st_mode)
        else:
            umask = os.umask(0)
            os.umask(umask)
            mode = 0o666 & ~umask
        os.chmod(temporary, mode)
        os.replace(temporary, target)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()
    return target


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".", help="repository or its subdirectory (default: current directory)")
    parser.add_argument("--output", default="CHANGELOG.md", help="output path, relative to repository root unless absolute")
    args = parser.parse_args()
    try:
        root, content = snapshot(args.repo)
        target = write_snapshot(root, args.output, content)
    except (ChangelogError, OSError, UnicodeError) as error:
        print(f"changelog: {error}", file=sys.stderr)
        return 1
    print(f"Wrote {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
