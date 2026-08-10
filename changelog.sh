#!/usr/bin/env bash
#
# changelog.sh — generate a structured CHANGELOG.md from git history.
#
# Collects the commits made since the last git tag, sorts them into
# Added / Fixed / Changed / Removed, and writes a Keep a Changelog section.
#
# Usage: bash changelog.sh [options]
# Run `bash changelog.sh --help` for the full option list.

set -euo pipefail

VERSION="1.0.0"

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------
REPO_DIR="."
FROM_REF=""
TO_REF="HEAD"
OUTPUT="CHANGELOG.md"
RELEASE=""
TO_STDOUT=0
SHOW_AUTHORS=0
SKIP_CHORE=0
FORCE=0

US=$'\x1f' # field separator inside a commit record
RS=$'\x1e' # record separator between commits

usage() {
  cat <<'EOF'
changelog.sh — generate a structured CHANGELOG.md from git history

USAGE
  bash changelog.sh [options]

OPTIONS
  -C, --repo <path>      Repository to read (default: current directory)
  -f, --from <ref>       Start of the range (default: most recent git tag)
  -t, --to <ref>         End of the range (default: HEAD)
  -o, --output <file>    File to write (default: CHANGELOG.md)
  -r, --release <name>   Version heading, e.g. v1.2.0 (default: the tag on
                         --to if there is one, otherwise "Unreleased")
      --stdout           Print the generated section, write nothing
      --authors          Append the commit author to every entry
      --no-chore         Drop chore/ci/build/style/test commits
      --force            Write even if that version heading already exists
  -h, --help             Show this help
  -v, --version          Show the script version

EXAMPLES
  bash changelog.sh                          # since the last tag, into CHANGELOG.md
  bash changelog.sh --stdout                 # preview without touching any file
  bash changelog.sh --from v1.0.0 --to v1.1.0 --release v1.1.0
  bash changelog.sh -C ../some-repo -o ../some-repo/CHANGELOG.md

CATEGORIES
  Added    feat, add, introduce, implement, create, new
  Fixed    fix, bugfix, hotfix, patch, resolve, correct
  Removed  remove, delete, drop, revert, deprecate
  Changed  everything else (refactor, perf, docs, chore, ...)
EOF
}

die() {
  printf 'changelog.sh: %s\n' "$1" >&2
  exit 1
}

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------
while [ $# -gt 0 ]; do
  case "$1" in
    -C|--repo)    [ $# -ge 2 ] || die "$1 needs a value"; REPO_DIR="$2"; shift 2 ;;
    -f|--from)    [ $# -ge 2 ] || die "$1 needs a value"; FROM_REF="$2"; shift 2 ;;
    -t|--to)      [ $# -ge 2 ] || die "$1 needs a value"; TO_REF="$2"; shift 2 ;;
    -o|--output)  [ $# -ge 2 ] || die "$1 needs a value"; OUTPUT="$2"; shift 2 ;;
    -r|--release) [ $# -ge 2 ] || die "$1 needs a value"; RELEASE="$2"; shift 2 ;;
    --stdout)     TO_STDOUT=1; shift ;;
    --authors)    SHOW_AUTHORS=1; shift ;;
    --no-chore)   SKIP_CHORE=1; shift ;;
    --force)      FORCE=1; shift ;;
    -h|--help)    usage; exit 0 ;;
    -v|--version) printf 'changelog.sh %s\n' "$VERSION"; exit 0 ;;
    *)            die "unknown option: $1 (try --help)" ;;
  esac
done

command -v git >/dev/null 2>&1 || die "git is not installed or not on PATH"
[ -d "$REPO_DIR" ] || die "no such directory: $REPO_DIR"

