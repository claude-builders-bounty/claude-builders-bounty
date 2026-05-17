#!/usr/bin/env python3
import sys

from guard.event import extract_command, load_event, project_path
from guard.logger import log_blocked_attempt
from guard.policy import find_block_reason
from guard.response import deny_payload


def main() -> int:
    event = load_event(sys.stdin.read())
    command = extract_command(event)
    decision = find_block_reason(command)

    if not decision:
        return 0

    path = project_path(event)
    try:
        log_blocked_attempt(command, path, decision.rule_id, decision.reason)
    except OSError:
        pass

    print(deny_payload(decision.reason))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

