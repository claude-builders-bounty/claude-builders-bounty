from typing import Dict, Any


def format_review_markdown(review_data: Dict[str, Any]) -> str:
    """
    Renders structured review data into polished Markdown.
    Guarantees conformance with bounty acceptance criteria:
      1. Summary of changes (2–3 sentences)
      2. Identified risks (list)
      3. Improvement suggestions (list)
      4. Confidence score: Low / Medium / High
    """
    metadata = review_data.get("metadata", {})
    pr_title = metadata.get("title", "Pull Request Review")
    pr_number = metadata.get("number", "PR")
    html_url = metadata.get("html_url", "")
    summary = review_data.get("summary", "")
    risks = review_data.get("risks", [])
    suggestions = review_data.get("suggestions", [])
    confidence = review_data.get("confidence", "Medium")
    rationale = review_data.get("confidence_rationale", "")
    metrics = review_data.get("metrics", {})

    confidence_badge = {
        "High": "🟢 **High**",
        "Medium": "🟡 **Medium**",
        "Low": "🔴 **Low**",
    }.get(confidence, f"**{confidence}**")

    risks_md = "\n".join(f"- {r}" for r in risks) if risks else "- No significant risks identified."
    suggestions_md = "\n".join(f"- {s}" for s in suggestions) if suggestions else "- No specific improvements requested."

    lines = [
        f"## 🤖 Claude Code PR Review: #{pr_number} {pr_title}",
        "",
        f"> **Review Target**: [{pr_title}]({html_url})" if html_url else f"> **Review Target**: #{pr_number} {pr_title}",
        f"> **Changeset Impact**: {metrics.get('files_changed', 0)} files changed, +{metrics.get('additions', 0)} additions, -{metrics.get('deletions', 0)} deletions",
        "",
        "### 📝 Summary of Changes",
        summary,
        "",
        "### ⚠️ Identified Risks",
        risks_md,
        "",
        "### 💡 Improvement Suggestions",
        suggestions_md,
        "",
        "### 📊 Confidence Score",
        f"- **Confidence Level**: {confidence_badge}",
        f"- **Assessment Rationale**: {rationale}",
        "",
        "---",
        "*Automated review conducted by [Claude Code Sub-Agent](https://github.com/claude-builders-bounty/claude-builders-bounty) — Powered by Opire.*"
    ]

    return "\n".join(lines)
