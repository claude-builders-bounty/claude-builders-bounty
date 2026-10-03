import json, pathlib

p = pathlib.Path(__file__).with_name("workflow.json")
data = json.loads(p.read_text())
names = {n["name"] for n in data["nodes"]}
for x in [
    "Friday 5pm",
    "Config",
    "GitHub Commits",
    "Closed Issues",
    "Closed PRs",
    "Aggregate Week",
    "Claude Summary",
    "Extract Summary",
    "Send to Slack",
]:
    assert x in names, x

raw = p.read_text()
for x in [
    "claude-sonnet-4-20250514",
    "GITHUB_REPO",
    "GITHUB_TOKEN",
    "SUMMARY_LANGUAGE",
    "SLACK_WEBHOOK_URL",
    "SLACK_CHANNEL",
    "ANTHROPIC_API_KEY",
]:
    assert x in raw, x

expected_chain = {
    "Friday 5pm": "Config",
    "Config": "GitHub Commits",
    "GitHub Commits": "Closed Issues",
    "Closed Issues": "Closed PRs",
    "Closed PRs": "Aggregate Week",
    "Aggregate Week": "Claude Summary",
    "Claude Summary": "Extract Summary",
    "Extract Summary": "Send to Slack",
}
for source, target in expected_chain.items():
    actual = data["connections"][source]["main"][0][0]["node"]
    assert actual == target, (source, actual, target)

trigger = next(n for n in data["nodes"] if n["name"] == "Friday 5pm")
interval = trigger["parameters"]["rule"]["interval"][0]
assert interval["field"] == "weeks"
assert interval["weeksInterval"] == 1
assert interval["triggerAtDay"] == [5]
assert interval["triggerAtHour"] == 17

aggregate = next(n for n in data["nodes"] if n["name"] == "Aggregate Week")
code = aggregate["parameters"]["jsCode"]
assert "merged_at" in code
assert "Date.now()-7*86400000" in code

print("workflow contract: PASS")

verification_path = pathlib.Path(__file__).with_name("verification_workflow.json")
verification = json.loads(verification_path.read_text())
verification_names = [n["name"] for n in verification["nodes"]]
assert verification_names == [
    "Manual verification",
    "Authorized verification fixture",
    "Mock Claude boundary",
    "Verification receipt",
]
verification_raw = verification_path.read_text()
for marker in [
    "verification_mode",
    "external_api_called:false",
    "captured-not-sent",
    "Claude and Slack intentionally mocked",
]:
    assert marker in verification_raw, marker

receipt_path = pathlib.Path(__file__).with_name("verification_receipt.json")
receipt = json.loads(receipt_path.read_text())
assert receipt["runtime"] == "n8n 2.41.6"
assert receipt["status"] == "success"
assert receipt["finished"] is True
assert receipt["output"]["status"] == "PASS"
assert receipt["output"]["delivery"] == "captured-not-sent"
assert set(receipt["node_statuses"].values()) == {"success"}

print("verification contract: PASS")
