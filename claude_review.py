import os
import sys
import re
import json
import argparse
import urllib.request
import urllib.parse
import urllib.error

# Configure console encoding for emoji and special character support
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

def parse_pr_url(url):
    """Extract owner, repo, and PR number from a GitHub Pull Request URL."""
    pattern = r"https://github\.com/([^/]+)/([^/]+)/pull/(\d+)"
    match = re.match(pattern, url.strip())
    if not match:
        raise ValueError("Invalid GitHub PR URL. Format must be: https://github.com/owner/repo/pull/123")
    return match.group(1), match.group(2), match.group(3)

def fetch_pr_diff(owner, repo, pr_number, github_token=None):
    """Retrieve raw diff of a Pull Request from GitHub API."""
    url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github.diff")
    req.add_header("User-Agent", "Aletheia-PR-Reviewer/1.0")
    if github_token:
        req.add_header("Authorization", f"token {github_token}")
        
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        print(f"❌ Error fetching PR diff (HTTP {e.code}): {e.read().decode()}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error fetching PR diff: {e}", file=sys.stderr)
        sys.exit(1)

def post_pr_comment(owner, repo, pr_number, comment_body, github_token):
    """Post review comment back to the Pull Request on GitHub."""
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/comments"
    payload = json.dumps({"body": comment_body}).encode("utf-8")
    
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header("Authorization", f"token {github_token}")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "Aletheia-PR-Reviewer/1.0")
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            res = json.loads(response.read().decode())
            print(f"✅ Successfully posted review comment to PR: {res.get('html_url')}")
    except Exception as e:
        print(f"⚠️ Warning: Could not post comment to PR: {e}", file=sys.stderr)

def generate_review(diff_text, gemini_api_key, model="gemini-2.5-flash"):
    """Audit diff text using Gemini API and output structured Markdown review."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={gemini_api_key}"
    
    system_prompt = (
        "You are an expert software engineer and code auditor. You are reviewing a Git diff of a Pull Request.\n"
        "Your task is to analyze the diff and return a structured Markdown review comment that complies EXACTLY with these guidelines:\n\n"
        "1. Summary of Changes: Provide a concise summary of the changes introduced in the diff (exactly 2 to 3 sentences).\n"
        "2. Identified Risks: A bulleted list of potential risks, including security vulnerabilities, performance regressions, logic errors, or edge cases.\n"
        "3. Improvement Suggestions: A bulleted list of concrete recommendations to improve the code quality, readability, or reliability.\n"
        "4. Confidence Score: End with a clear confidence score: 'Confidence Score: Low', 'Confidence Score: Medium', or 'Confidence Score: High'.\n\n"
        "Your output must be formatted in clean Markdown, without any outer wrapping or extra text. Be direct, professional, and helpful."
    )
    
    prompt = f"{system_prompt}\n\nHere is the Pull Request Git Diff to analyze:\n\n```diff\n{diff_text}\n```"
    
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST"
    )
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "Aletheia-PR-Reviewer/1.0")
    
    try:
        with urllib.request.urlopen(req, timeout=45) as response:
            res_data = json.loads(response.read().decode())
            return res_data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        print(f"❌ Error calling Gemini API: {e}", file=sys.stderr)
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Aletheia PR Reviewer Agent — Community Claude Code Bounty.")
    parser.add_argument("--pr", required=True, help="Full URL of the target GitHub Pull Request.")
    parser.add_argument("--model", default="gemini-2.5-flash", help="Gemini model to use (default: gemini-2.5-flash).")
    parser.add_argument("--no-post", action="store_true", help="Disable posting comment back to the PR on GitHub.")
    args = parser.parse_args()
    
    github_token = os.environ.get("GITHUB_TOKEN")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    
    if not gemini_key:
        print("❌ Error: GEMINI_API_KEY environment variable is not set.", file=sys.stderr)
        sys.exit(1)
        
    try:
        owner, repo, pr_number = parse_pr_url(args.pr)
    except ValueError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
        
    print(f"🔍 Fetching diff for PR #{pr_number} in {owner}/{repo}...")
    diff_text = fetch_pr_diff(owner, repo, pr_number, github_token)
    
    if not diff_text.strip():
        print("⚠️ Info: PR diff is empty. Nothing to review.", file=sys.stderr)
        sys.exit(0)
        
    print(f"⚙️ Running AI code audit using model '{args.model}'...")
    review_markdown = generate_review(diff_text, gemini_key, args.model)
    
    print("\n" + "="*60)
    print("                 AI CODE AUDIT REVIEW SUMMARY            ")
    print("="*60)
    print(review_markdown)
    print("="*60 + "\n")
    
    if github_token and not args.no_post:
        print("📤 Posting review comment back to GitHub PR...")
        post_pr_comment(owner, repo, pr_number, review_markdown, github_token)

if __name__ == "__main__":
    main()
