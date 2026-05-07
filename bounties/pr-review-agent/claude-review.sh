#!/usr/bin/env bash
set -euo pipefail

# =============================================================================
# claude-review — CLI tool to review GitHub PR diffs
#
# Usage:
#   claude-review --pr https://github.com/owner/repo/pull/123
#   claude-review --pr https://github.com/owner/repo/pull/123 --token ghp_xxx
#   claude-review --pr https://github.com/owner/repo/pull/123 --output review.md
#   claude-review --pr 123 --repo owner/repo
#   claude-review --help
# =============================================================================

VERSION="1.0.0"

# --- helpers ----------------------------------------------------------------
usage() {
  cat <<'USAGE'
claude-review v1.0.0 — GitHub PR Diff Reviewer

Usage:
  claude-review --pr <pr-url>                          Full PR URL
  claude-review --pr <number> --repo <owner/repo>      PR number + repo
  claude-review --pr <number>                          Auto-detect from git remote

Options:
  --pr <url|number>       PR URL or number to review (required)
  --repo <owner/repo>     Repository slug (optional, auto-detected from URL or git remote)
  --token <token>         GitHub personal access token (optional, falls back to GH_TOKEN env var)
  --output <file>         Write review to file (optional, prints to stdout if omitted)
  --help                  Show this help message and exit

Examples:
  claude-review --pr https://github.com/rust-lang/rust/pull/123456
  claude-review --pr 42 --repo torvalds/linux
  claude-review --pr 42 --token ghp_xxxxxxxxxxxx
  claude-review --pr 42 --output review.md

GitHub Action:
  See README.md for GitHub Actions usage instructions.
USAGE
  exit 0
}

die() { echo "❌ $*" >&2; exit 1; }
info() { echo "ℹ️  $*" >&2; }
ok()   { echo "✅ $*" >&2; }
warn() { echo "⚠️  $*" >&2; }

# --- argument parsing -------------------------------------------------------
PR_URL=""
PR_NUMBER=""
REPO=""
TOKEN="${GITHUB_TOKEN:-${GH_TOKEN:-}}"
OUTPUT_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --pr)       PR_URL="$2"; shift 2 ;;
    --repo)     REPO="$2"; shift 2 ;;
    --token)    TOKEN="$2"; shift 2 ;;
    --output)   OUTPUT_FILE="$2"; shift 2 ;;
    --help|-h)  usage ;;
    *)          die "Unknown option: $1. Use --help for usage." ;;
  esac
done

# --- extract repo & PR number -----------------------------------------------
if [[ -n "$PR_URL" ]]; then
  # Try to extract from full URL: https://github.com/owner/repo/pull/123
  if [[ "$PR_URL" =~ ^https?://github\.com/([^/]+)/([^/]+)/pull/([0-9]+) ]]; then
    REPO="${BASH_REMATCH[1]}/${BASH_REMATCH[2]}"
    PR_NUMBER="${BASH_REMATCH[3]}"
  # Also match: https://api.github.com/repos/owner/repo/pulls/123
  elif [[ "$PR_URL" =~ ^https?://api\.github\.com/repos/([^/]+)/([^/]+)/pulls/([0-9]+) ]]; then
    REPO="${BASH_REMATCH[1]}/${BASH_REMATCH[2]}"
    PR_NUMBER="${BASH_REMATCH[3]}"
  else
    # Maybe PR_URL is just a number
    PR_NUMBER="$PR_URL"
  fi
fi

# Auto-detect repo from git remote if not set
if [[ -z "$REPO" ]]; then
  if git rev-parse --git-dir &>/dev/null 2>&1; then
    REMOTE_URL="$(git remote get-url origin 2>/dev/null || true)"
    if [[ "$REMOTE_URL" =~ github\.com[:/]([^/]+)/([^/.]+)(\.git)? ]]; then
      REPO="${BASH_REMATCH[1]}/${BASH_REMATCH[2]}"
      ok "Auto-detected repo: $REPO"
    fi
  fi
fi

[[ -z "$PR_NUMBER" ]] && die "PR number is required. Use --pr <url|number>."
[[ -z "$REPO" ]]     && die "Repository slug is required. Use --repo <owner/repo> or --pr with full URL."
[[ ! "$PR_NUMBER" =~ ^[0-9]+$ ]] && die "PR number must be numeric, got: $PR_NUMBER"

# --- fetch PR data from GitHub API ------------------------------------------
AUTH_HEADER=""
[[ -n "$TOKEN" ]] && AUTH_HEADER="Authorization: Bearer ${TOKEN}"

info "Fetching PR #${PR_NUMBER} from ${REPO} ..."

PR_DATA="$(curl -sS --fail -H "${AUTH_HEADER}" \
  -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/repos/${REPO}/pulls/${PR_NUMBER}" 2>&1)" || {
  die "Failed to fetch PR data from GitHub API. Check your repo/token and network connectivity."
}

# Check for API errors
if echo "$PR_DATA" | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if 'id' in d else 1)" 2>/dev/null; then
  :
else
  ERROR_MSG="$(echo "$PR_DATA" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('message','Unknown API error'))" 2>/dev/null || echo "Unknown API error")"
  die "GitHub API error: ${ERROR_MSG}"
