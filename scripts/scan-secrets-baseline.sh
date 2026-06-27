#!/usr/bin/env bash
# secret-scanner baseline check — detect_secrets_version: '1.5.0'
# Replaces secret-scanner/action@0.2.1 which jq-parses 1.2.x audit JSON only.
set -euo pipefail

BASELINE_FILE="${BASELINE_FILE:-.secrets.baseline}"
DETECT_SECRETS_VERSION="${DETECT_SECRETS_VERSION:-1.5.0}"
DETECT_SECRET_ADDITIONAL_ARGS="${DETECT_SECRET_ADDITIONAL_ARGS:-}"

pip install -q "detect-secrets[gibberish]==${DETECT_SECRETS_VERSION}"

echo "Running detect-secrets scan (version ${DETECT_SECRETS_VERSION}) with args: ${DETECT_SECRET_ADDITIONAL_ARGS}"
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
