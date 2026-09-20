import json
from pathlib import Path


workflow = json.loads(Path("weekly-github-summary.json").read_text(encoding="utf-8"))
names = {node["name"] for node in workflow["nodes"]}
required = {
    "Every Friday at 17:00",
    "GitHub commits",
    "GitHub closed issues",
    "GitHub closed PRs",
    "Generate with Claude Sonnet 4",
    "Deliver to Discord",
}
assert required <= names, names ^ required
for source, branches in workflow["connections"].items():
    assert source in names, f"connection source missing: {source}"
    for branch in branches.values():
        for outputs in branch:
            for output in outputs:
                assert output["node"] in names, f"connection target missing: {output['node']}"
raw = Path("weekly-github-summary.json").read_text(encoding="utf-8")
assert "0 17 * * 5" in raw
assert "claude-sonnet-4-20250514" in raw
for variable in ("GITHUB_REPO", "GITHUB_TOKEN", "ANTHROPIC_API_KEY", "LANGUAGE", "DISCORD_WEBHOOK_URL"):
    assert variable in raw, variable
print(f"workflow smoke test passed: {len(workflow['nodes'])} nodes")