fi

# Extract PR metadata
PR_TITLE="$(echo "$PR_DATA" | python3 -c "import sys,json; print(json.load(sys.stdin)['title'])" 2>/dev/null || echo "Untitled PR")"
PR_BODY="$(echo "$PR_DATA" | python3 -c "import sys,json; print(json.load(sys.stdin).get('body','') or '')" 2>/dev/null || echo "")"
PR_AUTHOR="$(echo "$PR_DATA" | python3 -c "import sys,json; print(json.load(sys.stdin)['user']['login'])" 2>/dev/null || echo "unknown")"
PR_STATE="$(echo "$PR_DATA" | python3 -c "import sys,json; print(json.load(sys.stdin)['state'])" 2>/dev/null || echo "unknown")"
PR_BASE="$(echo "$PR_DATA" | python3 -c "import sys,json; print(json.load(sys.stdin)['base']['ref'])" 2>/dev/null || echo "unknown")"
PR_HEAD="$(echo "$PR_DATA" | python3 -c "import sys,json; print(json.load(sys.stdin)['head']['ref'])" 2>/dev/null || echo "unknown")"
PR_CREATED="$(echo "$PR_DATA" | python3 -c "import sys,json; print(json.load(sys.stdin)['created_at'])" 2>/dev/null || echo "unknown")"
PR_UPDATED="$(echo "$PR_DATA" | python3 -c "import sys,json; print(json.load(sys.stdin)['updated_at'])" 2>/dev/null || echo "unknown")"

ok "Fetched PR metadata: \"${PR_TITLE}\" by @${PR_AUTHOR}"

# --- fetch PR diff ----------------------------------------------------------
info "Fetching PR diff ..."

PR_DIFF="$(curl -sS --fail -H "${AUTH_HEADER}" \
  -H "Accept: application/vnd.github.v3.diff" \
  "https://api.github.com/repos/${REPO}/pulls/${PR_NUMBER}" 2>&1)" || {
  die "Failed to fetch PR diff from GitHub API."
}

DIFF_SIZE="$(echo "$PR_DIFF" | wc -c)"
ok "Fetched diff (${DIFF_SIZE} bytes)"

# --- parse diff into file-level stats ---------------------------------------
# We use python3 for robust diff parsing
PARSE_RESULT="$(python3 <<'PYEOF' 2>/dev/null || echo "PARSE_FAILED"
import sys
import json

diff_text = sys.stdin.read()

files = []
current_file = None
current_lines = []
additions = 0
deletions = 0
total_files = 0

for line in diff_text.split('\n'):
    if line.startswith('diff --git '):
        if current_file is not None:
            files.append({
                'path': current_file,
                'lines': current_lines,
                'additions': additions,
                'deletions': deletions,
            })
        # Parse file path from diff --git a/path b/path
        parts = line.split()
        if len(parts) >= 4:
            current_file = parts[3][2:]  # remove "b/" prefix
        else:
            current_file = "unknown"
        current_lines = []
        additions = 0
        deletions = 0
        total_files += 1
    elif line.startswith('+++') or line.startswith('---'):
        continue
    elif line.startswith('+') and not line.startswith('+++'):
        additions += 1
        current_lines.append(line)
    elif line.startswith('-') and not line.startswith('---'):
        deletions += 1
        current_lines.append(line)
    elif line.startswith('@@'):
        current_lines.append(line)
    elif line.startswith('diff --git'):
        pass
    else:
        current_lines.append(line)

