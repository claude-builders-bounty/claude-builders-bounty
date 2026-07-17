"""Claude Review Agent - Main logic for PR analysis."""

import subprocess
import json
import re
import sys
from dataclasses import dataclass, field
from typing import List, Optional
from pathlib import Path


@dataclass
class PRData:
    """Represents a GitHub Pull Request."""
    title: str
    body: str
    author: str
    repo: str
    number: int
    url: str
    diff: str
    files_changed: int = 0
    additions: int = 0
    deletions: int = 0


@dataclass
class ReviewResult:
    """Represents the review output."""
    summary: str
    risks: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    confidence: str = "Medium"


class PRReviewer:
    """Main class for reviewing GitHub PRs."""
    
    def __init__(self):
        pass
    
    def fetch_pr_data(self, pr_url: str) -> PRData:
        """Fetch PR data from GitHub."""
        owner, repo, pr_number = self._parse_pr_url(pr_url)
        
        # Get PR info
        pr_info = self._run_gh_command([
            'pr', 'view', str(pr_number),
            '--repo', f'{owner}/{repo}',
            '--json', 'title,body,author,additions,deletions,changedFiles'
        ])
        
        pr_data = json.loads(pr_info)
        
        # Get PR diff
        diff = self._run_gh_command([
            'pr', 'diff', str(pr_number),
            '--repo', f'{owner}/{repo}'
        ])
        
        return PRData(
            title=pr_data.get('title', ''),
            body=pr_data.get('body', ''),
            author=pr_data.get('author', {}).get('login', 'unknown'),
            repo=f'{owner}/{repo}',
            number=pr_number,
            url=pr_url,
            diff=diff,
            files_changed=pr_data.get('changedFiles', 0),
            additions=pr_data.get('additions', 0),
            deletions=pr_data.get('deletions', 0)
        )
    
    def review(self, pr_data: PRData) -> ReviewResult:
        """Analyze PR and generate review."""
        summary = self._generate_summary(pr_data)
        risks = self._identify_risks(pr_data)
        suggestions = self._generate_suggestions(pr_data)
        confidence = self._calculate_confidence(pr_data, risks)
        
        return ReviewResult(
            summary=summary,
            risks=risks,
            suggestions=suggestions,
            confidence=confidence
        )
    
    def _parse_pr_url(self, url: str) -> tuple:
        """Parse GitHub PR URL to extract owner, repo, and PR number."""
        match = re.search(
            r'github\.com/([^/]+)/([^/]+)/pull/(\d+)',
            url
        )
        if match:
            return match.group(1), match.group(2), int(match.group(3))
        
        raise ValueError(f"Invalid PR URL: {url}")
    
    def _run_gh_command(self, args: list) -> str:
        """Run a GitHub CLI command."""
        cmd = ['gh'] + args
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"Error running gh command: {e.stderr}", file=sys.stderr)
            raise
        except FileNotFoundError:
            print("Error: 'gh' CLI not found. Please install GitHub CLI.", file=sys.stderr)
            print("Install: https://cli.github.com/", file=sys.stderr)
            sys.exit(1)
    
    def _generate_summary(self, pr_data: PRData) -> str:
        """Generate a 2-3 sentence summary of changes."""
        diff_lines = pr_data.diff.split('\n')
        
        # Analyze file types
        file_types = set()
        for line in diff_lines:
            if line.startswith('+++ b/'):
                filename = line[6:]
                if filename.endswith('.py'):
                    file_types.add('Python')
                elif filename.endswith('.js') or filename.endswith('.ts'):
                    file_types.add('JavaScript/TypeScript')
                elif filename.endswith('.jsx') or filename.endswith('.tsx'):
                    file_types.add('React')
                elif filename.endswith('.yaml') or filename.endswith('.yml'):
                    file_types.add('YAML')
                elif filename.endswith('.md'):
                    file_types.add('Markdown')
                elif filename.endswith('.json'):
                    file_types.add('JSON')
                else:
                    file_types.add('Other')
        
        # Count new files
        new_files = len([l for l in diff_lines if l.startswith('new file')])
        
        # Build summary
        parts = []
        
        if pr_data.title:
            parts.append(f"This PR implements: {pr_data.title}.")
        
        if file_types:
            parts.append(f"Changes span {', '.join(file_types)} files.")
        
        stats = []
        if pr_data.additions > 0:
            stats.append(f"+{pr_data.additions}")
        if pr_data.deletions > 0:
            stats.append(f"-{pr_data.deletions}")
        if stats:
            parts.append(f"Net change: {', '.join(stats)} lines.")
        
        if new_files > 0:
            parts.append(f"Includes {new_files} new file(s).")
        
        return ' '.join(parts) if parts else f"Review of PR #{pr_data.number} by {pr_data.author}."
    
    def _identify_risks(self, pr_data: PRData) -> List[str]:
        """Identify potential risks in the PR."""
        risks = []
        diff_lower = pr_data.diff.lower()
        
        # Security risks
        if 'password' in diff_lower and '=' in diff_lower:
            risks.append("Potential hardcoded password or credential")
        
        if 'api_key' in diff_lower or 'apikey' in diff_lower:
            risks.append("Potential API key exposure")
        
        if 'token' in diff_lower and ('secret' in diff_lower or 'private' in diff_lower):
            risks.append("Potential secret token in code")
        
        if 'eval(' in diff_lower or 'exec(' in diff_lower:
            risks.append("Use of eval/exec - potential code injection risk")
        
        if 'subprocess' in diff_lower and 'shell=true' in diff_lower:
            risks.append("Shell command with shell=True - potential injection risk")
        
        # Code quality risks
        if 'todo' in diff_lower or 'fixme' in diff_lower:
            risks.append("Contains TODO/FIXME comments - unfinished work")
        
        if 'hack' in diff_lower or 'workaround' in diff_lower:
            risks.append("Contains hack/workaround - may need proper solution")
        
        if 'print(' in pr_data.diff and pr_data.diff.count('print(') > 5:
            risks.append("Multiple print statements - consider using logging")
        
        # Performance risks
        if 'while true' in diff_lower or re.search(r'for\s+\w+\s+in', diff_lower):
            if 'break' not in diff_lower:
                risks.append("Potential infinite loop - no break condition found")
        
        # Large PR risk
        if pr_data.additions + pr_data.deletions > 500:
            risks.append(f"Large PR ({pr_data.additions + pr_data.deletions} lines changed) - consider breaking into smaller PRs")
        
        if not risks:
            risks.append("No significant risks identified")
        
        return risks
    
    def _generate_suggestions(self, pr_data: PRData) -> List[str]:
        """Generate improvement suggestions."""
        suggestions = []
        diff_lower = pr_data.diff.lower()
        
        # Testing suggestions
        if 'test' not in diff_lower and '.test.' not in pr_data.diff:
            suggestions.append("Consider adding unit tests for new functionality")
        
        if 'assert' not in diff_lower and 'expect' not in diff_lower:
            suggestions.append("Add assertions to verify expected behavior")
        
        # Documentation suggestions
        if 'readme' not in diff_lower and pr_data.body == '':
            suggestions.append("Add a clear PR description explaining the changes")
        
        # Code quality suggestions
        if 'error' in diff_lower and 'try' not in diff_lower:
            suggestions.append("Add error handling for potential failure cases")
        
        if 'import' in pr_data.diff and 'from' in pr_data.diff:
            if 'typing' not in diff_lower:
                suggestions.append("Consider adding type hints for better code clarity")
        
        if 'class ' in pr_data.diff and '__doc__' not in diff_lower:
            suggestions.append("Add docstrings to new classes")
        
        if 'def ' in pr_data.diff and '"""' not in pr_data.diff and "'''" not in pr_data.diff:
            suggestions.append("Add docstrings to new functions")
        
        # Security suggestions
        if 'input(' in diff_lower:
            suggestions.append("Validate and sanitize user input")
        
        if 'request.' in diff_lower and 'validate' not in diff_lower:
            suggestions.append("Add input validation for request data")
        
        # Performance suggestions
        if 'for ' in diff_lower and 'range(' in diff_lower:
            suggestions.append("Consider using list comprehensions for better performance")
        
        if not suggestions:
            suggestions.append("Code looks good - no major suggestions")
        
        return suggestions
    
    def _calculate_confidence(self, pr_data: PRData, risks: List[str]) -> str:
        """Calculate confidence score based on analysis."""
        score = 100
        
        # Reduce score for risks
        high_risk_keywords = ['password', 'secret', 'eval(', 'exec(', 'shell=true']
        for risk in risks:
            risk_lower = risk.lower()
            for keyword in high_risk_keywords:
                if keyword in risk_lower:
                    score -= 20
                    break
            else:
                score -= 5
        
        # Reduce score for large PRs
        if pr_data.additions + pr_data.deletions > 300:
            score -= 10
        
        # Reduce score for missing description
        if not pr_data.body:
            score -= 5
        
        # Determine confidence level
        if score >= 80:
            return "High"
        elif score >= 60:
            return "Medium"
        else:
            return "Low"
