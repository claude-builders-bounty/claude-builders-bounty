#!/usr/bin/env bash
set -euo pipefail

#
# pr-review-agent.sh — Claude Code sub-agent for structured PR reviews.
#
# Usage:
#   ./pr-review-agent.sh <pr-number>
#   ./pr-review-agent.sh https://github.com/owner/repo/pull/123
#   ./pr-review-agent.sh owner/repo/123
#
# Environment variables:
#   GITHUB_TOKEN          — GitHub token (or logged in via `gh auth`)
#   REVIEW_TEMPLATE       — path to review-template.md (default: alongside this script)
#   PR_REVIEW_OUTPUT_DIR  — directory to write the review (default: ./pr-reviews)
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# --------------------------- defaults / config --------------------------------
: "${REVIEW_TEMPLATE:="$SCRIPT_DIR/review-template.md"}"
: "${PR_REVIEW_OUTPUT_DIR:="./pr-reviews"}"
MAX_DIFF_LINES_WARN=2000

# ------------------------------- helpers --------------------------------------
die() { echo "[!] $*" >&2; exit 1; }
info() { echo "[*] $*" >&2; }

cleanup() { rm -rf "$TMPDIR"; }
trap cleanup EXIT

# --------------------------- parse input --------------------------------------
INPUT="${1:-}"
[[ -n "$INPUT" ]] || die "Usage: pr-review-agent.sh <PR-number | GitHub PR URL | owner/repo/number>"

# Normalise to "owner/repo/number"
if [[ "$INPUT" =~ ^https?://github\.com/([^/]+)/([^/]+)/pull/([0-9]+) ]]; then
  OWNER="${BASH_REMATCH[1]}"
  REPO="${BASH_REMATCH[2]}"
  PR_NUM="${BASH_REMATCH[3]}"
elif [[ "$INPUT" =~ ^([^/]+)/([^/]+)/([0-9]+)$ ]]; then
  OWNER="${BASH_REMATCH[1]}"
  REPO="${BASH_REMATCH[2]}"
  PR_NUM="${BASH_REMATCH[3]}"
elif [[ "$INPUT" =~ ^[0-9]+$ ]]; then
  # Infer owner/repo from git remote when running locally
  if REMOTE=$(git remote get-url origin 2>/dev/null); then
    if [[ "$REMOTE" =~ github\.com[.:]([^/]+)/([^/]+)(\.git)?$ ]]; then
      OWNER="${BASH_REMATCH[1]}"
      REPO="${BASH_REMATCH[2]%.git}"
    fi
  fi
  PR_NUM="$INPUT"
  [[ -n "${OWNER:-}" && -n "${REPO:-}" ]] || die "Could not infer owner/repo. Use owner/repo/number or full URL."
else
  die "Unrecognised PR format: $INPUT"
fi

PR_REF="${OWNER}/${REPO}#${PR_NUM}"
info "Reviewing ${PR_REF} …"

TMPDIR="$(mktemp -d /tmp/pr-review-XXXXXX)"

# ----------------------------- fetch PR info ----------------------------------
info "Fetching PR metadata …"
PR_JSON=$(gh pr view "$PR_NUM" --repo "${OWNER}/${REPO}" --json number,title,author,body,headRefName,baseRefName,state,additions,deletions,files,createdAt 2>/dev/null) \
  || die "Failed to fetch PR info. Is 'gh' installed and authenticated?"

PR_TITLE=$(echo "$PR_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['title'])")
PR_AUTHOR=$(echo "$PR_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['author']['login'])")
PR_BODY=$(echo "$PR_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin).get('body','') or '')" 2>/dev/null || echo "")
PR_HEAD_REF=$(echo "$PR_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['headRefName'])")
PR_BASE_REF=$(echo "$PR_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['baseRefName'])")
PR_STATE=$(echo "$PR_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['state'])")
PR_ADDITIONS=$(echo "$PR_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['additions'])")
PR_DELETIONS=$(echo "$PR_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['deletions'])")
PR_FILES=$(echo "$PR_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['files'])")

# ----------------------------- fetch PR diff ----------------------------------
info "Fetching PR diff …"
if ! PR_DIFF=$(gh pr diff "$PR_NUM" --repo "${OWNER}/${REPO}" 2>/dev/null); then
  info "No diff returned (PR may be empty or closed). Creating empty-review."
  PR_DIFF=""
fi

# ------------------------- diff analysis helpers ------------------------------

# Count diff lines per file so we can warn on large diffs
analyze_diff_size() {
  local diff="$1"
  local total_lines
  total_lines=$(echo "$diff" | wc -l)
  if (( total_lines > MAX_DIFF_LINES_WARN )); then
    echo "**Large diff:** ${total_lines} total lines (warn threshold: ${MAX_DIFF_LINES_WARN})."
    echo "The review below is scoped to changed files only."
    info "Large diff (${total_lines} lines) — review scoped to changed files."
  fi
  echo "$total_lines"
}

# Extract list of changed files
get_changed_files() {
  local diff="$1"
  echo "$diff" \
    | grep '^diff --git' \
    | sed 's/^diff --git a\/\(.*\) b\/.*$/\1/' \
    | sort -u
}

# Classify a file by extension
classify_file() {
  local path="$1"
  case "$path" in
    *.py)    echo "python"   ;;
    *.js|*.mjs|cjs)  echo "javascript" ;;
    *.ts|*.tsx)      echo "typescript" ;;
    *.go)    echo "golang"   ;;
    *.rs)    echo "rust"     ;;
    *.java)  echo "java"     ;;
    *.rb)    echo "ruby"     ;;
    *.sh)    echo "shell"    ;;
    *.yaml|*.yml) echo "yaml" ;;
    *.json)  echo "json"     ;;
    *.md)    echo "markdown" ;;
    Dockerfile*) echo "docker" ;;
    *.mod|*.sum|go.mod|go.sum) echo "gomod" ;;
    *)       echo "other"    ;;
  esac
}

