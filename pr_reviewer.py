import os
import sys
import requests
import json

# Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

def get_pr_diff(repo, pr_number):
    url = f"https://api.github.com/repos/{repo}/pulls/{pr_number}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3.diff"}
    response = requests.get(url, headers=headers)
    return response.text

def analyze_diff_with_ai(diff):
    # This is a placeholder for the actual LLM call
    # In a real environment, we use the Anthropic API
    prompt = f"Review the following git diff and provide structured feedback:\n\n{diff}"
    # Simulated response
    return "### AI Code Review\n- **Security**: No immediate issues found.\n- **Performance**: Consider optimizing loops.\n- **Style**: Follow PEP8 conventions."

def post_comment(repo, pr_number, comment):
    url = f"https://api.github.com/repos/{repo}/issues/{pr_number}/comments"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Content-Type": "application/json"}
    payload = {"body": comment}
    requests.post(url, headers=headers, json=payload)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 pr_reviewer.py <repo> <pr_number>")
        sys.exit(1)
    
    repo_name = sys.argv[1]
    pr_num = sys.argv[2]
    
    diff_text = get_pr_diff(repo_name, pr_num)
    review = analyze_diff_with_ai(diff_text)
    post_comment(repo_name, pr_num, review)
    print(f"[SUCCESS] Review posted to {repo_name} PR #{pr_num}")
