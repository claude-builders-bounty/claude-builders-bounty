#!/usr/bin/env bash
#
# changelog.sh — turn git history into a Keep a Changelog section.
#
# Reads the commits between the last git tag and HEAD, sorts them into
# Added / Changed / Deprecated / Removed / Fixed / Security, and writes the
# result to CHANGELOG.md (or prints it with --stdout).
#
# Dependencies: git, bash 3.2+, awk, sed. Nothing to install.

set -euo pipefail

SECTIONS="Added Changed Deprecated Removed Fixed Security"

since=""
to="HEAD"
version=""
output="CHANGELOG.md"
repo_url=""
to_stdout=0
include_noise=0

die() { printf 'changelog.sh: %s\n' "$*" >&2; exit 1; }

usage() {
  cat <<'USAGE'
Usage: changelog.sh [options]

Options:
  --since <ref>     Start of the commit range (default: last tag reachable from HEAD)
  --to <ref>        End of the commit range (default: HEAD)
  --version <name>  Release heading (default: tag at HEAD, else "Unreleased")
  --output <file>   File to create or update (default: CHANGELOG.md)
  --repo <url>      Repository URL used for links (default: the "origin" remote)
  --stdout          Print the new section instead of writing to a file
  --all             Also include docs/chore/ci/build/test/style commits
  -h, --help        Show this help

Examples:
  ./changelog.sh                          # add an "Unreleased" section to CHANGELOG.md
  ./changelog.sh --version 1.4.0          # cut a dated release section
  ./changelog.sh --since v1.0.0 --stdout  # preview a range without touching the file
USAGE
}

need_value() { [ -n "${2:-}" ] || die "$1 requires a value"; }

while [ $# -gt 0 ]; do
  case "$1" in
    --since)   need_value "$1" "${2:-}"; since="$2"; shift 2 ;;
    --to)      need_value "$1" "${2:-}"; to="$2"; shift 2 ;;
    --version) need_value "$1" "${2:-}"; version="$2"; shift 2 ;;
    --output)  need_value "$1" "${2:-}"; output="$2"; shift 2 ;;
    --repo)    need_value "$1" "${2:-}"; repo_url="$2"; shift 2 ;;
    --stdout)  to_stdout=1; shift ;;
    --all)     include_noise=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *)         die "unknown option: $1 (try --help)" ;;
  esac
done

git rev-parse --git-dir >/dev/null 2>&1 || die "not inside a git repository"
git rev-parse --verify --quiet "$to^{commit}" >/dev/null || die "unknown ref: $to"

# --- range ------------------------------------------------------------------
# Default to the last tag reachable from --to. If --to *is* that tag, step back
# one more tag so you can generate the notes for the release you just tagged.
if [ -z "$since" ]; then
  since="$(git describe --tags --abbrev=0 "$to" 2>/dev/null || true)"
  if [ -n "$since" ] && [ "$(git rev-parse "$since^{commit}")" = "$(git rev-parse "$to^{commit}")" ]; then
    since="$(git describe --tags --abbrev=0 "$since^" 2>/dev/null || true)"
  fi
elif ! git rev-parse --verify --quiet "$since^{commit}" >/dev/null; then
  die "unknown ref: $since"
fi

if [ -n "$since" ]; then range="$since..$to"; else range="$to"; fi

# Name the section after the tag sitting on --to, when there is one, and use
# that tag in compare links so they keep working after HEAD moves on.
head_tag="$(git tag --points-at "$to" 2>/dev/null | head -n 1)"
compare_to="${head_tag:-$to}"
if [ -z "$version" ]; then
  version="${head_tag:-Unreleased}"
fi

# --- links ------------------------------------------------------------------
if [ -z "$repo_url" ]; then
  repo_url="$(git remote get-url origin 2>/dev/null || true)"
fi
if [ -n "$repo_url" ]; then
  repo_url="$(printf '%s' "$repo_url" \
    | sed -e 's#^git@\([^:]*\):#https://\1/#' -e 's#^ssh://git@#https://#' -e 's#\.git$##')"
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
for section in $SECTIONS; do : > "$tmp/$section"; done

# --- classification ---------------------------------------------------------
# Conventional Commits type -> section. Noise types return an empty string and
# are dropped unless --all was passed; unknown words return "?" so the caller
# can fall back to reading the subject as plain English.
section_for_type() {
  case "$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')" in
    feat|feature|add|added)                       printf 'Added' ;;
    fix|bugfix|hotfix|patch)                      printf 'Fixed' ;;
    perf|refactor|change|changed|update|revert)   printf 'Changed' ;;
    remove|removed|delete|deleted|drop)           printf 'Removed' ;;
    deprecate|deprecated)                         printf 'Deprecated' ;;
    security|sec)                                 printf 'Security' ;;
    docs|doc|chore|ci|build|test|tests|style|release)
      if [ "$include_noise" -eq 1 ]; then printf 'Changed'; fi ;;
    *)                                            printf '?' ;;
  esac
}

# Plain-English fallback for repos that do not use Conventional Commits: look at
# the leading verb only, so a "fix" buried mid-sentence cannot hijack the entry.
section_for_verb() {
  case "$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z].*$//')" in
    add|adds|added|new|introduce|introduces|introduced|implement|implements|implemented|support)
      printf 'Added' ;;
    fix|fixes|fixed|correct|corrects|corrected|resolve|resolves|resolved|repair|repairs|patched)
      printf 'Fixed' ;;
    remove|removes|removed|delete|deletes|deleted|drop|drops|dropped|purge|purged)
      printf 'Removed' ;;
    deprecate|deprecates|deprecated)
      printf 'Deprecated' ;;
    *)
      printf 'Changed' ;;
  esac
}

