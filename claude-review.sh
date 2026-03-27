#!/bin/bash
# claude-review — CLI tool for AI-powered PR code review
# Usage: claude-review --pr https://github.com/owner/repo/pull/123
#        claude-review --diff /path/to/diff.txt

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

usage() {
  echo "claude-review — AI-powered PR code review"
  echo ""
  echo "Usage:"
  echo "  claude-review --pr <url>         Review a GitHub PR"
  echo "  claude-review --diff <file>      Review a local diff file"
  echo "  claude-review --help             Show this help"
  echo ""
  echo "Examples:"
  echo "  claude-review --pr https://github.com/owner/repo/pull/123"
  echo "  claude-review --diff /tmp/changes.diff"
}

if [ $# -eq 0 ]; then
  usage
  exit 1
fi

MODE="diff"
INPUT=""

while [ $# -gt 0 ]; do
  case "$1" in
    --pr)
      MODE="pr"
      INPUT="$2"
      shift 2
      ;;
    --diff)
      MODE="diff"
      INPUT="$2"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo -e "${RED}Unknown option: $1${NC}"
      usage
      exit 1
      ;;
  esac
done

if [ -z "$INPUT" ]; then
  echo -e "${RED}Error: No input provided${NC}"
  usage
  exit 1
fi

echo -e "${GREEN}Fetching PR diff...${NC}"

if [ "$MODE" = "pr" ]; then
  if [[ ! "$INPUT" =~ github\.com/([^/]+)/([^/]+)/pull/([0-9]+) ]]; then
    echo -e "${RED}Error: Invalid GitHub PR URL${NC}"
    exit 1
  fi
  OWNER="${BASH_REMATCH[1]}"
  REPO="${BASH_REMATCH[2]}"
  PR_NUM="${BASH_REMATCH[3]}"
  DIFF_URL="https://github.com/${OWNER}/${REPO}/pull/${PR_NUM}.diff"
  DIFF_CONTENT=$(curl -s -H "Accept: application/vnd.github.v3.diff" "$DIFF_URL")
else
  DIFF_CONTENT=$(cat "$INPUT")
fi

if [ -z "$DIFF_CONTENT" ] || [ ${#DIFF_CONTENT} -lt 50 ]; then
  echo -e "${RED}Error: Could not fetch diff content${NC}"
  exit 1
fi

echo -e "${GREEN}Sending to Claude for analysis...${NC}"

PROMPT="You are a senior software engineer reviewing a code change. Analyze the following diff and provide a structured review in this exact JSON format (no markdown, no extra text):

{
  \"summary\": \"2-3 sentence summary of what this PR changes\",
  \"risks\": [\"list of specific risks or concerns\"],
  \"suggestions\": [\"actionable improvement suggestions\"],
  \"confidence\": \"Low|Medium|High\"
}

DIFF:
$DIFF_CONTENT"

RESPONSE=$(curl -s -X POST "https://api.anthropic.com/v1/messages" \
  -H "x-api-key: ${ANTHROPIC_API_KEY}" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d "{\"model\":\"claude-sonnet-4-20250514\",\"max_tokens\":1024,\"messages\":[{\"role\":\"user\",\"content\":$(printf '%s' "$PROMPT" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))")}}]}")

TEXT=$(echo "$RESPONSE" | python3 -c "
import sys,json
try:
    d=json.load(sys.stdin)
    print(d.get('content',[{}])[0].get('text','No response'))
except: print('Error:', sys.stdin.read()[:200])
" 2>/dev/null)

if [ -z "$TEXT" ] || echo "$TEXT" | grep -q "Error"; then
  echo -e "${YELLOW}Raw API response:${NC}"
  echo "$RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$RESPONSE"
else
  echo "$TEXT" | python3 -m json.tool 2>/dev/null || echo "$TEXT"
fi
