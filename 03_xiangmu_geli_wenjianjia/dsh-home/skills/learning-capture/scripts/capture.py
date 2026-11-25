#!/usr/bin/env python3
"""
Learning Capture - Core capture logic
Parses conversation for learning triggers and writes to .learnings/
"""

import re
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Literal

LEARNINGS_DIR = Path.home() / ".learnings"
LEARNINGS_FILE = LEARNINGS_DIR / "LEARNINGS.md"
ERRORS_FILE = LEARNINGS_DIR / "ERRORS.md"
FEATURES_FILE = LEARNINGS_DIR / "FEATURES.md"

TRIGGERS = {
    "correction": [
        r"不对[，,。]?\s*应该",
        r"其实是",
        r"更正[：:]",
        r"错了[，,。]",
        r"应该是",
        r"纠正[：:]",
        r"不，",
        r"不对劲",
    ],
    "insight": [
        r"关键是",
        r"核心在于",
        r"经验是",
        r"发现了",
        r"注意[：:]",
        r"重点是",
        r"要点是",
    ],
    "knowledge_gap": [
        r"不知道",
        r"没见过",
        r"不熟悉",
        r"第一次",
        r"从没",
        r"没接触过",
    ],
    "best_practice": [
        r"最好[是]?",
        r"推荐",
        r"标准做法",
        r"规范",
        r"最佳实践",
        r"建议",
    ],
}

ERROR_PATTERNS = [
    r"报错",
    r"failed",
    r"error[：:]",
    r"exception",
    r"崩了",
    r"炸了",
    r"traceback",
    r"❌",
]

FEATURE_PATTERNS = [
    r"能不能",
    r"有没有办法",
    r"想要",
    r"缺个",
    r"缺一个",
    r"希望有",
    r"能不能加个",
]


def init_learnings_dir():
    """Create .learnings directory and template files if not exist."""
    LEARNINGS_DIR.mkdir(exist_ok=True)
    
    if not LEARNINGS_FILE.exists():
        LEARNINGS_FILE.write_text("""# Learnings

**Categories**: correction | insight | knowledge_gap | best_practice

---

""", encoding='utf-8')
    
    if not ERRORS_FILE.exists():
        ERRORS_FILE.write_text("""# Errors

---

""", encoding='utf-8')
    
    if not FEATURES_FILE.exists():
        FEATURES_FILE.write_text("""# Feature Requests

---

""", encoding='utf-8')


def detect_category(text: str) -> Optional[str]:
    """Detect learning category from text."""
    text_lower = text.lower()
    for category, patterns in TRIGGERS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower):
                return category
    return None


def detect_error(text: str) -> bool:
    """Detect if text contains error indication."""
    text_lower = text.lower()
    for pattern in ERROR_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    return False


def detect_feature(text: str) -> bool:
    """Detect if text contains feature request."""
    text_lower = text.lower()
    for pattern in FEATURE_PATTERNS:
        if re.search(pattern, text_lower):
            return True
    return False


def append_learning(category: str, trigger: str, context: str, learning: str, source: str = "conversation"):
    """Append a learning entry to LEARNINGS.md."""
    init_learnings_dir()
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"""## {timestamp} — {category}
**Trigger**: {trigger}
**Context**: {context}
**Learning**: {learning}
**Source**: {source}
**Status**: active

"""
    
    with open(LEARNINGS_FILE, "a", encoding='utf-8') as f:
        f.write(entry)


def append_error(cmd: str, error: str, fix: str = "", status: str = "open"):
    """Append an error entry to ERRORS.md."""
    init_learnings_dir()
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"""## {timestamp} — terminal command failed
**Command**: {cmd}
**Error**: {error}
**Fix**: {fix}
**Status**: {status}
**Frequency**: 1

"""
    
    with open(ERRORS_FILE, "a", encoding='utf-8') as f:
        f.write(entry)


def append_feature(request: str, context: str, proposed_skill: str = "", priority: str = "medium"):
    """Append a feature request to FEATURES.md."""
    init_learnings_dir()
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"""## {timestamp}
**Request**: {request}
**Context**: {context}
**Proposed Skill**: {proposed_skill}
**Priority**: {priority}
**Status**: pending

"""
    
    with open(FEATURES_FILE, "a", encoding='utf-8') as f:
        f.write(entry)


