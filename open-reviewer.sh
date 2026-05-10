#!/bin/bash
# open-reviewer — Multi-Agent PR Review with Confidence Scoring
# Zero API keys required. Uses static analysis only.
set -eo pipefail

VERSION="1.0.0"
TMP="${TMPDIR:-/tmp}"
PID=$$

echo "🦞 Open-Reviewer v$VERSION — Multi-Agent PR Review"
echo ""

PR_REF="${1:-}"; REPO="${2:-}"; OUT="${3:-}"
while [ $# -gt 0 ]; do
  case "$1" in --pr) PR_REF="$2"; shift;; --repo) REPO="$2"; shift;; --output) OUT="$2"; shift;; --help|-h) echo "Usage: $0 --pr <url|num> [--repo owner/repo] [--output prefix]"; exit 0;; esac; shift
done

if echo "$PR_REF" | grep -qE '^https?://'; then
  REPO=$(echo "$PR_REF" | sed -E 's|https?://github.com/||;s|/pull/[0-9]+.*||')
  PR_NUM=$(echo "$PR_REF" | sed -E 's|.*/pull/||;s|/.*||')
elif echo "$PR_REF" | grep -qE '^[0-9]+$'; then PR_NUM="$PR_REF"
fi
[ -z "${REPO:-}" ] || [ -z "${PR_NUM:-}" ] && echo "Usage: $0 --pr https://github.com/owner/repo/pull/123" && exit 1
OUT="${OUT:-open_review_${PR_NUM}}"

echo "🔍 PR #$PR_NUM @ $REPO"
echo "📡 Fetching..."

PR_DATA=$(curl -s "https://api.github.com/repos/$REPO/pulls/$PR_NUM" 2>/dev/null || echo "{}")
echo "$PR_DATA" > "$TMP/_or_pr_$PID.json"
PR_DIFF=$(curl -s -H "Accept: application/vnd.github.v3.diff" "https://api.github.com/repos/$REPO/pulls/$PR_NUM" 2>/dev/null || echo "")
echo "$PR_DIFF" > "$TMP/_or_diff_$PID.txt"

# === Python Analysis Engine ===
python3 << PYEOF
import json, os, re, sys

pid = $PID; tmp = "$TMP"; repo = "$REPO"; pr_num = $PR_NUM

try:
    with open(f"{tmp}/_or_pr_{pid}.json") as f: pr = json.load(f)
    with open(f"{tmp}/_or_diff_{pid}.txt") as f: diff = f.read()
except: sys.exit(1)

# Stats
lines = diff.count('\n')
files_chg = len(re.findall(r'^diff --git', diff, re.M))
test_changes = len(re.findall(r'(?i)^\+.*test|spec|__test__', diff))

# = Agent 1: Security =
sec = []
for sev, pats in [
  ("CRITICAL", [(r'(?i)SELECT.*FROM|INSERT.*INTO|DROP\s+TABLE', 'SQL statement'),
                 (r'innerHTML|outerHTML', 'XSS injection')]),
  ("HIGH",    [(r'(?i)(password|secret|api_key|auth_token|private_key)\s*=', 'Credential hardcoded'),
               (r'eval\(|system\(|popen\(', 'Code execution')]),
  ("MEDIUM",  [(r'console\.log|console\.error', 'Debug output'),
               (r'localhost|127\.0\.0\.1', 'Hardcoded address')]),
  ("LOW",     [(r'TODO|FIXME|HACK', 'Todo markers')])
]:
    for pat, desc in pats:
        c = len(re.findall(pat, diff))
        if c: sec.append({"severity": sev, "desc": desc, "count": c})

# = Agent 2: Code Quality =
qual = []
for sev, pats in [
  ("HIGH",   [(r'(?i)^\+.*null|None', 'Null/None handling')]),
  ("MEDIUM", [(r'except:|catch\s*\(', 'Exception handling'),
              (r'^\+.*console\.log|console\.error', 'Debug leftover')])
]:
    for pat, desc in pats:
        c = len(re.findall(pat, diff))
        if c: qual.append({"severity": sev, "desc": desc, "count": c})

if lines > 1000: qual.append({"severity": "HIGH", "desc": f"Large diff ({lines} lines)", "count": 1})
if test_changes == 0 and lines > 50: qual.append({"severity": "MEDIUM", "desc": "No tests", "count": 1})

# Score
sp = 0 if lines < 100 else (0.05 if lines < 500 else (0.10 if lines < 1000 else 0.20))
fp = sum(f["count"] * (0.03 if f["severity"] in ("CRITICAL",) else 0.02) for f in sec)
fp += sum(f["count"] * (0.03 if f["severity"] in ("HIGH",) else 0.015) for f in qual)
fp = min(round(fp, 2), 0.3)
conf = max(round(0.85 - sp - fp, 2), 0.1)
label = "HIGH" if conf >= 0.7 else ("MEDIUM" if conf >= 0.4 else "LOW")

