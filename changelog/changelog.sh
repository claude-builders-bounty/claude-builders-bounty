#!/usr/bin/env bash
# changelog.sh - generate a structured CHANGELOG.md from git history.
#
# Usage: bash changelog.sh [OUTPUT]
#   OUTPUT  file to write (default: CHANGELOG.md); "-" prints to stdout.
#
# Run it inside the git repository you want a changelog for.
# - Collects commits since the most recent tag (all commits if there are no tags).
#   If HEAD itself is tagged, documents that release against the previous tag.
# - Sorts them into Added / Fixed / Changed / Removed using Conventional
#   Commit types (feat, fix, refactor, ...) or leading verbs (Add, Fix, Remove, ...).
# - An existing OUTPUT keeps its intro and older releases; a stale [Unreleased]
#   or same-version section is replaced, so re-running never duplicates entries.
# Needs only bash and git; avoids bash-4-only features (macOS ships bash 3.2).
set -euo pipefail
shopt -u patsub_replacement 2>/dev/null || true # bash 5.2+: keep '&' literal in ${x//a/b}

out="${1:-CHANGELOG.md}"
case "$out" in
  -h | --help) sed -n '2,/^set /{/^set /d;s/^# \{0,1\}//;p;}' "$0"; exit 0 ;;
esac

git rev-parse --is-inside-work-tree >/dev/null 2>&1 ||
  { echo "changelog.sh: not inside a git repository" >&2; exit 1; }

title="Unreleased"
date=""
range=""
since=""
if git rev-parse -q --verify HEAD >/dev/null; then
  range="HEAD"
  if tag=$(git describe --tags --exact-match HEAD 2>/dev/null); then
    title="$tag"
    date=$(git log -1 --format=%cd --date=short HEAD)
    since=$(git describe --tags --abbrev=0 HEAD^ 2>/dev/null || true) # HEAD^ fails on a root commit
  else
    since=$(git describe --tags --abbrev=0 HEAD 2>/dev/null || true)
  fi
  [ -n "$since" ] && range="$since..HEAD"
fi

# Link commit hashes when origin is on GitHub (any credentials in the URL are dropped).
base=$(git remote get-url origin 2>/dev/null || true)
case "$base" in
  *github.com[:/]*) base="${base#*github.com[:/]}"; base="https://github.com/${base%.git}" ;;
  *) base="" ;;
esac

shopt -s nocasematch
conv='^([a-z]+)(\(([^)]*)\))?(!)?:[[:space:]]*(.+)$'
add_re='^(add|adds|added|create|creates|created|implement|implements|implemented|introduce|introduces|introduced|new|support|supports)([^[:alnum:]]|$)'
fix_re='^(fix|fixes|fixed|bugfix|hotfix|resolve|resolves|resolved|patch|patches|patched|correct|corrects|corrected|repair|repairs|repaired)([^[:alnum:]]|$)'
brk_re=$'(^|\n)BREAKING[ -]CHANGE:'
rem_re='^(remove|removes|removed|delete|deletes|deleted|drop|drops|dropped|deprecate|deprecates|deprecated|rm)([^[:alnum:]]|$)'

added="" fixed="" changed="" removed=""
log=""
[ -n "$range" ] && log=$(git log --no-merges --format='%h%x1f%s%x1f%b%x1e' "$range")
while IFS= read -r -d $'\x1e' rec; do
  rec="${rec#$'\n'}"
  hash="${rec%%$'\x1f'*}"; rec="${rec#*$'\x1f'}"
  subj="${rec%%$'\x1f'*}"; body="${rec#*$'\x1f'}"
  [ -n "$hash" ] || continue

  type="" scope="" bang="" desc="$subj"
  if [[ $subj =~ $conv ]]; then
    type="${BASH_REMATCH[1]}" scope="${BASH_REMATCH[3]}" bang="${BASH_REMATCH[4]}" desc="${BASH_REMATCH[5]}"
  fi

  case "$type" in
    feat | feature) cat=added ;;
    fix | bugfix | hotfix) cat=fixed ;;
    *)
      if [[ $desc =~ $rem_re ]]; then cat=removed
      elif [ -z "$type" ] && [[ $desc =~ $add_re ]]; then cat=added
      elif [ -z "$type" ] && [[ $desc =~ $fix_re ]]; then cat=fixed
      else cat=changed
      fi ;;
  esac

  # Keep raw HTML in commit subjects from rendering (or vanishing) in Markdown.
  desc="${desc//&/&amp;}"; desc="${desc//</&lt;}"; desc="${desc//>/&gt;}"
  ref="\`$hash\`"
  [ -n "$base" ] && ref="[$ref]($base/commit/$hash)"
  line="- "
  if [ -n "$bang" ] || [[ $body =~ $brk_re ]]; then line+="**BREAKING:** "; fi
  # feat/fix are implied by their section; other types (docs, chore, ...) stay visible.
  case "$cat:$type" in
    added:* | fixed:* | *:) label="$scope" ;;
    *) label="$type${scope:+($scope)}" ;;
  esac
  [ -n "$label" ] && line+="**$label:** "
  line+="$desc ($ref)"$'\n'

  case "$cat" in
    added) added+="$line" ;;
    fixed) fixed+="$line" ;;
    changed) changed+="$line" ;;
    removed) removed+="$line" ;;
  esac
done <<<"$log"
shopt -u nocasematch

section="## [$title]${date:+ - $date}"$'\n\n'
[ -n "$added" ] && section+=$'### Added\n\n'"$added"$'\n'
[ -n "$fixed" ] && section+=$'### Fixed\n\n'"$fixed"$'\n'
[ -n "$changed" ] && section+=$'### Changed\n\n'"$changed"$'\n'
[ -n "$removed" ] && section+=$'### Removed\n\n'"$removed"$'\n'
if [ -z "$added$fixed$changed$removed" ]; then
  if [ -n "$since" ]; then section+="_No changes since \`$since\`._"$'\n\n'
  else section+=$'_No commits yet._\n\n'
  fi
fi

header=$'# Changelog\n\nAll notable changes to this project are documented in this file.\nThe format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).\n\n'

if [ "$out" = "-" ]; then
  printf '%s%s' "$header" "$section"
  exit 0
fi

tmp=$(mktemp "$out.XXXXXX")
trap 'rm -f "$tmp"' EXIT
if [ -s "$out" ]; then
  # Insert before the first "## " heading, dropping an old [Unreleased] / same-title section.
  CL_SECTION="$section" CL_TITLE="$title" awk '
    BEGIN { sec = ENVIRON["CL_SECTION"]; t = ENVIRON["CL_TITLE"] }
    /^## / {
      if (!done) { printf "%s", sec; done = 1 }
      skip = (index($0, "## [" t "]") == 1 || index($0, "## [Unreleased]") == 1)
    }
    !skip { print }
    END { if (!done) { if (NR) print ""; printf "%s", sec } }
  ' "$out" >"$tmp"
else
  printf '%s%s' "$header" "$section" >"$tmp"
fi
cat "$tmp" >"$out" # not mv: keeps the file's existing permissions (mktemp makes 0600)
echo "changelog.sh: wrote $out ($title${since:+, since $since})" >&2