def parse_and_save(context: dict):
    """
    Main entry: parse a conversation turn for learnings/errors/features.
    
    Args:
        context: {
            'message': user message,
            'response': assistant response,
            'session_id': str,
            'platform': str
        }
    """
    user_msg = context.get('message', '')
    assistant_msg = context.get('response', '')
    combined = f"{user_msg}\n{assistant_msg}"
    
    # Check for corrections/insights in USER message (user correcting assistant)
    category = detect_category(user_msg)
    if category:
        # Extract the learning part (text after trigger)
        trigger_text = user_msg[:200]
        append_learning(
            category=category,
            trigger=trigger_text,
            context=f"Session {context.get('session_id', 'unknown')}",
            learning=assistant_msg[:500] if assistant_msg else "User provided correction",
            source="user_correction"
        )
    
    # Check for errors in assistant response
    if detect_error(assistant_msg):
        # Try to extract command and error
        append_error(
            cmd="[from conversation]",
            error=assistant_msg[:500],
            fix="",
            status="open"
        )
    
    # Check for feature requests in user message
    if detect_feature(user_msg):
        append_feature(
            request=user_msg[:300],
            context=f"Session {context.get('session_id', 'unknown')}",
            proposed_skill="",
            priority="medium"
        )


def get_stats() -> dict:
    """Get statistics of learnings."""
    init_learnings_dir()
    
    stats = {"correction": 0, "insight": 0, "knowledge_gap": 0, "best_practice": 0, "errors": 0, "features": 0}
    
    if LEARNINGS_FILE.exists():
        content = LEARNINGS_FILE.read_text(encoding='utf-8')
        for cat in stats:
            if cat in ["correction", "insight", "knowledge_gap", "best_practice"]:
                stats[cat] = content.count(f" — {cat}")
    
    if ERRORS_FILE.exists():
        content = ERRORS_FILE.read_text(encoding='utf-8')
        stats["errors"] = content.count("## 202")
    
    if FEATURES_FILE.exists():
        content = FEATURES_FILE.read_text(encoding='utf-8')
        stats["features"] = content.count("## 202")
    
    return stats


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python3 capture.py <command> [args]")
        print("Commands: log, error, feature, stats, parse-context")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "log":
        # python3 capture.py log --type correction --trigger "..." --context "..." --learning "..."
        import argparse
        parser = argparse.ArgumentParser()
        parser.add_argument("--type", required=True, choices=["correction", "insight", "knowledge_gap", "best_practice"])
        parser.add_argument("--trigger", required=True)
        parser.add_argument("--context", required=True)
        parser.add_argument("--learning", required=True)
        parser.add_argument("--source", default="manual")
        args = parser.parse_args(sys.argv[2:])
        append_learning(args.type, args.trigger, args.context, args.learning, args.source)
        print(f"Logged {args.type} learning")
    
    elif cmd == "error":
        parser = argparse.ArgumentParser()
        parser.add_argument("--cmd", required=True)
        parser.add_argument("--err", required=True)
        parser.add_argument("--fix", default="")
        parser.add_argument("--status", default="open")
        args = parser.parse_args(sys.argv[2:])
        append_error(args.cmd, args.err, args.fix, args.status)
        print("Logged error")
    
    elif cmd == "feature":
        parser = argparse.ArgumentParser()
        parser.add_argument("--request", required=True)
        parser.add_argument("--context", required=True)
        parser.add_argument("--proposed-skill", default="")
        parser.add_argument("--priority", default="medium")
        args = parser.parse_args(sys.argv[2:])
        append_feature(args.request, args.context, args.proposed_skill, args.priority)
        print("Logged feature request")
    
    elif cmd == "stats":
        stats = get_stats()
        print("Learning Statistics:")
        for k, v in stats.items():
            print(f"  {k}: {v}")
        print(f"  Total: {sum(stats.values())}")
    
    elif cmd == "parse-context":
        # Read context from stdin (JSON)
        import json
        context = json.load(sys.stdin)
        parse_and_save(context)
        print("Parsed and saved")
    
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)