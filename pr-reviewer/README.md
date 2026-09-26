# PR Reviewer — Opire $150 bounty entry

CLI + Claude Code skill + GitHub Action: PR URL vào, Markdown review ra
(Summary 2–3 câu + Risks + Suggestions + Confidence Low/Medium/High).

## Chạy (cần `gh auth login` 1 lần, stdlib only)

```bash
./claude-review --pr https://github.com/owner/repo/pull/123
```

## Đã test trên 2 PR thật (outputs trong `samples/`)
- `samples/pr-278.md` — opencode-ai/opencode#278 (fix nhỏ, +5/-1, sạch)
- `samples/pr-230.md` — opencode-ai/opencode#230 (feature lớn, phát hiện diff 1324 dòng + thiếu test)

## Skill / Action
- `SKILL.md` — Claude Code skill (allowed-tools: Bash, read-only).
- `action.yml` — composite Action: review rồi comment vào PR.

## Nộp bounty
Comment `/opire try` vào issue → mở PR gồm code + 2 sample outputs → merge là auto-pay.
