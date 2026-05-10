#!/bin/bash
set -euo pipefail

PASS=0; FAIL=0
test() { local n="$1"; shift; echo -n "  🧪 $n... "; if eval "$@" 2>/dev/null; then echo "✅"; PASS=$((PASS+1)); else echo "❌"; FAIL=$((FAIL+1)); fi; }

echo "🧪 Open-Reviewer Test Suite"
echo "══════════════════════════════"

SCRIPT="../open-reviewer.sh"
test "Help显示" "$SCRIPT --help 2>&1 | grep -q Usage"

bash "$SCRIPT" --pr https://github.com/psf/requests/pull/7401 --output /tmp/_ot_small 2>/dev/null
test "小PR=HIGH" "python3 -c \"import json; assert json.load(open('/tmp/_ot_small.json'))['confidence']['label']=='HIGH'\""

bash "$SCRIPT" --pr https://github.com/astral-sh/uv/pull/19322 --output /tmp/_ot_large 2>/dev/null
test "大PR=LOW/MEDIUM" "python3 -c \"import json; d=json.load(open('/tmp/_ot_large.json')); assert d['confidence']['label'] in ('LOW','MEDIUM')\""

test "JSON含reviews+confidence" "python3 -c \"import json; d=json.load(open('/tmp/_ot_small.json')); assert 'reviews' in d and 'confidence' in d\""
test "MD文件存在" "test -f /tmp/_ot_small.md && grep -q Confidence /tmp/_ot_small.md"

echo ""
echo "📊 $PASS 通过, $FAIL 失败"
[ "$FAIL" -eq 0 ] || exit 1
