#!/usr/bin/env python3
import argparse
import datetime as dt
import subprocess
from pathlib import Path


def git(repo, *args):
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        return ""
    return completed.stdout.strip()


def latest_tag(repo):
    return git(repo, "describe", "--tags", "--abbrev=0")


def initial_commit(repo):
    return git(repo, "rev-list", "--max-parents=0", "HEAD").splitlines()[0]


def commit_range(repo, since):
    if since:
        return f"{since}..HEAD"
    first = initial_commit(repo)
    return f"{first}..HEAD"


def commits_since(repo, since):
    range_ref = commit_range(repo, since)
    output = git(repo, "log", "--no-merges", "--pretty=format:%H%x1f%s", range_ref)
    if not output and not since:
        output = git(repo, "log", "--no-merges", "--pretty=format:%H%x1f%s", "HEAD")
    commits = []
    for line in output.splitlines():
        if "\x1f" not in line:
            continue
        sha, subject = line.split("\x1f", 1)
        commits.append({"sha": sha[:7], "subject": subject.strip()})
    return commits


def category_for(subject):
    lowered = subject.lower().strip()
    padded = f" {lowered} "
    prefix = lowered.split(":", 1)[0]
    if prefix.startswith("feat") or any(word in padded for word in [" add ", " added ", " new ", " create ", " introduce "]):
        return "Added"
    if prefix.startswith("fix") or any(word in padded for word in [" bug ", " patch ", " resolve ", " repair "]):
        return "Fixed"
    if prefix.startswith("remove") or any(word in padded for word in [" remove ", " delete ", " drop ", " deprecate "]):
        return "Removed"
    return "Changed"


def grouped_commits(commits):
    groups = {name: [] for name in ["Added", "Fixed", "Changed", "Removed"]}
    for commit in commits:
        groups[category_for(commit["subject"])].append(commit)
    return groups


def render(version, since, commits):
    today = dt.date.today().isoformat()
    heading = version or "Unreleased"
    lines = [
        "# Changelog",
        "",
        f"## {heading} - {today}",
        "",
    ]
    if since:
        lines.extend([f"_Changes since `{since}`._", ""])
    else:
        lines.extend(["_Changes generated from repository history._", ""])

    groups = grouped_commits(commits)
    for category in ["Added", "Fixed", "Changed", "Removed"]:
        lines.append(f"### {category}")
        entries = groups[category]
        if entries:
            for commit in entries:
                lines.append(f"- {commit['subject']} ({commit['sha']})")
        else:
            lines.append("- None")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def write_changelog(path, content):
    target = Path(path)
    if target.exists():
        existing = target.read_text(encoding="utf-8")
        if existing.startswith("# Changelog\n"):
            rest = existing[len("# Changelog\n"):].lstrip()
            target.write_text("# Changelog\n\n" + "\n".join(content.splitlines()[2:]) + "\n\n" + rest, encoding="utf-8")
            return
    target.write_text(content, encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Generate a structured CHANGELOG.md from git history.")
    parser.add_argument("--repo", default=".", help="Git repository path.")
    parser.add_argument("--output", default="CHANGELOG.md", help="Output changelog path.")
    parser.add_argument("--version", default="Unreleased", help="Version heading.")
    parser.add_argument("--since", default="", help="Override the starting git tag or ref.")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    since = args.since or latest_tag(repo)
    commits = commits_since(repo, since)
    content = render(args.version, since, commits)
    output = Path(args.output)
    if not output.is_absolute():
        output = repo / output
    write_changelog(output, content)
    print(f"Wrote {output}")
    print(f"Included {len(commits)} commits")


if __name__ == "__main__":
    main()
