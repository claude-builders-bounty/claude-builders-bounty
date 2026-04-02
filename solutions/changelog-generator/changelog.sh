#!/usr/bin/env bash
# changelog.sh — Generate a structured CHANGELOG.md from git history
# Usage: bash changelog.sh [options]
#
# Options:
#   -o, --output FILE    Output file (default: CHANGELOG.md)
#   -f, --from REF       Start ref — tag or commit (default: auto-detect last tag)
#   -t, --to REF         End ref (default: HEAD)
#   -r, --repo DIR       Repository path (default: current directory)
#   -v, --version VER    Version label for this release (default: auto from tag/date)
#       --stdout         Print to stdout instead of file
#       --prepend        Prepend to existing CHANGELOG instead of overwriting
#   -h, --help           Show this help message

set -euo pipefail

# ── Defaults ─────────────────────────────────────────────────────────────────
OUTPUT="CHANGELOG.md"
FROM_REF=""
TO_REF="HEAD"
REPO_DIR="."
VERSION=""
TO_STDOUT=false
PREPEND=false

# ── Helpers ──────────────────────────────────────────────────────────────────
die()  { printf "Error: %s\n" "$1" >&2; exit 1; }
info() { printf "• %s\n" "$1" >&2; }

usage() {
  sed -n '3,/^$/s/^# \?//p' "$0"
  exit 0
}

# ── Argument parsing ─────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    -o|--output)   OUTPUT="$2";   shift 2 ;;
    -f|--from)     FROM_REF="$2"; shift 2 ;;
    -t|--to)       TO_REF="$2";   shift 2 ;;
    -r|--repo)     REPO_DIR="$2"; shift 2 ;;
    -v|--version)  VERSION="$2";  shift 2 ;;
    --stdout)      TO_STDOUT=true; shift ;;
    --prepend)     PREPEND=true;  shift ;;
    -h|--help)     usage ;;
    *)             die "Unknown option: $1" ;;
  esac
done

# ── Validate ─────────────────────────────────────────────────────────────────
cd "$REPO_DIR" || die "Cannot access repo at '$REPO_DIR'"
git rev-parse --is-inside-work-tree &>/dev/null || die "Not a git repository: $(pwd)"

# ── Resolve commit range ────────────────────────────────────────────────────
resolve_from_ref() {
  if [[ -n "$FROM_REF" ]]; then
    git rev-parse --verify "$FROM_REF" &>/dev/null || die "Invalid ref: $FROM_REF"
    echo "$FROM_REF"
    return
  fi

  # Try to find the latest tag reachable from $TO_REF
  local latest_tag
  latest_tag=$(git describe --tags --abbrev=0 "$TO_REF" 2>/dev/null || true)

  if [[ -n "$latest_tag" ]]; then
    # If TO_REF IS the tag itself, go one tag further back
    local tag_commit to_commit
    tag_commit=$(git rev-list -n1 "$latest_tag" 2>/dev/null)
    to_commit=$(git rev-list -n1 "$TO_REF" 2>/dev/null)

    if [[ "$tag_commit" == "$to_commit" ]]; then
      local prev_tag
      prev_tag=$(git describe --tags --abbrev=0 "${latest_tag}^" 2>/dev/null || true)
      if [[ -n "$prev_tag" ]]; then
        echo "$prev_tag"
        return
      fi
      # No previous tag — use root
      echo ""
      return
    fi
    echo "$latest_tag"
    return
  fi

  # No tags at all — use root of history
  echo ""
}

FROM_REF=$(resolve_from_ref)

if [[ -n "$FROM_REF" ]]; then
  RANGE="${FROM_REF}..${TO_REF}"
  info "Changelog range: $FROM_REF → $TO_REF"
else
  RANGE="$TO_REF"
  info "Changelog range: (repo root) → $TO_REF (no prior tags found)"
fi

# ── Resolve version label ───────────────────────────────────────────────────
if [[ -z "$VERSION" ]]; then
  # Try: tag at TO_REF → next logical version → date-based
  VERSION=$(git tag --points-at "$TO_REF" 2>/dev/null | head -n1 || true)
  if [[ -z "$VERSION" ]]; then
    local_latest=$(git describe --tags --abbrev=0 "$TO_REF" 2>/dev/null || true)
    if [[ -n "$local_latest" ]]; then
      # Bump patch: v1.2.3 → v1.2.4 (Unreleased)
      if [[ "$local_latest" =~ ^v?([0-9]+)\.([0-9]+)\.([0-9]+)(.*)$ ]]; then
        prefix=""
        [[ "$local_latest" == v* ]] && prefix="v"
        major="${BASH_REMATCH[1]}"
        minor="${BASH_REMATCH[2]}"
        patch="${BASH_REMATCH[3]}"
        VERSION="${prefix}${major}.${minor}.$((patch + 1))"
      else
        VERSION="$local_latest-next"
      fi
      VERSION="$VERSION (Unreleased)"
    else
      VERSION="$(date +%Y-%m-%d) (Unreleased)"
    fi
  fi
