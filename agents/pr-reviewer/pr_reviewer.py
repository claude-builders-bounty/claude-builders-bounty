import subprocess
import sys
import argparse
import os

def get_pr_diff(repo, pr_number):
    """Fetch the diff for a PR using gh CLI."""
    try:
        cmd = ['gh', 'pr', 'diff', str(pr_number)]
        if repo:
            cmd.extend(['--repo', repo])
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error fetching PR diff: {e.stderr}")
        sys.exit(1)
    except FileNotFoundError:
        print("Error: 'gh' CLI not found. Please install GitHub CLI (https://cli.github.com/).")
        sys.exit(1)

def analyze_diff(diff):
    """
    Analyze the diff and return structured Markdown.
    In a production agent, this would call an LLM API.
    """
    # This is a placeholder for the actual LLM integration.
    # For now, it constructs a prompt that the user can use, 
    # or it could be extended to call Gemini/Claude API.
    
    prompt = f"""
Analyze the following PR diff and provide a structured Markdown review.

Diff:
{diff[:10000]}  # Truncated for prompt length limits

Output Format:
### 📝 Summary of Changes
(2-3 sentences)

### ⚠️ Identified Risks
- (list risks)

### 💡 Improvement Suggestions
- (list suggestions)

### 📊 Confidence Score
Low / Medium / High
"""
    return prompt

def main():
    parser = argparse.ArgumentParser(description="PR Reviewer Agent - Analyze PR diffs with AI.")
    parser.add_argument("pr", help="PR number or URL")
    parser.add_argument("--repo", help="Repository (owner/repo format)")
    parser.add_argument("--mock", action="store_true", help="Output a mock review for demonstration")
    
    args = parser.parse_args()
    
    # Simple PR parsing (supports number or URL)
    pr_id = args.pr
    if "pull/" in pr_id:
        pr_id = pr_id.split("pull/")[-1].strip("/")
    
    print(f"Fetching diff for PR #{pr_id}...")
    diff = get_pr_diff(args.repo, pr_id)
    
    if args.mock:
        print("\n--- MOCK REVIEW ---")
        print("### 📝 Summary of Changes\nThis is a mock review for demonstration purposes.")
        print("\n### 📊 Confidence Score\nHigh")
    else:
        print("\n--- LLM PROMPT (Copy this to Claude/Gemini) ---")
        print(analyze_diff(diff))

if __name__ == "__main__":
    main()
