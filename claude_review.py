#!/usr/bin/env python3
"""
Claude PR Reviewer Agent
Analyzes PR diffs and produces structured Markdown reviews.
"""
import argparse
import json
import re
import subprocess
import sys
from typing import Dict, List, Tuple

def fetch_pr_diff(pr_url: str) -> str:
    """Fetch PR diff using gh CLI."""
    # Extract owner/repo/pr_number from URL
    match = re.search(r'github\.com/([^/]+)/([^/]+)/pull/(\d+)', pr_url)
    if not match:
        raise ValueError(f"Invalid PR URL: {pr_url}")
    
    owner, repo, pr_num = match.groups()
    
    # Use gh to get diff
    result = subprocess.run(
        ['gh', 'pr', 'diff', pr_num, '--repo', f'{owner}/{repo}'],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        raise RuntimeError(f"Failed to fetch PR diff: {result.stderr}")
    
    return result.stdout

def analyze_diff(diff: str) -> Dict:
    """Analyze diff and extract metrics."""
    lines = diff.split('\n')
    
    files_changed = set()
    additions = 0
    deletions = 0
    high_risk_patterns = []
    
    # Risk patterns to watch for
    risk_patterns = [
        (r'console\.(log|error|warn|debug)', 'Console statements left in code'),
        (r'todo:\s|fixme:\s', 'TODO/FIXME comments present'),
        (r'eval\s*\(', 'eval() usage'),
        (r'exec\s*\(', 'exec() usage'),
        (r'await.*await', 'Double await pattern'),
        (r'React\.useMemo|useEffect.*\[\]', 'React hooks without dependencies'),
        (r'DROP|TRUNCATE|DELETE.*WHERE', 'SQL destructive operations'),
        (r'process\.env\.(API|SECRET|KEY)', 'Hardcoded environment variable'),
        (r'<script|>on\w+\s*=', 'Inline event handlers/potential XSS'),
    ]
    
    for line in lines:
        # Track file changes
        if line.startswith('diff --git'):
            match = re.search(r'b/(.+)$', line)
            if match:
                files_changed.add(match.group(1))
        
        # Count additions/deletions
        if line.startswith('+') and not line.startswith('+++'):
            additions += 1
        elif line.startswith('-') and not line.startswith('---'):
            deletions += 1
        
        # Check risk patterns
        for pattern, desc in risk_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                high_risk_patterns.append(desc)
    
    total_changes = additions + deletions
    
    # Calculate confidence
    if total_changes <= 50 and not high_risk_patterns:
        confidence = "High"
    elif total_changes <= 200 or high_risk_patterns:
        confidence = "Medium"
    else:
        confidence = "Low"
    
    return {
        "files_changed": len(files_changed),
        "additions": additions,
        "deletions": deletions,
        "total_changes": total_changes,
        "high_risk_patterns": list(set(high_risk_patterns)),
        "confidence": confidence
    }

def generate_review(diff: str, metadata: Dict) -> str:
    """Generate structured Markdown review."""
    # Extract what changed (simplified)
    added_functions = re.findall(r'^\+.*def\s+(\w+)', diff, re.MULTILINE)
    modified_functions = re.findall(r'^\+\s+\w+\s*\(', diff[:1000])
    
    # Build summary
    summary_parts = []
    if metadata['additions'] > metadata['deletions']:
        summary_parts.append(f"adds {metadata['additions']} lines")
    else:
        summary_parts.append(f"modifies {metadata['total_changes']} lines")
    
    if metadata['files_changed'] > 1:
        summary_parts.append(f"across {metadata['files_changed']} files")
    
    summary = f"This PR {' and '.join(summary_parts)}."
    
    # Build risks list
    risks = []
    if metadata['high_risk_patterns']:
        risks.extend(metadata['high_risk_patterns'])
    if metadata['total_changes'] > 300:
        risks.append("Large change size may increase review burden")
    if len(risks) == 0:
        risks.append("No significant risks identified")
    
    # Build suggestions
    suggestions = []
    if 'Console statements left in code' in metadata['high_risk_patterns']:
        suggestions.append("Remove console.log statements before merge")
    if 'TODO/FIXME comments present' in metadata['high_risk_patterns']:
        suggestions.append("Address or convert TODOs to issues")
    if metadata['confidence'] == "Low":
        suggestions.append("Consider breaking into smaller PRs")
    if not suggestions:
        suggestions.append("Code looks good to merge")
    
    # Format output
    output = f"""## PR Review Summary

### Summary
{summary}

### Identified Risks
"""
    for risk in risks:
        output += f"- {risk}\n"
    
    output += f"""
### Improvement Suggestions
"""
    for suggestion in suggestions:
        output += f"- {suggestion}\n"
    
    output += f"""
### Confidence Score: **{metadata['confidence']}**

> Files: {metadata['files_changed']} | Additions: {metadata['additions']} | Deletions: {metadata['deletions']}
"""
    
    return output

def main():
    parser = argparse.ArgumentParser(description='Review a GitHub PR')
    parser.add_argument('--pr', required=True, help='PR URL')
    parser.add_argument('--output', '-o', help='Output file (default: stdout)')
    
    args = parser.parse_args()
    
    try:
        diff = fetch_pr_diff(args.pr)
        metadata = analyze_diff(diff)
        review = generate_review(diff, metadata)
        
        if args.output:
            with open(args.output, 'w') as f:
                f.write(review)
        else:
            print(review)
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()