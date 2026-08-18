#!/bin/bash
# Test script for PR Review Agent
# Run this to test the agent on real PRs
# Requires: ANTHROPIC_API_KEY and optional GITHUB_TOKEN

set -e

echo "=== PR Review Agent Test Script ==="
echo ""

# Check for API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "ERROR: ANTHROPIC_API_KEY environment variable not set"
    echo "Set it with: export ANTHROPIC_API_KEY='your-key'"
    exit 1
fi

echo "✓ ANTHROPIC_API_KEY found"
echo ""

# Test PR URLs (replace with actual PRs)
TEST_PRS=(
    "https://github.com/claude-builders-bounty/claude-builders-bounty/pull/1"
    "https://github.com/claude-builders-bounty/claude-builders-bounty/pull/2"
)

for i in "${!TEST_PRS[@]}"; do
    PR_URL="${TEST_PRS[$i]}"
    OUTPUT_FILE="test_output_$((i+1)).md"
    
    echo "Testing PR $((i+1)): $PR_URL"
    echo "Output: $OUTPUT_FILE"
    
    claude-review --pr "$PR_URL" --output "$OUTPUT_FILE"
    
    if [ -f "$OUTPUT_FILE" ]; then
        echo "✓ Review generated successfully"
        echo "File size: $(wc -c < "$OUTPUT_FILE") bytes"
    else
        echo "✗ Failed to generate review"
        exit 1
    fi
    
    echo ""
done

echo "=== All tests complete ==="
echo "Check test_output_1.md and test_output_2.md for results"