"""
Claude API Client for PR Review Agent
"""

import requests
from typing import Dict, Any


class ClaudeClient:
    """Claude API client for analyzing PR diffs"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        self.base_url = "https://api.anthropic.com/v1"
    
    def analyze_pr_diff(self, pr_diff: str, pr_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze PR diff using Claude and generate structured review.
        
        Args:
            pr_diff: PR diff content
            pr_details: PR details from GitHub
            
        Returns:
            Structured review data
        """
        # Truncate diff if too long (Claude context limit)
        max_diff_length = 100000
        truncated_diff = pr_diff[:max_diff_length] + ("..." if len(pr_diff) > max_diff_length else "")
        
        prompt = f"""You are a senior software engineer reviewing a pull request. 
Analyze the code changes and provide a structured review.

PR Details:
- Title: {pr_details.get('title', 'N/A')}
- Author: {pr_details.get('user', {}).get('login', 'N/A')}
- Description: {pr_details.get('body', 'N/A')}

Code Changes (diff format):
{truncated_diff}

Provide your review in the following JSON format:
{{
  "summary": "2-3 sentence summary of the changes",
  "risks": ["list", "of", "identified", "risks"],
  "suggestions": ["list", "of", "improvement", "suggestions"],
  "confidence": "Low/Medium/High"
}}

Focus on:
- Code quality and maintainability
- Security vulnerabilities
- Performance issues  
- Best practices violations
- Edge cases and error handling

Be specific and actionable in your feedback."""

        payload = {
            "model": "claude-3-opus-20240229",
            "max_tokens": 1000,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        response = requests.post(f"{self.base_url}/messages", headers=self.headers, json=payload)
        response.raise_for_status()
        
        # Parse Claude's response
        claude_response = response.json()
        content = claude_response["content"][0]["text"]
        
        # Extract JSON from response (Claude might add explanation text)
        import json
        try:
            # Try to parse as JSON directly
            review_data = json.loads(content)
        except json.JSONDecodeError:
            # Extract JSON from markdown code block or text
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                review_data = json.loads(json_match.group())
            else:
                # Fallback: create basic structure
                review_data = {
                    "summary": "Unable to parse Claude response",
                    "risks": ["API response parsing failed"],
                    "suggestions": ["Check Claude API configuration"],
                    "confidence": "Low"
                }
        
        return review_data