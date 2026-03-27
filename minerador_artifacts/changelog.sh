#!/usr/bin/env bash
set -euo pipefail
LAST_TAG="$(git describe --tags --abbrev=0 2>/dev/null || true)"
if [ -n "${LAST_TAG}" ]; then
  RANGE="${LAST_TAG}..HEAD"
else
  RANGE="HEAD"
fi
{
  echo "# Changelog"
  echo
  echo "## Added"
  git log --pretty=format:"- %s" ${RANGE} --grep="add\|feat" -i || true
  echo
  echo "## Changed"
  git log --pretty=format:"- %s" ${RANGE} --grep="change\|refactor" -i || true
  echo
  echo "## Fixed"
  git log --pretty=format:"- %s" ${RANGE} --grep="fix\|bug" -i || true
  echo
  echo "## Removed"
  git log --pretty=format:"- %s" ${RANGE} --grep="remove\|drop\|delete" -i || true
} > CHANGELOG.md
echo "CHANGELOG.md atualizado."