fi

DATE=$(date +%Y-%m-%d)

# ── Collect commits ─────────────────────────────────────────────────────────
# Format: HASH|SUBJECT
# We filter out merge commits for cleaner output
SEPARATOR="◆"
RAW_LOG=$(git log --no-merges --pretty=format:"%H${SEPARATOR}%s" "$RANGE" -- 2>/dev/null || true)

if [[ -z "$RAW_LOG" ]]; then
  info "No commits found in range. Nothing to generate."
  exit 0
fi

COMMIT_COUNT=$(echo "$RAW_LOG" | wc -l | tr -d ' ')
info "Processing $COMMIT_COUNT commit(s)…"

# ── Categorize commits ──────────────────────────────────────────────────────
# Strategy:
#   1. Conventional Commits prefix (feat:, fix:, etc.) — highest priority
#   2. Keyword heuristics on the subject line — fallback
#   3. Uncategorized → "Changed" bucket

declare -a ADDED=()
declare -a FIXED=()
declare -a CHANGED=()
declare -a REMOVED=()
declare -a SECURITY=()
declare -a DEPRECATED=()

categorize_commit() {
  local hash="$1"
  local subject="$2"
  local short_hash="${hash:0:7}"

  # Strip scope: "feat(auth): ..." → clean subject is "..."
  local clean_subject="$subject"
  local category=""

  # ── 1. Conventional Commits ──
  # Match: type[(scope)][!]: description
  if [[ "$subject" =~ ^([a-zA-Z]+)(\(.+\))?(!)?\:\ (.+)$ ]]; then
    local cc_type="${BASH_REMATCH[1],,}"  # lowercase
    local breaking="${BASH_REMATCH[3]}"
    clean_subject="${BASH_REMATCH[4]}"

    # Capitalize first letter of description
    clean_subject="$(echo "${clean_subject:0:1}" | tr '[:lower:]' '[:upper:]')${clean_subject:1}"

    case "$cc_type" in
      feat|feature|add)       category="added" ;;
      fix|bugfix|hotfix)      category="fixed" ;;
      refactor|perf|style|chore|build|ci|test|tests|docs)
                              category="changed" ;;
      remove|deprecate)       category="removed" ;;
      security|sec)           category="security" ;;
      revert)                 category="changed" ;;
      *)                      category="" ;;  # fall through to heuristics
    esac

    # Breaking changes always get extra visibility
    if [[ "$breaking" == "!" ]]; then
      clean_subject="**BREAKING:** $clean_subject"
    fi
  fi

  # ── 2. Keyword heuristics (fallback) ──
  if [[ -z "$category" ]]; then
    local lower_subject="${subject,,}"

    # Added
    if [[ "$lower_subject" =~ ^(add|added|create|created|implement|implemented|introduce|new|support) ]] ||
       [[ "$lower_subject" =~ (add|added|create|implement|introduce|new\ feature|support\ for) ]]; then
      category="added"
    # Fixed
    elif [[ "$lower_subject" =~ ^(fix|fixed|bugfix|hotfix|resolve|resolved|patch|repair|correct) ]] ||
         [[ "$lower_subject" =~ (fix|fixed|bug\ fix|bugfix|resolve|patch|correct|repair) ]]; then
      category="fixed"
    # Removed
    elif [[ "$lower_subject" =~ ^(remove|removed|delete|deleted|drop|dropped|deprecate|deprecated) ]] ||
         [[ "$lower_subject" =~ (remove|delete|drop|deprecate|clean\ ?up|prune) ]]; then
      category="removed"
    # Security
    elif [[ "$lower_subject" =~ (security|vulnerab|cve-|csrf|xss|injection|auth\ fix|patch\ vuln) ]]; then
      category="security"
    # Changed (broad fallback patterns)
    elif [[ "$lower_subject" =~ ^(update|updated|upgrade|upgraded|refactor|improve|improved|optimize|rename|move|migrate|change|changed|modify|bump|rev) ]] ||
         [[ "$lower_subject" =~ (update|upgrade|refactor|improve|optimize|rename|move|migrate|change|modify|rework|restructure|reorganize|simplify|enhance) ]]; then
      category="changed"
    else
      # Default bucket
      category="changed"
    fi

    # Capitalize first letter
    clean_subject="$(echo "${clean_subject:0:1}" | tr '[:lower:]' '[:upper:]')${clean_subject:1}"
  fi

  # ── 3. Format entry ──
  local entry="- ${clean_subject} (\`${short_hash}\`)"

  case "$category" in
    added)      ADDED+=("$entry") ;;
    fixed)      FIXED+=("$entry") ;;
    changed)    CHANGED+=("$entry") ;;
    removed)    REMOVED+=("$entry") ;;
    security)   SECURITY+=("$entry") ;;
    deprecated) DEPRECATED+=("$entry") ;;
  esac
}

