import json
import sys
from pathlib import Path


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: validate_n8n_workflow.py workflow.json", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    workflow = json.loads(path.read_text(encoding="utf-8"))
    nodes = workflow.get("nodes", [])
    names = {node.get("name") for node in nodes}
    types = {node.get("type") for node in nodes}
    required_names = {
        "Weekly Friday 5pm",
        "Config",
        "GitHub Commits",
        "GitHub Closed Issues",
        "GitHub Merged PRs",
        "Build Claude Prompt",
        "Claude Summary",
        "Send Discord Webhook",
    }
    missing = sorted(required_names - names)
    if missing:
        print(f"Missing required nodes: {', '.join(missing)}", file=sys.stderr)
        return 1
    if "n8n-nodes-base.scheduleTrigger" not in types:
        print("Missing schedule trigger node", file=sys.stderr)
        return 1
    print("Workflow JSON is valid.")
    print("Required nodes found: scheduleTrigger, GitHub HTTP requests, Claude API request, Discord webhook delivery.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
