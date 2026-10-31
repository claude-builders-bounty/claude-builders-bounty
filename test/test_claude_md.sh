#!/usr/bin/env bash
# Verification test suite for CLAUDE.md
set -euo pipefail

FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/CLAUDE.md"
PASS=0
FAIL=0
TOTAL=0

assert_contains() {
  local name="$1"
  local pattern="$2"
  TOTAL=$((TOTAL + 1))
  if grep -qiE "$pattern" "$FILE"; then
    echo "  ✅ PASS: $name"
    PASS=$((PASS + 1))
  else
    echo "  ❌ FAIL: $name (pattern '$pattern' not found)"
    FAIL=$((FAIL + 1))
  fi
}

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║    CLAUDE.MD SPECIFICATION COMPLIANCE TEST SUITE           ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# 1. Line count check (< 100 LoC constraint)
TOTAL=$((TOTAL + 1))
LINES=$(wc -l < "$FILE" | tr -d ' ')
if [ "$LINES" -le 100 ]; then
  echo "  ✅ PASS: Conciseness guard ($LINES lines <= 100 line target)"
  PASS=$((PASS + 1))
else
  echo "  ❌ FAIL: Too verbose ($LINES lines > 100)"
  FAIL=$((FAIL + 1))
fi

# 2. Stack coverage
assert_contains "Next.js 15 App Router" "Next\.js 15.*App Router"
assert_contains "React 19" "React 19"
assert_contains "TypeScript 5" "TypeScript 5"
assert_contains "better-sqlite3 / Turso" "better-sqlite3.*Turso"
assert_contains "Drizzle ORM" "Drizzle ORM"

# 3. SQLite Concurrency & Safety Pragmas
assert_contains "WAL mode pragma" "journal_mode\s*=\s*WAL"
assert_contains "Foreign keys pragma" "foreign_keys\s*=\s*ON"
assert_contains "Busy timeout pragma" "busy_timeout\s*=\s*5000"
assert_contains "Additive migration rule" "additive"

# 4. Architectural Rules
assert_contains "Server Components default" "Server Components by default"
assert_contains "use client boundary rule" "use client.*leaf"
assert_contains "Server Actions with use server" "use server"
assert_contains "server-only db protection" "server-only"
assert_contains "Parameterized queries" "Parameterized queries"

# 5. Core developer commands
assert_contains "Dev command" "npm run dev"
assert_contains "Build command" "npm run build"
assert_contains "DB migration command" "npm run db:migrate"

# 6. Negative anti-pattern guards (What We Do NOT Do)
assert_contains "What We Do NOT Do section" "What We Do NOT Do"
assert_contains "No Pages router anti-pattern" "Pages Router"
assert_contains "No useEffect fetch anti-pattern" "useEffect"
assert_contains "No drop table / sync force anti-pattern" "DROP TABLE|\.sync"
assert_contains "No raw SQL string concatenation" "concatenation"

echo ""
echo "╔══════════════════════════════════════════════════════════════╗"
echo "║    TEST RESULTS: $PASS/$TOTAL PASSED   ($FAIL failed)"
printf "║    %-57s║\n" "$([ $FAIL -eq 0 ] && echo '🏆 ALL CRITERIA VERIFIED' || echo '⚠️  SOME FAILED')"
echo "╚══════════════════════════════════════════════════════════════╝"