# Don't forget the last file
if current_file is not None:
    files.append({
        'path': current_file,
        'lines': current_lines,
        'additions': additions,
        'deletions': deletions,
    })

# Calculate totals
total_additions = sum(f['additions'] for f in files)
total_deletions = sum(f['deletions'] for f in files)

# Sort files by change magnitude
files.sort(key=lambda f: f['additions'] + f['deletions'], reverse=True)

print(json.dumps({
    'total_files': len(files),
    'total_additions': total_additions,
    'total_deletions': total_deletions,
    'files': files,
    'diff_text': diff_text,
}))
PYEOF
)" <<< "$PR_DIFF"

if [[ "$PARSE_RESULT" == "PARSE_FAILED" ]]; then
  die "Failed to parse diff output."
fi

# --- analysis: deep inspection of changed lines -----------------------------
ANALYSIS="$(python3 <<'PYEOF'
import sys, json, re, os

data = json.loads(sys.stdin.read())
files = data['files']
diff_text = data['diff_text']

# Patterns for risk/suggestion detection
SECRET_PATTERNS = [
    (r'(?i)(?:api[_-]?key|apikey)\s*[=:]\s*["\']?[A-Za-z0-9_\-]{16,}', "Hardcoded API key detected"),
    (r'(?i)(?:secret|password|passwd|pwd|token|credential)\s*[=:]\s*["\']?[A-Za-z0-9_\-\.]{8,}', "Potential hardcoded secret/password"),
    (r'(?i)-----BEGIN\s+(?:RSA|OPENSSH|EC|DSA|PGP)\s+PRIVATE\s+KEY-----', "Embedded private key detected"),
    (r'(?i)ghp_[A-Za-z0-9]{36}', "GitHub Personal Access Token detected"),
    (r'(?i)gho_[A-Za-z0-9]{36}', "GitHub OAuth Access Token detected"),
    (r'(?i)ghu_[A-Za-z0-9]{36}', "GitHub User Token detected"),
    (r'(?i)ghs_[A-Za-z0-9]{36}', "GitHub App Token detected"),
    (r'(?i)ghr_[A-Za-z0-9]{36}', "GitHub Refresh Token detected"),
    (r'(?i)sk-[A-Za-z0-9]{32,}', "OpenAI API key pattern detected"),
    (r'(?i)AKIA[0-9A-Z]{16}', "AWS Access Key ID detected"),
]

SECURITY_RISK_PATTERNS = [
    (r'(?i)(?:exec|system|popen|subprocess\.call|subprocess\.run|os\.system)\s*\(', "Command injection risk — executing shell commands"),
    (r'(?i)eval\s*\(', "Code injection risk — eval() used"),
    (r'(?i)innerHTML\s*=', "XSS risk — innerHTML assignment"),
    (r'(?i)dangerouslySetInnerHTML', "XSS risk — dangerouslySetInnerHTML in React"),
    (r'(?i)raw\(|mark_safe', "XSS risk — marking content as safe HTML"),
    (r'(?i)(?:SELECT|INSERT|UPDATE|DELETE)\s+.*\bWHERE\b.*\+|f(["\'"])', "SQL injection risk — string concatenation in SQL query"),
    (r'(?i)(?:SELECT|INSERT|UPDATE|DELETE)\s+.*[fF][\"\']', "SQL injection risk — f-string in SQL query"),
    (r'(?i)\.exec\(|\.query\(.*\+', "SQL injection risk — raw query execution"),
    (r'(?i)(?:pickle\.loads?|yaml\.load\b)(?!.*SafeLoader)', "Insecure deserialization risk"),
    (r'(?i)\b(strcpy|strcat|sprintf|gets|scanf)\b', "Memory safety risk — unsafe C function"),
    (r'(?i)\$\{.*\}\s*`|`.*\$\{', "Command injection risk — template literal in shell context"),
    (r'(?i)(?:rm\s+-rf|rmdir\s+/[sd]|format\s+|dd\s+if=)', "Destructive operation risk"),
]

