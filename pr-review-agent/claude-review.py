#!/usr/bin/env python3
"""claude-review — Analyze a GitHub PR diff and produce a structured review comment.
Usage: python claude-review.py --pr https://github.com/owner/repo/pull/123
"""
import subprocess, sys, re, argparse, os, tempfile
from pathlib import Path

def run(cmd, timeout=30):
    try:
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        r = subprocess.run(cmd, capture_output=True, timeout=timeout, cwd=os.getcwd(), env=env)
        out = r.stdout.decode("utf-8", errors="replace") if r.stdout else ""
        return out.strip() if r.returncode == 0 else ""
    except:
        return ""

def parse_diff(diff_text):
    files = []
    current_file = None
    for line in diff_text.split('\n'):
        if line.startswith('diff --git'):
            if current_file:
                files.append(current_file)
            current_file = {"path": "", "adds": 0, "dels": 0,
                           "hunks": 0, "risks": [], "ext": ""}
            parts = line.split(' ')
            if len(parts) >= 4:
                current_file["path"] = parts[3][2:]  # b/path
                ext = Path(current_file["path"]).suffix.lower()
                current_file["ext"] = ext
        elif current_file and line.startswith('+') and not line.startswith('+++'):
            current_file["adds"] += 1
        elif current_file and line.startswith('-') and not line.startswith('---'):
            current_file["dels"] += 1
        elif current_file and line.startswith('@@'):
            current_file["hunks"] += 1
    if current_file:
        files.append(current_file)
    return files

def analyze(files, diff_text):
    total_adds = sum(f["adds"] for f in files)
    total_dels = sum(f["dels"] for f in files)
    changed_files = len(files)

    risks = []
    suggestions = []
    confidence = "High"

    # Size-based risks
    if changed_files > 20:
        risks.append(f"**Large PR:** {changed_files} files changed. Consider splitting into smaller PRs.")
        confidence = "Low"
    elif changed_files > 10:
        risks.append(f"**Medium-sized PR:** {changed_files} files. Review each file carefully.")
        confidence = "Medium"

    if total_adds > 500:
        risks.append(f"**High churn:** {total_adds} lines added. Risk of unintended side effects.")
        confidence = "Low" if confidence != "Low" else "Low"

    # File type risks
    risky_exts = {".env": "Environment file", ".sql": "SQL migration",
                  ".py": None, ".js": None, ".ts": None}
    for f in files:
        if f["ext"] in (".sql",) and f["adds"] + f["dels"] > 20:
            risks.append(f"**SQL change:** `{f['path']}` ({f['adds']}+/ {f['dels']}-). Verify migration is reversible.")
        if f["ext"] in (".env", ".env.local", ".env.production"):
            risks.append(f"**Secrets file:** `{f['path']}` — ensure no credentials are committed.")

    # Security patterns
    SEC_PATTERNS = {
        r"exec\s*\(": ("potential code injection", "exec()"),
        r"eval\s*\(": ("potential code injection", "eval()"),
        r"subprocess\.(call|run|Popen)": ("shell execution", "subprocess"),
        r"innerHTML\s*=": ("XSS sink (innerHTML)", "DOM manipulation"),
        r"console\.log\s*\(.*(token|password|secret|key)": ("credential leak in logs", "console.log"),
    }
    for f in files:
        for pattern, (risk, name) in SEC_PATTERNS.items():
            if re.search(pattern, diff_text, re.IGNORECASE):
                if f"{risk} in `{f['path']}`" not in [r for r in risks]:
                    risks.append(f"**Security:** {risk} detected — `{name}` in `{f['path']}`.")

    # Suggestions
    if any(f["ext"] in (".test.ts", ".test.js", ".spec.ts", ".spec.js", "_test.py", "test_") for f in files):
        suggestions.append("Tests included — verify CI passes before merging.")
    else:
        suggestions.append("**No test files detected.** Consider adding tests for the changed logic.")

    if total_adds > 100:
        suggestions.append("Consider adding a CHANGELOG entry or updating documentation for this change.")

    # Summary
    file_summary = ", ".join(f"{f['path']} ({f['adds']}+/{f['dels']}-)" for f in files[:5])
    if changed_files > 5:
        file_summary += f", and {changed_files - 5} more"

    summary = (f"This PR changes {changed_files} file(s) with {total_adds} additions "
               f"and {total_dels} deletions.")

    return {
        "summary": summary,
        "files_changed": changed_files,
        "lines_added": total_adds,
        "lines_deleted": total_dels,
        "risks": risks if risks else ["No significant risks identified."],
        "suggestions": suggestions if suggestions else ["No specific suggestions."],
        "confidence": confidence,
        "file_summary": file_summary,
    }

def format_report(result, pr_url):
    lines = [
        f"# PR Review: {pr_url}",
        "",
        f"**Confidence:** {result['confidence']}",
        "",
        "## Summary",
        result["summary"],
        "",
        f"**Files:** {result['files_changed']} | **+{result['lines_added']}** / **-{result['lines_deleted']}**",
        "",
        "### Changed Files",
        result["file_summary"],
        "",
        "## Risks Identified",
    ]
    for r in result["risks"]:
        lines.append(f"- {r}")
    lines.extend(["", "## Suggestions", ""])
    for s in result["suggestions"]:
        lines.append(f"- {s}")
    lines.extend(["", "---", "*Generated by claude-review agent*"])
    return "\n".join(lines)

def main():
    p = argparse.ArgumentParser(description="PR review agent")
    p.add_argument("--pr", required=True, help="GitHub PR URL")
    args = p.parse_args()

    pr = args.pr.rstrip("/")
    print(f"Analyzing: {pr}")

    diff = run(["gh", "pr", "diff", pr])
    if not diff:
        print("Failed to fetch PR diff. Check gh CLI auth and URL.")
        sys.exit(1)

    files = parse_diff(diff)
    if not files:
        print("No changed files detected.")
        sys.exit(0)

    result = analyze(files, diff)
    report = format_report(result, pr)

    output_file = "PR_REVIEW.md"
    Path(output_file).write_text(report, encoding="utf-8")
    print(report)
    print(f"\nReport saved to: {output_file}")

if __name__ == "__main__":
    main()
