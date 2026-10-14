#!/usr/bin/env bash
# changelog.sh — generate a structured CHANGELOG.md from git history.
#
# Reads commits in a range (default: since the last git tag), categorizes
# them Keep-a-Changelog style (Added / Changed / Deprecated / Removed /
# Fixed / Security) from Conventional Commit prefixes with keyword
# fallbacks for messy messages, and writes or updates a CHANGELOG.md with
# version headings, dates, and compare links when a git remote exists.
#
# Dependencies: git + bash only. No network access is used.
#
# Usage:
#   bash changelog.sh [--version X.Y.Z] [--from REF] [--to REF]
#                     [--output FILE] [--date YYYY-MM-DD] [--repo-url URL]
#                     [--all] [--overwrite] [--stdout]
#
# Default behaviour:
#   * Range is "<last tag>..HEAD" (or the full history when no tag exists).
#   * Heading is "## [Unreleased]", or "## [<version>] - <date>" when
#     --version is given.
#   * If CHANGELOG.md already exists, the new section is inserted under
#     the file's preamble and any compare-link references are refreshed.
#     An existing section for the same version is an error (re-running
#     should never silently duplicate a release) unless --overwrite is
#     passed, which regenerates the file from scratch.
#   * --all generates one section per tag (newest first), plus an
#     Unreleased section when commits exist past the newest tag.
#   * Merge commits, bare version subjects ("1.2.0", "v1.2.0"), and
#     duplicate entries are skipped.

set -o pipefail

PROG="changelog.sh"

err() { printf '%s: %s\n' "$PROG" "$*" >&2; }
die() { err "$*"; exit 1; }

usage() {
  cat <<'EOF'
Usage: bash changelog.sh [options]

Generate a structured CHANGELOG.md from git history.

Options:
  --version X.Y.Z   Version heading for the new section (default: Unreleased)
  --from REF        Start of the commit range (default: last git tag)
  --to REF          End of the commit range (default: HEAD)
  --output FILE     Changelog file to write (default: CHANGELOG.md)
  --date DATE       Release date, YYYY-MM-DD (default: today)
  --repo-url URL    Base repo URL for compare links (default: origin remote)
  --all             Generate sections for every tag, newest first
  --overwrite       Regenerate the output file from scratch
  --stdout          Print to stdout instead of writing the output file
  -h, --help        Show this help

Categories (Keep a Changelog order): Added, Changed, Deprecated, Removed,
Fixed, Security. Conventional Commit types are mapped (feat -> Added,
fix -> Fixed, ...); non-conventional subjects fall back to keyword rules.
EOF
}

# ---------------------------------------------------------------- args ---

VERSION=""
FROM_REF=""
TO_REF="HEAD"
OUTPUT="CHANGELOG.md"
DATE_OVERRIDE=""
REPO_URL=""
ALL=0
OVERWRITE=0
TO_STDOUT=0

while [ $# -gt 0 ]; do
  case "$1" in
    --version)  [ $# -ge 2 ] || die "--version needs a value"; VERSION="$2"; shift 2 ;;
    --from)     [ $# -ge 2 ] || die "--from needs a value"; FROM_REF="$2"; shift 2 ;;
    --to)       [ $# -ge 2 ] || die "--to needs a value"; TO_REF="$2"; shift 2 ;;
    --output)   [ $# -ge 2 ] || die "--output needs a value"; OUTPUT="$2"; shift 2 ;;
    --date)     [ $# -ge 2 ] || die "--date needs a value"; DATE_OVERRIDE="$2"; shift 2 ;;
    --repo-url) [ $# -ge 2 ] || die "--repo-url needs a value"; REPO_URL="$2"; shift 2 ;;
    --all)      ALL=1; shift ;;
    --overwrite) OVERWRITE=1; shift ;;
    --stdout)   TO_STDOUT=1; shift ;;
    -h|--help)  usage; exit 0 ;;
    *)          die "unknown option: $1 (try --help)" ;;
  esac
done

command -v git >/dev/null 2>&1 || die "git is required but was not found in PATH"
git rev-parse --git-dir >/dev/null 2>&1 || die "not inside a git repository"

TODAY="${DATE_OVERRIDE:-$(date +%F)}"

# ------------------------------------------------------- repo URL / tags ---

detect_repo_url() {
  local url
  url="$(git remote get-url origin 2>/dev/null)" || { printf ''; return; }
  # git@github.com:org/repo.git -> https://github.com/org/repo
  case "$url" in
    git@*:* )
      local hostpath="${url#git@}"
      local host="${hostpath%%:*}"
      local path="${hostpath#*:}"
      url="https://${host}/${path}"
      ;;
    ssh://git@* )
      url="${url#ssh://git@}"
      url="https://${url}"
      ;;
  esac
  url="${url%.git}"
  url="${url%/}"
  printf '%s' "$url"
}