# Resolve the output path before changing directory, so a relative --output
# stays relative to where the user actually ran the script.
case "$OUTPUT" in
  /*|[A-Za-z]:[\\/]*) ;;
  *) OUTPUT="$PWD/$OUTPUT" ;;
esac

cd "$REPO_DIR"
git rev-parse --is-inside-work-tree >/dev/null 2>&1 \
  || die "$REPO_DIR is not a git repository"
git rev-parse --verify --quiet "$TO_REF" >/dev/null \
  || die "unknown ref: $TO_REF"

# ---------------------------------------------------------------------------
# Work out the commit range
# ---------------------------------------------------------------------------
if [ -z "$FROM_REF" ]; then
  # The newest tag reachable from --to; empty when the repo has no tags yet.
  FROM_REF="$(git describe --tags --abbrev=0 "$TO_REF" 2>/dev/null || true)"
  # If --to is itself a tag, start from the tag before it instead of from
  # itself, otherwise the range would always be empty.
  if [ -n "$FROM_REF" ] && \
     [ "$(git rev-parse "$FROM_REF")" = "$(git rev-parse "$TO_REF")" ]; then
    FROM_REF="$(git describe --tags --abbrev=0 "${FROM_REF}^" 2>/dev/null || true)"
  fi
elif ! git rev-parse --verify --quiet "$FROM_REF" >/dev/null; then
  die "unknown ref: $FROM_REF"
fi

if [ -n "$FROM_REF" ]; then
  RANGE="${FROM_REF}..${TO_REF}"
  SINCE_LABEL="$FROM_REF"
else
  RANGE="$TO_REF"
  SINCE_LABEL="the first commit"
fi

# ---------------------------------------------------------------------------
# Version heading and date
# ---------------------------------------------------------------------------
if [ -z "$RELEASE" ]; then
  RELEASE="$(git describe --exact-match --tags "$TO_REF" 2>/dev/null || true)"
  [ -n "$RELEASE" ] || RELEASE="Unreleased"
fi

if [ "$RELEASE" = "Unreleased" ]; then
  RELEASE_DATE="$(date +%Y-%m-%d)"
else
  RELEASE_DATE="$(git log -1 --format=%ad --date=short "$TO_REF" 2>/dev/null || date +%Y-%m-%d)"
fi

# ---------------------------------------------------------------------------
# Remote URL, used to link each entry to its commit
# ---------------------------------------------------------------------------
REPO_URL=""
remote_url="$(git config --get remote.origin.url 2>/dev/null || true)"
if [ -n "$remote_url" ]; then
  case "$remote_url" in
    git@*)  REPO_URL="https://${remote_url#git@}"; REPO_URL="${REPO_URL/://}" ;;
    ssh://git@*) REPO_URL="https://${remote_url#ssh://git@}" ;;
    http://*|https://*) REPO_URL="$remote_url" ;;
  esac
  REPO_URL="${REPO_URL%.git}"
  REPO_URL="${REPO_URL%/}"
fi

# ---------------------------------------------------------------------------
# Categorisation
# ---------------------------------------------------------------------------
ADDED=(); FIXED=(); CHANGED=(); REMOVED=()

# Echoes added | fixed | removed | "" based on the leading verb of a subject.
verb_bucket() {
  local lower
  lower="$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')"
  case "$lower" in
    add\ *|adds\ *|added\ *|introduce*|implement*|create\ *|support\ *|new\ *)
      printf 'added' ;;
    fix\ *|fixes\ *|fixed\ *|correct*|resolve*|repair*|patch\ *|hotfix*)
      printf 'fixed' ;;
    remove*|delete*|drop\ *|drops\ *|revert*|deprecate*|strip\ *|retire*)
      printf 'removed' ;;
  esac
}

# Reads a commit subject, echoes one of: added | fixed | changed | removed | skip
categorize() {
  local subject="$1" body="$2" type="" rest="$1" guess=""

  # Conventional commit prefix: type(scope)!: subject
  if [[ "$subject" =~ ^([a-zA-Z]+)(\([^\)]*\))?!?:[[:space:]]* ]]; then
    type="$(printf '%s' "${BASH_REMATCH[1]}" | tr '[:upper:]' '[:lower:]')"
    rest="${subject#"${BASH_REMATCH[0]}"}"
  fi

  case "$type" in
    feat|feature|add|added|new)  printf 'added'; return ;;
    fix|bugfix|hotfix|patch)     printf 'fixed'; return ;;
    remove|removed|delete|drop|revert|deprecate)
                                 printf 'removed'; return ;;
    chore|ci|build|style|test|tests)
      [ "$SKIP_CHORE" -eq 0 ] || { printf 'skip'; return ; } ;;
  esac

  # Unclassified type (chore, refactor, docs, perf, ...) or no prefix at all:
  # let the leading verb of the actual subject decide.
  guess="$(verb_bucket "$rest")"
  if [ -n "$guess" ]; then printf '%s' "$guess"; return; fi

  # A body announcing a breaking removal is still a removal.
  case "$body" in
    *BREAKING*remove*|*BREAKING*delete*) printf 'removed'; return ;;
  esac

  printf 'changed'
}

# Strips the conventional prefix, capitalises, drops the trailing period.
clean_subject() {
  local s="$1"
  if [[ "$s" =~ ^[a-zA-Z]+(\([^\)]*\))?!?:[[:space:]]* ]]; then
    s="${s#"${BASH_REMATCH[0]}"}"
  fi
  s="${s#"${s%%[![:space:]]*}"}" # trim leading whitespace
  s="${s%"${s##*[![:space:]]}"}" # trim trailing whitespace
  s="${s%.}"
  [ -n "$s" ] || return 0
  printf '%s%s' "$(printf '%s' "${s:0:1}" | tr '[:lower:]' '[:upper:]')" "${s:1}"
}

is_breaking() {
  local subject="$1" body="$2"
  [[ "$subject" =~ ^[a-zA-Z]+(\([^\)]*\))?!: ]] && return 0
  case "$subject$body" in *BREAKING\ CHANGE*|*BREAKING-CHANGE*) return 0 ;; esac
  return 1
}

COUNT=0
while IFS="$US" read -r -d "$RS" hash subject author body; do
  hash="${hash//[$'\n\r']/}"
  [ -n "$hash" ] || continue
  [ -n "$subject" ] || continue

  bucket="$(categorize "$subject" "$body")"
  [ "$bucket" != "skip" ] || continue

  text="$(clean_subject "$subject")"
  [ -n "$text" ] || continue

  is_breaking "$subject" "$body" && text="**BREAKING** $text"

  if [ -n "$REPO_URL" ]; then
    entry="- ${text} ([\`${hash}\`](${REPO_URL}/commit/${hash}))"
  else
    entry="- ${text} (\`${hash}\`)"
  fi
  [ "$SHOW_AUTHORS" -eq 0 ] || entry="${entry} — ${author}"

  case "$bucket" in
    added)   ADDED+=("$entry") ;;
    fixed)   FIXED+=("$entry") ;;
    removed) REMOVED+=("$entry") ;;
    *)       CHANGED+=("$entry") ;;
  esac
  COUNT=$((COUNT + 1))
done < <(git log --no-merges --reverse \
           --pretty=format:"%h${US}%s${US}%an${US}%b${RS}" "$RANGE")

if [ "$COUNT" -eq 0 ]; then
  printf 'changelog.sh: no commits between %s and %s — nothing to do.\n' \
    "$SINCE_LABEL" "$TO_REF" >&2
  exit 0
fi

# ---------------------------------------------------------------------------
# Render the section
# ---------------------------------------------------------------------------
SECTION="$(mktemp)"
trap 'rm -f "$SECTION"' EXIT

if [ "$RELEASE" = "Unreleased" ]; then
  HEADING="## [Unreleased] - ${RELEASE_DATE}"
else
  HEADING="## [${RELEASE}] - ${RELEASE_DATE}"
fi

{
  printf '%s\n\n' "$HEADING"
  for section in Added Changed Fixed Removed; do
    case "$section" in
      Added)   entries=("${ADDED[@]+"${ADDED[@]}"}") ;;
      Changed) entries=("${CHANGED[@]+"${CHANGED[@]}"}") ;;
      Fixed)   entries=("${FIXED[@]+"${FIXED[@]}"}") ;;
      Removed) entries=("${REMOVED[@]+"${REMOVED[@]}"}") ;;
    esac
    [ "${#entries[@]}" -gt 0 ] || continue
    printf '### %s\n\n' "$section"
    printf '%s\n' "${entries[@]}"
    printf '\n'
  done
} > "$SECTION"

if [ "$TO_STDOUT" -eq 1 ]; then
  cat "$SECTION"
  printf 'changelog.sh: %d commits since %s.\n' "$COUNT" "$SINCE_LABEL" >&2
  exit 0
fi

# ---------------------------------------------------------------------------
# Write the file — new section on top, existing history preserved
# ---------------------------------------------------------------------------
PREAMBLE="$(cat <<'EOF'
# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

EOF
)"

if [ ! -f "$OUTPUT" ]; then
  { printf '%s\n\n' "$PREAMBLE"; cat "$SECTION"; } > "$OUTPUT"
  printf 'changelog.sh: created %s (%d commits since %s).\n' \
    "$OUTPUT" "$COUNT" "$SINCE_LABEL" >&2
  exit 0
fi

if [ "$FORCE" -eq 0 ] && grep -Fq "$HEADING" "$OUTPUT"; then
  die "$OUTPUT already contains \"$HEADING\" — use --force to add it anyway"
fi

MERGED="$(mktemp)"
trap 'rm -f "$SECTION" "$MERGED"' EXIT

# Insert before the first existing "## " heading; append if there is none.
if grep -q '^## ' "$OUTPUT"; then
  awk -v section="$SECTION" '
    /^## / && !done { while ((getline line < section) > 0) print line; done = 1 }
    { print }
  ' "$OUTPUT" > "$MERGED"
else
  { cat "$OUTPUT"; printf '\n'; cat "$SECTION"; } > "$MERGED"
fi

cat "$MERGED" > "$OUTPUT"
printf 'changelog.sh: updated %s (%d commits since %s).\n' \
  "$OUTPUT" "$COUNT" "$SINCE_LABEL" >&2
