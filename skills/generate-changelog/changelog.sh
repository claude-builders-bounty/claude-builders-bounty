#!/usr/bin/env bash
# changelog.sh — Generate a Keep-a-Changelog formatted CHANGELOG.md from git history.
#
# Usage:
#   bash changelog.sh                    # write/update ./CHANGELOG.md (since last tag)
#   bash changelog.sh --stdout           # print to stdout, don't write file
#   bash changelog.sh --from v1.0.0      # commits since v1.0.0 (default: last tag)
#   bash changelog.sh --to HEAD          # commits up to ref (default: HEAD)
#   bash changelog.sh --version v1.2.0   # heading version (default: "Unreleased")
#   bash changelog.sh --all              # generate full changelog across all tags
#
# Categorizes Conventional Commits into Keep-a-Changelog sections:
#   feat        -> Added
#   fix         -> Fixed
#   refactor/perf/style/docs/build/ci/chore -> Changed
#   revert / "remove" / "delete" prefix     -> Removed
#   anything with "BREAKING CHANGE" or "!"  -> ⚠ Breaking Changes (called out at top)

set -euo pipefail

OUT_FILE="CHANGELOG.md"
WRITE=1
FROM=""
TO="HEAD"
VERSION=""
ALL=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --stdout)  WRITE=0; shift ;;
    --from)    FROM="$2"; shift 2 ;;
    --to)      TO="$2"; shift 2 ;;
    --version) VERSION="$2"; shift 2 ;;
    --output)  OUT_FILE="$2"; shift 2 ;;
    --all)     ALL=1; shift ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done

if ! git rev-parse --git-dir >/dev/null 2>&1; then
  echo "Error: not inside a git repository" >&2
  exit 1
fi

# repo URL for compare links (best-effort)
REPO_URL=""
origin=$(git config --get remote.origin.url 2>/dev/null || true)
if [[ -n "$origin" ]]; then
  REPO_URL=$(echo "$origin" | sed -E 's#git@github.com:#https://github.com/#; s#\.git$##')
fi