QUALITY_PATTERNS = [
    (r'(?i)TODO|FIXME|HACK|XXX|WORKAROUND', "Work-in-progress marker (TODO/FIXME/HACK)"),
    (r'(?i)console\.(log|debug|info|warn|error)\s*\(', "Debug logging left in code (console.*)"),
    (r'(?i)print\(|printf?\s*\(|fmt\.Print', "Debug print statement left in code"),
    (r'(?i)debugger\b', "Debugger statement left in code"),
    (r'(?i)commented.+(?:code|out)|//.*TODO|#.*TODO|<!--.*TODO', "Large commented-out code block"),
    (r'(?i)#\s*(?:TODO|FIXME|HACK)', "TODO/FIXME comment requiring attention"),
    (r'(?i)except\s*:\s*$|catch\s*\{|catch\s*\(', "Bare exception handler (too broad)"),
    (r'(?i)except\s+Exception\s*:\s*pass|catch\s*\{.*\}', "Silently swallowed exception"),
    (r'(?i)(?:type|any|object)\s+\w+\s*=\s*$', "Untyped variable declaration (TypeScript)"),
]

risks = []
suggestions = []
secret_findings = []
quality_findings = []
security_findings = []

per_file_notes = []

for f in files:
    path = f['path']
    added = f['additions']
    removed = f['deletions']
    lines = f['lines']

    file_risks = []
    file_suggestions = []

    # Check file size
    if added > 500:
        file_suggestions.append(f"File `{path}` adds {added} lines — consider splitting into smaller, focused changes for easier review.")

    # Check for binary/file type indicators
    ext = os.path.splitext(path)[1].lower()
    
    # Check for lockfile changes
    if ext in ('.lock', '.sum', '.mod') and added + removed > 10:
        file_suggestions.append(f"Dependency lockfile `{path}` changed — verify no unexpected dependency drift. Consider running `diff` against the base branch lockfile.")

    # Config file changes
    if os.path.basename(path) in ('.env', '.env.example', 'config.yaml', 'config.yml', 'config.json', 'config.toml', 'credentials'):
        file_risks.append(f"Configuration file `{path}` changed — ensure no secrets are committed and verify correctness in all environments.")
    
    # Dockerfile changes
    if os.path.basename(path).startswith('Dockerfile') or path == 'docker-compose.yml' or path == 'docker-compose.yaml':
        file_suggestions.append(f"Container definition `{path}` changed — verify image tags are pinned to specific versions, not `:latest`.")
    
    # CI/CD changes
    if '.github/workflows' in path or 'Jenkinsfile' in path or '.gitlab-ci' in path:
        file_risks.append(f"CI/CD pipeline file `{path}` changed — review for security implications (credential exposure, privilege escalation).")
    
    # Database migration
    if 'migration' in path.lower() or 'migrate' in path.lower() or 'schema' in path.lower():
        file_risks.append(f"Database schema/migration `{path}` changed — ensure backward compatibility and rollback plan.")
        file_suggestions.append(f"Verify that migration `{path}` has a corresponding down-migration for safe rollback.")
    
    # API changes
    if any(p in path.lower() for p in ['api/', 'routes/', 'endpoint', 'controller', 'handler']):
        file_suggestions.append(f"API definition `{path}` changed — verify versioning, backward compatibility, and update API documentation.")

    # Test files
    if 'test' in path.lower() or 'spec' in path.lower() or ext in ('.test.', '.spec.'):
        pass  # Test files are good
    elif added > 0 and not any(p in path.lower() for p in ['test', 'spec', 'doc', 'config', '.md', '.yml', '.yaml', '.json', '.lock']):
        # Check if there are any test changes in the PR
        pass  # We'll note this globally

    # Scan lines for patterns
    for line in lines:
        if line.startswith('+'):
            for pattern, desc in SECRET_PATTERNS:
                if re.search(pattern, line):
                    secret_findings.append((path, line.strip(), desc))
            for pattern, desc in SECURITY_RISK_PATTERNS:
                if re.search(pattern, line):
                    security_findings.append((path, line.strip(), desc))
            for pattern, desc in QUALITY_PATTERNS:
                if re.search(pattern, line):
                    quality_findings.append((path, line.strip(), desc))

    if file_risks:
        risks.extend(file_risks)
    if file_suggestions:
        suggestions.extend(file_suggestions)

# Build the analysis result
result = {
    'risks': risks,
    'suggestions': suggestions,
    'secret_findings': secret_findings,
    'security_findings': security_findings,
    'quality_findings': quality_findings,
}
print(json.dumps(result))
PYEOF
)" <<< "$PARSE_RESULT"

