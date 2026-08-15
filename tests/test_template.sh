#!/usr/bin/env bash
set -euo pipefail

TEMPLATE_DIR="templates/nextjs-sqlite"
FAILED=0

echo "=== Running Next.js + SQLite Template Test Suite ==="

# 1. Check template directory
if [ ! -d "$TEMPLATE_DIR" ]; then
  echo "FAIL: Directory $TEMPLATE_DIR does not exist"
  exit 1
fi
echo "PASS: Template directory exists"

# 2. Check essential files exist
for file in "CLAUDE.md" "package.json" "README.md"; do
  if [ -f "$TEMPLATE_DIR/$file" ]; then
    echo "PASS: File $TEMPLATE_DIR/$file exists"
  else
    echo "FAIL: File $TEMPLATE_DIR/$file missing"
    FAILED=1
  fi
done

# 3. Verify JSON parses cleanly
if command -v node >/dev/null 2>&1; then
  if node -e "JSON.parse(require('fs').readFileSync('$TEMPLATE_DIR/package.json', 'utf8'))" 2>/dev/null; then
    echo "PASS: package.json parses as valid JSON"
  else
    echo "FAIL: package.json is invalid JSON"
    FAILED=1
  fi
elif command -v python3 >/dev/null 2>&1; then
  if python3 -c "import json; json.load(open('$TEMPLATE_DIR/package.json'))" 2>/dev/null; then
    echo "PASS: package.json parses as valid JSON"
  else
    echo "FAIL: package.json is invalid JSON"
    FAILED=1
  fi
fi

# 4. Verify package.json contains required scripts
REQUIRED_SCRIPTS=("dev" "build" "lint" "db:generate" "db:migrate" "test")
for script in "${REQUIRED_SCRIPTS[@]}"; do
  if grep -q "\"$script\":" "$TEMPLATE_DIR/package.json"; then
    echo "PASS: package.json contains script '$script'"
  else
    echo "FAIL: package.json missing required script '$script'"
    FAILED=1
  fi
done

# 5. Verify markdown headers in CLAUDE.md and README.md conform to specifications
if grep -qi "Next.js App Router" "$TEMPLATE_DIR/CLAUDE.md" && \
   grep -qi "Server Action" "$TEMPLATE_DIR/CLAUDE.md" && \
   grep -qi "Drizzle" "$TEMPLATE_DIR/CLAUDE.md" && \
   grep -qi "SQLite" "$TEMPLATE_DIR/CLAUDE.md" && \
   grep -qi "TypeScript" "$TEMPLATE_DIR/CLAUDE.md"; then
  echo "PASS: CLAUDE.md covers Next.js App Router, Server Actions, Drizzle ORM, SQLite, and TypeScript rules"
else
  echo "FAIL: CLAUDE.md missing required architectural sections"
  FAILED=1
fi

if grep -q "3-Step Quick Start Guide" "$TEMPLATE_DIR/README.md" || grep -qi "3-step" "$TEMPLATE_DIR/README.md"; then
  echo "PASS: README.md contains 3-step guide"
else
  echo "FAIL: README.md missing 3-step guide"
  FAILED=1
fi

echo "===================================================="
if [ $FAILED -eq 0 ]; then
  echo "ALL TESTS PASSED (100% pass rate)"
  exit 0
else
  echo "SOME TESTS FAILED"
  exit 1
fi
