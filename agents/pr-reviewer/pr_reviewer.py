import subprocess
import sys
import argparse
import os
import re
import json
import google.generativeai as genai
import anthropic
from datetime import datetime

# Security patterns to scan in the diff
SECURITY_PATTERNS = {
    "Potential Secret/Token": r"(?i)(password|secret|key|token|auth|pwd)[ \t]*[:=][ \t]*['\"][^'\"]+['\"]",
    "Hardcoded AWS/API Key": r"[A-Za-z0-9/+=]{40,}",
    "Private Key": r"-----BEGIN [A-Z ]+ PRIVATE KEY-----",
    "Environment File": r"\.env(\..+)?",
    "Dangerous Permission": r"chmod\s+777",
    "SQL Injection Pattern": r"(\%27)|(\')|(\-\-)|(\%23)|(#)",
    "XSS Pattern": r"<script.*?>.*?</script>",
    "Insecure Eval": r"eval\(.*?\)",
}

SENSITIVE_FILES = [
    ".env", "config.py", "settings.py", "manage.py", "Dockerfile", 
    "docker-compose.yml", "package.json", "requirements.txt"
]

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

def calculate_risk_score(diff, security_findings):
    """Calculate a quantitative risk score (0-10)."""
    score = 0
    
    # 1. Security Findings (up to 4 points)
    score += min(len(security_findings) * 2, 4)
    
    # 2. Impact Scale (up to 3 points)
    line_count = len(diff.splitlines())
    if line_count > 500:
        score += 3
    elif line_count > 100:
        score += 2
    elif line_count > 20:
        score += 1
        
    # 3. Sensitive Files (up to 3 points)
    sensitive_count = 0
    for f in SENSITIVE_FILES:
        if f in diff:
            sensitive_count += 1
    score += min(sensitive_count, 3)
    
    return min(score, 10)

def calculate_confidence_score(diff):
    """
    Calculate a confidence score (0-10) for the AI review.
    Factors: Diff size, file count, and presence of tests.
    """
    score = 10
    
    # 1. Diff Size (Large diffs reduce AI focus/confidence)
    line_count = len(diff.splitlines())
    if line_count > 1000:
        score -= 4
    elif line_count > 500:
        score -= 2
        
    # 2. File Breadth
    file_count = diff.count("diff --git")
    if file_count > 20:
        score -= 3
    elif file_count > 10:
        score -= 1
        
    # 3. Verification Context (Lack of tests reduces confidence)
    has_tests = any(kw in diff.lower() for kw in ["test_", "_test", "spec", "pytest", "unittest"])
    if not has_tests:
        score -= 2
        
    return max(score, 1)

def scan_security(diff):
    """Scan the diff for potential security risks."""
    findings = []
    for name, pattern in SECURITY_PATTERNS.items():
        if re.search(pattern, diff):
            findings.append(name)
    return findings

