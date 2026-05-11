import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / "workflows" / "n8n-weekly-dev-summary.json"


def main() -> int:
    workflow = json.loads(WORKFLOW.read_text(encoding="utf-8"))
    for key in ("name", "nodes", "connections", "settings"):
        assert key in workflow, f"missing top-level key: {key}"

    nodes = workflow["nodes"]
    assert isinstance(nodes, list) and nodes, "nodes must be a non-empty list"
    names = {node["name"] for node in nodes}
    required_names = {
        "Weekly Friday 5pm",
        "Build Config",
        "Fetch Commits",
        "Fetch Closed Issues",
        "Fetch Merged PRs",
        "Build Claude Prompt",
        "Generate Claude Summary",
        "Format Delivery Message",
        "Send Slack Summary",
    }
    missing = required_names - names
    assert not missing, f"missing required nodes: {sorted(missing)}"

    assert "claude-sonnet-4-20250514" in WORKFLOW.read_text(encoding="utf-8")
    assert "SLACK_WEBHOOK_URL" in WORKFLOW.read_text(encoding="utf-8")
    assert "SUMMARY_LANGUAGE" in WORKFLOW.read_text(encoding="utf-8")
    assert "GITHUB_REPO" in WORKFLOW.read_text(encoding="utf-8")

    for source, outputs in workflow["connections"].items():
        assert source in names, f"connection source missing node: {source}"
        for branch in outputs.get("main", []):
            for edge in branch:
                assert edge["node"] in names, f"connection target missing node: {edge['node']}"

    print(f"validated {WORKFLOW} ({len(nodes)} nodes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
