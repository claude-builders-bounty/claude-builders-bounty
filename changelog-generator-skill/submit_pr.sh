#!/bin/bash
# submit_pr.sh - Submit CHANGELOG generator skill for $50 bounty
# Requires: git, curl, GitHub Personal Access Token

set -e

# Configuration
REPO_OWNER="claude-builders-bounty"
REPO_NAME="claude-builders-bounty"
ISSUE_NUMBER=1
SKILL_DIR="/root/.openclaw/workspace/changelog-generator-skill"
BRANCH_NAME="changelog-generator-skill"
PR_TITLE="Add CHANGELOG generator skill for issue #1"
PR_DESCRIPTION="This PR adds a complete CHANGELOG generator skill as requested in issue #1.

## Features
- Python script for generating structured CHANGELOG from git history
- Bash wrapper script (changelog.sh) for easy command-line usage  
- Claude Code SKILL.md for integration with Claude Code
- Auto-categorization of commits into Added/Fixed/Changed/Removed
- Support for multiple output formats (Markdown, JSON, text)
- Complete documentation with 3-step setup

## Testing
Tested on a real repository, sample output included in TEST_CHANGELOG.md

## Acceptance Criteria Met
✅ Works via /generate-changelog command (Claude Code skill)
✅ Works via bash changelog.sh (bash wrapper)
✅ Fetches commits since the last git tag
✅ Auto-categorizes into Added/Fixed/Changed/Removed
✅ Outputs properly formatted CHANGELOG.md
✅ Tested on a real GitHub repo (sample output included)
✅ README with setup instructions in 3 steps or fewer"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== CHANGELOG Generator PR Submission ===${NC}"
echo "Repository: $REPO_OWNER/$REPO_NAME"
echo "Issue: #$ISSUE_NUMBER"
echo "Skill directory: $SKILL_DIR"
echo ""

