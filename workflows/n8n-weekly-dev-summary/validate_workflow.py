import json
from pathlib import Path


workflow = json.loads(Path("weekly-dev-summary.json").read_text(encoding="utf-8"))
nodes = {node["name"]: node for node in workflow["nodes"]}

required = {
    "Weekly Friday 5pm",
    "Fetch Commits",
    "Fetch Closed Issues",
    "Fetch Closed PRs",
    "Prepare Summary Input",
    "Generate Claude Summary",
    "Format Discord Message",
    "Send Discord Summary",
}

missing = required - set(nodes)
assert not missing, f"missing nodes: {sorted(missing)}"
assert nodes["Weekly Friday 5pm"]["parameters"]["rule"]["interval"][0]["expression"] == "0 17 * * 5"
assert "claude-sonnet-4-20250514" in nodes["Generate Claude Summary"]["parameters"]["jsonBody"]
assert "DISCORD_WEBHOOK_URL" in nodes["Send Discord Summary"]["parameters"]["url"]
assert "SUMMARY_LANGUAGE" in nodes["Prepare Summary Input"]["parameters"]["jsCode"]

print("workflow validation passed")

