#!/usr/bin/env bash
# Issue #2853 hands-on verification — reuses a single zeroeye checkout and archives
# session diffs for fleet review (peer review: commit session diffs, avoid redundant clones).
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ZEROEYE_BRANCH="${ZEROEYE_BRANCH:-pr-3-read-tool-hook}"
ZEROEYE_REPO="${ZEROEYE_REPO:-https://github.com/advancedresearcharray/zeroeye.git}"
ZEROEYE_DIR="${ZEROEYE_ROOT:-${REPO_ROOT}/.cache/zeroeye-${ZEROEYE_BRANCH}}"
SESSION_DIR="${REPO_ROOT}/bounties/issue-2853/sessions"
LABEL="${VERIFY_SESSION_LABEL:-hands-on}"

mkdir -p "$SESSION_DIR"

archive_session_diff() {
  local phase="$1"
  local stamp
  stamp="$(date -u +%Y%m%dT%H%M%SZ)"
  local patch="${SESSION_DIR}/session-${stamp}-${LABEL}-${phase}.patch"
  {
    git -C "$REPO_ROOT" diff HEAD
    git -C "$REPO_ROOT" diff --cached HEAD
  } >"$patch" 2>/dev/null || true
  if [[ -s "$patch" ]]; then
    echo "Archived session diff: ${patch#${REPO_ROOT}/}"
  else
    rm -f "$patch"
  fi
}

ensure_zeroeye() {
  if [[ -d "${ZEROEYE_DIR}/.git" ]]; then
    echo "Reusing zeroeye checkout at ${ZEROEYE_DIR}"
    if ! git -C "$ZEROEYE_DIR" rev-parse --verify HEAD >/dev/null 2>&1; then
      echo "zeroeye checkout corrupt; recloning" >&2
      rm -rf "$ZEROEYE_DIR"
    fi
  fi

  if [[ ! -d "${ZEROEYE_DIR}/.git" ]]; then
    echo "Cloning zeroeye branch ${ZEROEYE_BRANCH} to ${ZEROEYE_DIR}"
    mkdir -p "$(dirname "$ZEROEYE_DIR")"
    if ! git clone --depth 1 --branch "$ZEROEYE_BRANCH" "$ZEROEYE_REPO" "$ZEROEYE_DIR"; then
      echo "zeroeye clone failed (branch=${ZEROEYE_BRANCH})" >&2
      return 1
    fi
  fi
}

on_fail() {
  archive_session_diff "failed"
  echo "verify-issue-2853: FAILED (session diff archived for troubleshooting)" >&2
}

trap on_fail ERR

archive_session_diff "start"
ensure_zeroeye

export ZEROEYE_ROOT="$ZEROEYE_DIR"
cd "$REPO_ROOT"

npm test
archive_session_diff "post-npm-test"

ZEROEYE_ROOT="$ZEROEYE_DIR" npm run test:issue-2853
archive_session_diff "complete"

trap - ERR
echo "OK: issue #2853 verification passed (zeroeye reused at ${ZEROEYE_DIR})"
