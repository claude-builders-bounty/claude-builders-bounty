from claude_review.formatter import format_review_markdown


def test_format_review_markdown():
    review_data = {
        "metadata": {
            "title": "Fix database deadlock on booking confirm",
            "number": 42,
            "html_url": "https://github.com/calcom/cal.com/pull/42",
        },
        "summary": "This pull request by @alice updates PostgreSQL query indexing. It reduces deadlock lock contention by replacing raw table locks with row-level SELECT FOR UPDATE SKIP LOCKED. All existing regression tests continue to pass.",
        "risks": [
            "High concurrency lock starvation on legacy nodes without SKIP LOCKED support.",
        ],
        "suggestions": [
            "Verify database migration rollbacks on PostgreSQL 14 and 15 staging instances.",
        ],
        "confidence": "High",
        "confidence_rationale": "Well-scoped changes with dedicated regression tests.",
        "metrics": {
            "files_changed": 3,
            "additions": 45,
            "deletions": 12,
        }
    }

    md = format_review_markdown(review_data)

    assert "## 🤖 Claude Code PR Review: #42 Fix database deadlock on booking confirm" in md
    assert "### 📝 Summary of Changes" in md
    assert "### ⚠️ Identified Risks" in md
    assert "### 💡 Improvement Suggestions" in md
    assert "### 📊 Confidence Score" in md
    assert "🟢 **High**" in md
    assert "High concurrency lock starvation" in md
    assert "Verify database migration rollbacks" in md
