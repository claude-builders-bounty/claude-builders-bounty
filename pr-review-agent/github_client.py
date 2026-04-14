"""
GitHub API Client for PR Review Agent
"""

import requests
from typing import Dict, Any


class GitHubClient:
    """GitHub API client for fetching PR information"""
    
    def __init__(self, token: str):
        self.token = token
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self.base_url = "https://api.github.com"
    
    def get_pr_details(self, owner: str, repo: str, pr_number: int) -> Dict[str, Any]:
        """
        Get PR details including title, description, author, etc.
        
        Args:
            owner: Repository owner
            repo: Repository name  
            pr_number: PR number
            
        Returns:
            Dictionary with PR details
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_pr_diff(self, owner: str, repo: str, pr_number: int) -> str:
        """
        Get PR diff content.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            
        Returns:
            PR diff as string
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        response = requests.get(url, headers={**self.headers, "Accept": "application/vnd.github.v3.diff"})
        response.raise_for_status()
        return response.text