# --- read history -----------------------------------------------------------
count=0
log_output="$(git log --no-merges --pretty=format:'%h%x1f%s%x1f%b%x1e' "$range" -- 2>/dev/null || true)"

while [ -n "$log_output" ]; do
  record="${log_output%%$'\x1e'*}"
  if [ "$record" = "$log_output" ]; then log_output=""; else log_output="${log_output#*$'\x1e'}"; fi
  record="${record#$'\n'}"
  [ -n "$record" ] || continue

  short="${record%%$'\x1f'*}";  rest="${record#*$'\x1f'}"
  subject="${rest%%$'\x1f'*}";  body="${rest#*$'\x1f'}"

  scope=""
  breaking=0
  case "$body" in *"BREAKING CHANGE"*|*"BREAKING-CHANGE"*) breaking=1 ;; esac

  if [[ "$subject" =~ ^([a-zA-Z]+)(\(([^\)]*)\))?(!)?:[[:space:]]*(.+)$ ]]; then
    section="$(section_for_type "${BASH_REMATCH[1]}")"
    if [ "$section" = "?" ]; then          # "wip: ..." and friends are not types
      text="$subject"
      section="$(section_for_verb "$subject")"
    else
      scope="${BASH_REMATCH[3]:-}"
      [ -n "${BASH_REMATCH[4]:-}" ] && breaking=1
      text="${BASH_REMATCH[5]}"
    fi
  else
    text="$subject"
    section="$(section_for_verb "$subject")"
  fi

  [ -n "$section" ] || continue            # noise, and --all was not passed

  # Pull a trailing "(#123)" out of the subject so it can become a PR link.
  pr=""
  if [[ "$text" =~ ^(.+)[[:space:]]\(#([0-9]+)\)$ ]]; then
    text="${BASH_REMATCH[1]}"
    pr="${BASH_REMATCH[2]}"
  fi

  entry="$text"
  [ -n "$scope" ] && entry="**${scope}**: ${entry}"
  [ "$breaking" -eq 1 ] && entry="**BREAKING** ${entry}"

  if [ -n "$repo_url" ] && [ -n "$pr" ]; then
    entry="${entry} ([#${pr}](${repo_url}/pull/${pr}))"
  elif [ -n "$repo_url" ]; then
    entry="${entry} ([\`${short}\`](${repo_url}/commit/${short}))"
  elif [ -n "$pr" ]; then
    entry="${entry} (#${pr})"
  else
    entry="${entry} (\`${short}\`)"
  fi

  # Prefix each line with a dedupe key (the entry minus its link) so the same
  # change cherry-picked under two hashes collapses to a single bullet.
  printf -- '%s\037- %s\n' "${entry% (*)}" "$entry" >> "$tmp/$section"
  count=$((count + 1))
done

if [ "$count" -eq 0 ]; then
  printf 'changelog.sh: no changelog-worthy commits in %s — nothing to write.\n' "$range" >&2
  exit 0
fi

# --- render -----------------------------------------------------------------
rendered=""
emit() { rendered="${rendered}${1}"$'\n'; }

if [ "$version" = "Unreleased" ]; then
  emit "## [Unreleased]"
else
  # A release named after an existing tag is dated by that tag, not by today,
  # so re-generating an old section reproduces the same heading.
  if [ -n "$head_tag" ] && [ "$version" = "$head_tag" ]; then
    release_date="$(git log -1 --format=%ad --date=short "$head_tag" 2>/dev/null || true)"
  fi
  emit "## [${version}] - ${release_date:-$(date +%Y-%m-%d)}"
fi
emit ""

# The blockquote describes the range itself, so it counts every commit in it —
# not just the ones that earned a bullet.
scanned="$(git rev-list --count --no-merges "$range" -- 2>/dev/null || printf '%s' "$count")"
if [ "$scanned" -eq 1 ]; then tally="1 commit"; else tally="${scanned} commits"; fi

if [ -n "$since" ] && [ -n "$repo_url" ]; then
  emit "> ${tally} since \`${since}\` · [full diff](${repo_url}/compare/${since}...${compare_to})"
elif [ -n "$since" ]; then
  emit "> ${tally} since \`${since}\`"
else
  emit "> ${tally} — full history"
fi
emit ""

for section in $SECTIONS; do
  [ -s "$tmp/$section" ] || continue
  emit "### ${section}"
  emit ""
  while IFS= read -r line; do emit "$line"; done \
    < <(awk -F'\037' '!seen[$1]++ { print $2 }' "$tmp/$section")
  emit ""
done

rendered="${rendered%$'\n'}"    # drop the final newline emit() appended
rendered="${rendered%$'\n'}"    # ...and the blank line after the last section

if [ "$to_stdout" -eq 1 ]; then
  printf '%s\n' "$rendered"
  exit 0
fi

printf '%s\n' "$rendered" > "$tmp/section.md"

if [ ! -f "$output" ]; then
  {
    cat <<'HEADER'
# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

HEADER
    cat "$tmp/section.md"
  } > "$output"
else
  if grep -q "^## \[${version}\]" "$output"; then
    die "$output already has a section for [${version}] — bump --version, or preview with --stdout"
  fi
  # Insert above the newest existing release; keep the file's preamble intact.
  awk -v secfile="$tmp/section.md" '
    !inserted && /^## / {
      while ((getline line < secfile) > 0) print line
      print ""
      inserted = 1
    }
    { print }
    END {
      if (!inserted) {
        while ((getline line < secfile) > 0) print line
      }
    }
  ' "$output" > "$tmp/updated.md"
  mv "$tmp/updated.md" "$output"
fi

entries="$(printf '%s\n' "$rendered" | grep -c '^- ' || true)"
printf 'changelog.sh: wrote [%s] — %s entries from %s to %s\n' \
  "$version" "$entries" "$tally" "$output" >&2
