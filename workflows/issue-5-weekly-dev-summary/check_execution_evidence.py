"""Offline structural check of an owner-supplied n8n execution export.

Never contacts services, reads environment credentials, or prints node payloads.
Passing is NOT authentication of the export or proof of actual Discord receipt.
"""
import argparse
import json
from pathlib import Path


def check(execution, workflow):
    if not isinstance(execution, dict):
        raise ValueError("Expected one execution object")
    if execution.get("status") != "success" or execution.get("finished") is not True:
        raise ValueError("Execution is not finished successfully")
    if not execution.get("startedAt") or not execution.get("stoppedAt"):
        raise ValueError("Execution timestamps are missing")
    data = execution.get("data", {})
    result = data.get("resultData", {})
    if result.get("error"):
        raise ValueError("Execution includes an error")
    snapshot = data.get("workflowData", execution.get("workflowData", {}))
    # Compare executable configuration, not runtime positions/version metadata.
    fields = ("name", "type", "typeVersion", "parameters", "executeOnce",
              "alwaysOutputData", "retryOnFail", "maxTries", "waitBetweenTries")
    def signature(nodes):
        signatures = []
        for node in nodes:
            entry = {k: node[k] for k in fields if k in node}
            # Exports may explicitly serialize defaults. Compare behavior while
            # rejecting snapshots that disable a node or continue after errors.
            for flag in ("disabled", "continueOnFail"):
                value = node.get(flag, False)
                if not isinstance(value, bool):
                    raise ValueError("Invalid execution flag")
                entry[flag] = value
            entry["onError"] = node.get("onError", "stopWorkflow")
            signatures.append(entry)
        return sorted(signatures, key=lambda node: node["name"])
    if signature(snapshot.get("nodes", [])) != signature(workflow["nodes"]):
        raise ValueError("Execution workflow nodes differ from this submission")
    if snapshot.get("connections") != workflow["connections"]:
        raise ValueError("Execution workflow connections differ from this submission")
    runs = result.get("runData", {})
    for node in workflow["nodes"]:
        entries = runs.get(node["name"], [])
        if not entries or any(entry.get("error") or entry.get("executionStatus") != "success"
                              for entry in entries):
            raise ValueError("A required node lacks successful execution data")
    model = runs["Generate Claude Summary"][-1].get("data", {}).get("main", [])
    items = [item for branch in model if branch for item in branch]
    if not any(part.get("type") == "text" and part.get("text", "").strip()
               for item in items for part in item.get("json", {}).get("content", [])):
        raise ValueError("Claude node has no nonempty text response")
    message = runs["Prepare Discord Message"][-1].get("data", {}).get("main", [])
    texts = [item.get("json", {}).get("message", "") for branch in message if branch
             for item in branch]
    if not texts or any(not text.strip() or len(text) > 1900 for text in texts):
        raise ValueError("Discord message is missing or exceeds the delivery boundary")
    return "execution structure matches; owner must attest authenticity and Discord receipt"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("execution", type=Path)
    args = parser.parse_args()
    try:
        workflow = json.loads(Path(__file__).with_name(
            "weekly-github-claude-summary.workflow.json").read_text(encoding="utf-8"))
        print(check(json.loads(args.execution.read_text(encoding="utf-8-sig")), workflow))
    except (ValueError, KeyError, TypeError, AttributeError, OSError):
        # Do not echo exceptions: malformed external payloads can contain secrets.
        parser.exit(1, "Execution evidence rejected: missing, failed, or mismatched data.\n")