# --- build the Markdown review ----------------------------------------------
# Merge PR metadata with parse results into a clean summary JSON
# Write PR_DATA to temp file to avoid quoting issues
_PR_DATA_FILE="$(mktemp)"
echo "$PR_DATA" > "$_PR_DATA_FILE"
SUMMARY_JSON="$(python3 -c "
import sys, json
with open('${_PR_DATA_FILE}') as f:
    pr_data = json.load(f)
parse_data = json.loads(sys.stdin.read())
summary = {
    'title': pr_data.get('title', ''),
    'author': pr_data.get('user', {}).get('login', 'unknown'),
    'state': pr_data.get('state', 'unknown'),
    'base': pr_data.get('base', {}).get('ref', 'unknown'),
    'head': pr_data.get('head', {}).get('ref', 'unknown'),
    'created': pr_data.get('created_at', 'unknown'),
    'updated': pr_data.get('updated_at', 'unknown'),
    'total_files': parse_data.get('total_files', 0),
    'total_additions': parse_data.get('total_additions', 0),
    'total_deletions': parse_data.get('total_deletions', 0),
    'body_preview': (pr_data.get('body', '') or '')[:500],
}
print(json.dumps(summary))
" <<< "$PARSE_RESULT" 2>/dev/null || echo '{}')"
rm -f "$_PR_DATA_FILE"

# Generate the final Markdown

