#!/bin/bash
echo "Testing hook..."
./pre-tool-use-hook.sh rm -rf / 2>/dev/null && echo "FAIL" || echo "PASS: rm -rf / blocked"
./pre-tool-use-hook.sh echo "hello" && echo "PASS: safe command allowed"