# Step 1: Check for GitHub token
if [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${YELLOW}⚠️  GITHUB_TOKEN environment variable not set${NC}"
    echo "Please set your GitHub Personal Access Token:"
    echo "  export GITHUB_TOKEN='your_token_here'"
    echo "Or pass it as an argument: ./submit_pr.sh your_token_here"
    
    if [ $# -eq 1 ]; then
        GITHUB_TOKEN="$1"
        echo -e "${GREEN}✅ Using token from command line argument${NC}"
    else
        echo -e "${RED}❌ No GitHub token provided. Exiting.${NC}"
        exit 1
    fi
fi

# Step 2: Comment /opire try on the issue
echo -e "${GREEN}📝 Step 1: Commenting '/opire try' on issue #$ISSUE_NUMBER${NC}"
COMMENT_RESPONSE=$(curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/issues/$ISSUE_NUMBER/comments" \
  -d '{"body":"/opire try"}')

if echo "$COMMENT_RESPONSE" | grep -q '"message": "Not Found"'; then
    echo -e "${RED}❌ Failed to post comment. Check token permissions.${NC}"
    echo "Response: $COMMENT_RESPONSE"
    exit 1
else
    echo -e "${GREEN}✅ Successfully commented '/opire try' on issue #$ISSUE_NUMBER${NC}"
fi

# Step 3: Fork the repository (if not already forked)
echo -e "${GREEN}🍴 Step 2: Checking fork status${NC}"
FORK_CHECK=$(curl -s -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/forks")

# Check if we already have a fork
FORK_EXISTS=$(echo "$FORK_CHECK" | grep -c '"fork": true' || true)

if [ "$FORK_EXISTS" -eq 0 ]; then
    echo -e "${YELLOW}Creating fork of $REPO_OWNER/$REPO_NAME...${NC}"
    FORK_RESPONSE=$(curl -s -X POST \
      -H "Authorization: token $GITHUB_TOKEN" \
      -H "Accept: application/vnd.github.v3+json" \
      "https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/forks")
    
    if echo "$FORK_RESPONSE" | grep -q '"message":'; then
        echo -e "${RED}❌ Failed to create fork. Check token permissions.${NC}"
        echo "Response: $FORK_RESPONSE"
        exit 1
    fi
    
    FORK_OWNER=$(echo "$FORK_RESPONSE" | grep '"login"' | head -1 | cut -d'"' -f4)
    echo -e "${GREEN}✅ Fork created for user: $FORK_OWNER${NC}"
else
    FORK_OWNER=$(echo "$FORK_CHECK" | grep '"login"' | head -1 | cut -d'"' -f4)
    echo -e "${GREEN}✅ Using existing fork for user: $FORK_OWNER${NC}"
fi

# Step 4: Clone the fork
echo -e "${GREEN}📥 Step 3: Cloning repository${NC}"
if [ -d "/tmp/$REPO_NAME" ]; then
    rm -rf "/tmp/$REPO_NAME"
fi

git clone "https://github.com/$FORK_OWNER/$REPO_NAME.git" "/tmp/$REPO_NAME"
cd "/tmp/$REPO_NAME"

# Step 5: Create and checkout new branch
echo -e "${GREEN}🌿 Step 4: Creating branch '$BRANCH_NAME'${NC}"
git checkout -b "$BRANCH_NAME"

# Step 6: Copy skill files
echo -e "${GREEN}📁 Step 5: Copying skill files${NC}"
SKILL_DEST="skills/changelog-generator"
mkdir -p "$SKILL_DEST"

cp -r "$SKILL_DIR"/* "$SKILL_DEST/"
echo -e "${GREEN}✅ Skill files copied to $SKILL_DEST${NC}"

# Step 7: Create sample output
echo -e "${GREEN}📄 Step 6: Creating sample output${NC}"
cd "$SKILL_DEST"
python3 scripts/generate_changelog.py /tmp/$REPO_NAME --output SAMPLE_CHANGELOG.md
cd "/tmp/$REPO_NAME"

# Step 8: Commit changes
echo -e "${GREEN}💾 Step 7: Committing changes${NC}"
git add .
git commit -m "Add CHANGELOG generator skill for issue #1

- Complete CHANGELOG generator skill with Python script and bash wrapper
- Auto-categorization of commits into Added/Fixed/Changed/Removed  
- Support for multiple output formats (Markdown, JSON, text)
- Tested on real repository with sample output
- 3-step setup instructions in README.md

Addresses issue #1"

# Step 9: Push to fork
echo -e "${GREEN}📤 Step 8: Pushing to fork${NC}"
git push origin "$BRANCH_NAME"

# Step 10: Create Pull Request
echo -e "${GREEN}🔀 Step 9: Creating Pull Request${NC}"
PR_RESPONSE=$(curl -s -X POST \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  "https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/pulls" \
  -d "{
    \"title\": \"$PR_TITLE\",
    \"body\": \"$PR_DESCRIPTION\",
    \"head\": \"$FORK_OWNER:$BRANCH_NAME\",
    \"base\": \"main\"
  }")

if echo "$PR_RESPONSE" | grep -q '"message":'; then
    echo -e "${RED}❌ Failed to create Pull Request${NC}"
    echo "Response: $PR_RESPONSE"
    exit 1
else
    PR_URL=$(echo "$PR_RESPONSE" | grep '"html_url"' | cut -d'"' -f4)
    echo -e "${GREEN}✅ Pull Request created successfully!${NC}"
    echo -e "${GREEN}🔗 PR URL: $PR_URL${NC}"
fi

# Step 11: Cleanup
echo -e "${GREEN}🧹 Step 10: Cleaning up${NC}"
cd /tmp
rm -rf "/tmp/$REPO_NAME"

echo -e "${GREEN}🎉 All steps completed!${NC}"
echo -e "${YELLOW}💰 The $50 bounty will be automatically released when the PR is merged.${NC}"
echo ""
echo "Next steps:"
echo "1. Wait for maintainer review"
echo "2. Address any feedback if needed"
echo "3. PR will be merged"
echo "4. Payment will be released automatically via Opire"