"""Generate a deterministic, unreleased changelog from local Git history."""
import argparse
import html
from pathlib import Path
import re
import subprocess
import sys

CATEGORIES = ("Added", "Fixed", "Changed", "Removed")
CONVENTIONAL = re.compile(r"^([a-z]+)(?:\([^\r\n)]*\))?!?:", re.I)
VERB = re.compile(r"^(add|adds|added|fix|fixes|fixed|remove|removes|removed)(?=\s|:|$)",
                  re.I)


class GitError(Exception):
    pass


def git(repo, *args):
    result = subprocess.run(["git", "-C", str(repo), *args],
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode:
        raise GitError(result.stderr.decode("utf-8", errors="replace").strip())
    return result.stdout.decode("utf-8", errors="replace").strip()


def category(subject):
    match = VERB.match(subject)
    if match:
        word = match[1].lower()
        if word in ("add", "adds", "added"):
            return "Added"
        if word in ("fix", "fixes", "fixed"):
            return "Fixed"
        return "Removed"
    match = CONVENTIONAL.match(subject)
    if match:
        return {"feat": "Added", "fix": "Fixed", "remove": "Removed"}.get(
            match[1].lower(), "Changed")
    return "Changed"


def markdown(text):
    # Commit messages are content, never Markdown links, HTML, or instructions.
    escaped = html.escape(text, quote=False)
    return re.sub(r"([\\`*_{}\[\]()#+.!|~>\-])", r"\\\1", escaped)


def generate(repo):
    root = Path(git(repo, "rev-parse", "--show-toplevel"))
    if git(root, "rev-parse", "--is-shallow-repository") == "true":
        raise GitError("shallow repository: use a complete local clone with tags")
    head = git(root, "rev-parse", "--verify", "HEAD^{commit}")
    reachable_tags = git(root, "tag", "--merged", head)
    base = None
    if reachable_tags:
        tag = git(root, "describe", "--tags", "--abbrev=0", head)
        base = git(root, "rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}")
    revision = f"{base}..{head}" if base else head
    # NUL is not allowed in normal Git commit messages; no shell parses content.
    log = git(root, "log", "--no-show-signature", "--no-decorate",
              "--reverse", "--topo-order", "--format=%H%x00%s",
              revision, "--")
    groups = {name: [] for name in CATEGORIES}
    for record in log.split("\n") if log else []:
        sha, subject = record.split("\0", 1)
        groups[category(subject)].append(f"- {markdown(subject)} ({sha})")
    start = f"`{base}`" if base else "beginning of history (no reachable tag)"
    lines = ["# CHANGELOG", "", "## Unreleased", "",
             f"From: {start}.", "", f"To: `{head}`.", ""]
    for name in CATEGORIES:
        lines.extend([f"### {name}", "", *(groups[name] or ["- None."]), ""])
    return root, "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd(),
                        help="Git repository (default: current directory)")
    parser.add_argument("--output", type=Path,
                        help="new output file, relative to cwd (default: repo/CHANGELOG.md)")
    args = parser.parse_args()
    try:
        root, content = generate(args.repo)
        output = args.output if args.output is not None else root / "CHANGELOG.md"
        # Exclusive creation also rejects existing symlinks, including dangling ones.
        with output.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
        print(f"Created {output}")
    except (GitError, OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
