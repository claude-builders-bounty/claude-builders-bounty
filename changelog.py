#!/usr/bin/env python3
import subprocess, sys, datetime

def run(cmd, cwd="."):
    r = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
    return r.stdout.strip()

def categorize(commit):
    cl = commit.lower()
    if any(x in cl for x in ["feat", "add", "new", "implement"]): return "Added"
    if any(x in cl for x in ["fix", "bug", "patch"]): return "Fixed"
    if any(x in cl for x in ["refactor", "change", "update", "improve"]): return "Changed"
    if any(x in cl for x in ["rem", "del", "drop", "deprecate"]): return "Removed"
    return "Other"

def main():
    repo = sys.argv[1] if len(sys.argv) > 1 else "."
    outfile = sys.argv[2] if len(sys.argv) > 2 else "CHANGELOG.md"
    last = run("git describe --tags --abbrev=0 2>/dev/null", repo)
    if last:
        commits = run("git log " + last + "..HEAD --pretty=format:(s=", repo).split(chr(10))
        version = last
    else:
        commits = run("git log --pretty=format:%s -n 50", repo).split(chr(10))
        version = "unreleased"
    commits = [c for c in commits if c.strip()]
    cats = {"Added": [], "Fixed": [], "Changed": [], "Removed": [], "Other": []}
    for c in commits:
        cats[categorize(c)].append(c)
    today = datetime.date.today().isoformat()
    out = ["# Changelog", "## [" + version + "] - " + today, ""]
    for name in ["Added", "Fixed", "Changed", "Removed"]:
        if cats[name]:
            out.append("### " + name)
            for x in cats[name]: out.append("- " + x)
            out.append("")
    if cats["Other"]:
        out.append("### Other")
        for x in cats["Other"]: out.append("- " + x)
        out.append("")
    open(outfile, "w", encoding="utf-8").write(chr(10).join(out))
    print("Generated " + outfile + " with " + str(len(commits)) + " commits")

if __name__ == "__main__":
    main()
