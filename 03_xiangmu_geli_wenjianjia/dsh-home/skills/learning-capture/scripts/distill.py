#!/usr/bin/env python3
"""
Learning Distillation - Cluster learnings and generate skill drafts
Runs daily via auto-skill-distill cron or manually.
"""

import re
import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from typing import List, Dict

LEARNINGS_DIR = Path.home() / ".learnings"
SKILLS_DIR = Path("/home/user01/.hermes/skills")
AUTO_GEN_DIR = SKILLS_DIR / "auto-generated"

# Distillation rules
MIN_OCCURRENCES_FOR_SKILL = 3  # Same category + similar context
MIN_ERRORS_FOR_TROUBLESHOOTING = 2  # Same error pattern
FEATURE_AGE_DAYS = 7  # High-priority feature pending this long


def read_learnings_file(filepath: Path) -> List[Dict]:
    """Parse LEARNINGS.md / ERRORS.md / FEATURES.md into structured entries."""
    if not filepath.exists():
        return []
    
    content = filepath.read_text(encoding='utf-8')
    entries = []
    
    # Split by "## YYYY-MM-DD"
    pattern = r'## (\d{4}-\d{2}-\d{2} \d{2}:\d{2}) — ([^\n]+)\n(.*?)(?=\n## |\Z)'
    matches = re.findall(pattern, content, re.DOTALL)
    
    for timestamp_str, header, body in matches:
        entry = {"timestamp": timestamp_str, "header": header.strip(), "body": body.strip()}
        
        # Extract fields
        for line in body.split('\n'):
            if line.startswith('**') and '**:' in line:
                key = line.split('**:')[0][2:].strip().lower().replace(' ', '_')
                value = line.split('**:', 1)[1].strip()
                entry[key] = value
        
        entries.append(entry)
    
    return entries


def cluster_learnings(learnings: List[Dict]) -> Dict[str, List[Dict]]:
    """Group learnings by category + similar context (simple keyword overlap)."""
    clusters = defaultdict(list)
    
    for entry in learnings:
        category = entry.get('category', '').strip() or entry.get('status', '').strip()
        context = entry.get('context', '').lower()
        
        # Simple clustering: category + first 2 words of context
        context_words = context.split()[:3]
        cluster_key = f"{category}:{' '.join(context_words)}"
        
        clusters[cluster_key].append(entry)
    
    # Filter clusters with enough occurrences
    return {k: v for k, v in clusters.items() if len(v) >= MIN_OCCURRENCES_FOR_SKILL}


def cluster_errors(errors: List[Dict]) -> Dict[str, List[Dict]]:
    """Group errors by similar error message."""
    clusters = defaultdict(list)
    
    for entry in errors:
        error_msg = entry.get('error', '').lower()
        # Extract error type (first 5 words)
        error_type = ' '.join(error_msg.split()[:5])
        clusters[error_type].append(entry)
    
    return {k: v for k, v in clusters.items() if len(v) >= MIN_ERRORS_FOR_TROUBLESHOOTING}


def generate_skill_name(category: str, context: str) -> str:
    """Generate a valid skill name from category and context."""
    # Extract key terms
    words = re.findall(r'[a-zA-Z]+', context.lower())
    key_words = [w for w in words if w not in ['the', 'and', 'or', 'to', 'for', 'with', 'using', 'session', 'unknown']][:3]
    name = f"{category}-{'-'.join(key_words)}" if key_words else category
    return re.sub(r'[^a-z0-9-]', '', name.lower())


def generate_skill_draft(cluster_key: str, entries: List[Dict], skill_type: str) -> str:
    """Generate a SKILL.md draft from a cluster."""
    category = cluster_key.split(':')[0]
    context = ' '.join(cluster_key.split(':')[1:]) if ':' in cluster_key else ''
    skill_name = generate_skill_name(category, context)
    
    # Aggregate learnings
    learnings_text = '\n'.join([f"- {e.get('learning', e.get('insight', 'N/A'))}" for e in entries[:5]])
    
    if skill_type == "learning":
        desc = f"Auto-generated from {len(entries)} recurring {category} learnings about {context}"
        usage = f"""## When to Use
- {category.capitalize()} triggered in context: {context}
- Similar situations where this pattern applies

## Aggregated Learnings
{learnings_text}

## Source
Auto-distilled from `.learnings/LEARNINGS.md` on {datetime.now().strftime('%Y-%m-%d')}
- Cluster: {cluster_key}
- Occurrences: {len(entries)}
"""
    else:  # troubleshooting
        desc = f"Troubleshooting guide for recurring error: {cluster_key}"
        fixes = [e.get('fix', '') for e in entries if e.get('fix')]
        fixes_text = '\n'.join([f"- {f}" for f in fixes if f]) or "- [No fix recorded yet]"
        usage = f"""## Error Pattern
{cluster_key}

## Known Fixes
{fixes_text}

## Source
Auto-distilled from `.learnings/ERRORS.md` on {datetime.now().strftime('%Y-%m-%d')}
- Occurrences: {len(entries)}
"""
    
    draft = f"""---
name: {skill_name}
description: "{desc}"
auto_generated: true
source_cluster: "{cluster_key}"
occurrences: {len(entries)}
generated_at: "{datetime.now().isoformat()}"
---

# {skill_name.replace('-', ' ').title()}

{desc}

{usage}

## TODO
- [ ] Review and refine description
- [ ] Add concrete usage examples
- [ ] Add scripts/references if applicable
- [ ] Move to proper skill directory (remove auto-generated/)
- [ ] Update source learnings with **Status**: promoted_to_skill
"""
    return draft, skill_name


