#!/usr/bin/env python3
"""
Claude Code PR Reviewer Agent
CLI tool to review GitHub Pull Requests using gh CLI.
Outputs structured Markdown with summary, risks, suggestions, and confidence.
"""

import argparse
import json
import subprocess
import sys
from typing import List, Dict, Any

def get_pr_diff(pr_url: str) -> str:
    """Extract PR diff using gh CLI."""
    # Parse PR URL to owner/repo/pr_number
    # URL format: https://github.com/owner/repo/pull/123
    parts = pr_url.strip('/').split('/')
    if len(parts) < 7 or parts[2] != 'github.com' or parts[5] != 'pull':
        raise ValueError(f"Invalid PR URL: {pr_url}")
    owner_repo = f"{parts[3]}/{parts[4]}"
    pr_number = parts[6]
    
    # Get diff using gh pr diff
    try:
        result = subprocess.run(
            ['gh', 'pr', 'diff', pr_number, '--repo', owner_repo],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error getting PR diff: {e.stderr}", file=sys.stderr)
        sys.exit(1)

def analyze_diff(diff: str) -> Dict[str, Any]:
    """Analyze diff content for risks and improvements."""
    lines = diff.split('\n')
    
    risks = []
    suggestions = []
    
    # Simple heuristic analysis
    for line in lines:
        if line.startswith('+') and not line.startswith('+++'):
            content = line[1:].strip()
            # Ensure content is a string
            if not isinstance(content, str):
                continue
            
            # Security risks
            try:
                if 'password' in content.lower() and '=' in content:
                    risks.append("Potential hardcoded password detected")
                if 'api_key' in content.lower() or 'apikey' in content.lower():
                    risks.append("Potential hardcoded API key detected")
                if 'token' in content.lower() and '=' in content:
                    risks.append("Potential hardcoded token detected")
            except Exception as e:
                print(f"Debug: content={content!r}, type={type(content)}", file=sys.stderr)
                raise
            
            # SQL injection
            if 'execute(' in content and ('%' in content or '+' in content):
                risks.append("Potential SQL injection vulnerability")
            if 'query(' in content and ('%' in content or '+' in content):
                risks.append("Potential SQL injection vulnerability")
            
            # XSS
            if 'innerHTML' in content or 'document.write' in content:
                risks.append("Potential XSS vulnerability (innerHTML/document.write)")
            if 'eval(' in content:
                risks.append("Use of eval() is dangerous")
            
            # Hardcoded URLs
            if 'http://' in content and 'localhost' not in content:
                risks.append("Hardcoded HTTP URL (should use HTTPS)")
            
            # Error handling
            if 'catch' in content and '{}' in content:
                suggestions.append("Empty catch block - consider proper error handling")
            if 'except:' in content and 'pass' in content:
                suggestions.append("Bare except with pass - consider specific exceptions")
            
            # Performance
            if 'for' in content and 'range' in content and 'len(' in content:
                suggestions.append("Consider using enumerate() instead of range(len())")
            
            # Code quality
            if 'TODO' in content or 'FIXME' in content:
                suggestions.append("TODO/FIXME found - address before merging")
            if 'print(' in content and 'debug' not in content.lower():
                suggestions.append("Consider using logging instead of print()")
    
    # Determine confidence
    if len(risks) > 3:
        confidence = "High"
    elif len(risks) > 0:
        confidence = "Medium"
    else:
        confidence = "Low"
    
    # Generate summary
    summary = f"Changed {len(lines)} lines. "
    if risks:
        summary += f"Found {len(risks)} potential risks. "
    if suggestions:
        summary += f"{len(suggestions)} improvement suggestions."
    
    return {
        "summary": summary,
        "risks": risks,
        "suggestions": suggestions,
        "confidence": confidence
    }

def format_markdown(analysis: Dict[str, Any], pr_url: str) -> str:
    """Format analysis results as structured Markdown."""
    md = f"# PR Review: {pr_url}\n\n"
    md += f"## Summary\n{analysis['summary']}\n\n"
    
    md += "## Risks\n"
    if analysis['risks']:
        for risk in analysis['risks']:
            md += f"- ⚠️ {risk}\n"
    else:
        md += "- No risks identified\n"
    md += "\n"
    
    md += "## Improvement Suggestions\n"
    if analysis['suggestions']:
        for suggestion in analysis['suggestions']:
            md += f"- 💡 {suggestion}\n"
    else:
        md += "- No suggestions\n"
    md += "\n"
    
    md += f"## Confidence\n{analysis['confidence']}\n"
    
    return md

def main():
    parser = argparse.ArgumentParser(description='Claude Code PR Reviewer Agent')
    parser.add_argument('--pr', required=True, help='GitHub PR URL')
    args = parser.parse_args()
    
    try:
        diff = get_pr_diff(args.pr)
        if not diff.strip():
            print("No diff found for this PR.", file=sys.stderr)
            sys.exit(1)
        
        analysis = analyze_diff(diff)
        markdown = format_markdown(analysis, args.pr)
        
        print(markdown)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()