r = {
    "version": "$VERSION", "repository": repo, "pr_number": pr_num,
    "pr_title": pr.get("title", ""),
    "stats": {"diff_lines": lines, "files_changed": files_chg, "test_changes": test_changes,
              "additions": pr.get("additions", 0), "deletions": pr.get("deletions", 0),
              "changed_files": pr.get("changed_files", 0)},
    "reviews": {"security": {"findings": sec}, "code_quality": {"findings": qual}},
    "confidence": {"score": conf, "label": label, "formula": f"base(0.85)-sp({sp})-fp({fp})"}, "size_penalty": sp, "finding_penalty": fp
}

with open(f"{tmp}/_or_result_{pid}.json", "w") as f:
    json.dump(r, f, indent=2, ensure_ascii=False)

with open(f"{tmp}/_or_env_{pid}.sh", "w") as f:
    f.write(f"CONFIDENCE={conf}\nCONFIDENCE_LABEL={label}\nLINES={lines}\n")
    f.write(f"SEC_COUNT={len(sec)}\nQUAL_COUNT={len(qual)}\nSP={sp}\nFP={fp}\n")

print(f"  ✦ {files_chg} files, {lines} lines")
print(f"  ✦ Security: {len(sec)} finding(s) | Quality: {len(qual)} finding(s)")
print(f"  ✦ Confidence: {conf} ({label})")
PYEOF

# Load results
source "$TMP/_or_env_$PID.sh" 2>/dev/null || true
cp "$TMP/_or_result_$PID.json" "${OUT}.json" 2>/dev/null || true

# === Markdown Generation (Python) ===
python3 << PYEOF
import json, os
r = json.load(open("${TMP}/_or_result_${PID}.json"))
md = []
md.append(f"# Open-Reviewer — PR Review #{r['pr_number']}")
md.append("")
md.append(f"**Repository:** {r['repository']}")
md.append(f"**PR:** {r.get('pr_title', 'N/A')}")
s = r['stats']
md.append(f"**Changes:** +{s['additions']}/-{s['deletions']} across {s['changed_files']} files")
md.append(f"**Confidence:** {r['confidence']['score']} ({r['confidence']['label']})")
md.append("")
md.append("---")
md.append("")

md.append("## 🔒 Security Review (Agent 1)")
md.append("")
sec = r['reviews']['security']['findings']
if sec:
    for f in sec: md.append(f"- [{f['severity']}] {f['desc']} ({f['count']}x)")
else:
    md.append("No security issues detected.")
md.append("")

md.append("## 📐 Code Quality Review (Agent 2)")
md.append("")
qual = r['reviews']['code_quality']['findings']
if qual:
    for f in qual: md.append(f"- [{f['severity']}] {f['desc']} ({f['count']}x)")
else:
    md.append("No quality issues detected.")
md.append("")

if not r["stats"].get("test_changes", 0) and s['diff_lines'] > 50:
    md.append("**💡 Suggestion:** Add test coverage for new/modified functionality.")
    md.append("")

md.append("## 📊 Confidence Assessment")
md.append("")
md.append("| Metric | Value |")
md.append("|--------|-------|")
md.append(f"| Base | 0.85 |")
md.append(f"| Size Penalty | {r['confidence'].get('size_penalty', 0)} ({s['diff_lines']} lines) |")
md.append(f"| Finding Penalty | {r['confidence'].get('finding_penalty', 0)} |")
md.append(f"| **Final Score** | **{r['confidence']['score']} ({r['confidence']['label']})** |")
md.append("")
md.append("### What This Means")
if r['confidence']['label'] == 'HIGH':
    md.append("Clean, focused PR. Quick review recommended.")
elif r['confidence']['label'] == 'MEDIUM':
    md.append("Moderate risk — spot-check flagged areas.")
else:
    md.append("Large/risky change — thorough manual review required.")
md.append("")
md.append(f"_Generated by Open-Reviewer v$VERSION on $(date '+%Y-%m-%d %H:%M') — Zero API keys_")

with open("${OUT}.md", "w") as f:
    f.write('\n'.join(md))
print("✅ Markdown output generated")
PYEOF

echo ""
echo "📄 ${OUT}.md"
echo "📊 ${OUT}.json"
echo ""

# Cleanup
rm -f "$TMP/_or_pr_$PID.json" "$TMP/_or_diff_$PID.txt" "$TMP/_or_env_$PID.sh" "$TMP/_or_result_$PID.json" 2>/dev/null || true