generate_review() {
  local summary_json="$1"
  local analysis_json="$2"
  local parse_json="$3"

  local title author state base head created updated
  local total_files total_additions total_deletions body_preview

  title=$(echo "$summary_json" | python3 -c "import sys,json; print(json.load(sys.stdin).get('title','Unknown'))" 2>/dev/null || echo "Unknown")
  author=$(echo "$summary_json" | python3 -c "import sys,json; print(json.load(sys.stdin).get('author','unknown'))" 2>/dev/null || echo "unknown")
  state=$(echo "$summary_json" | python3 -c "import sys,json; print(json.load(sys.stdin).get('state','unknown'))" 2>/dev/null || echo "unknown")
  base=$(echo "$summary_json" | python3 -c "import sys,json; print(json.load(sys.stdin).get('base','unknown'))" 2>/dev/null || echo "unknown")
  head=$(echo "$summary_json" | python3 -c "import sys,json; print(json.load(sys.stdin).get('head','unknown'))" 2>/dev/null || echo "unknown")
  created=$(echo "$summary_json" | python3 -c "import sys,json; print(json.load(sys.stdin).get('created','unknown'))" 2>/dev/null || echo "unknown")
  updated=$(echo "$summary_json" | python3 -c "import sys,json; print(json.load(sys.stdin).get('updated','unknown'))" 2>/dev/null || echo "unknown")
  total_files=$(echo "$summary_json" | python3 -c "import sys,json; print(json.load(sys.stdin).get('total_files',0))" 2>/dev/null || echo "0")
  total_additions=$(echo "$summary_json" | python3 -c "import sys,json; print(json.load(sys.stdin).get('total_additions',0))" 2>/dev/null || echo "0")
  total_deletions=$(echo "$summary_json" | python3 -c "import sys,json; print(json.load(sys.stdin).get('total_deletions',0))" 2>/dev/null || echo "0")
  body_preview=$(echo "$summary_json" | python3 -c "import sys,json; print(json.load(sys.stdin).get('body_preview',''))" 2>/dev/null || echo "")

  # Extract analysis components
  local risks suggestions secrets security quality
  risks=$(echo "$analysis_json" | python3 -c "import sys,json; print('\n'.join(f'- {r}' for r in json.load(sys.stdin).get('risks',[])))" 2>/dev/null || echo "- None identified")
  suggestions=$(echo "$analysis_json" | python3 -c "import sys,json; print('\n'.join(f'- {s}' for s in json.load(sys.stdin).get('suggestions',[])))" 2>/dev/null || echo "- None suggested")

  # Secret findings
  secrets=$(echo "$analysis_json" | python3 -c "
import sys, json
data = json.load(sys.stdin)
findings = data.get('secret_findings', [])
if not findings:
    print('  - ✅ No secrets detected.')
else:
    for path, line, desc in findings:
        print(f'  - 🔴 **{desc}** in `{path}`')
        # Truncate line for display
        line_stripped = line.strip()[:120]
        print(f'    ```text')
        print(f'    {line_stripped}')
        print(f'    ```')
" 2>/dev/null || echo "  - No secrets detected.")

  security=$(echo "$analysis_json" | python3 -c "
import sys, json
data = json.load(sys.stdin)
findings = data.get('security_findings', [])
if not findings:
    print('  - ✅ No obvious security anti-patterns detected.')
else:
    for path, line, desc in findings:
        print(f'  - ⚠️  **{desc}** in `{path}`')
        line_stripped = line.strip()[:100]
        print(f'    ```text')
        print(f'    {line_stripped}')
        print(f'    ```')
" 2>/dev/null || echo "  - No security issues detected.")

  quality=$(echo "$analysis_json" | python3 -c "
import sys, json
data = json.load(sys.stdin)
findings = data.get('quality_findings', [])
if not findings:
    print('  - ✅ No code quality issues detected.')
else:
    for path, line, desc in findings:
        print(f'  - 📝 **{desc}** in `{path}`')
        line_stripped = line.strip()[:100]
        print(f'    ```text')
        print(f'    {line_stripped}')
        print(f'    ```')
" 2>/dev/null || echo "  - No quality issues detected.")

  # Build file breakdown
  local file_breakdown=""
  file_breakdown=$(echo "$parse_json" | python3 -c "
import sys, json
data = json.load(sys.stdin)
files = data.get('files', [])
out = []
for f in files[:20]:
    path = f['path']
    a = f['additions']
    d = f['deletions']
    icon = '📝'
    if a == 0 and d > 0:
        icon = '🗑️'
    elif a > 0 and d == 0:
        icon = '✨'
    elif a > d * 2:
        icon = '➕'
    elif d > a * 2:
        icon = '➖'
    elif a + d > 200:
        icon = '📦'
    out.append(f'| {icon} | {path} | +{a}/-{d} |')
if not out:
    out.append('| | No files changed | |')
print('\n'.join(out))
" 2>/dev/null || echo "| | No files changed | |")

  # Generate summary text (2-3 sentences)
  local summary_text
  if [[ "$total_files" -eq 0 ]]; then
    summary_text="No file changes detected in this pull request."
  else
    summary_text="This PR by **@${author}** makes **${total_files}** file change(s) across **${total_additions}** additions and **${total_deletions}** deletions. "
    summary_text+="It targets the **\`${base}\`** branch from **\`${head}\`**. "
    if [[ -n "$body_preview" ]]; then
      # Truncate body for summary
      local body_short="${body_preview:0:200}"
      summary_text+="The description indicates: _${body_short}_"
    fi
  fi

  cat <<REVIEW
# 🔍 PR Review: #${PR_NUMBER} — ${title}

> **Repository:** ${REPO} \\
> **Author:** @${author} \\
> **State:** ${state} \\
> **Branch:** \`${base}\` ← \`${head}\` \\
> **Created:** ${created} \\
> **Updated:** ${updated}

---

## 📋 Summary of Changes

${summary_text}

---

## 📁 Files Changed

| Type | File | +/- |
|------|------|:---:|
${file_breakdown}

---

## 🔴 Identified Risks

### Secrets & Credentials
${secrets}

### Security Anti-Patterns
${security}

### General Risks
${risks:-_None identified._}

---

## 💡 Improvement Suggestions

### Code Quality
${quality}

### Recommendations
${suggestions:-_No specific suggestions._}

---

## 📊 Review Stats

| Metric | Value |
|--------|:-----:|
| Files changed | ${total_files} |
| Lines added | ${total_additions} |
| Lines removed | ${total_deletions} |
| Net change | $(( total_additions - total_deletions )) |

---

<sub>Generated by **claude-review v${VERSION}** · Automated static analysis — does not replace human review.</sub>
REVIEW
}

REVIEW_TEXT="$(generate_review "$SUMMARY_JSON" "$ANALYSIS" "$PARSE_RESULT")"

# --- output ----------------------------------------------------------------
if [[ -n "$OUTPUT_FILE" ]]; then
  echo "$REVIEW_TEXT" > "$OUTPUT_FILE"
  ok "Review written to ${OUTPUT_FILE}"
else
  echo "$REVIEW_TEXT"
fi