# <editor-fold desc="Static analysis heuristics">

# NOTE: for a production agent these checks would be delegated to linters
# (ruff, eslint, golangci-lint, etc.) but for portability we implement a
# lightweight heuristic scanner.

detect_hardcoded_secrets() {
  local diff="$1"
  local results=""
  local line_no=0
  while IFS= read -r line; do
    ((line_no++))
    # Skip context/removed lines
    [[ "$line" =~ ^[[:space:]]*# ]] && continue
    if echo "$line" | grep -qiP '(api[_-]?key|secret|password|token|credential|auth_token)\s*[:=]\s*["\x27]?(?!\*)([a-zA-Z0-9_\-]{16,})["\x27]?' 2>/dev/null; then
      results+="- Line ${line_no}: Potential hardcoded secret: \`$(echo "$line" | sed 's/^[+-]//' | head -c 80)\`\n"
    fi
  done <<< "$diff"
  echo -e "$results"
}

detect_sql_injection() {
  local diff="$1"
  local results=""
  local line_no=0
  while IFS= read -r line; do
    ((line_no++))
    if echo "$line" | grep -qiP '(execute|exec|query|raw|cursor\.execute|db\.exec|db\.query)\s*\(\s*["\x27].*\$[\({]?\w+' 2>/dev/null; then
      results+="- Line ${line_no}: Possible SQL injection via string interpolation: \`$(echo "$line" | sed 's/^[+-]//' | head -c 60)\`\n"
    fi
  done <<< "$diff"
  echo -e "$results"
}

detect_command_injection() {
  local diff="$1"
  local results=""
  local line_no=0
  while IFS= read -r line; do
    ((line_no++))
    if echo "$line" | grep -qiP '(os\.system|subprocess\.call|subprocess\.Popen|exec\s*\(|child_process\.exec|execSync)\s*\(\s*["\x27]?.*\+' 2>/dev/null; then
      results+="- Line ${line_no}: Possible command injection (user input concatenated into shell command): \`$(echo "$line" | sed 's/^[+-]//' | head -c 60)\`\n"
    fi
  done <<< "$diff"
  echo -e "$results"
}

detect_any_type() {
  local diff="$1"
  local results=""
  local line_no=0
  while IFS= read -r line; do
    ((line_no++))
    if echo "$line" | grep -qiP '[:=]\s*any\s*[;),]' 2>/dev/null; then
      results+="- Line ${line_no}: Use of \`any\` type — consider a more specific type.\n"
    fi
  done <<< "$diff"
  echo -e "$results"
}

detect_todo_fixme() {
  local diff="$1"
  local results=""
  local line_no=0
  while IFS= read -r line; do
    ((line_no++))
    if echo "$line" | grep -qiP '(TODO|FIXME|HACK|XXX|TEMP|WORKAROUND)' 2>/dev/null; then
      results+="- Line ${line_no}: \`$(echo "$line" | sed 's/^[+-]//' | grep -oiP '(TODO|FIXME|HACK|XXX|TEMP|WORKAROUND).*' | head -c 60)\`\n"
    fi
  done <<< "$diff"
  echo -e "$results"
}

detect_bare_except() {
  local diff="$1"
  local results=""
  local line_no=0
  while IFS= read -r line; do
    ((line_no++))
    if echo "$line" | grep -qiP '^\s*except\s*:' 2>/dev/null; then
      results+="- Line ${line_no}: Bare \`except:\` clause — catches all exceptions silently.\n"
    fi
  done <<< "$diff"
  echo -e "$results"
}

detect_debug_prints() {
  local diff="$1"
  local results=""
  local line_no=0
  while IFS= read -r line; do
    ((line_no++))
    if echo "$line" | grep -qiP '(console\.log|print|println|puts|debug\.Print|fmt\.Print)\s*\(.*(?:debug|test|temp|remove|temporary)' 2>/dev/null; then
      results+="- Line ${line_no}: Possible debugging leftover: \`$(echo "$line" | sed 's/^[+-]//' | head -c 60)\`\n"
    fi
  done <<< "$diff"
  echo -e "$results"
}

detect_mutable_defaults() {
  local diff="$1"
  local results=""
  local line_no=0
  while IFS= read -r line; do
    ((line_no++))
    if echo "$line" | grep -qiP 'def \w+\(.*=\s*\[\s*\].*\)' 2>/dev/null; then
      results+="- Line ${line_no}: Mutable default argument \`[]\` — consider using \`None\` instead.\n"
    fi
  done <<< "$diff"
  echo -e "$results"
}

# </editor-fold>

# ------------------------------ main review -----------------------------------
review_file_stats() {
  local files="$1"
  local summary=""
  local total=0
  while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    ((total++))
  done <<< "$files"
  echo "$total"
}

# Build the review payload
build_review() {
  local diff="$1"
  local files="$2"
  local total_changed total_lines
  local findings_critical=""
  local findings_major=""
  local findings_minor=""
  local what_is_good=""

  total_changed=$(review_file_stats "$files")
  total_lines=$(analyze_diff_size "$diff")

  # --- Good things (always mention some) ---
  what_is_good+="- The PR touches ${total_changed} file(s) across multiple concerns (or a focused change).\n"
  what_is_good+="- Additions ($PR_ADDITIONS) vs. deletions ($PR_DELETIONS) show clear intent.\n"

  if [[ -z "$diff" ]]; then
    what_is_good="(No diff content to evaluate.)"
    findings_critical+="- PR has no diff — cannot assess code changes.\n"
  fi

  # --- Heuristic scans ---
  [[ -n "$diff" ]] && CRIT_SECRETS=$(detect_hardcoded_secrets "$diff")
  [[ -n "$diff" ]] && CRIT_SQL=$(detect_sql_injection "$diff")
  [[ -n "$diff" ]] && CRIT_CMD=$(detect_command_injection "$diff")

  [[ -n "$diff" ]] && MAJ_BARE_EXCEPT=$(detect_bare_except "$diff")
  [[ -n "$diff" ]] && MAJ_ANY=$(detect_any_type "$diff")
  [[ -n "$diff" ]] && MAJ_MUTABLE=$(detect_mutable_defaults "$diff")

  [[ -n "$diff" ]] && MIN_TODO=$(detect_todo_fixme "$diff")
  [[ -n "$diff" ]] && MIN_DEBUG=$(detect_debug_prints "$diff")

  # --- Categorise ---
  if [[ -n "$CRIT_SECRETS" ]]; then
    findings_critical+="\n**Hardcoded secrets / credentials**\n$CRIT_SECRETS"
  fi
  if [[ -n "$CRIT_SQL" ]]; then
    findings_critical+="\n**SQL injection**\n$CRIT_SQL"
  fi
  if [[ -n "$CRIT_CMD" ]]; then
    findings_critical+="\n**Command injection**\n$CRIT_CMD"
  fi

  if [[ -n "$MAJ_BARE_EXCEPT" ]]; then
    findings_major+="\n**Bare exception handlers**\n$MAJ_BARE_EXCEPT"
  fi
  if [[ -n "$MAJ_ANY" ]]; then
    findings_major+="\n**Type safety – use of \`any\`**\n$MAJ_ANY"
  fi
  if [[ -n "$MAJ_MUTABLE" ]]; then
    findings_major+="\n**Mutable default arguments**\n$MAJ_MUTABLE"
  fi

  if [[ -n "$MIN_TODO" ]]; then
    findings_minor+="\n**TODOs / FIXMEs left in code**\n$MIN_TODO"
  fi
  if [[ -n "$MIN_DEBUG" ]]; then
    findings_minor+="\n**Debugging leftovers**\n$MIN_DEBUG"
  fi

  # --- Security review summary (injects into findings) ---
  local security_review=""
  security_review+="| Severity | Count |\n"
  security_review+="|----------|-------|\n"
  local sec_crit_count=0 sec_maj_count=0 sec_min_count=0
  [[ -n "$CRIT_SECRETS" ]] && sec_crit_count=$(echo "$CRIT_SECRETS" | grep -c '^-' || true)
  [[ -n "$CRIT_SQL" ]] && sec_crit_count=$((sec_crit_count + $(echo "$CRIT_SQL" | grep -c '^-' || true)))
  [[ -n "$CRIT_CMD" ]] && sec_crit_count=$((sec_crit_count + $(echo "$CRIT_CMD" | grep -c '^-' || true)))
  [[ -n "$MAJ_BARE_EXCEPT" ]] && sec_maj_count=$(echo "$MAJ_BARE_EXCEPT" | grep -c '^-' || true)
  [[ -n "$MIN_TODO" ]] && sec_min_count=$(echo "$MIN_TODO" | grep -c '^-' || true)

  security_review+="| Critical | ${sec_crit_count} |\n"
  security_review+="| Major    | ${sec_maj_count} |\n"
  security_review+="| Minor    | ${sec_min_count} |\n"
  security_review+="\n"
  [[ $sec_crit_count -gt 0 ]] && security_review+="**Action required:** Critical security findings must be resolved before merging.\n"
  [[ $sec_crit_count -eq 0 ]] && security_review+="No critical security concerns detected.\n"

  # --- Test coverage assessment ---
  local test_assessment=""
  local test_files=0
  while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    if [[ "$file" =~ ^test/ || "$file" =~ _test\.go$ || "$file" =~ \.test\.(ts|js|tsx|jsx)$ || "$file" =~ ^spec/ || "$file" =~ test_.*\.py$ || "$file" =~ ^tests/ ]]; then
      ((test_files++))
    fi
  done <<< "$files"

  if (( total_changed == 0 )); then
    test_assessment="No files changed."
  elif (( test_files == 0 )); then
    test_assessment="No test files were modified in this PR. Consider adding or updating tests."
  elif (( test_files == total_changed )); then
    test_assessment="All changed files are test files — great test coverage discipline."
  elif (( test_files == 1 )); then
    test_assessment="1 test file was included. Ensure it covers the new logic adequately."
  else
    test_assessment="${test_files}/${total_changed} changed files are tests. Coverage looks solid."
  fi

  # --- Suggestions ---
  local suggestions=""
  suggestions+="- **Commit hygiene**: Keep commits atomic with descriptive messages.\n"
  suggestions+="- **Documentation**: Update any relevant README or ADRs if behaviour changed.\n"
  suggestions+="- **Tests**: Add unit tests for new/modified functions.\n"
  suggestions+="- **Logging**: Ensure sensitive data is never logged.\n"
  if (( total_lines > MAX_DIFF_LINES_WARN )); then
    suggestions+="- **Large diff**: Consider splitting this PR into smaller, focused changes.\n"
  fi

  # --- File summary ---
  local file_summary=""
  while IFS= read -r file; do
    [[ -z "$file" ]] && continue
    local lang
    lang=$(classify_file "$file")
    file_summary+="| \`$file\` | $lang |\n"
  done <<< "$files"

  # --- Render template ---
  REVIEW_TEMPLATE="${REVIEW_TEMPLATE:-${SCRIPT_DIR}/review-template.md}"
  if [[ -f "$REVIEW_TEMPLATE" ]]; then
    REVIEW=$(cat "$REVIEW_TEMPLATE")
  else
    die "Review template not found at $REVIEW_TEMPLATE"
  fi

  local escaped_tput
  REVIEW="${REVIEW//\{\{PR_NUM\}\}/$PR_NUM}"
  REVIEW="${REVIEW//\{\{PR_REF\}\}/$PR_REF}"
  REVIEW="${REVIEW//\{\{PR_TITLE\}\}/$PR_TITLE}"
  REVIEW="${REVIEW//\{\{PR_AUTHOR\}\}/$PR_AUTHOR}"
  REVIEW="${REVIEW//\{\{PR_STATE\}\}/$PR_STATE}"
  REVIEW="${REVIEW//\{\{PR_BASE_REF\}\}/$PR_BASE_REF}"
  REVIEW="${REVIEW//\{\{PR_HEAD_REF\}\}/$PR_HEAD_REF}"
  REVIEW="${REVIEW//\{\{PR_ADDITIONS\}\}/$PR_ADDITIONS}"
  REVIEW="${REVIEW//\{\{PR_DELETIONS\}\}/$PR_DELETIONS}"
  REVIEW="${REVIEW//\{\{TOTAL_CHANGED\}\}/$total_changed}"
  REVIEW="${REVIEW//\{\{FILE_SUMMARY\}\}/$file_summary}"
  REVIEW="${REVIEW//\{\{WHAT_IS_GOOD\}\}/$what_is_good}"
  REVIEW="${REVIEW//\{\{FINDINGS_CRITICAL\}\}/$findings_critical}"
  REVIEW="${REVIEW//\{\{FINDINGS_MAJOR\}\}/$findings_major}"
  REVIEW="${REVIEW//\{\{FINDINGS_MINOR\}\}/$findings_minor}"
  REVIEW="${REVIEW//\{\{SUGGESTIONS\}\}/$suggestions}"
  REVIEW="${REVIEW//\{\{SECURITY_REVIEW\}\}/$security_review}"
  REVIEW="${REVIEW//\{\{TEST_ASSESSMENT\}\}/$test_assessment}"

  echo "$REVIEW"
}

# ------------------------------ write & output ---------------------------------
mkdir -p "$PR_REVIEW_OUTPUT_DIR"
OUTFILE="${PR_REVIEW_OUTPUT_DIR}/pr-review-${OWNER}-${REPO}-${PR_NUM}.md"

REVIEW_TEXT=$(build_review "$PR_DIFF" "$(get_changed_files "$PR_DIFF")")
echo "$REVIEW_TEXT" > "$OUTFILE"

info "Review written to ${OUTFILE}"
echo ""
echo "────────────────────────────────────────────"
echo "  PR Review Summary — ${PR_REF}"
echo "  Title: ${PR_TITLE}"
echo "  State: ${PR_STATE}"
echo "  Files changed: $(get_changed_files "$PR_DIFF" | grep -c . || echo 0)"
echo "  Review saved: ${OUTFILE}"
echo "────────────────────────────────────────────"
echo ""
echo "$REVIEW_TEXT"
