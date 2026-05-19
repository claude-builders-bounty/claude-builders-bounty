import subprocess
import sys
import argparse
import os
import google.generativeai as genai

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
    Analyze the diff and return structured Markdown using Gemini.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Error: GEMINI_API_KEY not found in environment. Please set it to use the AI reviewer."

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-flash-latest')
    
    prompt = f"""
You are an expert software engineer and security auditor.
Analyze the following PR diff and provide a structured Markdown review.

Diff:
{diff[:20000]}  # Increased limit for Gemini 1.5

Your review MUST follow this structure:
### 📝 Summary of Changes
(Provide a high-level overview of what this PR achieves in 2-3 sentences.)

### 📋 Per-File Analysis
| File | Changes | Risk Level |
|------|---------|------------|
| file_path | summary of changes | Low/Medium/High |

### ⚠️ Identified Risks
- **Security**: (e.g., auth bypass, hardcoded secrets, injection vulnerabilities)
- **Performance**: (e.g., N+1 queries, inefficient loops)
- **Logic**: (e.g., edge cases not handled, breaking changes)

### 💡 Improvement Suggestions
- (Specific, actionable code improvements)

### 📊 Confidence Score
**Low / Medium / High** (Explain why)
"""
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error calling Gemini API: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description="PR Reviewer Agent - Analyze PR diffs with Gemini AI.")
    parser.add_argument("--pr", help="PR number or URL", required=True)
    parser.add_argument("--repo", help="Repository (owner/repo format)")
    parser.add_argument("--mock", action="store_true", help="Output a mock review for demonstration")
    
    args = parser.parse_args()
    
    # Handle PR URL or number
    pr_input = args.pr
    repo = args.repo
    
    if "github.com/" in pr_input:
        # Extract owner/repo and PR number from URL
        # Format: https://github.com/owner/repo/pull/123
        parts = pr_input.split("github.com/")[-1].split("/")
        if len(parts) >= 4 and parts[2] == "pull":
            repo = f"{parts[0]}/{parts[1]}"
            pr_id = parts[3]
        else:
            print(f"Error: Invalid PR URL format: {pr_input}")
            sys.exit(1)
    else:
        pr_id = pr_input

    print(f"Fetching diff for {repo if repo else ''} PR #{pr_id}...")
    diff = get_pr_diff(repo, pr_id)
    
    if args.mock:
        print("\n--- MOCK REVIEW ---")
        print("### 📝 Summary of Changes\nThis is a mock review for demonstration purposes.")
        print("\n### 📊 Confidence Score\nHigh")
    else:
        print("\n--- AI PR REVIEW ---")
        review = analyze_diff(diff)
        print(review)

if __name__ == "__main__":
    main()
