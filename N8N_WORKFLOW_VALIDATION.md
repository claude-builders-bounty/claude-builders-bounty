# Local validation

Validation run: 2026-05-03.

- `weekly-dev-summary-n8n.json` parses successfully as JSON.
- Contains an importable n8n workflow object with `nodes` and `connections`.
- Contains 11 nodes connected from schedule trigger through email delivery.
- Includes weekly schedule trigger node: `Weekly Friday 17:00`.
- Includes GitHub API request nodes:
  - `Fetch commits`
  - `Fetch closed issues and PRs`
  - `Fetch closed PRs`
- Includes Claude API request node: `Generate narrative with Claude` using `claude-sonnet-4-20250514`.
- Includes email delivery node: `Send summary email`.
- Configurable values are read from env vars: `GITHUB_REPO`, `DESTINATION_EMAIL`, `SUMMARY_LANGUAGE`.

Verification command used locally:

```bash
python3 -c "import json; from pathlib import Path; workflow=json.loads(Path('weekly-dev-summary-n8n.json').read_text()); names=[node.get('name') for node in workflow['nodes']]; required=['Weekly Friday 17:00','Fetch commits','Fetch closed issues and PRs','Fetch closed PRs','Generate narrative with Claude','Send summary email']; missing=[name for name in required if name not in names]; assert not missing, missing; assert workflow.get('connections'), 'workflow has no connections'; print(f'OK: {len(names)} nodes, {len(workflow["connections"])} connection groups')"
```

Limit: no live credentialed n8n screenshot was included because this environment does not have a configured n8n instance with GitHub/Anthropic/SMTP secrets. The workflow avoids embedding secrets and uses n8n credentials/environment variables instead.
