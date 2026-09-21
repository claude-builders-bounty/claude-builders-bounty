import json
from pathlib import Path
w=json.loads(Path(__file__).with_name("weekly-dev-summary.json").read_text())
names={n["name"]:n for n in w["nodes"]}
required=["Friday 5pm","Build weekly API requests","Fetch GitHub activity","Build Claude prompt","Generate narrative with Claude","Extract Claude text","Post to Slack"]
assert all(x in names for x in required)
assert names["Friday 5pm"]["parameters"]["rule"]["interval"][0]["expression"]=="0 17 * * 5"
blob=json.dumps(w)
for token in ["GITHUB_REPO","GITHUB_TOKEN","ANTHROPIC_API_KEY","SLACK_WEBHOOK_URL","SUMMARY_LANGUAGE","claude-sonnet-4-20250514","/commits?","/issues?","/pulls?"]:
    assert token in blob, token
print("ok")
