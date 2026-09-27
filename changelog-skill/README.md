# Changelog Skill — Opire $50 bounty entry (issue #1)

![bash](https://img.shields.io/badge/bash-changelog.sh-blue) ![skill](https://img.shields.io/badge/Claude-SKILL.md-purple) ![deps](https://img.shields.io/badge/deps-none-lightgrey)

Bash-only skill: commits từ tag gần nhất vào `CHANGELOG.md` có cấu trúc
(Added / Fixed / Changed / Removed). Không dependency, chạy được trên bash 3.2+ (macOS).

## Chạy (3 bước)

```bash
git clone <repo-này> && cd changelog-skill
bash changelog.sh --repo /path/to/project
cat CHANGELOG.md
```

| Flag | Mặc định | Ý nghĩa |
|---|---|---|
| `--since <tag>` | tag gần nhất (tự tìm) | Chỉ lấy commit sau tag |
| `--out <file>` | `CHANGELOG.md` | File output |
| `--repo <dir>` | `.` | Repo cần sinh changelog |

## Sample thật
`samples/CHANGELOG.harness-sample.md` — chạy trên repo harness (13 commits, phân loại C:12).

## Nộp bounty
Comment `/opire try` vào issue #1 → mở PR gồm script + SKILL.md + sample → merge là auto-pay.
