#!/usr/bin/env python3
import sys
import os
import urllib.request
import urllib.parse
import json
import re

def load_env():
    # Manually load .env variables without external packages
    current = os.getcwd()
    for _ in range(5):
        env_path = os.path.join(current, ".env")
        if os.path.exists(env_path):
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        # Remove potential wrapping quotes
                        val = v.strip().strip("'").strip('"')
                        os.environ[k.strip()] = val
            break
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent

def fetch_diff(pr_url):
    # Standardize URL to get raw diff
    if not pr_url.endswith(".diff"):
        # Remove trailing slashes
        pr_url = pr_url.rstrip("/")
        # If it matches /pull/123 format, append .diff
        if "/pull/" in pr_url:
            pr_url = pr_url + ".diff"
        else:
            raise ValueError("Invalid Pull Request URL. Must be in the format: https://github.com/owner/repo/pull/num")

    print(f"Fetching raw diff from: {pr_url}...")
    headers = {"User-Agent": "Mozilla/5.0"}
    req = urllib.request.Request(pr_url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.read().decode("utf-8", errors="ignore")
    except Exception as e:
        raise RuntimeError(f"Failed to fetch PR diff: {e}")

def run_static_review(diff_content):
    # Fallback static analysis engine
    print("No valid AI API Key found (or query failed). Running rule-based static review...")
    
    files_changed = []
    risks = []
    suggestions = []
    
    current_file = None
    added_lines_count = 0
    removed_lines_count = 0
    
    # Simple parsing of diff
    for line in diff_content.splitlines():
        if line.startswith("diff --git"):
            parts = line.split(" ")
            if len(parts) >= 4:
                current_file = parts[3].lstrip("b/")
                files_changed.append(current_file)
        elif line.startswith("+++ b/"):
            current_file = line[6:]
        elif line.startswith("+") and not line.startswith("+++"):
            added_lines_count += 1
            added_code = line[1:].strip()
            
            # Risk check: Hardcoded keys/secrets
            if any(x in added_code.lower() for x in ["api_key", "apikey", "secret", "password", "token"]) and "=" in added_code:
                # Check if it has string assignment
                if re.search(r'["\'][a-zA-Z0-9_\-]{8,}["\']', added_code):
                    risks.append(f"Potential hardcoded secret/credential in `{current_file}`: `{added_code[:50]}...`")
            
            # Risk check: Debugging statements left behind
            if "console.log(" in added_code or "print(" in added_code:
                if current_file and not any(x in current_file.lower() for x in ["test", "spec", "scratch"]):
                    risks.append(f"Active debug logging left in production code in `{current_file}`: `{added_code}`")
                    
            # Suggestion check: Missing error handling in async actions
            if "await " in added_code and "try" not in added_code and "catch" not in added_code:
                suggestions.append(f"Ensure proper error handling/try-catch wrapper for async call in `{current_file}`: `{added_code}`")
                
        elif line.startswith("-") and not line.startswith("---"):
            removed_lines_count += 1

    # Compile findings
    if not risks:
        risks.append("No critical security risks or debugging artifacts detected in the static check.")
    if not suggestions:
        suggestions.append("Code structure looks clean. Consider adding unit tests for new changes if not already present.")

    summary = f"Analyzed {len(files_changed)} files containing {added_lines_count} additions and {removed_lines_count} deletions. "
    if files_changed:
        summary += f"Key modified files: " + ", ".join([f"`{f}`" for f in files_changed[:5]])
        if len(files_changed) > 5:
            summary += f" and {len(files_changed) - 5} more."
    else:
        summary += "No file changes detected."

    markdown_report = f"""# PR Code Review Report (Static Fallback Mode)

## Summary of Changes
{summary}

## Identified Risks
{chr(10).join([f'- [ ] {r}' for r in risks])}

## Improvement Suggestions
{chr(10).join([f'- {s}' for s in suggestions])}

## Confidence Score
**Confidence Score**: Medium (Static Rules Analysis)
"""
    return markdown_report

def run_ai_review(diff_content, api_key, model_type="gemini"):
    prompt = f"""You are a professional senior code reviewer. Review the following git diff and provide a structured Markdown report.
You MUST output exactly the following sections in Markdown:

# PR Code Review Report

## Summary of Changes
(Provide a concise 2-3 sentences summarizing what changes are made in the PR)

## Identified Risks
(List any identified security risks, performance bugs, logic errors, or code smells as task items, e.g. - [ ] risk. If none, write "None detected.")

## Improvement Suggestions
(List specific code improvements, optimizations, readability fixes, or recommendations. If none, write "None.")

## Confidence Score
**Confidence Score**: (Low / Medium / High - choose one based on review confidence)

Here is the raw git diff:
```diff
{diff_content[:15000]}
```
"""
    
    if model_type == "gemini":
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        data = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                res = json.loads(response.read().decode("utf-8"))
                return res["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            print(f"Gemini API call failed: {e}")
            return None
    return None

def main():
    load_env()
    
    if len(sys.argv) < 3 or sys.argv[1] != "--pr":
        print("Usage: claude-review --pr <https://github.com/owner/repo/pull/num>")
        sys.exit(1)
        
    pr_url = sys.argv[2]
    
    try:
        diff_content = fetch_diff(pr_url)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
        
    # Check for API Key
    api_key = os.getenv("GEMINI_API_KEY")
    
    report = None
    if api_key and api_key != "your_key_here":
        print("API Key found. Querying Gemini AI...")
        report = run_ai_review(diff_content, api_key, "gemini")
        
    if not report:
        report = run_static_review(diff_content)
        
    print("\n=== GENERATED REVIEW REPORT ===\n")
    print(report)
    
    # Save the output to pr_review_report.md
    output_file = "pr_review_report.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\nSUCCESS: Review report saved to {output_file}")

if __name__ == "__main__":
    main()