# Parse each commit
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  hash="${line%%${SEPARATOR}*}"
  subject="${line#*${SEPARATOR}}"
  categorize_commit "$hash" "$subject"
done <<< "$RAW_LOG"

# ── Build CHANGELOG content ─────────────────────────────────────────────────
CHANGELOG=""

append_section() {
  local title="$1"
  shift
  local -a items=("$@")

  if [[ ${#items[@]} -gt 0 ]]; then
    CHANGELOG+="### ${title}"$'\n\n'
    for item in "${items[@]}"; do
      CHANGELOG+="${item}"$'\n'
    done
    CHANGELOG+=$'\n'
  fi
}

CHANGELOG="# Changelog"$'\n\n'
CHANGELOG+="All notable changes to this project will be documented in this file."$'\n\n'
CHANGELOG+="The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),"$'\n'
CHANGELOG+="and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html)."$'\n\n'
CHANGELOG+="## [${VERSION}] — ${DATE}"$'\n\n'

append_section "Added"      "${ADDED[@]+"${ADDED[@]}"}"
append_section "Fixed"      "${FIXED[@]+"${FIXED[@]}"}"
append_section "Changed"    "${CHANGED[@]+"${CHANGED[@]}"}"
append_section "Removed"    "${REMOVED[@]+"${REMOVED[@]}"}"
append_section "Security"   "${SECURITY[@]+"${SECURITY[@]}"}"
append_section "Deprecated" "${DEPRECATED[@]+"${DEPRECATED[@]}"}"

# Stats footer
TOTAL=$((${#ADDED[@]} + ${#FIXED[@]} + ${#CHANGED[@]} + ${#REMOVED[@]} + ${#SECURITY[@]} + ${#DEPRECATED[@]}))
CHANGELOG+="---"$'\n\n'
CHANGELOG+="*Generated by [changelog.sh](https://github.com) — ${TOTAL} commits categorized "
CHANGELOG+="(${#ADDED[@]} added, ${#FIXED[@]} fixed, ${#CHANGED[@]} changed, ${#REMOVED[@]} removed)*"$'\n'

# ── Output ───────────────────────────────────────────────────────────────────
if [[ "$TO_STDOUT" == true ]]; then
  echo "$CHANGELOG"
else
  if [[ "$PREPEND" == true && -f "$OUTPUT" ]]; then
    # Prepend new release to existing changelog
    # Find the first "## [" line (start of previous release) and insert before it
    EXISTING=$(cat "$OUTPUT")
    # Remove the header (first 5 lines: title + description + format note)
    RELEASE_BLOCK="## [${VERSION}] — ${DATE}"$'\n\n'

    for section_name in "Added" "Fixed" "Changed" "Removed" "Security" "Deprecated"; do
      case "$section_name" in
        Added)      arr=("${ADDED[@]+"${ADDED[@]}"}") ;;
        Fixed)      arr=("${FIXED[@]+"${FIXED[@]}"}") ;;
        Changed)    arr=("${CHANGED[@]+"${CHANGED[@]}"}") ;;
        Removed)    arr=("${REMOVED[@]+"${REMOVED[@]}"}") ;;
        Security)   arr=("${SECURITY[@]+"${SECURITY[@]}"}") ;;
        Deprecated) arr=("${DEPRECATED[@]+"${DEPRECATED[@]}"}") ;;
      esac
      if [[ ${#arr[@]} -gt 0 ]]; then
        RELEASE_BLOCK+="### ${section_name}"$'\n\n'
        for item in "${arr[@]}"; do
          RELEASE_BLOCK+="${item}"$'\n'
        done
        RELEASE_BLOCK+=$'\n'
      fi
    done

    # Insert after the header block (after the semver line)
    if grep -q "^## \[" "$OUTPUT"; then
      # Has existing releases — insert before first one
      awk -v block="$RELEASE_BLOCK" '
        /^## \[/ && !done { print block; done=1 }
        { print }
      ' "$OUTPUT" > "${OUTPUT}.tmp" && mv "${OUTPUT}.tmp" "$OUTPUT"
    else
      # No existing releases — just append
      echo "" >> "$OUTPUT"
      echo "$RELEASE_BLOCK" >> "$OUTPUT"
    fi
    info "Prepended release to $OUTPUT"
  else
    echo "$CHANGELOG" > "$OUTPUT"
    info "Written to $OUTPUT"
  fi
fi

info "Done! ✅"
