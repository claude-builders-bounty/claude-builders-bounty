import json
from pathlib import Path

WORKFLOW_DIR = Path(__file__).resolve().parent.parent / "workflows" / "weekly-dev-summary"
WORKFLOW_JSON_PATH = WORKFLOW_DIR / "n8n-workflow.json"
README_PATH = WORKFLOW_DIR / "README.md"

def test_workflow_files_exist():
    assert WORKFLOW_DIR.is_dir(), "workflows/weekly-dev-summary directory must exist"
    assert WORKFLOW_JSON_PATH.is_file(), "n8n-workflow.json must exist"
    assert README_PATH.is_file(), "README.md must exist"

def test_workflow_json_structure():
    with open(WORKFLOW_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "nodes" in data, "Workflow must contain 'nodes' array"
    assert "connections" in data, "Workflow must contain 'connections' mapping"
    assert len(data["nodes"]) >= 5, "Workflow should contain pipeline nodes"

    node_types = [n.get("type") for n in data["nodes"]]
    node_names = [n.get("name") for n in data["nodes"]]

    # Verify Schedule trigger
    has_trigger = any("schedule" in t.lower() or "cron" in t.lower() for t in node_types)
    assert has_trigger, "Workflow must include a schedule/cron trigger node"

    # Verify GitHub API HTTP node
    workflow_str = json.dumps(data)
    assert "api.github.com" in workflow_str, "Workflow must query api.github.com"
    assert "commits" in workflow_str, "Workflow must fetch commits"
    assert "issues" in workflow_str, "Workflow must fetch issues/PRs"

    # Verify Claude Sonnet 4
    assert "claude-sonnet-4-20250514" in workflow_str, "Workflow must use model claude-sonnet-4-20250514"
    assert "api.anthropic.com" in workflow_str, "Workflow must call api.anthropic.com"

    # Verify configurable variables (repo, language EN/FR, destination)
    assert "LANGUAGE" in workflow_str or "language" in workflow_str, "Must support configurable language (EN/FR)"
    assert "GITHUB_REPO" in workflow_str or "repo" in workflow_str, "Must support configurable repo"
    assert "WEBHOOK_URL" in workflow_str or "webhook" in workflow_str, "Must support delivery webhook"

def test_readme_setup_instructions():
    content = README_PATH.read_text(encoding="utf-8")
    assert "Step 1" in content or "1." in content, "README must include numbered setup steps"
    assert "claude-sonnet-4-20250514" in content, "README must mention claude-sonnet-4-20250514"
    assert "FR" in content and "EN" in content, "README must document language options (EN/FR)"
    assert "Discord" in content or "Slack" in content, "README must document delivery channel"