[ -n "$REPO_URL" ] || REPO_URL="$(detect_repo_url)"

# Tags sorted newest-version first (falls back gracefully for odd tag names).
list_tags() {
  git tag --sort=-version:refname 2>/dev/null
}

LAST_TAG="$(list_tags | head -n 1)"
[ -n "$LAST_TAG" ] || LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"

tag_date() { # date of the commit a tag points at
  git log -1 --format=%as "$1" 2>/dev/null
}

# ------------------------------------------------------------ categorizer ---

# categorize TYPE SUBJECT -> prints one of Added/Changed/Deprecated/Removed/Fixed/Security
categorize() {
  local type="$1" subject="$2" lower
  lower="$(printf '%s' "$subject" | tr '[:upper:]' '[:lower:]')"
  case "$type" in
    feat|feature)            printf 'Added'; return ;;
    fix|bugfix|hotfix)       printf 'Fixed'; return ;;
    security)                printf 'Security'; return ;;
    deprecate|deprecated)    printf 'Deprecated'; return ;;
    remove|removed)          printf 'Removed'; return ;;
    perf|refactor|style|docs|test|build|ci|chore|revert) printf 'Changed'; return ;;
  esac
  # Keyword fallback for non-conventional subjects (and unknown types).
  case "$lower" in
    *security*|*cve-*|*vulnerabilit*|*xss*|*csrf*) printf 'Security'; return ;;
  esac
  case "$lower" in
    deprecat*) printf 'Deprecated'; return ;;
  esac
  case "$lower" in
    remove\ *|removes\ *|removed\ *|delete\ *|deletes\ *|deleted\ *|drop\ *|dropped\ *)
      printf 'Removed'; return ;;
  esac
  case "$lower" in
    fix\ *|fixes\ *|fixed\ *|fixing\ *|resolve\ *|resolves\ *|resolved\ *|\
    hotfix*|bugfix*|*bug\ fix*|patch\ *)
      printf 'Fixed'; return ;;
  esac
  case "$lower" in
    add\ *|adds\ *|added\ *|implement*|introduce*|create\ *|creates\ *|new\ *)
      printf 'Added'; return ;;
  esac
  printf 'Changed'
}

cap_first() { # portable first-letter capitalization (bash 3.2 safe)
  local s="$1" first rest
  first="$(printf '%s' "$s" | cut -c1 | tr '[:lower:]' '[:upper:]')"
  rest="$(printf '%s' "$s" | cut -c2-)"
  printf '%s%s' "$first" "$rest"
}

# Render one commit as a changelog bullet on stdout (empty output = skip).
render_commit() {
  local subject="$1" body="$2"
  local type="" scope="" bang="" rest=""
  local conv_re='^([A-Za-z]+)(\(([^)]*)\))?(!)?:[[:space:]]+(.+)$'
  if [[ "$subject" =~ $conv_re ]]; then
    type="$(printf '%s' "${BASH_REMATCH[1]}" | tr '[:upper:]' '[:lower:]')"
    scope="${BASH_REMATCH[3]}"
    bang="${BASH_REMATCH[4]}"
    rest="${BASH_REMATCH[5]}"
  else
    rest="$subject"
  fi
  # Skip bare version subjects ("1.2.0", "v1.2.0") and merge commits.
  case "$rest" in
    [vV][0-9]*.[0-9]*.[0-9]*|[0-9]*.[0-9]*.[0-9]*) 
      case "$rest" in *[!0-9.vV]*) : ;; *) return 0 ;; esac ;;
  esac
  case "$subject" in Merge\ *|merge\ *) return 0 ;; esac

  local breaking=0
  [ "$bang" = "!" ] && breaking=1
  case "$body" in *"BREAKING CHANGE:"*|*"BREAKING-CHANGE:"*) breaking=1 ;; esac

  local cat
  cat="$(categorize "$type" "$rest")"
  rest="$(cap_first "$rest")"

  local line="- "
  [ "$breaking" = 1 ] && line="${line}**BREAKING:** "
  [ -n "$scope" ] && line="${line}**${scope}:** "
  line="${line}${rest}"
  printf '%s\t%s\n' "$cat" "$line"
}

# ------------------------------------------------------------- sections ---

