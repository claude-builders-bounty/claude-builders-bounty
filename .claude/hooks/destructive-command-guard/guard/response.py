import json


def deny_payload(reason: str) -> str:
    """Build Claude Code's structured PreToolUse denial response."""
    return json.dumps(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        },
        ensure_ascii=True,
    )

