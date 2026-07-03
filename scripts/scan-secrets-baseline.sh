#!/usr/bin/env bash
# secret-scanner baseline check — detect_secrets_version: '1.5.0'
# Replaces secret-scanner/action@0.2.1 which jq-parses 1.2.x audit JSON only.
set -euo pipefail

BASELINE_FILE="${BASELINE_FILE:-.secrets.baseline}"
DETECT_SECRETS_VERSION="${DETECT_SECRETS_VERSION:-1.5.0}"
DETECT_SECRET_ADDITIONAL_ARGS="${DETECT_SECRET_ADDITIONAL_ARGS:-}"

# Pin detect-secrets to match .secrets.baseline "version" — mismatched versions rewrite
# the baseline hash and fail CI with false positives.
pip install -q "detect-secrets[gibberish]==${DETECT_SECRETS_VERSION}"

echo "Running detect-secrets scan (version ${DETECT_SECRETS_VERSION}) with args: ${DETECT_SECRET_ADDITIONAL_ARGS}"
# Rescan tracked files and update the baseline in-place. Only UNVERIFIED hits block merge;
# entries marked is_secret:false in the baseline are reviewed placeholders (e.g. .env.example
# SESSION_SECRET docs) and must never contain real credentials.
# shellcheck disable=SC2086
detect-secrets scan ${DETECT_SECRET_ADDITIONAL_ARGS} --baseline "${BASELINE_FILE}"

audit_json="$(detect-secrets audit "${BASELINE_FILE}" --report --json)"
new_secrets="$(echo "${audit_json}" | jq '[.results[]? | select(.category == "UNVERIFIED")]')"

if [ "${new_secrets}" != "[]" ] && [ -n "${new_secrets}" ]; then
  echo "Potential new secrets discovered:"
  echo "${new_secrets}" | jq -r '.[] | "- \(.filename): \(.types | join(", "))"'
  exit 1
fi

echo "No new secrets found"