# Render a single section [from..to] with given heading.
render_section() {
  local from_ref="$1" to_ref="$2" heading="$3" date="$4"
  local range
  if [[ -n "$from_ref" ]]; then
    range="${from_ref}..${to_ref}"
  else
    range="$to_ref"
  fi

  # Use a unit separator we'll never see in commit text.
  local commits
  commits=$(git log --no-merges --pretty=format:'%H%x1f%s%x1f%b%x1e' "$range" 2>/dev/null || true)

  if [[ -z "$commits" ]]; then
    return 0
  fi

  local added=() fixed=() changed=() removed=() breaking=() other=()

  # Split on record separator (0x1e)
  while IFS= read -r -d $'\x1e' rec; do
    # Strip leading newlines that bleed in from previous record's body
    while [[ "$rec" == $'\n'* ]]; do rec="${rec#$'\n'}"; done
    [[ -z "$rec" ]] && continue
    local sha subject body
    # Split record on unit separator (0x1f) using bash IFS
    local _oldifs="$IFS"
    IFS=$'\x1f' read -r sha subject body <<< "$rec"
    IFS="$_oldifs"
    [[ -z "$subject" ]] && continue

    local short="${sha:0:7}"
    local link="$short"
    if [[ -n "$REPO_URL" ]]; then
      link="[\`$short\`]($REPO_URL/commit/$sha)"
    fi

    # Detect breaking
    local is_breaking=0
    if [[ "$subject" == *"!:"* ]] || [[ "$subject" == *"!("* ]] || [[ "$body" == *"BREAKING CHANGE"* ]]; then
      is_breaking=1
    fi

    # Parse Conventional Commit type/scope using sed (portable, avoids bash regex quirks)
    # Forms: "type: msg" | "type(scope): msg" | "type!: msg" | "type(scope)!: msg"
    local type="" desc="$subject" scope=""
    local prefix
    prefix=$(printf '%s' "$subject" | sed -n 's/^\([a-zA-Z][a-zA-Z]*\)\(([^)]*)\)\{0,1\}!\{0,1\}:.*/\1/p')
    if [[ -n "$prefix" ]]; then
      type=$(echo "$prefix" | tr '[:upper:]' '[:lower:]')
      scope=$(printf '%s' "$subject" | sed -n 's/^[a-zA-Z][a-zA-Z]*(\([^)]*\))!\{0,1\}:.*/\1/p')
      desc=$(printf '%s' "$subject" | sed 's/^[a-zA-Z][a-zA-Z]*\(([^)]*)\)\{0,1\}!\{0,1\}:[[:space:]]*//')
      if [[ -n "$scope" ]]; then
        desc="**${scope}:** $desc"
      fi
    fi

    local entry="- ${desc} (${link})"

    if [[ $is_breaking -eq 1 ]]; then
      breaking+=("$entry")
    fi

    case "$type" in
      feat|feature)                added+=("$entry") ;;
      fix|bugfix|hotfix)           fixed+=("$entry") ;;
      revert)                      removed+=("$entry") ;;
      perf|refactor|style|docs|build|ci|chore|test)
                                   changed+=("$entry") ;;
      *)
        # Heuristics on description
        local low
        low=$(echo "$desc" | tr '[:upper:]' '[:lower:]')
        if [[ "$low" == add\ * || "$low" == added\ * ]]; then
          added+=("$entry")
        elif [[ "$low" == fix\ * || "$low" == fixed\ * ]]; then
          fixed+=("$entry")
        elif [[ "$low" == remove\ * || "$low" == removed\ * || "$low" == delete\ * ]]; then
          removed+=("$entry")
        else
          other+=("$entry")
        fi
        ;;
    esac
  done <<< "$commits"

  echo "## [$heading] - $date"
  echo

  if [[ ${#breaking[@]} -gt 0 ]]; then
    echo "### ⚠ Breaking Changes"
    printf '%s\n' "${breaking[@]}"
    echo
  fi
  if [[ ${#added[@]} -gt 0 ]]; then
    echo "### Added"
    printf '%s\n' "${added[@]}"
    echo
  fi
  if [[ ${#changed[@]} -gt 0 ]]; then
    echo "### Changed"
    printf '%s\n' "${changed[@]}"
    echo
  fi
  if [[ ${#fixed[@]} -gt 0 ]]; then
    echo "### Fixed"
    printf '%s\n' "${fixed[@]}"
    echo
  fi
  if [[ ${#removed[@]} -gt 0 ]]; then
    echo "### Removed"
    printf '%s\n' "${removed[@]}"
    echo
  fi
  if [[ ${#other[@]} -gt 0 ]]; then
    echo "### Other"
    printf '%s\n' "${other[@]}"
    echo
  fi
}

# Build header + body
build() {
  echo "# Changelog"
  echo
  echo "All notable changes to this project are documented here."
  echo "Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and"
  echo "[Conventional Commits](https://www.conventionalcommits.org/)."
  echo

  local today
  today=$(date +%Y-%m-%d)

  if [[ $ALL -eq 1 ]]; then
    # Iterate tags newest -> oldest, plus unreleased.
    local tags
    tags=$(git tag --sort=-creatordate)
    local prev="$TO"
    if [[ -n "$tags" ]]; then
      local newest_tag
      newest_tag=$(echo "$tags" | head -n1)
      # Unreleased section if HEAD is past newest tag
      if [[ "$(git rev-parse "$newest_tag")" != "$(git rev-parse HEAD)" ]]; then
        render_section "$newest_tag" "HEAD" "Unreleased" "$today"
      fi
      local prev_tag=""
      while IFS= read -r tag; do
        local date
        date=$(git log -1 --format=%ad --date=short "$tag")
        if [[ -z "$prev_tag" ]]; then
          # oldest visible: from beginning to this tag... but we go newest first
          render_section "" "$tag" "${tag}" "$date" 2>/dev/null || true
        fi
        prev_tag="$tag"
      done <<< "$tags"
      # Now do pairwise newest..older
      local prev=""
      while IFS= read -r tag; do
        if [[ -n "$prev" ]]; then
          local date
          date=$(git log -1 --format=%ad --date=short "$prev")
          render_section "$tag" "$prev" "$prev" "$date"
        fi
        prev="$tag"
      done <<< "$tags"
      # oldest tag: from root
      local oldest
      oldest=$(echo "$tags" | tail -n1)
      local odate
      odate=$(git log -1 --format=%ad --date=short "$oldest")
      render_section "" "$oldest" "$oldest" "$odate"
    else
      render_section "" "$TO" "${VERSION:-Unreleased}" "$today"
    fi
    return
  fi

  # Single-section mode
  local from_ref="$FROM"
  if [[ -z "$from_ref" ]]; then
    from_ref=$(git describe --tags --abbrev=0 2>/dev/null || true)
  fi
  local heading="${VERSION:-Unreleased}"
  render_section "$from_ref" "$TO" "$heading" "$today"
}

OUTPUT=$(build)

if [[ $WRITE -eq 1 ]]; then
  printf '%s\n' "$OUTPUT" > "$OUT_FILE"
  echo "Wrote $OUT_FILE" >&2
else
  printf '%s\n' "$OUTPUT"
fi
