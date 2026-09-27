# PR Reviewer — Opire $150 bounty entry

![cli](https://img.shields.io/badge/CLI-claude--review-blue) ![action](https://img.shields.io/badge/GitHub-Action-green) ![stdlib](https://img.shields.io/badge/stdlib--only-python-lightgrey) ![license](https://img.shields.io/badge/license-MIT-green)

CLI + Claude Code skill + GitHub Action: PR URL vào, structured review ra
(Summary 2–3 câu + Risks kèm severity + Security table + Suggestions + Confidence Low/Medium/High).

## Chạy (cần `gh auth login` 1 lần, stdlib only)

```bash
./claude-review --pr https://github.com/owner/repo/pull/123
./claude-review --pr <url> --depth deep --format json
./claude-review --pr <url> --post-comment   # đăng thẳng thành PR comment
```

| Flag | Giá trị | Mặc định | Ý nghĩa |
|---|---|---|---|
| `--depth` | `quick\|standard\|deep` | `standard` | quick = secrets+size; deep thêm auth-bypass/hash-yếu/XSS |
| `--format` | `md\|json` | `md` | JSON cho pipeline/automation |
| `--post-comment` | — | off | Đăng review thành comment vào PR |

## Đã test trên 2 PR thật (outputs trong `samples/`)
- `samples/pr-278.md` — opencode-ai/opencode#278 (fix nhỏ, +5/-1, sạch, depth standard)
- `samples/pr-230.json` — opencode-ai/opencode#230 (feature lớn, diff 1324 dòng + thiếu test, depth deep + JSON)

## Skill / Action
- `SKILL.md` — Claude Code skill (allowed-tools: Bash, read-only).
- `action.yml` — composite Action: review rồi comment vào PR (inputs: `pr-url`, `depth`, `format`).

## Nộp bounty
Comment `/opire try` vào issue → mở PR gồm code + 2 sample outputs → merge là auto-pay.