def analyze_diff(diff, security_findings, engine="claude", mock=False):
    """
    Analyze the diff and return structured Markdown using AI.
    """
    risk_score = calculate_risk_score(diff, security_findings)
    risk_label = "CRITICAL" if risk_score >= 8 else "HIGH" if risk_score >= 6 else "MEDIUM" if risk_score >= 3 else "LOW"
    
    conf_score = calculate_confidence_score(diff)
    conf_label = "High" if conf_score >= 8 else "Medium" if conf_score >= 5 else "Low"
    
    if mock:
        return f"""
## 🤖 AI PR Review (MOCK)

### 📊 Risk Assessment
**Score: {risk_score}/10** | **Level: {risk_label}**

### 🎯 Review Confidence
**Score: {conf_score}/10** | **Level: {conf_label}**

### 📝 Summary of Changes
This is a mock review. The diff contains {len(diff)} characters.
"""

    security_note = ""
    if security_findings:
        security_note = f"\n⚠️ **Automated Scan Findings:** Potential risks detected: {', '.join(security_findings)}\n"

    prompt = f"""
You are an expert Senior Software Engineer and Security Auditor.
Analyze the following PR diff and provide a comprehensive, structured Markdown review.

---
### 📊 Risk Assessment (Pre-Calculated)
- **Calculated Risk Score**: {risk_score}/10
- **Risk Level**: {risk_label}
- **Factors**: {len(security_findings)} security hits, {len(diff.splitlines())} lines changed.

### 🎯 Review Confidence (Pre-Calculated)
- **Confidence Score**: {conf_score}/10
- **Confidence Level**: {conf_label}
---

{security_note}

Diff:
{diff[:30000]} 

Your review MUST follow this structure:

## 🤖 AI PR Review

### 📊 Risk Profile
(Briefly explain the {risk_score}/10 score and {risk_label} level. Mention specific risk factors like security findings or diff size.)

### 🎯 Review Confidence
(Explain why the confidence is {conf_label} ({conf_score}/10). Mention if the PR includes tests or if the diff is too large for perfect accuracy.)

### 📝 Summary of Changes
(High-level overview of what this PR achieves in 2-3 sentences.)

### 📋 Per-File Analysis
| File | Changes | Risk Level |
|------|---------|------------|
| file_path | summary of changes | Low/Medium/High |

### ⚠️ Identified Risks
- **Security**: (e.g., auth bypass, hardcoded secrets, injection vulnerabilities)
- **Performance**: (e.g., N+1 queries, inefficient loops)
- **Logic**: (e.g., edge cases not handled, breaking changes)
- **Maintainability**: (e.g., code duplication, lack of documentation, complex logic)

### 💡 Improvement Suggestions
- (Specific, actionable code improvements or refactorings)

---
*Review generated by PR Reviewer Agent v3.2 ({engine.capitalize()}) — High Signal Defense Enabled*
"""
    
    if engine == "claude":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("Warning: ANTHROPIC_API_KEY not found. Falling back to Gemini...")
            return analyze_diff(diff, security_findings, engine="gemini", mock=mock)
        
        client = anthropic.Anthropic(api_key=api_key)
        try:
            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                system="You are a senior code reviewer.",
                messages=[{"role": "user", "content": prompt}]
            )
            return message.content[0].text
        except Exception as e:
            return f"Error calling Claude API: {str(e)}"

    else:  # Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "Error: Neither ANTHROPIC_API_KEY nor GEMINI_API_KEY found."

        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error calling Gemini API: {str(e)}"

def main():
    parser = argparse.ArgumentParser(description="PR Reviewer Agent - Analyze PR diffs with AI.")
    parser.add_argument("--pr", help="PR number or URL", required=True)
    parser.add_argument("--repo", help="Repository (owner/repo format)")
    parser.add_argument("--engine", choices=["claude", "gemini"], default="claude", help="AI engine to use (default: claude)")
    parser.add_argument("--output", help="Output file path (Markdown)")
    parser.add_argument("--mock", action="store_true", help="Run in mock mode")
    
    args = parser.parse_args()
    
    # Handle PR URL or number
    pr_input = args.pr
    repo = args.repo
    
    if "github.com/" in pr_input:
        # Extract owner/repo and PR number from URL
        parts = pr_input.split("github.com/")[-1].split("/")
        if len(parts) >= 4 and parts[2] == "pull":
            repo = f"{parts[0]}/{parts[1]}"
            pr_id = parts[3]
        else:
            print(f"Error: Invalid PR URL format: {pr_input}")
            sys.exit(1)
    else:
        pr_id = pr_input

    print(f"🚀 Fetching diff for {repo if repo else ''} PR #{pr_id}...")
    diff = get_pr_diff(repo, pr_id)
    
    print("🔍 Scanning for security patterns...")
    security_findings = scan_security(diff)
    
    print(f"🤖 Generating {args.engine.capitalize()} review...")
    review = analyze_diff(diff, security_findings, engine=args.engine, mock=args.mock)
    
    if args.output:
        with open(args.output, "w") as f:
            f.write(review)
        print(f"✅ Review saved to {args.output}")
    else:
        print("\n" + "="*50)
        print(review)
        print("="*50)

if __name__ == "__main__":
    main()
