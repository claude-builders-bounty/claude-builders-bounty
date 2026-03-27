# Sample Review: dn-institute PR #741

> `claude-review --pr https://github.com/1712n/dn-institute/pull/741`

### Summary
Refactors the Market Health Reporter's system and analysis prompts to produce more structured, evidence-based market manipulation reports. Adds confidence calibration to each metric, introduces multi-metric correlation patterns, and restructures the output format with explicit severity levels.

### Risks
- Significantly longer prompt may increase token usage and API costs per report generation
- The new severity system (Critical / Elevated / Normal) is subjective and not tied to quantitative thresholds, which could lead to inconsistent triage across different datasets

### Suggestions
- Consider adding concrete examples of what "Critical" vs "Elevated" looks like with actual metric values so the model has calibration anchors
- The multi-metric correlation section is good but could reference specific threshold combinations (e.g., "vvcorrelation < 0.3 AND K-S rejection AND volume distribution exponent > 5")

### Confidence
**Medium** -- the prompt changes are well-reasoned but without running them against real market data it's hard to confirm they actually improve output quality vs the originals.