# build_section RANGE_TSV_HEADING -> prints a full "## ..." section or nothing
# Args: $1 = git log range (may be plain "HEAD" etc.), $2 = heading text line,
#       $3, $4... = unused. Entries are deduplicated per category, order kept.
build_section() {
  local range="$1" heading="$2"
  local tmp
  tmp="$(mktemp)" || die "mktemp failed"
  git log --no-merges --pretty=format:'%s%x1f%b%x1e' $range > "$tmp.raw" 2>/dev/null || {
    rm -f "$tmp" "$tmp.raw"; return 0;
  }
  : > "$tmp"
  local subject body
  while IFS="$(printf '\037')" read -r -d "$(printf '\036')" subject body; do
    subject="${subject#$'\n'}"
    [ -n "$subject" ] || continue
    render_commit "$subject" "$body" >> "$tmp"
  done < "$tmp.raw"
  rm -f "$tmp.raw"
  if [ ! -s "$tmp" ]; then rm -f "$tmp"; return 0; fi

  printf '%s\n' "$heading"
  local cat
  for cat in Added Changed Deprecated Removed Fixed Security; do
    local entries
    entries="$(awk -F '\t' -v c="$cat" '$1 == c { print $2 }' "$tmp" | awk '!seen[$0]++')"
    [ -n "$entries" ] || continue
    printf '\n### %s\n\n%s\n' "$cat" "$entries"
  done
  rm -f "$tmp"
}

HEADER='# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).'

# --------------------------------------------------------------- driver ---

SECTIONS=""
LINK_REFS=""

add_link_refs() { # $1 = new version (or Unreleased), $2 = previous tag/ref
  [ -n "$REPO_URL" ] || return 0
  local newref="$1" prevref="$2"
  if [ "$newref" = "Unreleased" ]; then
    if [ -n "$prevref" ]; then
      LINK_REFS="${LINK_REFS}
[Unreleased]: ${REPO_URL}/compare/${prevref}...HEAD"
    fi
  else
    if [ -n "$prevref" ]; then
      LINK_REFS="${LINK_REFS}
[${newref}]: ${REPO_URL}/compare/${prevref}...${newref}
[Unreleased]: ${REPO_URL}/compare/${newref}...HEAD"
    else
      LINK_REFS="${LINK_REFS}
[${newref}]: ${REPO_URL}/releases/tag/${newref}"
    fi
  fi
}

if [ "$ALL" = 1 ]; then
  # Newest tag first; sections newest release -> oldest.
  TAGS_FILE="$(mktemp)" || die "mktemp failed"
  list_tags > "$TAGS_FILE"
  # Unreleased section for commits past the newest tag.
  if [ -n "$LAST_TAG" ]; then
    S="$(build_section "${LAST_TAG}..HEAD" '## [Unreleased]')"
    if [ -n "$S" ]; then
      SECTIONS="${SECTIONS}${S}
"
      add_link_refs "Unreleased" "$LAST_TAG"
    fi
  else
    S="$(build_section "HEAD" '## [Unreleased]')"
    if [ -n "$S" ]; then SECTIONS="${SECTIONS}${S}
"; fi
  fi
  PREV=""
  while IFS= read -r TAG; do
    [ -n "$TAG" ] || continue
    if [ -n "$PREV" ]; then :; fi
    # Range for this tag: previous (older) tag..this tag, or root..tag.
    NEXT_OLDER="$(awk -v t="$TAG" 'found { print; exit } $0 == t { found=1 }' "$TAGS_FILE")"
    if [ -n "$NEXT_OLDER" ]; then RANGE="${NEXT_OLDER}..${TAG}"; else RANGE="${TAG}"; fi
    S="$(build_section "$RANGE" "## [${TAG}] - $(tag_date "$TAG")")"
    if [ -n "$S" ]; then
      [ -n "$SECTIONS" ] && SECTIONS="${SECTIONS}
"
      SECTIONS="${SECTIONS}${S}
"
      add_link_refs "$TAG" "$NEXT_OLDER"
    fi
    PREV="$TAG"
  done < "$TAGS_FILE"
  rm -f "$TAGS_FILE"
else
  RANGE=""
  if [ -n "$FROM_REF" ]; then
    RANGE="${FROM_REF}..${TO_REF}"
  elif [ -n "$LAST_TAG" ]; then
    RANGE="${LAST_TAG}..${TO_REF}"
  else
    RANGE="${TO_REF}"
  fi
  # Compare-link base: an explicit --from wins over the auto-detected tag.
  PREV_REF="$LAST_TAG"
  [ -n "$FROM_REF" ] && PREV_REF="$FROM_REF"
  if [ -n "$VERSION" ]; then
    HEADING="## [${VERSION}] - ${TODAY}"
    S="$(build_section "$RANGE" "$HEADING")"
    [ -n "$S" ] || { err "no commits in range ${RANGE} — nothing to add."; exit 0; }
    SECTIONS="${S}