def run_distillation():
    """Main distillation process."""
    print("🔬 Starting learning distillation...")
    
    # Read all learning files
    learnings = read_learnings_file(LEARNINGS_DIR / "LEARNINGS.md")
    errors = read_learnings_file(LEARNINGS_DIR / "ERRORS.md")
    features = read_learnings_file(LEARNINGS_DIR / "FEATURES.md")
    
    print(f"  Learnings: {len(learnings)} entries")
    print(f"  Errors: {len(errors)} entries")
    print(f"  Features: {len(features)} entries")
    
    # Cluster learnings
    learning_clusters = cluster_learnings(learnings)
    print(f"  Learning clusters (≥{MIN_OCCURRENCES_FOR_SKILL}): {len(learning_clusters)}")
    
    # Cluster errors
    error_clusters = cluster_errors(errors)
    print(f"  Error clusters (≥{MIN_ERRORS_FOR_TROUBLESHOOTING}): {len(error_clusters)}")
    
    # Check stale high-priority features
    stale_features = []
    for feat in features:
        if feat.get('priority') == 'high' and feat.get('status') == 'pending':
            try:
                ts = datetime.strptime(feat['timestamp'], "%Y-%m-%d %H:%M")
                if datetime.now() - ts > timedelta(days=FEATURE_AGE_DAYS):
                    stale_features.append(feat)
            except:
                pass
    print(f"  Stale high-priority features (>{FEATURE_AGE_DAYS}d): {len(stale_features)}")
    
    # Generate skill drafts
    AUTO_GEN_DIR.mkdir(exist_ok=True)
    generated = 0
    
    for cluster_key, entries in learning_clusters.items():
        draft, skill_name = generate_skill_draft(cluster_key, entries, "learning")
        skill_path = AUTO_GEN_DIR / skill_name
        skill_path.mkdir(exist_ok=True)
        (skill_path / "SKILL.md").write_text(draft, encoding='utf-8')
        print(f"  ✅ Generated learning skill: {skill_name}")
        generated += 1
    
    for cluster_key, entries in error_clusters.items():
        draft, skill_name = generate_skill_draft(cluster_key, entries, "troubleshooting")
        skill_path = AUTO_GEN_DIR / skill_name
        skill_path.mkdir(exist_ok=True)
        (skill_path / "SKILL.md").write_text(draft, encoding='utf-8')
        print(f"  ✅ Generated troubleshooting skill: {skill_name}")
        generated += 1
    
    for feat in stale_features:
        skill_name = generate_skill_name("feature", feat.get('proposed_skill', 'request'))
        draft = f"""---
name: {skill_name}
description: "Auto-generated from stale feature request: {feat.get('request', '')}"
auto_generated: true
source_feature: "{feat.get('request', '')}"
priority: high
generated_at: "{datetime.now().isoformat()}"
---

# {skill_name.replace('-', ' ').title()}

**Original Request**: {feat.get('request', '')}
**Context**: {feat.get('context', '')}
**Proposed Skill**: {feat.get('proposed_skill', 'TBD')}

## TODO
- [ ] Design skill specification
- [ ] Implement core functionality
- [ ] Add tests/examples
- [ ] Move to proper skill directory
- [ ] Update feature status: **Status**: promoted_to_skill
"""
        skill_path = AUTO_GEN_DIR / skill_name
        skill_path.mkdir(exist_ok=True)
        (skill_path / "SKILL.md").write_text(draft, encoding='utf-8')
        print(f"  ✅ Generated feature skill skeleton: {skill_name}")
        generated += 1
    
    print(f"\n🎯 Distillation complete: {generated} skill drafts in {AUTO_GEN_DIR}")
    return generated


if __name__ == "__main__":
    run_distillation()