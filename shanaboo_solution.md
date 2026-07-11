Based on the issue, I need to create a bash script (`changelog.sh`) that generates a structured CHANGELOG.md from git history. Since the repo only shows README.md and LICENSE, I'll create the new script file and update the README.md with setup instructions.

```diff
--- /dev/null
+++ b/changelog.sh
@@ -0,0 +1,148 @@
+#!/usr/bin/env bash
+#
+# changelog.sh — Generate a structured CHANGELOG.md from git history
+#
+# Usage:
+#   ./changelog.sh                    # writes CHANGELOG.md in current dir
+#   ./changelog.sh -o RELEASE.md      # custom output filename
+#   ./changelog.sh -t v1.0.0          # start from a specific tag
+#   ./changelog.sh -d                 # dry-run (print to stdout only)
+#
+# Requirements: git, bash 4+
+
+set -euo pipefail
+
+# --- defaults ---
+OUTPUT="CHANGELOG.md"
+START_TAG=""
+DRY_RUN=false
+
+# --- parse flags ---
+while [[ $# -gt 0 ]]; do
+  case "$1" in
+    -o|--output) OUTPUT="$2"; shift 2 ;;
+    -t|--tag)    START_TAG="$2"; shift 2 ;;
+    -d|--dry-run) DRY_RUN=true; shift ;;
+    -h|--help)
+      echo "Usage: $0 [-o OUTPUT] [-t TAG] [-d]"
+      echo "  -o, --output   Output file (default: CHANGELOG.md)"
+      echo "  -t, --tag      Start from a specific tag (default: latest tag)"
+      echo "  -d, --dry-run  Print to stdout instead of writing file"
+      exit 0
+      ;;
+    *) echo "Unknown option: $1"; exit 1 ;;
+  esac
+done
+
+# --- ensure we are inside a git repo ---
+if ! git rev-parse --git-dir > /dev/null 2>&1; then
+  echo "Error: not inside a git repository." >&2
+  exit 1
+fi
+
+# --- determine starting point ---
+if [[ -z "$START_TAG" ]]; then
+  # latest tag reachable from HEAD
+  START_TAG=$(git describe --tags --abbrev=0 2>/dev/null || true)
+fi
+
+if [[ -n "$START_TAG" ]]; then
+  RANGE="${START_TAG}..HEAD"
+  echo "→ Collecting commits since tag: $START_TAG"
+else
+  # no tags at all — use the first commit
+  FIRST_COMMIT=$(git rev-list --max-parents=0 HEAD)
+  RANGE="${FIRST_COMMIT}..HEAD"
+  echo "→ No tags found; collecting all commits."
+fi
+
+# --- fetch commits (one per line: hash | author date | subject) ---
+COMMITS=$(git log "${RANGE}" --pretty=format:"%h | %ad | %s" --date=short 2>/dev/null || true)
+
+if [[ -z "$COMMITS" ]]; then
+  echo "→ No new commits since ${START_TAG:-the beginning}. Nothing to do."
+  exit 0
+fi
+
+# --- categorisation helpers ---
+declare -A CATEGORIES
+CATEGORIES=(
+  ["Added"]=""
+  ["Fixed"]=""
+  ["Changed"]=""
+  ["Removed"]=""
+)
+
+# keywords that map a commit to a category (case-insensitive match on subject)
+declare -A KEYWORDS
+KEYWORDS=(
+  ["Added"]="add|implement|introduce|create|new|feat"
+  ["Fixed"]="fix|resolve|patch|repair|bug|hotfix|correct"
+  ["Changed"]="change|update|refactor|improve|tweak|adjust|modify|enhance|upgrade|move|rename"
+  ["Removed"]="remove|delete|drop|deprecate|retire|cleanup|purge"
+)
+
+# --- classify each commit ---
+while IFS= read -r line; do
+  [[ -z "$line" ]] && continue
+
+  HASH=$(echo "$line" | cut -d'|' -f1 | xargs)
+  DATE=$(echo "$line" | cut -d'|' -f2 | xargs)
+  SUBJECT=$(echo "$line" | cut -d'|' -f3- | xargs)
+
+  CAT="Changed"   # default fallback
+  SUBJECT_LOWER=$(echo "$SUBJECT" | tr '[:upper:]' '[:lower:]')
+
+  for SECTION in "${!KEYWORDS[@]}"; do
+    if echo "$SUBJECT_LOWER" | grep -qE "\b(${KEYWORDS[$SECTION]})\b"; then
+      CAT="$SECTION"
+      break
+    fi
+  done
+
+  # append bullet
+  if [[ -z "${CATEGORIES[$CAT]}" ]]; then
+    CATEGORIES[$CAT]="- ${SUBJECT} (${HASH}, ${DATE})"
+  else
+    CATEGORIES[$CAT]+=$'\n'"- ${SUBJECT} (${HASH}, ${DATE})"
+  fi
+done <<< "$COMMITS"
+
+# --- build changelog ---
+TODAY=$(date +%Y-%m-%d)
+VERSION="${START_TAG:-0.0.0} → HEAD"
+
+CHANGELOG="# Changelog\n\n## [${VERSION}] — ${TODAY}\n"
+
+for SECTION in "Added" "Fixed" "Changed" "Removed"; do
+  ENTRIES="${CATEGORIES[$SECTION]}"
+  if [[ -n "$ENTRIES" ]]; then
+    CHANGELOG+="\n### ${SECTION}\n${ENTRIES}\n"
+  fi
+done
+
+CHANGELOG+="\n---\n"
+
+# --- output ---
+if $DRY_RUN; then
+  echo -e "$CHANGELOG"
+else
+  if [[ -f "$OUTPUT" ]]; then
+    # Prepend to existing changelog (keep old entries below the new block)
+    TMP=$(mktemp)
+    echo -e "$CHANGELOG" > "$TMP"
+    cat "$OUTPUT" >> "$TMP