"
    add_link_refs "$VERSION" "$PREV_REF"
  else
    HEADING='## [Unreleased]'
    S="$(build_section "$RANGE" "$HEADING")"
    [ -n "$S" ] || { err "no commits in range ${RANGE} — nothing to add."; exit 0; }
    SECTIONS="${S}
"
    add_link_refs "Unreleased" "$PREV_REF"
  fi
fi

if [ -z "$(printf '%s' "$SECTIONS" | tr -d '[:space:]')" ]; then
  err "no changelog entries generated — nothing to do."
  exit 0
fi

# De-duplicate link refs (--all adds an [Unreleased] ref per section pass).
if [ -n "$LINK_REFS" ]; then
  LINK_REFS="$(printf '%s' "$LINK_REFS" | awk 'NF && !seen[$0]++')"
  LINK_REFS="
${LINK_REFS}"
fi

# ---------------------------------------------------------------- output ---

if [ "$TO_STDOUT" = 1 ]; then
  printf '%s\n\n%s' "$HEADER" "$SECTIONS"
  [ -n "$LINK_REFS" ] && printf '%s\n' "$LINK_REFS"
  exit 0
fi

if [ "$OVERWRITE" = 1 ] || [ ! -f "$OUTPUT" ]; then
  {
    printf '%s\n\n%s' "$HEADER" "$SECTIONS"
    [ -n "$LINK_REFS" ] && printf '%s\n' "$LINK_REFS"
  } > "$OUTPUT"
  printf '%s: wrote %s\n' "$PROG" "$OUTPUT" >&2
  exit 0
fi

# Insert into an existing file: refuse duplicate version sections, splice the
# new section under the preamble, and refresh the link refs we own.
if [ -n "$VERSION" ] && grep -q "^## \[${VERSION}\]" "$OUTPUT"; then
  die "a section for ${VERSION} already exists in ${OUTPUT} (edit it, or use --overwrite)"
fi
if [ -z "$VERSION" ] && grep -q '^## \[Unreleased\]' "$OUTPUT"; then
  die "an [Unreleased] section already exists in ${OUTPUT} (use --version for a release, or --overwrite)"
fi

TMP_OUT="$(mktemp)" || die "mktemp failed"
awk -v sections="$SECTIONS" '
  /^## / && !done { printf "%s\n", sections; done=1 }
  { print }
  END { if (!done) printf "%s", sections }
' "$OUTPUT" > "$TMP_OUT"
# Trim trailing blank lines so appended link refs sit in one clean block.
awk '{ lines[NR] = $0 } END {
       last = NR; while (last > 0 && lines[last] == "") last--
       for (i = 1; i <= last; i++) print lines[i]
     }' "$TMP_OUT" > "$TMP_OUT.trim" && mv "$TMP_OUT.trim" "$TMP_OUT"

if [ -n "$LINK_REFS" ]; then
  # Drop stale refs for the labels we are about to write, then append fresh.
  LABELS="$(printf '%s' "$LINK_REFS" | sed -n 's/^\[\([^]]*\)\]:.*/\1/p' | sort -u)"
  FILTERED="$(mktemp)" || die "mktemp failed"
  cp "$TMP_OUT" "$FILTERED"
  for L in $LABELS; do
    grep -v "^\[${L}\]:" "$FILTERED" > "$TMP_OUT" || true
    cp "$TMP_OUT" "$FILTERED"
  done
  rm -f "$FILTERED"
  awk '{ lines[NR] = $0 } END {
         last = NR; while (last > 0 && lines[last] == "") last--
         for (i = 1; i <= last; i++) print lines[i]
       }' "$TMP_OUT" > "$TMP_OUT.trim" && mv "$TMP_OUT.trim" "$TMP_OUT"
  # Append contiguously when the file already ends in a link-ref block.
  REFS_PLAIN="${LINK_REFS#$'\n'}"
  LASTLINE="$(tail -n 1 "$TMP_OUT")"
  case "$LASTLINE" in
    \[*\]:*) printf '%s\n' "$REFS_PLAIN" >> "$TMP_OUT" ;;
    *)       printf '\n%s\n' "$REFS_PLAIN" >> "$TMP_OUT" ;;
  esac
fi

mv "$TMP_OUT" "$OUTPUT"
printf '%s: updated %s\n' "$PROG" "$OUTPUT" >&2
