# Local n8n Execution Evidence

Date: 2026-05-30
n8n version: 2.22.5
Mode: local CLI execution against a real n8n install

Secret-free test substitutions:
- Weekly Schedule was replaced with Manual Test Trigger only in the local test copy.
- GitHub, Anthropic, and Discord endpoints were pointed at a localhost mock server.
- The submitted workflow JSON keeps the real weekly schedule and real GitHub/Anthropic/Discord URL configuration.

Successful nodes:
- Manual Test Trigger
- Set Config
- Prepare Window
- Fetch Commits
- Fetch Closed Issues
- Fetch Closed Pull Requests
- Build Claude Request
- Generate Claude Summary
- Format Discord Message
- Send Discord Summary

Result:
- lastNodeExecuted: Send Discord Summary
- status: success
- commitsCount: 2
- closedIssuesCount: 1
- mergedPullRequestsCount: 1
