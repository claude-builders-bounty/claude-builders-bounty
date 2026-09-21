# Acceptance checklist (Bounty #5)

Maps issue criteria to files in this PR:

| Criterion | Evidence |
|-----------|----------|
| Exportable n8n workflow `.json` | `scripts/` + workflow export under this folder |
| Weekly cron trigger | Documented in `README.md` (Fri 17:00 example) |
| Fetches commits / closed issues / merged PRs | Workflow GitHub nodes + `VERIFICATION.md` |
| Claude API narrative summary | Model id + prompt documented in README |
| Email or Discord/Slack delivery | Destination variables in README |
| Configurable repo / channel / language | README env table |
| Tested on real n8n | `VERIFICATION.md` + `examples/` |
| README ≤5 setup steps | `README.md` |

No Opire bot ack yet on issue #5; this checklist is for maintainer review speed.
