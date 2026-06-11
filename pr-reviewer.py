#!/usr/bin/env python3
"""PR Reviewer with structured Markdown output"""

import json
import sys
from datetime import datetime

class PRReviewer:
    def __init__(self):
        self.review_categories = {
            "code_quality": {
                "title": "Code Quality",
                "score_range": (1, 5),
                "description": "Overall code quality and readability"
            },
            "security": {
                "title": "Security",
                "score_range": (1, 5),
                "description": "Security vulnerabilities and best practices"
            },
            "performance": {
                "title": "Performance",
                "score_range": (1, 5),
                "description": "Performance implications and optimizations"
            },
            "testing": {
                "title": "Testing",
                "score_range": (1, 5),
                "description": "Test coverage and quality"
            }
        }
    
    def review(self, pr_data):
        """Perform PR review and generate structured output"""
        review = {
            "timestamp": datetime.now().isoformat(),
            "pr_title": pr_data.get("title"),
            "pr_author": pr_data.get("user", {}).get("login"),
            "overall_score": 0,
            "categories": {},
            "recommendations": [],
            "suggestions": []
        }
        
        # Review each category
        for category, details in self.review_categories.items():
            score = self._score_category(pr_data, category)
            review["categories"][category] = {
                "score": score,
                "feedback": self._generate_feedback(pr_data, category, score)
            }
            
        # Calculate overall score
        scores = [v["score"] for v in review["categories"].values()]
        review["overall_score"] = sum(scores) / len(scores)
        
        return review
    
    def _score_category(self, pr_data, category):
        """Score a specific category"""
        # Mock scoring logic
        return 4  # Good score for demo
    
    def _generate_feedback(self, pr_data, category, score):
        """Generate feedback for a category"""
        return f"Good {category} practices observed."

if __name__ == "__main__":
    reviewer = PRReviewer()
    pr_data = json.load(sys.stdin)
    review = reviewer.review(pr_data)
    print(json.dumps(review, indent=2))
