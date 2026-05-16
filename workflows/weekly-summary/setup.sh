#!/bin/bash
# setup.sh — One-command setup for Weekly GitHub Activity Summary
# Sets up environment and imports workflow into n8n

set -euo pipefail

echo "🚀 Weekly GitHub Activity Summary — Setup"
echo ""

# ── Config ─────────────────────────────────────────────────────────
N8N_URL="${N8N_URL:-http://localhost:5678}"
N8N_API_KEY="${N8N_API_KEY:-}"
WORKFLOW_FILE="weekly-summary-workflow.json"

# ── Check prerequisites ────────────────────────────────────────────
echo "📋 Checking prerequisites..."

if ! command -v node &>/dev/null; then
  echo "❌ Node.js is required for n8n. Install it first."
  exit 1
fi

# ── Validate environment ───────────────────────────────────────────
if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
  echo "⚠️  ANTHROPIC_API_KEY not set. Claude API won't work."
  echo "   Edit your n8n environment to add it."
fi

if [ -z "${GITHUB_PAT:-}" ]; then
  echo "⚠️  GITHUB_PAT not set. GitHub API calls may be rate-limited."
fi

# ── Check file exists ──────────────────────────────────────────────
if [ ! -f "$WORKFLOW_FILE" ]; then
  echo "❌ Workflow file '$WORKFLOW_FILE' not found."
  echo "   Download it first:"
  echo "   curl -sfLO https://raw.githubusercontent.com/..."
  exit 1
fi

# ── Validate JSON ──────────────────────────────────────────────────
echo "✅ Validating workflow JSON..."
python3 -c "import json; json.load(open('$WORKFLOW_FILE')); print('   JSON is valid')"

# ── Import into n8n (if API key provided) ──────────────────────────
if [ -n "$N8N_API_KEY" ]; then
  echo ""
  echo "📦 Importing workflow into n8n at $N8N_URL..."
  
  RESPONSE=$(curl -sf -X POST "$N8N_URL/rest/workflows" \
    -H "Authorization: Bearer $N8N_API_KEY" \
    -H "Content-Type: application/json" \
    -d @"$WORKFLOW_FILE" 2>&1 || true)
  
  if echo "$RESPONSE" | grep -q '"id"'; then
    WORKFLOW_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])")
    echo "✅ Imported! Workflow ID: $WORKFLOW_ID"
  else
    echo "⚠️  Could not auto-import. Import manually in n8n UI."
    echo "   Open $N8N_URL → Workflows → Import from File"
  fi
else
  echo ""
  echo "📦 To import into n8n:"
  echo "   1. Open n8n → Workflows → Import from File"
  echo "   2. Upload $WORKFLOW_FILE"
  echo "   3. Set environment variables (see README)"
  echo "   4. Activate the workflow ✅"
fi

echo ""
echo "🎉 Setup complete!"
